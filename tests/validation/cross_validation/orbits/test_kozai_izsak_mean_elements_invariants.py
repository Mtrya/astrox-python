#!/usr/bin/env python3
"""Kozai-Izsak mean-element cross-validation against orbital angle invariants."""

# Coverage:
#   Branches:
#     - kozai_izsak_mean_elements: partial
#   Fields:
#     - SemimajorAxis/Eccentricity/Inclination: partial (bounded near osculating input for a representative LEO)
#     - RAAN/ArgOfPerigee/MeanAnomaly: partial (finite angular values checked)
#     - LongitudeOfPerigee: verified against RAAN + ArgOfPerigee modulo 360
#     - MeanLongitude: verified against LongitudeOfPerigee + MeanAnomaly modulo 360
#     - ArgOfLatitude: partial (finite angular value checked; ASTROX convention not fully calibrated)
#   Parameters:
#     - input osculating KeplerianElements: partial for one representative LEO case
#   Comparison:
#     - External: local angular identities for Keplerian mean elements and bounded near-orbit physical invariants
#     - Constants: NEAR_SEMI_MAJOR_AXIS_ABS_M, NEAR_ECCENTRICITY_ABS, NEAR_INCLINATION_ABS_DEG
#     - Tolerances: ANGLE_ABS_DEG plus near-orbit bounds
#   Unresolved:
#     - Full Kozai-Izsak short-period removal has not yet been compared with a Vallado-style independent implementation

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits
from tests.validation._support import LiveConfigError, configure_astrox_from_env


ANGLE_ABS_DEG = 1.0e-9
NEAR_SEMI_MAJOR_AXIS_ABS_M = 2500.0
NEAR_ECCENTRICITY_ABS = 5.0e-4
NEAR_INCLINATION_ABS_DEG = 1.0e-2


class CrossValidationError(Exception):
    """Raised when Kozai-Izsak mean elements violate local invariants."""


def leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def test_kozai_izsak_mean_elements_match_angle_identities() -> None:
    configure_astrox_from_env()
    osculating = leo_orbit()
    mean = orbits.kozai_izsak_mean_elements(osculating)
    failures: list[str] = []
    failures.extend(
        compare_scalar(
            "semi_major_axis_m",
            mean.semi_major_axis_m,
            osculating.semi_major_axis_m,
            NEAR_SEMI_MAJOR_AXIS_ABS_M,
        )
    )
    failures.extend(
        compare_scalar(
            "eccentricity",
            mean.eccentricity,
            osculating.eccentricity,
            NEAR_ECCENTRICITY_ABS,
        )
    )
    failures.extend(
        compare_scalar(
            "inclination_deg",
            mean.inclination_deg,
            osculating.inclination_deg,
            NEAR_INCLINATION_ABS_DEG,
        )
    )
    for field, value in (
        ("argument_of_perigee_deg", mean.argument_of_perigee_deg),
        ("raan_deg", mean.raan_deg),
        ("mean_anomaly_deg", mean.mean_anomaly_deg),
        ("argument_of_latitude_deg", mean.argument_of_latitude_deg),
        ("longitude_of_perigee_deg", mean.longitude_of_perigee_deg),
        ("mean_longitude_deg", mean.mean_longitude_deg),
    ):
        if not math.isfinite(value):
            failures.append(f"{field} is not finite: {value!r}")
    failures.extend(
        compare_angle(
            "longitude_of_perigee_deg",
            mean.longitude_of_perigee_deg,
            mean.raan_deg + mean.argument_of_perigee_deg,
        )
    )
    failures.extend(
        compare_angle(
            "mean_longitude_deg",
            mean.mean_longitude_deg,
            mean.longitude_of_perigee_deg + mean.mean_anomaly_deg,
        )
    )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_scalar(field: str, actual: float, expected: float, tolerance: float) -> list[str]:
    error = abs(actual - expected)
    if error <= tolerance:
        return []
    return [
        f"{field} error {error:.12g} exceeds {tolerance:.12g}; actual={actual:.12g} expected={expected:.12g}"
    ]


def compare_angle(field: str, actual: float, expected: float) -> list[str]:
    error = abs(wrapped_angle_error_deg(actual, expected))
    if error <= ANGLE_ABS_DEG:
        return []
    return [
        f"{field} error {error:.12g} deg exceeds {ANGLE_ABS_DEG:.12g} deg; actual={actual:.12g} expected={expected % 360.0:.12g}"
    ]


def wrapped_angle_error_deg(actual: float, expected: float) -> float:
    return (actual - expected + 180.0) % 360.0 - 180.0


def main() -> int:
    try:
        test_kozai_izsak_mean_elements_match_angle_identities()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
