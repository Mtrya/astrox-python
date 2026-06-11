#!/usr/bin/env python3
"""Ballistic propagator cross-validation against WGS84 endpoint invariants."""

# Coverage:
#   Branches:
#     - nominal ballistic branch: partial (launch/impact endpoint geometry verified)
#     - DeltaV branch: partial (launch/impact endpoint geometry verified)
#     - DeltaV_MinEcc branch: partial (launch/impact endpoint geometry verified)
#     - ApogeeAlt branch: partial (launch/impact endpoint geometry and sampled maximum WGS84 altitude verified)
#     - TimeOfFlight branch: partial (launch/impact endpoint geometry and final sample time verified)
#   Fields:
#     - Period: unresolved (ASTROX reports 6000 s for all tested branches; this script does not assert an interpretation)
#     - Position.epoch/referenceFrame/interpolationAlgorithm/interpolationDegree: verified for expected response metadata shape
#     - Position.cartesianVelocity first and final positions: verified against independent WGS84 geodetic conversion
#     - Position.cartesianVelocity final sample time for TimeOfFlight: verified
#     - Position.cartesianVelocity maximum WGS84 altitude for ApogeeAlt: partial (sampled trajectory peak is bounded near requested altitude)
#     - velocity components: partial (not solved by the endpoint-geometry oracle)
#   Parameters:
#     - launch/impact latitude/longitude/altitude: verified through endpoint ECEF samples
#     - step_s: partial (sample-grid divisibility checked)
#     - delta_v_m_s: unresolved for velocity interpretation
#     - apogee_altitude_m: partial (sampled maximum altitude is checked within the step-grid sampling residual)
#     - time_of_flight_s: verified through final sample time
#   Comparison:
#     - External: local WGS84 geodetic-to-ECEF and ECEF-to-height derivations
#     - Constants: WGS84_A_M, WGS84_E2
#     - Tolerances: POSITION_ABS_M, ALTITUDE_ABS_M, TIME_ABS_S
#   Unresolved:
#     - ASTROX ballistic velocity convention, exact impact surface convention, continuous apogee interpolation, and Period field meaning need deeper trajectory-model calibration

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


WGS84_A_M = 6378137.0
WGS84_E2 = 6.6943799901413165e-3
POSITION_ABS_M = 15.0
ALTITUDE_ABS_M = 1000.0
TIME_ABS_S = 1.0e-9


class CrossValidationError(Exception):
    """Raised when ballistic output violates an independent physical invariant."""


@dataclass(frozen=True, kw_only=True)
class BallisticCase:
    label: str
    call: Callable[[], tuple[float, propagator.PropagatorPosition]]
    expected_final_time_s: float | None = None
    expected_max_altitude_m: float | None = None


def base_inputs() -> dict[str, float | str]:
    return {
        "start": "2024-01-01T12:00:00.000Z",
        "step_s": 30.0,
        "launch_latitude_deg": 28.5721,
        "launch_longitude_deg": -80.648,
        "launch_altitude_m": 10.0,
        "impact_latitude_deg": 30.0,
        "impact_longitude_deg": -70.0,
        "impact_altitude_m": 0.0,
    }


def ballistic_cases() -> tuple[BallisticCase, ...]:
    base = base_inputs()
    return (
        BallisticCase(label="nominal", call=lambda: propagator.ballistic(**base)),
        BallisticCase(
            label="delta_v",
            call=lambda: propagator.ballistic_delta_v(**base, delta_v_m_s=3000.0),
        ),
        BallisticCase(
            label="delta_v_min_ecc",
            call=lambda: propagator.ballistic_delta_v_min_ecc(**base, delta_v_m_s=3000.0),
        ),
        BallisticCase(
            label="apogee_altitude",
            call=lambda: propagator.ballistic_apogee_altitude(
                **base,
                apogee_altitude_m=200000.0,
            ),
            expected_max_altitude_m=200000.0,
        ),
        BallisticCase(
            label="time_of_flight",
            call=lambda: propagator.ballistic_time_of_flight(
                **base,
                time_of_flight_s=600.0,
            ),
            expected_final_time_s=600.0,
        ),
    )


def test_ballistic_branches_match_wgs84_endpoint_invariants() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in ballistic_cases():
        failures.extend(compare_case(case))
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_case(case: BallisticCase) -> list[str]:
    _, position = case.call()
    rows = cartesian_rows(position.cartesian_velocity)
    failures = compare_metadata(case.label, position)
    failures.extend(compare_step_grid(case.label, rows, step_s=30.0))
    launch = geodetic_to_ecef_m(latitude_deg=28.5721, longitude_deg=-80.648, height_m=10.0)
    impact = geodetic_to_ecef_m(latitude_deg=30.0, longitude_deg=-70.0, height_m=0.0)
    failures.extend(compare_position(f"{case.label} launch", rows[0][1:4], launch))
    failures.extend(compare_position(f"{case.label} impact", rows[-1][1:4], impact))
    if case.expected_final_time_s is not None:
        time_error = abs(rows[-1][0] - case.expected_final_time_s)
        if time_error > TIME_ABS_S:
            failures.append(
                f"{case.label}: final time error {time_error:.12g} s exceeds {TIME_ABS_S:.12g} s"
            )
    if case.expected_max_altitude_m is not None:
        max_altitude = max(ecef_height_m(*row[1:4]) for row in rows)
        altitude_error = abs(max_altitude - case.expected_max_altitude_m)
        if altitude_error > ALTITUDE_ABS_M:
            failures.append(
                f"{case.label}: max altitude error {altitude_error:.12g} m exceeds {ALTITUDE_ABS_M:.12g} m"
            )
    return failures


def compare_metadata(label: str, position: propagator.PropagatorPosition) -> list[str]:
    failures: list[str] = []
    expected = {
        "central_body": "Earth",
        "epoch": "2024-01-01T12:00:00.000Z",
        "reference_frame": "FIXED",
        "interpolation_algorithm": "LAGRANGE",
        "interpolation_degree": 5,
    }
    for field, expected_value in expected.items():
        actual = getattr(position, field)
        if actual != expected_value:
            failures.append(f"{label}: metadata {field}: actual={actual!r} expected={expected_value!r}")
    return failures


def compare_step_grid(
    label: str,
    rows: list[tuple[float, float, float, float, float, float, float]],
    *,
    step_s: float,
) -> list[str]:
    failures: list[str] = []
    for index, row in enumerate(rows):
        quotient = row[0] / step_s
        if abs(quotient - round(quotient)) > 1.0e-9 and index != len(rows) - 1:
            failures.append(f"{label}: sample {index} time {row[0]:.12g} is not on {step_s:.12g} s grid")
    return failures


def cartesian_rows(values: tuple[float, ...]) -> list[tuple[float, float, float, float, float, float, float]]:
    if not values:
        raise CrossValidationError("cartesianVelocity payload is empty")
    if len(values) % 7 != 0:
        raise CrossValidationError(f"cartesianVelocity length {len(values)} is not divisible by 7")
    return [
        (
            float(values[index]),
            float(values[index + 1]),
            float(values[index + 2]),
            float(values[index + 3]),
            float(values[index + 4]),
            float(values[index + 5]),
            float(values[index + 6]),
        )
        for index in range(0, len(values), 7)
    ]


def compare_position(
    label: str,
    actual: tuple[float, float, float],
    expected: tuple[float, float, float],
) -> list[str]:
    error = norm(tuple(actual[index] - expected[index] for index in range(3)))
    if error <= POSITION_ABS_M:
        return []
    return [
        f"{label} ECEF position error {error:.12g} m exceeds {POSITION_ABS_M:.12g} m; actual={actual} expected={expected}"
    ]


def geodetic_to_ecef_m(
    *,
    latitude_deg: float,
    longitude_deg: float,
    height_m: float,
) -> tuple[float, float, float]:
    latitude = math.radians(latitude_deg)
    longitude = math.radians(longitude_deg)
    sin_lat = math.sin(latitude)
    cos_lat = math.cos(latitude)
    radius = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    x_m = (radius + height_m) * cos_lat * math.cos(longitude)
    y_m = (radius + height_m) * cos_lat * math.sin(longitude)
    z_m = (radius * (1.0 - WGS84_E2) + height_m) * sin_lat
    return x_m, y_m, z_m


def ecef_height_m(x_m: float, y_m: float, z_m: float) -> float:
    p_m = math.hypot(x_m, y_m)
    latitude = math.atan2(z_m, p_m * (1.0 - WGS84_E2))
    for _ in range(7):
        radius = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * math.sin(latitude) ** 2)
        latitude = math.atan2(z_m + WGS84_E2 * radius * math.sin(latitude), p_m)
    radius = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * math.sin(latitude) ** 2)
    return p_m / math.cos(latitude) - radius


def norm(values: tuple[float, ...]) -> float:
    return math.sqrt(sum(value * value for value in values))


def main() -> int:
    try:
        test_ballistic_branches_match_wgs84_endpoint_invariants()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=5")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
