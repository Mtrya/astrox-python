#!/usr/bin/env python3
"""Live close-approach cross-validation against Skyfield SGP4 geometry."""

# Coverage:
#   Branches:
#     - CA_ComputeV3 with TLE primary and TLE targets: verified for four target
#       mean-anomaly cases and 60-second samples over a 10-minute window
#     - CA_ComputeV4 with CZML primary and TLE targets: verified for three
#       stop-time cases using a 60-second public SGP4 position
#   Fields:
#     - CA_MinRange_Time: verified as the nearest sampled epoch
#     - CA_MinRange: verified against GCRS 3-D separation, rounded to 0.001 km
#     - CA_DeltaV: verified against GCRS relative speed, rounded to 1e-6 km/s
#     - CA_Theta: verified as the TLE inclination difference for V3 and the
#       GCRS angular-momentum angle for V4; V3 is rounded to 0.01 deg and V4
#       to 0.001 deg
#     - CA_Probability: unresolved (no covariance input or independent probability
#       oracle is exposed by the promoted request)
#   Parameters:
#     - target TLE mean anomaly: verified for 130/135/137.7421/140/145 deg;
#       130 deg is also retained as a no-result filter boundary
#     - V3 stop time: verified at 5, 8, and 10 minutes
#     - V4 stop time: verified at 5, 8, and 10 minutes; the final CZML sample
#       is excluded by the observed server interval convention
#   Comparison:
#     - External: Skyfield 1.54 EarthSatellite GCRS state propagation
#     - Constants: checked-in TLEs, UTC epochs, 60-second sample interval
#     - Tolerances: 0.001 km range, 5e-7 km/s relative speed, and the stated
#       decimal precision of the server's angle fields
#
# Calibration notes:
#   - The naive continuous-time interpretation was not used as the maintained
#     oracle: ASTROX reports the nearest one-minute sampled epoch for these
#     requests. A 1-second Skyfield scan confirmed that the reported samples
#     are the nearest values on the server's 60-second grid.
#   - V3 includes the stop sample. V4, when supplied with a public SGP4 CZML
#     position sampled at 60 seconds, reports from the interval ending one step
#     before Stop. The comparison path models that observed boundary convention.
#   - Skyfield GCRS is the comparison frame for range, relative speed, and V4
#     plane angle. V3's plane angle matches the absolute TLE inclination
#     difference instead of the instantaneous GCRS angular-momentum angle.

from __future__ import annotations

import math
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
from skyfield.api import EarthSatellite, load

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import components, conjunction, orbits, propagator  # noqa: E402
from tests.validation._support import configure_astrox_from_env  # noqa: E402


START = "2024-01-01T00:00:00.000Z"
PRIMARY_LINE1 = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995"
)
PRIMARY_LINE2 = (
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456"
)
TARGET_LINE1 = (
    "1 25545U 99999A   24001.00000000  .00000000  00000-0  00000-0 0  9993"
)
TARGET_LINE2_TEMPLATE = (
    "2 25545  51.6264 339.8059 0009386 217.1816 {mean_anomaly:07.4f} "
    "15.52489080    03"
)
SAMPLE_STEP_S = 60
RANGE_ABS_KM = 0.001
RELATIVE_SPEED_ABS_KM_S = 5.0e-7
V3_ANGLE_ABS_DEG = 0.0051
V4_ANGLE_ABS_DEG = 0.00051


class CrossValidationError(Exception):
    """Raised when ASTROX and the Skyfield geometry disagree."""


def tle_checksum(line: str) -> str:
    """Return a TLE line with its checksum recomputed."""
    total = 0
    for character in line[:68]:
        if character.isdigit():
            total += int(character)
        elif character == "-":
            total += 1
    return line[:68] + str(total % 10)


def primary_tle() -> orbits.Tle:
    return orbits.tle(
        line1=PRIMARY_LINE1,
        line2=PRIMARY_LINE2,
        name="ISS",
        catalog_number="25544",
    )


def target_tle(mean_anomaly_deg: float) -> orbits.Tle:
    line2 = tle_checksum(
        TARGET_LINE2_TEMPLATE.format(mean_anomaly=mean_anomaly_deg)
    )
    return orbits.tle(
        line1=TARGET_LINE1,
        line2=line2,
        name=f"probe-{mean_anomaly_deg:g}",
        catalog_number="25545",
    )


def target_satellite(tle: orbits.Tle) -> EarthSatellite:
    timescale = load.timescale(builtin=True)
    return EarthSatellite(tle.line1, tle.line2, tle.catalog_number or "target", timescale)


def sample_offsets(stop_s: int, *, include_stop: bool) -> tuple[int, ...]:
    final = stop_s if include_stop else stop_s - SAMPLE_STEP_S
    return tuple(range(0, final + SAMPLE_STEP_S, SAMPLE_STEP_S))


def sample_state(
    satellite: EarthSatellite,
    offset_s: int,
) -> tuple[np.ndarray, np.ndarray]:
    timescale = load.timescale(builtin=True)
    timestamp = timescale.utc(2024, 1, 1, 0, 0, offset_s)
    state = satellite.at(timestamp)
    return np.asarray(state.position.m), np.asarray(state.velocity.m_per_s)


def nearest_sample(
    primary: EarthSatellite,
    target: EarthSatellite,
    offsets_s: tuple[int, ...],
) -> tuple[int, float, float, float]:
    best: tuple[int, float, float, float] | None = None
    for offset_s in offsets_s:
        primary_position, primary_velocity = sample_state(primary, offset_s)
        target_position, target_velocity = sample_state(target, offset_s)
        relative_position = primary_position - target_position
        relative_velocity = primary_velocity - target_velocity
        range_km = float(np.linalg.norm(relative_position) / 1000.0)
        relative_speed_km_s = float(np.linalg.norm(relative_velocity) / 1000.0)
        primary_h = np.cross(primary_position, primary_velocity)
        target_h = np.cross(target_position, target_velocity)
        plane_angle_deg = math.degrees(
            math.acos(
                float(
                    np.clip(
                        np.dot(primary_h, target_h)
                        / (np.linalg.norm(primary_h) * np.linalg.norm(target_h)),
                        -1.0,
                        1.0,
                    )
                )
            )
        )
        candidate = (offset_s, range_km, relative_speed_km_s, plane_angle_deg)
        if best is None or candidate[1] < best[1]:
            best = candidate
    if best is None:
        raise CrossValidationError("comparison sample set is empty")
    return best


def timestamp_for_offset(offset_s: int) -> str:
    timestamp = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(seconds=offset_s)
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def compare_close_approach(
    actual: conjunction.CloseApproachesResult,
    *,
    expected: tuple[int, float, float, float],
    angle_tolerance_deg: float,
    label: str,
) -> None:
    if not actual.is_success:
        raise CrossValidationError(f"{label} returned IsSuccess=false: {actual.message}")
    if len(actual.results) != 1:
        raise CrossValidationError(
            f"{label} returned {len(actual.results)} results; expected one"
        )
    result = actual.results[0]
    expected_offset_s, expected_range_km, expected_speed_km_s, expected_angle_deg = expected
    if result.min_range_time != timestamp_for_offset(expected_offset_s):
        raise CrossValidationError(
            f"{label} TCA={result.min_range_time!r}, expected "
            f"{timestamp_for_offset(expected_offset_s)!r}"
        )
    range_error_km = abs(result.min_range_km - expected_range_km)
    if range_error_km > RANGE_ABS_KM:
        raise CrossValidationError(
            f"{label} range error {range_error_km:.12g} km exceeds "
            f"{RANGE_ABS_KM:.12g} km"
        )
    speed_error_km_s = abs(result.relative_speed_km_s - expected_speed_km_s)
    if speed_error_km_s > RELATIVE_SPEED_ABS_KM_S:
        raise CrossValidationError(
            f"{label} relative-speed error {speed_error_km_s:.12g} km/s exceeds "
            f"{RELATIVE_SPEED_ABS_KM_S:.12g} km/s"
        )
    angle_error_deg = abs(result.orbital_plane_angle_deg - expected_angle_deg)
    if angle_error_deg > angle_tolerance_deg:
        raise CrossValidationError(
            f"{label} plane-angle error {angle_error_deg:.12g} deg exceeds "
            f"{angle_tolerance_deg:.12g} deg"
        )


def compare_v3_case(
    mean_anomaly_deg: float,
    *,
    stop_s: str = "2024-01-01T00:10:00.000Z",
    stop_s_seconds: int = 600,
) -> None:
    target = target_tle(mean_anomaly_deg)
    result = conjunction.find_tle_close_approaches(
        start=START,
        stop=stop_s,
        tle=primary_tle(),
        targets=[target],
        tol_max_distance_km=1000.0,
        tol_cross_dt_s=1000.0,
        tol_theta_deg=180.0,
        tol_dh_km=1000.0,
    )
    primary = EarthSatellite(
        PRIMARY_LINE1,
        PRIMARY_LINE2,
        "25544",
        load.timescale(builtin=True),
    )
    target_satellite_value = target_satellite(target)
    expected_sample = nearest_sample(
        primary,
        target_satellite_value,
        sample_offsets(stop_s_seconds, include_stop=True),
    )
    expected = (
        expected_sample[0],
        expected_sample[1],
        expected_sample[2],
        abs(primary.model.inclo - target_satellite_value.model.inclo)
        * 180.0
        / math.pi,
    )
    compare_close_approach(
        result,
        expected=expected,
        angle_tolerance_deg=V3_ANGLE_ABS_DEG,
        label=f"CA V3 mean_anomaly={mean_anomaly_deg:g}, stop={stop_s}",
    )


def test_ca_v3_matches_skyfield_sampled_close_approach() -> None:
    configure_astrox_from_env()
    for mean_anomaly_deg in (135.0, 137.7421, 140.0, 145.0):
        compare_v3_case(mean_anomaly_deg)
    for stop_s, stop_s_seconds in (
        ("2024-01-01T00:05:00.000Z", 300),
        ("2024-01-01T00:08:00.000Z", 480),
        ("2024-01-01T00:10:00.000Z", 600),
    ):
        compare_v3_case(
            137.7421,
            stop_s=stop_s,
            stop_s_seconds=stop_s_seconds,
        )


def propagated_czml_position(stop: str) -> components.CzmlPosition:
    _, position = propagator.sgp4(
        start=START,
        stop=stop,
        step_s=float(SAMPLE_STEP_S),
        tle=primary_tle(),
    )
    return components.czml_position(
        epoch=position.epoch,
        central_body=position.central_body,
        interpolation_algorithm=position.interpolation_algorithm,
        interpolation_degree=position.interpolation_degree,
        reference_frame=position.reference_frame,
        cartesian_velocity=position.cartesian_velocity,
    )


def compare_v4_case(stop_s: str, stop_s_seconds: int) -> None:
    target = target_tle(137.7421)
    result = conjunction.find_czml_close_approaches(
        start=START,
        stop=stop_s,
        position=propagated_czml_position(stop_s),
        targets=[target],
        tol_max_distance_km=1000.0,
    )
    primary = EarthSatellite(PRIMARY_LINE1, PRIMARY_LINE2, "25544", load.timescale(builtin=True))
    expected = nearest_sample(
        primary,
        target_satellite(target),
        sample_offsets(stop_s_seconds, include_stop=False),
    )
    compare_close_approach(
        result,
        expected=expected,
        angle_tolerance_deg=V4_ANGLE_ABS_DEG,
        label=f"CA V4 stop={stop_s}",
    )


def test_ca_v3_no_result_filter_boundary() -> None:
    configure_astrox_from_env()
    result = conjunction.find_tle_close_approaches(
        start=START,
        stop="2024-01-01T00:10:00.000Z",
        tle=primary_tle(),
        targets=[target_tle(130.0)],
        tol_max_distance_km=1000.0,
        tol_cross_dt_s=1000.0,
        tol_theta_deg=180.0,
        tol_dh_km=1000.0,
    )
    if result.total_number != 1 or result.results:
        raise CrossValidationError(
            "CA V3 mean_anomaly=130 did not preserve the observed filtered-empty result"
        )


def test_ca_v4_matches_skyfield_czml_sample_boundary() -> None:
    configure_astrox_from_env()
    for stop_s, stop_s_seconds in (
        ("2024-01-01T00:05:00.000Z", 300),
        ("2024-01-01T00:08:00.000Z", 480),
        ("2024-01-01T00:10:00.000Z", 600),
    ):
        compare_v4_case(stop_s, stop_s_seconds)


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "CA_Probability remains unresolved: the promoted requests expose no "
        "covariance or collision-probability oracle, and live zero values alone "
        "cannot establish probability semantics."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_ca_collision_probability_remains_unresolved() -> None:
    configure_astrox_from_env()
    result = conjunction.find_tle_close_approaches(
        start=START,
        stop="2024-01-01T00:10:00.000Z",
        tle=primary_tle(),
        targets=[target_tle(137.7421)],
        tol_max_distance_km=1000.0,
        tol_cross_dt_s=1000.0,
        tol_theta_deg=180.0,
        tol_dh_km=1000.0,
    )
    if not result.results:
        raise CrossValidationError("CA probability case returned no result")
    raise CrossValidationError(
        "CA_Probability has no independent covariance-based comparison path"
    )


def main() -> int:
    try:
        configure_astrox_from_env()
        test_ca_v3_matches_skyfield_sampled_close_approach()
        test_ca_v3_no_result_filter_boundary()
        test_ca_v4_matches_skyfield_czml_sample_boundary()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=3")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
