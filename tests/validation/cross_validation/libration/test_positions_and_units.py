#!/usr/bin/env python3
"""Live cross-validation for equilibrium points and CRTBP unit scales."""

# Coverage:
#   Branches:
#     - positions: Earth-Moon, Sun-Earth, and synthetic mass ratios: verified
#     - units: omitted defaults plus explicit Earth-Moon and Sun-Earth-like systems: verified
#   Fields:
#     - all five named point coordinates and all three collinear distances: verified
#     - both gravitational parameters, mass ratio, length, time, and velocity units: verified
#   Parameters:
#     - mass ratio, both gravitational parameters, and mean separation: verified
#   Comparison:
#     - collinear points use independently bracketed scalar roots; L4/L5 use their analytic coordinates
#     - unit scales use mu=GM2/(GM1+GM2), TU=sqrt(L^3/(GM1+GM2)), and VU=L/TU
#   Tolerances:
#     - 5e-13 absolute for nondimensional roots; 5e-15 relative for closed-form scales

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import libration  # noqa: E402
from tests.validation._support import configure_astrox_from_env  # noqa: E402
from tests.validation.cross_validation.libration._support import (  # noqa: E402
    EARTH_GM_M3_S2,
    EARTH_MOON_MASS_RATIO,
    EARTH_MOON_MEAN_SEPARATION_M,
    MOON_GM_M3_S2,
    ROOT_ABS_TOL,
    UNIT_REL_TOL,
    CrossValidationError,
    equilibrium_solution,
    unit_scales,
)


POSITION_CASES = (
    ("earth_moon", EARTH_MOON_MASS_RATIO),
    ("sun_earth", 3.003143144634591e-6),
    ("synthetic", 0.1),
)
UNIT_CASES = (
    (
        "earth_moon_explicit",
        EARTH_GM_M3_S2,
        MOON_GM_M3_S2,
        EARTH_MOON_MEAN_SEPARATION_M,
    ),
    (
        "sun_earth_like",
        1.32712440018e20,
        3.986004418e14,
        149597870700.0,
    ),
)


def compare_positions(case_id: str, mass_ratio: float) -> None:
    actual = libration.positions(mass_ratio=mass_ratio)
    expected = equilibrium_solution(mass_ratio)
    actual_points = (
        (actual.l1.x, actual.l1.y),
        (actual.l2.x, actual.l2.y),
        (actual.l3.x, actual.l3.y),
        (actual.l4.x, actual.l4.y),
        (actual.l5.x, actual.l5.y),
    )
    actual_distances = (
        actual.l1_distance_to_secondary,
        actual.l2_distance_to_secondary,
        actual.l3_distance_to_primary,
    )
    residuals = [
        abs(actual_value - expected_value)
        for actual_point, expected_point in zip(
            actual_points,
            expected.points,
            strict=True,
        )
        for actual_value, expected_value in zip(
            actual_point,
            expected_point,
            strict=True,
        )
    ]
    residuals.extend(
        abs(actual_value - expected_value)
        for actual_value, expected_value in zip(
            actual_distances,
            expected.distances,
            strict=True,
        )
    )
    max_residual = max(residuals)
    print(f"LIBRATION_POSITIONS_CASE={case_id} max_abs_residual={max_residual:.12g}")
    if max_residual > ROOT_ABS_TOL:
        raise CrossValidationError(
            f"{case_id} point residual={max_residual:.12g}, tolerance={ROOT_ABS_TOL:.12g}"
        )


def compare_units(
    case_id: str,
    primary_gm: float,
    secondary_gm: float,
    separation_m: float,
) -> None:
    actual = libration.units(
        primary_gravitational_parameter_m3_s2=primary_gm,
        secondary_gravitational_parameter_m3_s2=secondary_gm,
        mean_separation_m=separation_m,
    )
    expected = unit_scales(
        primary_gravitational_parameter_m3_s2=primary_gm,
        secondary_gravitational_parameter_m3_s2=secondary_gm,
        mean_separation_m=separation_m,
    )
    actual_values = (
        actual.mass_ratio,
        actual.length_unit_m,
        actual.time_unit_s,
        actual.velocity_unit_m_s,
    )
    for name, actual_value, expected_value in zip(
        ("mass_ratio", "length_unit_m", "time_unit_s", "velocity_unit_m_s"),
        actual_values,
        expected,
        strict=True,
    ):
        if not math.isclose(
            actual_value,
            expected_value,
            rel_tol=UNIT_REL_TOL,
            abs_tol=0.0,
        ):
            raise CrossValidationError(
                f"{case_id} {name}={actual_value:.17g}, expected={expected_value:.17g}"
            )
    if actual.primary_gravitational_parameter_m3_s2 != primary_gm:
        raise CrossValidationError(f"{case_id} primary GM was not echoed exactly")
    if actual.secondary_gravitational_parameter_m3_s2 != secondary_gm:
        raise CrossValidationError(f"{case_id} secondary GM was not echoed exactly")
    print(
        f"LIBRATION_UNITS_CASE={case_id} mass_ratio={actual.mass_ratio:.12g} "
        f"time_unit_s={actual.time_unit_s:.12g}"
    )


def test_positions_match_independent_equilibrium_solutions() -> None:
    configure_astrox_from_env()
    for case_id, mass_ratio in POSITION_CASES:
        compare_positions(case_id, mass_ratio)


def test_units_match_closed_form_scales() -> None:
    configure_astrox_from_env()
    for case in UNIT_CASES:
        compare_units(*case)


def test_units_server_defaults_match_their_echoed_closed_form_system() -> None:
    configure_astrox_from_env()
    actual = libration.units()
    expected = unit_scales(
        primary_gravitational_parameter_m3_s2=actual.primary_gravitational_parameter_m3_s2,
        secondary_gravitational_parameter_m3_s2=actual.secondary_gravitational_parameter_m3_s2,
        mean_separation_m=actual.length_unit_m,
    )
    actual_values = (
        actual.mass_ratio,
        actual.length_unit_m,
        actual.time_unit_s,
        actual.velocity_unit_m_s,
    )
    if any(
        not math.isclose(actual_value, expected_value, rel_tol=UNIT_REL_TOL)
        for actual_value, expected_value in zip(actual_values, expected, strict=True)
    ):
        raise CrossValidationError("server-default unit scales do not follow the closed-form convention")


def main() -> int:
    try:
        test_positions_match_independent_equilibrium_solutions()
        test_units_match_closed_form_scales()
        test_units_server_defaults_match_their_echoed_closed_form_system()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    checked = len(POSITION_CASES) + len(UNIT_CASES) + 1
    print(f"CROSS_VALIDATION_CHECKED={checked}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
