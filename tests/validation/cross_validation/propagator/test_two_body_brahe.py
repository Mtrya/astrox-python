#!/usr/bin/env python3
"""Live two-body cross-validation between ASTROX and Brahe."""

# Coverage:
#   Branches:
#     - two_body Cartesian state propagation: verified
#     - two_body Keplerian element propagation: verified
#   Fields:
#     - Position.cartesian_velocity time/position/velocity samples: verified (Brahe Keplerian propagation)
#     - final Keplerian elements: verified (Brahe propagated state converted back to elements)
#   Parameters:
#     - orbit: partial (LEO and inclined LEO samples)
#     - gravitational_parameter_m3_s2: verified for Brahe Earth GM
#     - start/target/step_s: partial (fixed 10-minute window)
#   Comparison:
#     - External: Brahe two-body state transition and element conversion
#     - Constants: EARTH_MU, START, TARGET, STEP_S
#     - Tolerances: POSITION_ABS_M, VELOCITY_ABS_M_S, SEMI_MAJOR_AXIS_ABS_M, ECCENTRICITY_ABS, ANGLE_ABS_DEG

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
EARTH_MU = bh.GM_EARTH
POSITION_ABS_M = 1.0e-5
VELOCITY_ABS_M_S = 1.0e-8
SEMI_MAJOR_AXIS_ABS_M = 1.0e-5
ECCENTRICITY_ABS = 1.0e-12
ANGLE_ABS_DEG = 1.0e-8


@dataclass(frozen=True, kw_only=True)
class ElementSample:
    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    argument_of_periapsis_deg: float
    raan_deg: float
    true_anomaly_deg: float


class CrossValidationError(Exception):
    """Raised when ASTROX and Brahe disagree."""


def leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
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


def brahe_epoch(value: str) -> bh.Epoch:
    date, time = value.replace("Z", "").split("T")
    year, month, day = (int(part) for part in date.split("-"))
    hour, minute, second = time.split(":")
    return bh.Epoch.from_datetime(
        year,
        month,
        day,
        int(hour),
        int(minute),
        float(second),
        0.0,
        bh.TimeSystem.UTC,
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


def brahe_propagator(
    orbit_epoch: str,
    orbit: orbits.KeplerianElements,
) -> bh.KeplerianPropagator:
    elements = np.array(
        [
            orbit.semi_major_axis_m,
            orbit.eccentricity,
            orbit.inclination_deg,
            orbit.raan_deg,
            orbit.argument_of_periapsis_deg,
            true_to_mean_deg(orbit.true_anomaly_deg, orbit.eccentricity),
        ]
    )
    return bh.KeplerianPropagator.from_keplerian(
        brahe_epoch(orbit_epoch),
        elements,
        bh.AngleFormat.DEGREES,
        STEP_S,
    )


def brahe_elements_at(
    orbit_epoch: str,
    orbit: orbits.KeplerianElements,
    target_epoch: str,
) -> ElementSample:
    elements = brahe_propagator(orbit_epoch, orbit).state_koe_osc(
        brahe_epoch(target_epoch),
        bh.AngleFormat.DEGREES,
    )
    return ElementSample(
        semi_major_axis_m=float(elements[0]),
        eccentricity=float(elements[1]),
        inclination_deg=float(elements[2]),
        raan_deg=float(elements[3] % 360.0),
        argument_of_periapsis_deg=float(elements[4] % 360.0),
        true_anomaly_deg=_true_anomaly_from_brahe_elements_deg(elements),
    )


def _true_anomaly_from_brahe_elements_deg(elements: np.ndarray) -> float:
    return mean_to_true_deg(float(elements[5]), float(elements[1]))


def compare_single_two_body() -> None:
    orbit = leo_orbit()
    _, position = propagator.two_body(
        start=START,
        stop=TARGET,
        orbit_epoch=START,
        orbit=orbit,
        step_s=STEP_S,
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU,
    )
    brahe = brahe_propagator(START, orbit)
    failures: list[str] = []
    for sample_index, offset_s in enumerate((0.0, 300.0, 600.0)):
        expected = brahe.state_eci(brahe_epoch(START) + offset_s)
        start = sample_index * 7
        actual = np.array(position.cartesian_velocity[start + 1 : start + 7])
        position_error_m = float(np.max(np.abs(actual[:3] - expected[:3])))
        velocity_error_m_s = float(np.max(np.abs(actual[3:] - expected[3:])))
        if position_error_m > POSITION_ABS_M:
            failures.append(
                f"two_body position error at offset_s={offset_s:g} is {position_error_m:.12g}, tolerance {POSITION_ABS_M:.12g}"
            )
        if velocity_error_m_s > VELOCITY_ABS_M_S:
            failures.append(
                f"two_body velocity error at offset_s={offset_s:g} is {velocity_error_m_s:.12g}, tolerance {VELOCITY_ABS_M_S:.12g}"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_multi_two_body() -> None:
    cases = [
        (START, leo_orbit()),
        ("2024-01-01T00:03:00.000Z", inclined_orbit()),
    ]
    actual = propagator.multi_two_body(
        epoch=TARGET,
        gravitational_parameter_m3_s2=EARTH_MU,
        states=cases,
    )
    failures: list[str] = []
    for index, ((orbit_epoch, orbit), actual_element) in enumerate(zip(cases, actual, strict=True)):
        expected = brahe_elements_at(orbit_epoch, orbit, TARGET)
        failures.extend(compare_elements(f"multi_two_body[{index}]", expected, actual_element))
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
        ("inclination_deg", expected.inclination_deg, actual.inclination_deg, ANGLE_ABS_DEG),
        ("argument_of_periapsis_deg", expected.argument_of_periapsis_deg, actual.argument_of_periapsis_deg, ANGLE_ABS_DEG),
        ("raan_deg", expected.raan_deg, actual.raan_deg % 360.0, ANGLE_ABS_DEG),
        ("true_anomaly_deg", expected.true_anomaly_deg, actual.true_anomaly_deg % 360.0, ANGLE_ABS_DEG),
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


def test_two_body_matches_brahe_keplerian_propagation() -> None:
    configure_astrox_from_env()
    compare_single_two_body()
    compare_multi_two_body()


def main() -> int:
    try:
        test_two_body_matches_brahe_keplerian_propagation()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=2")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
