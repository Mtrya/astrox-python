#!/usr/bin/env python3
"""Supporting consistency checks across ASTROX libration endpoints."""

# Coverage:
#   Branches:
#     - L1 Halo, L2 Halo, and DRO family outputs integrated by crtbp_trajectory: verified
#     - unit-derived Earth-Moon mass ratio reused by positions and trajectory: verified
#     - default unit-system mass ratio versus periodic-family mass ratio: verified distinct
#   Fields:
#     - corrected initial state, period, shared ListT/ListX samples, mass ratio, origin: verified
#   Parameters:
#     - family, output step, mass ratio, unit inputs, and origin: verified for the listed matrix
#   Comparison:
#     - cross-endpoint agreement is supporting evidence only; independent equations are primary
#     - fixed OutStep=0.01 includes each family timestamp expressible on that grid plus final time
#   Tolerances:
#     - 2e-10 absolute per shared state component and 5e-13 for unit/position reconciliation

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

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
    TRAJECTORY_STATE_ABS_TOL,
    CrossValidationError,
    equilibrium_solution,
    maximum_absolute_residual,
)


@dataclass(frozen=True, kw_only=True)
class FamilyCase:
    id: str
    result: libration.PeriodicOrbit


def family_cases() -> tuple[FamilyCase, ...]:
    return (
        FamilyCase(
            id="l1_halo",
            result=libration.earth_moon_l1_halo(z_amplitude=0.05, southern=False),
        ),
        FamilyCase(
            id="l2_halo",
            result=libration.earth_moon_l2_halo(x_amplitude=0.10, southern=False),
        ),
        FamilyCase(
            id="dro",
            result=libration.earth_moon_dro(x_amplitude=0.1801),
        ),
    )


def test_family_samples_match_crtbp_trajectory_at_shared_times() -> None:
    configure_astrox_from_env()
    for case in family_cases():
        trajectory = libration.crtbp_trajectory(
            initial_state=case.result.corrected_state,
            mass_ratio=EARTH_MOON_MASS_RATIO,
            start_time=0.0,
            end_time=case.result.period,
            barycentric=case.result.is_barycentric,
            output_step=0.01,
        )
        trajectory_by_time = {
            round(sample.time, 12): np.asarray(sample.state.to_wire(), dtype=float)
            for sample in trajectory.samples
        }
        residuals: list[float] = []
        for sample in case.result.samples:
            trajectory_state = trajectory_by_time.get(round(sample.time, 12))
            if trajectory_state is not None:
                residuals.append(
                    maximum_absolute_residual(
                        np.asarray(sample.state.to_wire(), dtype=float),
                        trajectory_state,
                    )
                )
        if len(residuals) < 3:
            raise CrossValidationError(f"{case.id} has only {len(residuals)} shared samples")
        max_residual = max(residuals)
        initial_residual = maximum_absolute_residual(
            np.asarray(trajectory.samples[0].state.to_wire(), dtype=float),
            np.asarray(case.result.corrected_state.to_wire(), dtype=float),
        )
        print(
            f"CROSS_ENDPOINT_CASE={case.id} shared_samples={len(residuals)} "
            f"state={max_residual:.12g} initial={initial_residual:.12g}"
        )
        if max(max_residual, initial_residual) > TRAJECTORY_STATE_ABS_TOL:
            raise CrossValidationError(
                f"{case.id} family/trajectory residual={max_residual:.12g}"
            )


def test_unit_mass_ratio_reproduces_positions_and_trajectory_echo() -> None:
    configure_astrox_from_env()
    units = libration.units(
        primary_gravitational_parameter_m3_s2=EARTH_GM_M3_S2,
        secondary_gravitational_parameter_m3_s2=MOON_GM_M3_S2,
        mean_separation_m=EARTH_MOON_MEAN_SEPARATION_M,
    )
    points = libration.positions(mass_ratio=units.mass_ratio)
    expected = equilibrium_solution(units.mass_ratio)
    point_residual = max(
        abs(actual - reference)
        for actual_point, expected_point in zip(
            (points.l1, points.l2, points.l3, points.l4, points.l5),
            expected.points,
            strict=True,
        )
        for actual, reference in zip(
            (actual_point.x, actual_point.y),
            expected_point,
            strict=True,
        )
    )
    initial = libration.crtbp_state(
        x=1.189017399646985,
        y=0.0,
        z=0.06060558718057466,
        vx=0.0,
        vy=-0.17403902743307584,
        vz=0.0,
    )
    trajectory = libration.crtbp_trajectory(
        initial_state=initial,
        mass_ratio=units.mass_ratio,
        start_time=0.0,
        end_time=0.2,
        barycentric=False,
        output_step=0.1,
    )
    print(
        f"CROSS_ENDPOINT_CASE=unit_mass_ratio point={point_residual:.12g} "
        f"echo={abs(trajectory.mass_ratio - units.mass_ratio):.12g}"
    )
    if point_residual > ROOT_ABS_TOL:
        raise CrossValidationError(f"unit-derived point residual={point_residual:.12g}")
    if trajectory.mass_ratio != units.mass_ratio:
        raise CrossValidationError("trajectory did not echo the unit-derived mass ratio")


def test_default_unit_system_is_distinct_from_periodic_family_system() -> None:
    configure_astrox_from_env()
    units = libration.units()
    difference = abs(units.mass_ratio - EARTH_MOON_MASS_RATIO)
    print(
        f"CROSS_ENDPOINT_CASE=default_unit_vs_family mass_ratio_difference={difference:.12g}"
    )
    if difference <= 1.0e-6:
        raise CrossValidationError(
            "the default unit/family mass-ratio distinction changed; reassess the public caveat"
        )


def main() -> int:
    try:
        test_family_samples_match_crtbp_trajectory_at_shared_times()
        test_unit_mass_ratio_reproduces_positions_and_trajectory_echo()
        test_default_unit_system_is_distinct_from_periodic_family_system()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=5")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
