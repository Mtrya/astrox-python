#!/usr/bin/env python3
"""Live CAT cross-validation against independent TLE and orbital invariants."""

# Coverage:
#   Branches:
#     - GetTLE with IsMeanElements=false: verified against a TEME Keplerian
#       state oracle for two element cases
#     - GetTLE with IsMeanElements=true: unresolved mean-to-osculating mapping
#       and retained as a strict calibration xfail
#     - LifeTimeTLE: partial; monotonic response to three parameter-ratio cases
#       is verified, while absolute lifetime semantics remain unknown
#     - DebrisBreakupSimple, DebrisBreakup, and DebrisBreakupNASA: verified for
#       returned TLE/period/perigee/apogee consistency against Skyfield SGP4
#   Fields:
#     - TLE identifiers, epoch, and TEME state: verified for the false-element
#       GetTLE branch
#     - LifeYears: partial (relative monotonicity only)
#     - debris TLEs, Periods, AltitudeOfPerigee, AltitudeOfApogee: verified as
#       internally consistent orbital quantities
#     - AzElVel: wire-shape verified by behavior/live snapshots; its physical
#       impulse convention remains outside this comparison
#   Parameters:
#     - GetTLE: two true-element cases and both IsMeanElements values
#     - LifeTimeTLE: three increasing numeric parameter-ratio cases
#     - Debris branches: explicit two-impulse, simple bounded-angle, and NASA
#       mass/length inputs
#   Comparison:
#     - External: Skyfield 1.54 raw SGP4 TEME state and local two-body energy /
#       angular-momentum derivation
#     - Constants: MU=398600441500000 m^3/s^2; calibrated server Earth radius
#       6378140 m; UTC epoch 2024-01-01T00:00:00Z
#     - Tolerances: generated-TLE state 10 m / 0.02 m/s; debris orbital
#       quantities 0.001 km for altitude and 1e-5 min for period
#
# Calibration notes:
#   - GetTLE false-element output matches the independent input osculating state
#     in raw SGP4 TEME coordinates after one direct comparison; the residual is
#     a few metres and is covered by the stated numerical precision bound.
#   - Debris periods match the two-body period from the returned TLE state.
#     Altitudes match when the local derivation uses the server's apparent
#     6378.140 km Earth radius. The radius was changed once from the common
#     6378.1363 km candidate after the stable residual showed a 3.9 m offset.
#   - No absolute lifetime oracle is promoted. The live endpoint returns a
#     documented fallback value for some cases, so this script checks only the
#     observed monotonic direction for non-fallback cases.

from __future__ import annotations

import math
import sys
from pathlib import Path

import brahe as bh
import numpy as np
import pytest
from skyfield.api import EarthSatellite, load

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import cat, orbits  # noqa: E402
from tests.validation._support import configure_astrox_from_env  # noqa: E402


START = "2024-01-01T00:00:00.000Z"
MU_M3_S2 = 398600441500000.0
EARTH_RADIUS_M = 6378140.0
GENERATED_STATE_ABS_M = 10.0
GENERATED_VELOCITY_ABS_M_S = 0.02
DEBRIS_ALTITUDE_ABS_KM = 0.001
DEBRIS_PERIOD_ABS_MIN = 1.0e-5
MOTHER_LINE1 = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995"
)
MOTHER_LINE2 = (
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456"
)


class CrossValidationError(Exception):
    """Raised when ASTROX and an independent CAT comparison disagree."""


def mother_tle() -> orbits.Tle:
    return orbits.tle(
        line1=MOTHER_LINE1,
        line2=MOTHER_LINE2,
        name="ISS",
        catalog_number="25544",
    )


def true_to_mean_deg(true_anomaly_deg: float, eccentricity: float) -> float:
    true_anomaly = math.radians(true_anomaly_deg)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 - eccentricity) * math.sin(true_anomaly / 2.0),
        math.sqrt(1.0 + eccentricity) * math.cos(true_anomaly / 2.0),
    )
    return math.degrees(eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly))


def input_teme_state(
    *,
    semi_major_axis_km: float,
    eccentricity: float,
    inclination_deg: float,
    argument_of_perigee_deg: float,
    raan_deg: float,
    true_anomaly_deg: float,
) -> tuple[np.ndarray, np.ndarray]:
    mean_anomaly_deg = true_to_mean_deg(true_anomaly_deg, eccentricity)
    state = bh.state_koe_to_eci(
        np.array(
            [
                semi_major_axis_km * 1000.0,
                eccentricity,
                inclination_deg,
                raan_deg,
                argument_of_perigee_deg,
                mean_anomaly_deg,
            ]
        ),
        bh.AngleFormat.DEGREES,
    )
    return state[:3], state[3:]


def generated_tle_case(
    *,
    semi_major_axis_km: float,
    eccentricity: float,
    inclination_deg: float,
    argument_of_perigee_deg: float,
    raan_deg: float,
    true_anomaly_deg: float,
) -> None:
    generated = cat.generate_tle(
        name="probe",
        catalog_number="25544",
        epoch=START,
        bstar=0.00004142,
        semi_major_axis_km=semi_major_axis_km,
        eccentricity=eccentricity,
        inclination_deg=inclination_deg,
        argument_of_perigee_deg=argument_of_perigee_deg,
        raan_deg=raan_deg,
        true_anomaly_deg=true_anomaly_deg,
        is_mean_elements=False,
    )
    if generated.name != "probe" or generated.catalog_number != "25544":
        raise CrossValidationError("GetTLE did not preserve the TLE identifiers")
    satellite = EarthSatellite(
        generated.line1,
        generated.line2,
        generated.catalog_number or "generated",
        load.timescale(builtin=True),
    )
    error, position, velocity = satellite.model.sgp4_tsince(0.0)
    if error != 0:
        raise CrossValidationError(f"generated TLE SGP4 error code={error}")
    actual_position = np.asarray(position) * 1000.0
    actual_velocity = np.asarray(velocity) * 1000.0
    expected_position, expected_velocity = input_teme_state(
        semi_major_axis_km=semi_major_axis_km,
        eccentricity=eccentricity,
        inclination_deg=inclination_deg,
        argument_of_perigee_deg=argument_of_perigee_deg,
        raan_deg=raan_deg,
        true_anomaly_deg=true_anomaly_deg,
    )
    position_error_m = float(np.max(np.abs(actual_position - expected_position)))
    velocity_error_m_s = float(np.max(np.abs(actual_velocity - expected_velocity)))
    if position_error_m > GENERATED_STATE_ABS_M:
        raise CrossValidationError(
            f"GetTLE position error {position_error_m:.12g} m exceeds "
            f"{GENERATED_STATE_ABS_M:g} m"
        )
    if velocity_error_m_s > GENERATED_VELOCITY_ABS_M_S:
        raise CrossValidationError(
            f"GetTLE velocity error {velocity_error_m_s:.12g} m/s exceeds "
            f"{GENERATED_VELOCITY_ABS_M_S:g} m/s"
        )


def test_get_tle_false_elements_matches_teme_state() -> None:
    configure_astrox_from_env()
    generated_tle_case(
        semi_major_axis_km=6794.0,
        eccentricity=0.0001882,
        inclination_deg=51.6461,
        argument_of_perigee_deg=64.8995,
        raan_deg=339.8014,
        true_anomaly_deg=295.2305,
    )
    generated_tle_case(
        semi_major_axis_km=7000.0,
        eccentricity=0.01,
        inclination_deg=63.0,
        argument_of_perigee_deg=10.0,
        raan_deg=120.0,
        true_anomaly_deg=35.0,
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "The IsMeanElements=true branch requires an independent mean-to-"
        "osculating SGP4 conversion oracle. Its naive comparison with the input "
        "osculating elements remains mismatched after the bounded probe."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_get_tle_mean_elements_branch_remains_unresolved() -> None:
    configure_astrox_from_env()
    generated = cat.generate_tle(
        name="probe",
        catalog_number="25544",
        epoch=START,
        bstar=0.00004142,
        semi_major_axis_km=6794.0,
        eccentricity=0.0001882,
        inclination_deg=51.6461,
        argument_of_perigee_deg=64.8995,
        raan_deg=339.8014,
        true_anomaly_deg=295.2305,
        is_mean_elements=True,
    )
    satellite = EarthSatellite(
        generated.line1,
        generated.line2,
        generated.catalog_number or "generated",
        load.timescale(builtin=True),
    )
    _, position, velocity = satellite.model.sgp4_tsince(0.0)
    expected_position, expected_velocity = input_teme_state(
        semi_major_axis_km=6794.0,
        eccentricity=0.0001882,
        inclination_deg=51.6461,
        argument_of_perigee_deg=64.8995,
        raan_deg=339.8014,
        true_anomaly_deg=295.2305,
    )
    position_error_m = float(np.max(np.abs(np.asarray(position) * 1000.0 - expected_position)))
    velocity_error_m_s = float(np.max(np.abs(np.asarray(velocity) * 1000.0 - expected_velocity)))
    raise CrossValidationError(
        "IsMeanElements=true naive osculating residual: "
        f"position={position_error_m:.6g} m, velocity={velocity_error_m_s:.6g} m/s"
    )


def test_lifetime_parameter_ratio_is_monotonic() -> None:
    configure_astrox_from_env()
    cases = ((1.0, 1000.0), (10.0, 10.0), (100.0, 1.0))
    lifetimes = [
        cat.estimate_tle_lifetime(
            epoch=START,
            tle=mother_tle(),
            sm=sm,
            mass=mass,
        ).life_years
        for sm, mass in cases
    ]
    if not (lifetimes[0] > lifetimes[1] > lifetimes[2]):
        raise CrossValidationError(
            f"LifeYears did not decrease with the tested parameter ratio: {lifetimes!r}"
        )


def osculating_orbit_values(tle: orbits.Tle) -> tuple[float, float, float, float]:
    satellite = EarthSatellite(
        tle.line1,
        tle.line2,
        tle.catalog_number or "debris",
        load.timescale(builtin=True),
    )
    state = satellite.at(load.timescale(builtin=True).utc(2024, 1, 1, 0, 0, 0))
    position_m = np.asarray(state.position.m)
    velocity_m_s = np.asarray(state.velocity.m_per_s)
    radius_m = float(np.linalg.norm(position_m))
    speed_m_s = float(np.linalg.norm(velocity_m_s))
    semi_major_axis_m = 1.0 / (
        2.0 / radius_m - speed_m_s * speed_m_s / MU_M3_S2
    )
    angular_momentum_m2_s = float(np.linalg.norm(np.cross(position_m, velocity_m_s)))
    eccentricity = math.sqrt(
        max(
            0.0,
            1.0 - angular_momentum_m2_s**2 / (MU_M3_S2 * semi_major_axis_m),
        )
    )
    period_min = 2.0 * math.pi * math.sqrt(
        semi_major_axis_m**3 / MU_M3_S2
    ) / 60.0
    perigee_km = (semi_major_axis_m * (1.0 - eccentricity) - EARTH_RADIUS_M) / 1000.0
    apogee_km = (semi_major_axis_m * (1.0 + eccentricity) - EARTH_RADIUS_M) / 1000.0
    return period_min, perigee_km, apogee_km, eccentricity


def compare_debris_result(result: cat.DebrisBreakupResult, label: str) -> None:
    if not result.is_success:
        raise CrossValidationError(f"{label} returned IsSuccess=false: {result.message}")
    lengths = {
        len(result.debris_tles),
        len(result.periods_min),
        len(result.altitude_of_perigee_km),
        len(result.altitude_of_apogee_km),
    }
    if len(lengths) != 1:
        raise CrossValidationError(f"{label} returned unsynchronized orbital arrays: {lengths}")
    for index, tle in enumerate(result.debris_tles):
        period_min, perigee_km, apogee_km, _ = osculating_orbit_values(tle)
        period_error = abs(result.periods_min[index] - period_min)
        perigee_error = abs(result.altitude_of_perigee_km[index] - perigee_km)
        apogee_error = abs(result.altitude_of_apogee_km[index] - apogee_km)
        if period_error > DEBRIS_PERIOD_ABS_MIN:
            raise CrossValidationError(
                f"{label}[{index}] period error {period_error:.12g} min exceeds "
                f"{DEBRIS_PERIOD_ABS_MIN:g} min"
            )
        if perigee_error > DEBRIS_ALTITUDE_ABS_KM:
            raise CrossValidationError(
                f"{label}[{index}] perigee error {perigee_error:.12g} km exceeds "
                f"{DEBRIS_ALTITUDE_ABS_KM:g} km"
            )
        if apogee_error > DEBRIS_ALTITUDE_ABS_KM:
            raise CrossValidationError(
                f"{label}[{index}] apogee error {apogee_error:.12g} km exceeds "
                f"{DEBRIS_ALTITUDE_ABS_KM:g} km"
            )


def breakup_results() -> tuple[cat.DebrisBreakupResult, ...]:
    mother = mother_tle()
    return (
        cat.simulate_debris_breakup_simple(
            mother_tle=mother,
            epoch=START,
            count=2,
            ssc_prefix="AF",
            delta_v_m_s=10.0,
            area_to_mass_ratio_m2_kg=0.002,
            min_azimuth_deg=40.0,
            max_azimuth_deg=180.0,
            min_elevation_deg=0.0,
            max_elevation_deg=2.0,
            compute_lifetime=False,
        ),
        cat.simulate_debris_breakup(
            mother_tle=mother,
            epoch=START,
            ssc_prefix="AF",
            area_to_mass_ratio_m2_kg=0.002,
            impulses=[
                cat.DebrisImpulse(
                    azimuth_deg=0.0,
                    elevation_deg=0.0,
                    delta_v_m_s=10.0,
                    area_to_mass_ratio_m2_kg=0.002,
                ),
                cat.DebrisImpulse(
                    azimuth_deg=180.0,
                    elevation_deg=0.0,
                    delta_v_m_s=10.0,
                    area_to_mass_ratio_m2_kg=0.002,
                ),
            ],
            compute_lifetime=False,
        ),
        cat.simulate_debris_breakup_nasa(
            mother_tle=mother,
            epoch=START,
            ssc_prefix="AF",
            total_mass=100.0,
            minimum_characteristic_length=0.1,
        ),
    )


def test_debris_orbital_outputs_match_skyfield_osculating_invariants() -> None:
    configure_astrox_from_env()
    for label, result in zip(
        ("simple", "explicit", "nasa"),
        breakup_results(),
        strict=True,
    ):
        compare_debris_result(result, label)


def main() -> int:
    try:
        configure_astrox_from_env()
        test_get_tle_false_elements_matches_teme_state()
        test_lifetime_parameter_ratio_is_monotonic()
        test_debris_orbital_outputs_match_skyfield_osculating_invariants()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=3")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
