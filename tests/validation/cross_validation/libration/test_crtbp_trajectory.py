#!/usr/bin/env python3
"""Live cross-validation for ASTROX nondimensional CRTBP integration."""

# Coverage:
#   Branches:
#     - primary-centered and barycentric origins: verified
#     - forward and reverse integration: verified
#     - OutStep=0 adaptive nodes and fixed output steps 0.05 and 0.1: verified
#     - planar and out-of-plane states: verified
#   Parameters:
#     - Earth-Moon and synthetic mass ratios: verified
#     - durations 0.2, 0.35, and 0.6 nondimensional time: verified
#   Fields:
#     - response mass ratio/origin, every returned sample time, and all six state components: verified
#     - locally recomputed max(abs(C(t)-C(0))) Jacobi drift: verified
#   Comparison:
#     - independent DOP853 integration of explicitly written barycentric rotating-frame equations
#     - origin conversion is x_barycentric=x_primary-mu; velocities are unchanged
#   Tolerances:
#     - 2e-10 absolute per state component and 5e-10 absolute total Jacobi drift

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
    EARTH_MOON_MASS_RATIO,
    JACOBI_DRIFT_ABS_TOL,
    TRAJECTORY_STATE_ABS_TOL,
    TRAJECTORY_TIME_ABS_TOL,
    CrossValidationError,
    jacobi_drift,
    maximum_absolute_residual,
    propagate_local,
    trajectory_arrays,
)


@dataclass(frozen=True, kw_only=True)
class TrajectoryCase:
    """One hypothesis-driven CRTBP integration comparison."""

    id: str
    mass_ratio: float
    initial_state: libration.CrtbpState
    start_time: float
    end_time: float
    barycentric: bool
    output_step: float


PRIMARY_OUT_OF_PLANE = libration.crtbp_state(
    x=1.189017399646985,
    y=0.0,
    z=0.06060558718057466,
    vx=0.0,
    vy=-0.17403902743307584,
    vz=0.0,
)
BARYCENTRIC_OUT_OF_PLANE = libration.crtbp_state(
    x=PRIMARY_OUT_OF_PLANE.x - EARTH_MOON_MASS_RATIO,
    y=PRIMARY_OUT_OF_PLANE.y,
    z=PRIMARY_OUT_OF_PLANE.z,
    vx=PRIMARY_OUT_OF_PLANE.vx,
    vy=PRIMARY_OUT_OF_PLANE.vy,
    vz=PRIMARY_OUT_OF_PLANE.vz,
)
REVERSE_START = libration.crtbp_state(
    x=1.1858521851789159,
    y=-0.03411863250063764,
    z=0.05802670310302977,
    vx=-0.031129245925864593,
    vy=-0.1637429285613642,
    vz=-0.02565088873596596,
)
PLANAR_SYNTHETIC = libration.crtbp_state(
    x=0.25,
    y=0.3,
    z=0.0,
    vx=-0.2,
    vy=0.1,
    vz=0.0,
)


CASES = (
    TrajectoryCase(
        id="earth_moon_primary_forward_step_0_1",
        mass_ratio=EARTH_MOON_MASS_RATIO,
        initial_state=PRIMARY_OUT_OF_PLANE,
        start_time=0.0,
        end_time=0.2,
        barycentric=False,
        output_step=0.1,
    ),
    TrajectoryCase(
        id="earth_moon_barycentric_forward_step_0_1",
        mass_ratio=EARTH_MOON_MASS_RATIO,
        initial_state=BARYCENTRIC_OUT_OF_PLANE,
        start_time=0.0,
        end_time=0.2,
        barycentric=True,
        output_step=0.1,
    ),
    TrajectoryCase(
        id="earth_moon_primary_reverse_step_0_05",
        mass_ratio=EARTH_MOON_MASS_RATIO,
        initial_state=REVERSE_START,
        start_time=0.2,
        end_time=0.0,
        barycentric=False,
        output_step=0.05,
    ),
    TrajectoryCase(
        id="earth_moon_primary_forward_adaptive",
        mass_ratio=EARTH_MOON_MASS_RATIO,
        initial_state=PRIMARY_OUT_OF_PLANE,
        start_time=0.0,
        end_time=0.35,
        barycentric=False,
        output_step=0.0,
    ),
    TrajectoryCase(
        id="synthetic_planar_barycentric_step_0_05",
        mass_ratio=0.1,
        initial_state=PLANAR_SYNTHETIC,
        start_time=0.0,
        end_time=0.6,
        barycentric=True,
        output_step=0.05,
    ),
)


def compare_case(case: TrajectoryCase) -> None:
    result = libration.crtbp_trajectory(
        initial_state=case.initial_state,
        mass_ratio=case.mass_ratio,
        start_time=case.start_time,
        end_time=case.end_time,
        barycentric=case.barycentric,
        output_step=case.output_step,
    )
    if result.mass_ratio != case.mass_ratio:
        raise CrossValidationError(
            f"{case.id} response mass_ratio={result.mass_ratio}, requested={case.mass_ratio}"
        )
    if result.is_barycentric is not case.barycentric:
        raise CrossValidationError(
            f"{case.id} response origin={result.is_barycentric}, requested={case.barycentric}"
        )
    times, states = trajectory_arrays(result)
    if abs(times[0] - case.start_time) > TRAJECTORY_TIME_ABS_TOL:
        raise CrossValidationError(f"{case.id} first time={times[0]:.12g}")
    if abs(times[-1] - case.end_time) > TRAJECTORY_TIME_ABS_TOL:
        raise CrossValidationError(f"{case.id} last time={times[-1]:.12g}")
    independent = propagate_local(
        mass_ratio=case.mass_ratio,
        initial_state=case.initial_state.to_wire(),
        times=times,
        is_barycentric=case.barycentric,
    )
    state_residual = maximum_absolute_residual(states, independent)
    drift = jacobi_drift(
        states,
        mass_ratio=case.mass_ratio,
        is_barycentric=case.barycentric,
    )
    planar_residual = float(np.max(np.abs(states[:, (2, 5)]))) if case.id.startswith("synthetic_planar") else 0.0
    print(
        f"CRTBP_TRAJECTORY_CASE={case.id} samples={len(times)} "
        f"max_state_residual={state_residual:.12g} jacobi_drift={drift:.12g}"
    )
    failures: list[str] = []
    if state_residual > TRAJECTORY_STATE_ABS_TOL:
        failures.append(
            f"state residual={state_residual:.12g} > {TRAJECTORY_STATE_ABS_TOL:.12g}"
        )
    if drift > JACOBI_DRIFT_ABS_TOL:
        failures.append(f"Jacobi drift={drift:.12g} > {JACOBI_DRIFT_ABS_TOL:.12g}")
    if planar_residual > TRAJECTORY_STATE_ABS_TOL:
        failures.append(f"planar z/vz residual={planar_residual:.12g}")
    if failures:
        raise CrossValidationError(f"{case.id}: " + "; ".join(failures))


def test_crtbp_trajectories_match_independent_integration() -> None:
    configure_astrox_from_env()
    for case in CASES:
        compare_case(case)


def test_primary_and_barycentric_origins_are_exact_x_shift_branches() -> None:
    configure_astrox_from_env()
    primary = libration.crtbp_trajectory(
        initial_state=PRIMARY_OUT_OF_PLANE,
        mass_ratio=EARTH_MOON_MASS_RATIO,
        start_time=0.0,
        end_time=0.2,
        barycentric=False,
        output_step=0.05,
    )
    barycentric = libration.crtbp_trajectory(
        initial_state=BARYCENTRIC_OUT_OF_PLANE,
        mass_ratio=EARTH_MOON_MASS_RATIO,
        start_time=0.0,
        end_time=0.2,
        barycentric=True,
        output_step=0.05,
    )
    primary_times, primary_states = trajectory_arrays(primary)
    barycentric_times, barycentric_states = trajectory_arrays(barycentric)
    shifted = primary_states.copy()
    shifted[:, 0] -= EARTH_MOON_MASS_RATIO
    time_residual = maximum_absolute_residual(primary_times, barycentric_times)
    state_residual = maximum_absolute_residual(shifted, barycentric_states)
    if time_residual > TRAJECTORY_TIME_ABS_TOL or state_residual > TRAJECTORY_STATE_ABS_TOL:
        raise CrossValidationError(
            f"origin shift residuals: time={time_residual:.12g}, state={state_residual:.12g}"
        )


def main() -> int:
    try:
        test_crtbp_trajectories_match_independent_integration()
        test_primary_and_barycentric_origins_are_exact_x_shift_branches()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"CROSS_VALIDATION_CHECKED={len(CASES) + 1}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
