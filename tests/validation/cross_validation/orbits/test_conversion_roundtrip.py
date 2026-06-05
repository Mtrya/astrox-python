#!/usr/bin/env python3
"""Live ASTROX-internal cross-validation for orbit conversions."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits
from tests.validation._support import LiveConfigError, configure_astrox_from_env


SEMI_MAJOR_AXIS_ABS_M = 0.1
ECCENTRICITY_ABS = 2.0e-9
ANGLE_ABS_DEG = 1.0e-6
ARGUMENT_OF_LATITUDE_ABS_DEG = 1.0e-9
POSITION_ABS_M = 1.0e-4
VELOCITY_ABS_M_S = 5.0e-6


@dataclass(frozen=True, kw_only=True)
class RoundtripFailure:
    label: str
    field: str
    error: float
    tolerance: float

    def format(self) -> str:
        return (
            f"{self.label}.{self.field} error {self.error:.12g} "
            f"exceeds tolerance {self.tolerance:.12g}"
        )


class CrossValidationError(Exception):
    """Raised when ASTROX orbit conversions are not internally consistent."""


def leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def inclined_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=7078137.0,
        eccentricity=0.002,
        inclination_deg=51.6,
        argument_of_periapsis_deg=10.0,
        raan_deg=120.0,
        true_anomaly_deg=5.0,
    )


def geo_like_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=42164000.0,
        eccentricity=0.0001,
        inclination_deg=0.2,
        argument_of_periapsis_deg=0.0,
        raan_deg=30.0,
        true_anomaly_deg=20.0,
    )


def eccentric_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=26560000.0,
        eccentricity=0.55,
        inclination_deg=63.4,
        argument_of_periapsis_deg=270.0,
        raan_deg=200.0,
        true_anomaly_deg=30.0,
    )


def cartesian_sample() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=6114454.0,
        y_m=2870352.0,
        z_m=3308542.0,
        vx_m_s=-3548.0,
        vy_m_s=6463.0,
        vz_m_s=1830.0,
    )


def compare_orbit(
    label: str,
    expected: orbits.KeplerianElements,
    actual: orbits.KeplerianElements,
) -> list[RoundtripFailure]:
    checks = [
        (
            "semi_major_axis_m",
            expected.semi_major_axis_m,
            actual.semi_major_axis_m,
            SEMI_MAJOR_AXIS_ABS_M,
        ),
        (
            "eccentricity",
            expected.eccentricity,
            actual.eccentricity,
            ECCENTRICITY_ABS,
        ),
        (
            "inclination_deg",
            expected.inclination_deg,
            actual.inclination_deg,
            ANGLE_ABS_DEG,
        ),
        ("raan_deg", expected.raan_deg, actual.raan_deg, ANGLE_ABS_DEG),
    ]
    failures: list[RoundtripFailure] = []
    for field, expected_value, actual_value, tolerance in checks:
        if field.endswith("_deg"):
            error = angle_error_deg(expected_value, actual_value)
        else:
            error = abs(expected_value - actual_value)
        if error > tolerance:
            failures.append(
                RoundtripFailure(
                    label=label,
                    field=field,
                    error=error,
                    tolerance=tolerance,
                )
            )
    if expected.eccentricity < 0.01:
        expected_arg_latitude = (
            expected.argument_of_periapsis_deg + expected.true_anomaly_deg
        )
        actual_arg_latitude = actual.argument_of_periapsis_deg + actual.true_anomaly_deg
        error = angle_error_deg(expected_arg_latitude, actual_arg_latitude)
        if error > ARGUMENT_OF_LATITUDE_ABS_DEG:
            failures.append(
                RoundtripFailure(
                    label=label,
                    field="argument_of_latitude_deg",
                    error=error,
                    tolerance=ARGUMENT_OF_LATITUDE_ABS_DEG,
                )
            )
    else:
        for field, expected_value, actual_value in [
            (
                "argument_of_periapsis_deg",
                expected.argument_of_periapsis_deg,
                actual.argument_of_periapsis_deg,
            ),
            (
                "true_anomaly_deg",
                expected.true_anomaly_deg,
                actual.true_anomaly_deg,
            ),
        ]:
            error = angle_error_deg(expected_value, actual_value)
            if error > ANGLE_ABS_DEG:
                failures.append(
                    RoundtripFailure(
                        label=label,
                        field=field,
                        error=error,
                        tolerance=ANGLE_ABS_DEG,
                    )
                )
    return failures


def compare_cartesian(
    label: str,
    expected: orbits.CartesianState,
    actual: orbits.CartesianState,
) -> list[RoundtripFailure]:
    checks = [
        ("x_m", expected.x_m, actual.x_m, POSITION_ABS_M),
        ("y_m", expected.y_m, actual.y_m, POSITION_ABS_M),
        ("z_m", expected.z_m, actual.z_m, POSITION_ABS_M),
        ("vx_m_s", expected.vx_m_s, actual.vx_m_s, VELOCITY_ABS_M_S),
        ("vy_m_s", expected.vy_m_s, actual.vy_m_s, VELOCITY_ABS_M_S),
        ("vz_m_s", expected.vz_m_s, actual.vz_m_s, VELOCITY_ABS_M_S),
    ]
    failures: list[RoundtripFailure] = []
    for field, expected_value, actual_value, tolerance in checks:
        error = abs(expected_value - actual_value)
        if error > tolerance:
            failures.append(
                RoundtripFailure(
                    label=label,
                    field=field,
                    error=error,
                    tolerance=tolerance,
                )
            )
    return failures


def angle_error_deg(left: float, right: float) -> float:
    return abs((left - right + 180.0) % 360.0 - 180.0)


def compare_keplerian_cartesian_roundtrip() -> None:
    failures: list[RoundtripFailure] = []
    for label, orbit in [
        ("leo", leo_orbit()),
        ("inclined", inclined_orbit()),
        ("geo_like", geo_like_orbit()),
        ("eccentric", eccentric_orbit()),
    ]:
        state = orbits.keplerian_to_cartesian(orbit)
        roundtrip = orbits.cartesian_to_keplerian(state)
        failures.extend(compare_orbit(label, orbit, roundtrip))

    state = cartesian_sample()
    orbit = orbits.cartesian_to_keplerian(state)
    roundtrip_state = orbits.keplerian_to_cartesian(orbit)
    failures.extend(compare_cartesian("cartesian_sample", state, roundtrip_state))

    if failures:
        raise CrossValidationError("\n".join(failure.format() for failure in failures))


def test_orbit_conversions_are_internally_consistent() -> None:
    configure_astrox_from_env()
    compare_keplerian_cartesian_roundtrip()


def main() -> int:
    try:
        test_orbit_conversions_are_internally_consistent()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
