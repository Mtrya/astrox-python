#!/usr/bin/env python3
"""Live multi-SGP4 cross-validation between ASTROX and Skyfield."""

# Coverage:
#   Branches:
#     - multi-SGP4 element query for multiple TLEs: verified
#   Fields:
#     - semi_major_axis_m/eccentricity/inclination_deg: verified (Skyfield state converted with Brahe)
#     - raan_deg/argument_of_periapsis_deg/true_anomaly_deg: verified (Skyfield/Brahe element conversion with mean-to-true anomaly)
#   Parameters:
#     - target time: verified for TARGET
#     - TLE list: partial (ISS and Hubble regimes covered)
#   Comparison:
#     - External: Skyfield GCRS states converted to Keplerian elements with Brahe
#     - Constants: ISS_TLE, HUBBLE_TLE, TARGET
#     - Tolerances: SEMI_MAJOR_AXIS_ABS_M, ECCENTRICITY_ABS, INCLINATION_ABS_DEG, ANGLE_ABS_DEG

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import brahe as bh
import numpy as np
from skyfield.api import EarthSatellite, load

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


SEMI_MAJOR_AXIS_ABS_M = 0.02
ECCENTRICITY_ABS = 2.0e-9
INCLINATION_ABS_DEG = 1.0e-6
ANGLE_ABS_DEG = 1.0e-4
TARGET = "2024-01-01T00:10:00.000Z"
SATELLITE_NUMBER = "25544"
ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
HUBBLE_TLE = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)


@dataclass(frozen=True, kw_only=True)
class ElementSample:
    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    argument_of_periapsis_deg: float
    raan_deg: float
    true_anomaly_deg: float


class CrossValidationError(Exception):
    """Raised when ASTROX and Skyfield disagree."""


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


def skyfield_elements(
    tle_lines: tuple[str, str],
    satellite_number: str,
) -> ElementSample:
    timescale = load.timescale(builtin=True)
    satellite = EarthSatellite(
        tle_lines[0],
        tle_lines[1],
        satellite_number,
        timescale,
    )
    state = satellite.at(timescale.utc(2024, 1, 1, 0, 10, 0))
    cartesian = np.array([*state.position.m, *state.velocity.m_per_s])
    elements = bh.state_eci_to_koe(cartesian, bh.AngleFormat.DEGREES)
    return ElementSample(
        semi_major_axis_m=float(elements[0]),
        eccentricity=float(elements[1]),
        inclination_deg=float(elements[2]),
        raan_deg=float(elements[3] % 360.0),
        argument_of_periapsis_deg=float(elements[4] % 360.0),
        true_anomaly_deg=mean_to_true_deg(float(elements[5]), float(elements[1])),
    )


def compare() -> None:
    actual = propagator.multi_sgp4(
        epoch=TARGET,
        tle_sets=[
            ISS_TLE,
            HUBBLE_TLE,
        ],
    )
    expected = [
        skyfield_elements(ISS_TLE, SATELLITE_NUMBER),
        skyfield_elements(HUBBLE_TLE, "20580"),
    ]
    failures: list[str] = []
    for index, (expected_element, actual_element) in enumerate(zip(expected, actual, strict=True)):
        failures.extend(compare_elements(f"multi_sgp4[{index}]", expected_element, actual_element))
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


def test_multi_sgp4_matches_skyfield_gcrs_elements() -> None:
    configure_astrox_from_env()
    compare()


def main() -> int:
    try:
        test_multi_sgp4_matches_skyfield_gcrs_elements()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
