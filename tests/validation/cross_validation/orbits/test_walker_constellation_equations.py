#!/usr/bin/env python3
"""Walker constellation cross-validation against standard Walker equations."""

# Coverage:
#   Branches:
#     - Walker Delta: verified for plane count, satellites per plane, RAAN spacing, in-plane spacing, and inter-plane phasing
#     - Walker Star: verified for plane count, satellites per plane, RAAN spacing, in-plane spacing, and inter-plane phasing
#     - Walker Custom: verified for plane count, satellites per plane, explicit RAAN spacing, explicit inter-plane true-anomaly spacing, and in-plane spacing
#   Fields:
#     - WalkerSatellites nested plane/satellite shape: verified
#     - SemimajorAxis/Eccentricity/Inclination/ArgumentOfPeriapsis inheritance from seed: verified
#     - RightAscensionOfAscendingNode: verified against standard Walker spacing equations
#     - TrueAnomaly: verified against in-plane spacing plus branch phasing equations
#   Parameters:
#     - seed_orbit: partial (one representative LEO seed)
#     - num_planes/num_sats_per_plane: verified for 3x2 constellation shape
#     - inter_plane_phase_increment: verified for Delta and Star with F=1
#     - inter_plane_true_anomaly_increment_deg/raan_increment_deg: verified for Custom with 30 deg and 60 deg
#   Comparison:
#     - External: local derivation from standard Walker Delta, Star, and custom phasing equations
#     - Constants: no tuned physical constants; all expected values derive from public inputs
#     - Tolerances: ANGLE_ABS_DEG for wrapped angular fields, SCALAR_ABS for inherited scalar elements

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits
from tests.validation._support import LiveConfigError, configure_astrox_from_env


ANGLE_ABS_DEG = 1.0e-9
SCALAR_ABS = 1.0e-9


class CrossValidationError(Exception):
    """Raised when ASTROX Walker geometry disagrees with the local equations."""


@dataclass(frozen=True, kw_only=True)
class WalkerCase:
    label: str
    call: Callable[[], tuple[tuple[orbits.KeplerianElements, ...], ...]]
    expected_raan_spacing_deg: float
    expected_inter_plane_true_anomaly_spacing_deg: float


def seed_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=53.0,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=0.0,
    )


def walker_cases() -> tuple[WalkerCase, ...]:
    seed = seed_orbit()
    num_planes = 3
    num_sats_per_plane = 2
    phase_increment = 1
    return (
        WalkerCase(
            label="delta",
            call=lambda: orbits.walker_delta(
                seed_orbit=seed,
                num_planes=num_planes,
                num_sats_per_plane=num_sats_per_plane,
                inter_plane_phase_increment=phase_increment,
            ),
            expected_raan_spacing_deg=360.0 / num_planes,
            expected_inter_plane_true_anomaly_spacing_deg=360.0
            * phase_increment
            / (num_planes * num_sats_per_plane),
        ),
        WalkerCase(
            label="star",
            call=lambda: orbits.walker_star(
                seed_orbit=seed,
                num_planes=num_planes,
                num_sats_per_plane=num_sats_per_plane,
                inter_plane_phase_increment=phase_increment,
            ),
            expected_raan_spacing_deg=180.0 / num_planes,
            expected_inter_plane_true_anomaly_spacing_deg=360.0
            * phase_increment
            / (num_planes * num_sats_per_plane),
        ),
        WalkerCase(
            label="custom",
            call=lambda: orbits.walker_custom(
                seed_orbit=seed,
                num_planes=num_planes,
                num_sats_per_plane=num_sats_per_plane,
                inter_plane_true_anomaly_increment_deg=30.0,
                raan_increment_deg=60.0,
            ),
            expected_raan_spacing_deg=60.0,
            expected_inter_plane_true_anomaly_spacing_deg=30.0,
        ),
    )


def test_walker_constellations_match_standard_walker_equations() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in walker_cases():
        failures.extend(compare_walker_case(case))
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_walker_case(case: WalkerCase) -> list[str]:
    seed = seed_orbit()
    constellation = case.call()
    failures: list[str] = []
    expected_planes = 3
    expected_sats_per_plane = 2
    if len(constellation) != expected_planes:
        failures.append(f"{case.label}: expected {expected_planes} planes, got {len(constellation)}")
        return failures
    in_plane_spacing_deg = 360.0 / expected_sats_per_plane
    for plane_index, plane in enumerate(constellation):
        if len(plane) != expected_sats_per_plane:
            failures.append(
                f"{case.label}: plane {plane_index} expected {expected_sats_per_plane} satellites, got {len(plane)}"
            )
            continue
        expected_raan = seed.raan_deg + plane_index * case.expected_raan_spacing_deg
        for sat_index, satellite in enumerate(plane):
            failures.extend(compare_inherited_fields(case.label, plane_index, sat_index, seed, satellite))
            expected_true_anomaly = (
                seed.true_anomaly_deg
                + plane_index * case.expected_inter_plane_true_anomaly_spacing_deg
                + sat_index * in_plane_spacing_deg
            )
            failures.extend(
                compare_angle(
                    case.label,
                    plane_index,
                    sat_index,
                    "RAAN",
                    satellite.raan_deg,
                    expected_raan,
                )
            )
            failures.extend(
                compare_angle(
                    case.label,
                    plane_index,
                    sat_index,
                    "true_anomaly",
                    satellite.true_anomaly_deg,
                    expected_true_anomaly,
                )
            )
    return failures


def compare_inherited_fields(
    label: str,
    plane_index: int,
    sat_index: int,
    seed: orbits.KeplerianElements,
    actual: orbits.KeplerianElements,
) -> list[str]:
    failures: list[str] = []
    scalar_fields = (
        ("semi_major_axis_m", seed.semi_major_axis_m, actual.semi_major_axis_m),
        ("eccentricity", seed.eccentricity, actual.eccentricity),
        ("inclination_deg", seed.inclination_deg, actual.inclination_deg),
        (
            "argument_of_periapsis_deg",
            seed.argument_of_periapsis_deg,
            actual.argument_of_periapsis_deg,
        ),
    )
    for field, expected, value in scalar_fields:
        error = abs(value - expected)
        if error > SCALAR_ABS:
            failures.append(
                f"{label}: plane={plane_index} sat={sat_index} {field} error {error:.12g} exceeds {SCALAR_ABS:.12g}"
            )
    return failures


def compare_angle(
    label: str,
    plane_index: int,
    sat_index: int,
    field: str,
    value_deg: float,
    expected_deg: float,
) -> list[str]:
    error = abs(wrapped_angle_error_deg(value_deg, expected_deg))
    if error <= ANGLE_ABS_DEG:
        return []
    return [
        (
            f"{label}: plane={plane_index} sat={sat_index} {field} "
            f"error {error:.12g} deg exceeds {ANGLE_ABS_DEG:.12g} deg; "
            f"actual={value_deg:.12g} expected={expected_deg % 360.0:.12g}"
        )
    ]


def wrapped_angle_error_deg(actual_deg: float, expected_deg: float) -> float:
    return (actual_deg - expected_deg + 180.0) % 360.0 - 180.0


def main() -> int:
    try:
        test_walker_constellations_match_standard_walker_equations()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=3")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
