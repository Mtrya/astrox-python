#!/usr/bin/env python3
"""Live multi-SGP4 cross-validation between ASTROX and Skyfield."""

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
TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
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


def skyfield_elements() -> ElementSample:
    timescale = load.timescale(builtin=True)
    satellite = EarthSatellite(
        TLE_LINES[0],
        TLE_LINES[1],
        SATELLITE_NUMBER,
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
            TLE_LINES,
            TLE_LINES,
        ],
    )
    expected = skyfield_elements()
    failures: list[str] = []
    for index, element in enumerate(actual):
        failures.extend(compare_elements(f"multi_sgp4[{index}]", expected, element))
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
