#!/usr/bin/env python3
"""Simple-ascent cross-validation against WGS84 geodetic endpoint geometry."""

# Coverage:
#   Branches:
#     - simple_ascent launch-to-burnout branch: partial
#   Fields:
#     - Period: partial (ASTROX currently reports 6000 s; no independent interpretation is asserted here)
#     - Position.epoch/referenceFrame/interpolationAlgorithm/interpolationDegree: verified for expected response metadata shape
#     - Position.cartesianVelocity sample times: verified for start/stop/step_s sample grid
#     - Position.cartesianVelocity first position: verified against independent WGS84 launch geodetic conversion
#     - Position.cartesianVelocity final position: verified against independent WGS84 burnout geodetic conversion
#     - Position.cartesianVelocity final velocity magnitude: verified against burnout_velocity_m_s
#   Parameters:
#     - start/stop/step_s: verified for the sample grid
#     - launch latitude/longitude/altitude: verified through first ECEF sample
#     - burnout latitude/longitude/altitude/velocity: verified through final ECEF sample and velocity magnitude
#     - central_body: partial (Earth fixed-frame behavior only)
#   Comparison:
#     - External: local WGS84 geodetic-to-ECEF derivation and Euclidean velocity norm
#     - Constants: WGS84_A_M, WGS84_E2
#     - Tolerances: POSITION_ABS_M, SPEED_ABS_M_S, TIME_ABS_S

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


WGS84_A_M = 6378137.0
WGS84_E2 = 6.6943799901413165e-3
POSITION_ABS_M = 2.0e-5
SPEED_ABS_M_S = 1.0e-9
TIME_ABS_S = 1.0e-9


class CrossValidationError(Exception):
    """Raised when simple-ascent output disagrees with independent geometry."""


def test_simple_ascent_matches_wgs84_endpoint_geometry() -> None:
    configure_astrox_from_env()
    _, position = propagator.simple_ascent(
        start="2024-01-01T03:00:00.000Z",
        stop="2024-01-01T03:02:00.000Z",
        step_s=30.0,
        central_body="Earth",
        launch_latitude_deg=40.9575,
        launch_longitude_deg=100.2912,
        launch_altitude_m=1000.0,
        burnout_velocity_m_s=7800.0,
        burnout_latitude_deg=41.3,
        burnout_longitude_deg=101.0,
        burnout_altitude_m=200000.0,
    )
    rows = cartesian_rows(position.cartesian_velocity)
    failures: list[str] = []
    failures.extend(compare_metadata(position))
    failures.extend(compare_sample_times(rows, expected_times_s=[0.0, 30.0, 60.0, 90.0, 120.0]))
    failures.extend(
        compare_position(
            "launch",
            rows[0][1:4],
            geodetic_to_ecef_m(latitude_deg=40.9575, longitude_deg=100.2912, height_m=1000.0),
        )
    )
    failures.extend(
        compare_position(
            "burnout",
            rows[-1][1:4],
            geodetic_to_ecef_m(latitude_deg=41.3, longitude_deg=101.0, height_m=200000.0),
        )
    )
    final_speed = norm(rows[-1][4:7])
    if abs(final_speed - 7800.0) > SPEED_ABS_M_S:
        failures.append(
            f"burnout speed error {abs(final_speed - 7800.0):.12g} m/s exceeds {SPEED_ABS_M_S:.12g} m/s"
        )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_metadata(position: propagator.PropagatorPosition) -> list[str]:
    failures: list[str] = []
    expected = {
        "central_body": "Earth",
        "epoch": "2024-01-01T03:00:00.000Z",
        "reference_frame": "FIXED",
        "interpolation_algorithm": "LAGRANGE",
        "interpolation_degree": 5,
    }
    for field, expected_value in expected.items():
        actual = getattr(position, field)
        if actual != expected_value:
            failures.append(f"metadata {field}: actual={actual!r} expected={expected_value!r}")
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


def compare_sample_times(
    rows: list[tuple[float, float, float, float, float, float, float]],
    *,
    expected_times_s: list[float],
) -> list[str]:
    actual_times = [row[0] for row in rows]
    failures: list[str] = []
    if len(actual_times) != len(expected_times_s):
        failures.append(f"sample count actual={len(actual_times)} expected={len(expected_times_s)}")
        return failures
    for index, (actual, expected) in enumerate(zip(actual_times, expected_times_s, strict=True)):
        if abs(actual - expected) > TIME_ABS_S:
            failures.append(
                f"sample {index} time error {abs(actual - expected):.12g} s exceeds {TIME_ABS_S:.12g} s"
            )
    return failures


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


def norm(values: tuple[float, ...]) -> float:
    return math.sqrt(sum(value * value for value in values))


def main() -> int:
    try:
        test_simple_ascent_matches_wgs84_endpoint_geometry()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
