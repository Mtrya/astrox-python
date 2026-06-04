#!/usr/bin/env python3
"""Live J2 cross-validation against the analytical secular J2 model."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import brahe as bh
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


START = "2024-01-01T00:00:00.000Z"
TARGET = "2024-01-01T00:10:00.000Z"
STEP_S = 300.0
EARTH_MU = 398600441500000.0
EARTH_RADIUS_M = 6378136.3
J2_NORMALIZED_VALUE = 0.000484165143790815
POSITION_ABS_M = 5.0
VELOCITY_ABS_M_S = 5.0e-3
SEMI_MAJOR_AXIS_ABS_M = 1.0e-6
ECCENTRICITY_ABS = 1.0e-12
INCLINATION_ABS_DEG = 1.0e-10
SECULAR_ANGLE_ABS_DEG = 1.0e-4


@dataclass(frozen=True, kw_only=True)
class ElementSample:
    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    argument_of_periapsis_deg: float
    raan_deg: float
    true_anomaly_deg: float


class CrossValidationError(Exception):
    """Raised when ASTROX and the analytical J2 model disagree."""


def leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )


def true_to_mean_deg(true_anomaly_deg: float, eccentricity: float) -> float:
    nu = math.radians(true_anomaly_deg)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 - eccentricity) * math.sin(nu / 2.0),
        math.sqrt(1.0 + eccentricity) * math.cos(nu / 2.0),
    )
    mean_anomaly = eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly)
    return math.degrees(mean_anomaly) % 360.0


def mean_to_true_deg(mean_anomaly_deg: float, eccentricity: float) -> float:
    mean_anomaly = math.radians(mean_anomaly_deg)
    eccentric_anomaly = mean_anomaly
    for _ in range(30):
        eccentric_anomaly -= (
            eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly) - mean_anomaly
        ) / (1.0 - eccentricity * math.cos(eccentric_anomaly))
    true_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 + eccentricity) * math.sin(eccentric_anomaly / 2.0),
        math.sqrt(1.0 - eccentricity) * math.cos(eccentric_anomaly / 2.0),
    )
    return math.degrees(true_anomaly) % 360.0


def analytical_j2_elements(
    orbit: orbits.KeplerianElements,
    offset_s: float,
) -> ElementSample:
    semi_major_axis_m = orbit.semi_major_axis_m
    eccentricity = orbit.eccentricity
    inclination_rad = math.radians(orbit.inclination_deg)
    p = semi_major_axis_m * (1.0 - eccentricity * eccentricity)
    mean_motion_rad_s = math.sqrt(EARTH_MU / semi_major_axis_m**3)
    j2 = math.sqrt(5.0) * J2_NORMALIZED_VALUE
    factor = j2 * (EARTH_RADIUS_M / p) ** 2
    cos_i = math.cos(inclination_rad)

    raan_rate = -1.5 * mean_motion_rad_s * factor * cos_i
    argument_rate = 0.75 * mean_motion_rad_s * factor * (5.0 * cos_i * cos_i - 1.0)
    mean_anomaly_rate = mean_motion_rad_s + (
        0.75
        * mean_motion_rad_s
        * factor
        * math.sqrt(1.0 - eccentricity * eccentricity)
        * (3.0 * cos_i * cos_i - 1.0)
    )
    mean_anomaly_deg = true_to_mean_deg(orbit.true_anomaly_deg, eccentricity)

    return ElementSample(
        semi_major_axis_m=semi_major_axis_m,
        eccentricity=eccentricity,
        inclination_deg=orbit.inclination_deg,
        argument_of_periapsis_deg=(
            orbit.argument_of_periapsis_deg + math.degrees(argument_rate * offset_s)
        )
        % 360.0,
        raan_deg=(orbit.raan_deg + math.degrees(raan_rate * offset_s)) % 360.0,
        true_anomaly_deg=mean_to_true_deg(
            mean_anomaly_deg + math.degrees(mean_anomaly_rate * offset_s),
            eccentricity,
        ),
    )


def elements_to_cartesian(elements: ElementSample) -> np.ndarray:
    mean_anomaly_deg = true_to_mean_deg(
        elements.true_anomaly_deg,
        elements.eccentricity,
    )
    return bh.state_koe_to_eci(
        np.array(
            [
                elements.semi_major_axis_m,
                elements.eccentricity,
                elements.inclination_deg,
                elements.raan_deg,
                elements.argument_of_periapsis_deg,
                mean_anomaly_deg,
            ]
        ),
        bh.AngleFormat.DEGREES,
    )


def compare_single_j2() -> None:
    orbit = leo_orbit()
    _, position = propagator.j2(
        start=START,
        stop=TARGET,
        orbit_epoch=START,
        orbit=orbit,
        step_s=STEP_S,
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU,
        j2_normalized_value=J2_NORMALIZED_VALUE,
        ref_distance_m=EARTH_RADIUS_M,
    )
    failures: list[str] = []
    for sample_index, offset_s in enumerate((0.0, 300.0, 600.0)):
        expected = elements_to_cartesian(analytical_j2_elements(orbit, offset_s))
        start = sample_index * 7
        actual = np.array(position.cartesian_velocity[start + 1 : start + 7])
        position_error_m = float(np.max(np.abs(actual[:3] - expected[:3])))
        velocity_error_m_s = float(np.max(np.abs(actual[3:] - expected[3:])))
        if position_error_m > POSITION_ABS_M:
            failures.append(
                f"j2 position error at offset_s={offset_s:g} is {position_error_m:.12g}, tolerance {POSITION_ABS_M:.12g}"
            )
        if velocity_error_m_s > VELOCITY_ABS_M_S:
            failures.append(
                f"j2 velocity error at offset_s={offset_s:g} is {velocity_error_m_s:.12g}, tolerance {VELOCITY_ABS_M_S:.12g}"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_multi_j2() -> None:
    orbit = leo_orbit()
    actual = propagator.multi_j2(
        epoch=TARGET,
        gravitational_parameter_m3_s2=EARTH_MU,
        states=[(START, orbit)],
    )[0]
    expected = analytical_j2_elements(orbit, 600.0)
    failures = compare_elements("multi_j2[0]", expected, actual)
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_elements(
    label: str,
    expected: ElementSample,
    actual: orbits.KeplerianElements,
) -> list[str]:
    checks = [
        ("semi_major_axis_m", expected.semi_major_axis_m, actual.semi_major_axis_m, SEMI_MAJOR_AXIS_ABS_M),
        ("eccentricity", expected.eccentricity, actual.eccentricity, ECCENTRICITY_ABS),
        ("inclination_deg", expected.inclination_deg, actual.inclination_deg, INCLINATION_ABS_DEG),
        ("argument_of_periapsis_deg", expected.argument_of_periapsis_deg, actual.argument_of_periapsis_deg, SECULAR_ANGLE_ABS_DEG),
        ("raan_deg", expected.raan_deg, actual.raan_deg % 360.0, SECULAR_ANGLE_ABS_DEG),
        ("true_anomaly_deg", expected.true_anomaly_deg, actual.true_anomaly_deg % 360.0, SECULAR_ANGLE_ABS_DEG),
    ]
    failures: list[str] = []
    for field, expected_value, actual_value, tolerance in checks:
        if field.endswith("_deg"):
            error = angle_error_deg(expected_value, actual_value)
        else:
            error = abs(expected_value - actual_value)
        if error > tolerance:
            failures.append(
                f"{label}.{field} error {error:.12g} exceeds tolerance {tolerance:.12g}"
            )
    return failures


def angle_error_deg(left: float, right: float) -> float:
    return abs((left - right + 180.0) % 360.0 - 180.0)


def test_j2_matches_analytical_secular_model() -> None:
    configure_astrox_from_env()
    compare_single_j2()
    compare_multi_j2()


def main() -> int:
    try:
        test_j2_matches_analytical_secular_model()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=2")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
