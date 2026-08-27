#!/usr/bin/env python3
"""Qualify the pinned e2m2e dependency for narrow secondary CRTBP comparisons."""

# Coverage:
#   Accepted roles:
#     - equations of motion, propagation, STM, L1/L2 Halo generation, DRO generation: verified
#     - two-dimensional and three-dimensional fixed-x differential correction: verified for maintained cases
#   Constrained role:
#     - jacobi_error: partial; audited as adjacent-sample change and excluded as total drift
#   Parameters:
#     - three mass ratios, planar/out-of-plane, forward/reverse, north/south, Halo/DRO: verified
#   Reconciliation:
#     - e2m2e uses the standard barycentric rotating origin
#     - its family APIs take dimensional amplitudes in km; the custom system scale is 384400 km
#     - its DRO amplitude is the mean of minimum/maximum Moon distance, unlike ASTROX x_amplitude
#   Tolerances:
#     - 5e-12 equations/propagation; 1e-8 STM finite differences; 1e-12 STM determinant
#     - 2e-8 periodic closure/symmetry and ASTROX correction agreement

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import libration  # noqa: E402
from e2m2e.algorithm.dynamics import CR3BP_Dynamics, CR3BP_System  # noqa: E402
from e2m2e.algorithm.family import design_dro, design_halo  # noqa: E402
from e2m2e.algorithm.solver import DifferentialCorrection  # noqa: E402
from e2m2e.data.templates import ConvergenceState  # noqa: E402
from e2m2e.data.types import Orbit  # noqa: E402
from tests.validation._support import configure_astrox_from_env  # noqa: E402
from tests.validation.cross_validation.libration._support import (  # noqa: E402
    EARTH_MOON_MASS_RATIO,
    EARTH_MOON_MEAN_SEPARATION_M,
    JACOBI_DRIFT_ABS_TOL,
    PERIODIC_CLOSURE_ABS_TOL,
    PERIODIC_SAMPLE_ABS_TOL,
    SYMMETRY_ABS_TOL,
    CrossValidationError,
    crtbp_derivative,
    equilibrium_solution,
    jacobi_drift,
    maximum_absolute_residual,
    propagate_local,
)


EARTH_MOON_LENGTH_KM = EARTH_MOON_MEAN_SEPARATION_M / 1000.0
EARTH_MOON_TIME_UNIT_S = 375190.2589931179
EQUATION_ABS_TOL = 5.0e-12
PROPAGATION_ABS_TOL = 5.0e-12
STM_FINITE_DIFFERENCE_ABS_TOL = 1.0e-8
STM_DETERMINANT_ABS_TOL = 1.0e-12
CORRECTION_ABS_TOL = PERIODIC_SAMPLE_ABS_TOL
DRO_TARGET_AMPLITUDE_KM = 30000.0
DRO_AMPLITUDE_ABS_TOL_KM = 20.0


@dataclass(frozen=True, kw_only=True)
class DynamicsCase:
    id: str
    mass_ratio: float
    state: tuple[float, float, float, float, float, float]
    times: tuple[float, ...]


DYNAMICS_CASES = (
    DynamicsCase(
        id="earth_moon_out_of_plane_forward",
        mass_ratio=EARTH_MOON_MASS_RATIO,
        state=(0.823844660756625, 0.03, 0.05, -0.01, 0.159703975128827, 0.02),
        times=(0.0, 0.05, 0.1, 0.15, 0.2),
    ),
    DynamicsCase(
        id="sun_earth_out_of_plane_forward",
        mass_ratio=3.003143144634591e-6,
        state=(0.98, 0.01, 0.005, 0.0, 0.02, -0.01),
        times=(0.0, 0.05, 0.1, 0.15, 0.2),
    ),
    DynamicsCase(
        id="synthetic_planar_forward",
        mass_ratio=0.1,
        state=(0.25, 0.3, 0.0, -0.2, 0.1, 0.0),
        times=(0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3),
    ),
)


def e2m2e_system(mass_ratio: float = EARTH_MOON_MASS_RATIO) -> CR3BP_System:
    system = CR3BP_System(mass_ratio, "Earth", "Moon")
    if mass_ratio == EARTH_MOON_MASS_RATIO:
        system.set_characteristic_scales(
            EARTH_MOON_LENGTH_KM,
            2.0 * np.pi * EARTH_MOON_TIME_UNIT_S,
        )
        system.compute_libration_points()
    return system


def barycentric_state(state: libration.CrtbpState) -> np.ndarray:
    values = np.asarray(state.to_wire(), dtype=float)
    values[0] -= EARTH_MOON_MASS_RATIO
    return values


def assert_periodic_state(
    *,
    case_id: str,
    initial_state: np.ndarray,
    period: float,
    mass_ratio: float = EARTH_MOON_MASS_RATIO,
) -> tuple[float, float, float]:
    times = np.linspace(0.0, period, 501)
    states = propagate_local(
        mass_ratio=mass_ratio,
        initial_state=initial_state,
        times=times,
        is_barycentric=True,
    )
    closure = maximum_absolute_residual(states[-1], states[0])
    drift = jacobi_drift(states, mass_ratio=mass_ratio, is_barycentric=True)
    half_state = states[len(states) // 2]
    symmetry = max(abs(float(half_state[index])) for index in (1, 3, 5))
    if closure > PERIODIC_CLOSURE_ABS_TOL:
        raise CrossValidationError(f"{case_id} closure={closure:.12g}")
    if drift > JACOBI_DRIFT_ABS_TOL:
        raise CrossValidationError(f"{case_id} Jacobi drift={drift:.12g}")
    if symmetry > SYMMETRY_ABS_TOL:
        raise CrossValidationError(f"{case_id} half-period symmetry={symmetry:.12g}")
    return closure, drift, symmetry


def test_e2m2e_equations_and_propagation_match_local_crtbp() -> None:
    for case in DYNAMICS_CASES:
        state = np.asarray(case.state, dtype=float)
        times = np.asarray(case.times, dtype=float)
        dynamics = CR3BP_Dynamics(e2m2e_system(case.mass_ratio))
        derivative_residual = maximum_absolute_residual(
            dynamics.equations_of_motion(float(times[0]), state),
            crtbp_derivative(float(times[0]), state, case.mass_ratio),
        )
        result = dynamics.propagate(
            state,
            (float(times[0]), float(times[-1])),
            t_eval=times,
            with_jacobi=True,
        )
        independent = propagate_local(
            mass_ratio=case.mass_ratio,
            initial_state=state,
            times=times,
            is_barycentric=True,
        )
        propagation_residual = maximum_absolute_residual(result["states"], independent)
        total_drift = jacobi_drift(
            result["states"],
            mass_ratio=case.mass_ratio,
            is_barycentric=True,
        )
        adjacent_drift = float(np.max(np.abs(np.diff(np.asarray(result["jacobi"])))))
        if result["jacobi_error"] != adjacent_drift:
            raise CrossValidationError(f"{case.id} jacobi_error definition changed")
        print(
            f"E2M2E_DYNAMICS_CASE={case.id} derivative={derivative_residual:.12g} "
            f"propagation={propagation_residual:.12g} total_jacobi={total_drift:.12g}"
        )
        if derivative_residual > EQUATION_ABS_TOL:
            raise CrossValidationError(f"{case.id} derivative={derivative_residual:.12g}")
        if propagation_residual > PROPAGATION_ABS_TOL:
            raise CrossValidationError(f"{case.id} propagation={propagation_residual:.12g}")
        if total_drift > JACOBI_DRIFT_ABS_TOL:
            raise CrossValidationError(f"{case.id} Jacobi drift={total_drift:.12g}")

    reverse_case = DYNAMICS_CASES[0]
    initial = np.asarray(reverse_case.state, dtype=float)
    dynamics = CR3BP_Dynamics(e2m2e_system(reverse_case.mass_ratio))
    forward = dynamics.propagate(initial, (0.0, 0.2), t_eval=(0.0, 0.2))
    reverse_times = np.asarray((0.2, 0.15, 0.1, 0.05, 0.0))
    reverse = dynamics.propagate(
        forward["states"][-1],
        (0.2, 0.0),
        t_eval=reverse_times,
    )
    independent_reverse = propagate_local(
        mass_ratio=reverse_case.mass_ratio,
        initial_state=forward["states"][-1],
        times=reverse_times,
        is_barycentric=True,
    )
    residual = maximum_absolute_residual(reverse["states"], independent_reverse)
    if residual > PROPAGATION_ABS_TOL:
        raise CrossValidationError(f"e2m2e reverse propagation={residual:.12g}")


def test_e2m2e_stm_matches_finite_differences() -> None:
    state = np.asarray((0.823844660756625, 0.0, 0.05, 0.0, 0.159703975128827, 0.0))
    final_time = 0.3
    dynamics = CR3BP_Dynamics(e2m2e_system())
    result = dynamics.propagate(
        state,
        (0.0, final_time),
        t_eval=(final_time,),
        with_stm=True,
    )
    stm = np.asarray(result["stm"][-1], dtype=float)
    epsilon = 1.0e-6
    finite_difference = np.empty((6, 6))
    for column in range(6):
        positive = state.copy()
        negative = state.copy()
        positive[column] += epsilon
        negative[column] -= epsilon
        positive_final = propagate_local(
            mass_ratio=EARTH_MOON_MASS_RATIO,
            initial_state=positive,
            times=(0.0, final_time),
            is_barycentric=True,
        )[-1]
        negative_final = propagate_local(
            mass_ratio=EARTH_MOON_MASS_RATIO,
            initial_state=negative,
            times=(0.0, final_time),
            is_barycentric=True,
        )[-1]
        finite_difference[:, column] = (positive_final - negative_final) / (2.0 * epsilon)
    residual = maximum_absolute_residual(stm, finite_difference)
    determinant_residual = abs(float(np.linalg.det(stm)) - 1.0)
    print(
        f"E2M2E_STM_CASE=earth_moon_0_3 finite_difference={residual:.12g} "
        f"determinant_residual={determinant_residual:.12g}"
    )
    if residual > STM_FINITE_DIFFERENCE_ABS_TOL:
        raise CrossValidationError(f"e2m2e STM finite-difference residual={residual:.12g}")
    if determinant_residual > STM_DETERMINANT_ABS_TOL:
        raise CrossValidationError(
            f"e2m2e STM determinant residual={determinant_residual:.12g}"
        )


def generated_orbits() -> tuple[tuple[str, Orbit], ...]:
    dynamics = CR3BP_Dynamics(e2m2e_system())
    return (
        (
            "l1_halo_north",
            design_halo(1, 0.05 * EARTH_MOON_LENGTH_KM, dynamics=dynamics),
        ),
        (
            "l1_halo_south",
            design_halo(1, -0.05 * EARTH_MOON_LENGTH_KM, dynamics=dynamics),
        ),
        (
            "l2_halo_north",
            design_halo(2, 0.05 * EARTH_MOON_LENGTH_KM, dynamics=dynamics),
        ),
        (
            "l2_halo_south",
            design_halo(2, -0.05 * EARTH_MOON_LENGTH_KM, dynamics=dynamics),
        ),
        (
            "dro_30000_km",
            design_dro(
                DRO_TARGET_AMPLITUDE_KM,
                dynamics=dynamics,
                tol_km=DRO_AMPLITUDE_ABS_TOL_KM,
            ),
        ),
    )


def assert_halo_family_and_branch(case_id: str, state: np.ndarray) -> None:
    point, _, branch = case_id.split("_", maxsplit=2)
    equilibria = equilibrium_solution(EARTH_MOON_MASS_RATIO)
    secondary_x = 1.0 - EARTH_MOON_MASS_RATIO
    if point == "l1":
        family_matches = equilibria.points[0][0] < state[0] < secondary_x
    elif point == "l2":
        family_matches = state[0] > equilibria.points[1][0]
    else:
        raise CrossValidationError(f"unsupported e2m2e Halo case {case_id}")
    if not family_matches:
        raise CrossValidationError(
            f"{case_id} initial x={state[0]:.12g} does not identify the requested family"
        )

    expected_z_sign = -1.0 if branch == "south" else 1.0
    if expected_z_sign * float(state[2]) <= 0.0:
        raise CrossValidationError(
            f"{case_id} initial z={state[2]:.12g} has the wrong branch sign"
        )
    crossing_residual = max(abs(float(state[index])) for index in (1, 3, 5))
    if crossing_residual > SYMMETRY_ABS_TOL:
        raise CrossValidationError(
            f"{case_id} initial XZ-plane crossing residual={crossing_residual:.12g}"
        )


def assert_halo_reflections(orbits: dict[str, Orbit]) -> None:
    for point in ("l1", "l2"):
        north = orbits[f"{point}_halo_north"]
        south = orbits[f"{point}_halo_south"]
        north_state = np.asarray(north.states[0], dtype=float)
        expected_south = north_state.copy()
        expected_south[[2, 5]] *= -1.0
        reflection_residual = maximum_absolute_residual(
            np.asarray(south.states[0], dtype=float),
            expected_south,
        )
        period_residual = abs(float(south.period) - float(north.period))
        if max(reflection_residual, period_residual) > PERIODIC_SAMPLE_ABS_TOL:
            raise CrossValidationError(
                f"{point} Halo north/south reflection={reflection_residual:.12g}, "
                f"period={period_residual:.12g}"
            )


def test_e2m2e_halo_and_dro_generators_match_local_invariants() -> None:
    generated = generated_orbits()
    for case_id, orbit in generated:
        if orbit.period is None:
            raise CrossValidationError(f"{case_id} did not return a period")
        state = np.asarray(orbit.states[0], dtype=float)
        closure, drift, symmetry = assert_periodic_state(
            case_id=case_id,
            initial_state=state,
            period=orbit.period,
        )
        if case_id.startswith("dro"):
            times = np.linspace(0.0, orbit.period, 4001)
            states = propagate_local(
                mass_ratio=EARTH_MOON_MASS_RATIO,
                initial_state=state,
                times=times,
                is_barycentric=True,
            )
            moon = np.asarray((1.0 - EARTH_MOON_MASS_RATIO, 0.0, 0.0))
            distances_km = np.linalg.norm(states[:, :3] - moon, axis=1) * EARTH_MOON_LENGTH_KM
            measured_amplitude = 0.5 * (float(distances_km.min()) + float(distances_km.max()))
            if abs(measured_amplitude - DRO_TARGET_AMPLITUDE_KM) > DRO_AMPLITUDE_ABS_TOL_KM:
                raise CrossValidationError(
                    f"{case_id} amplitude={measured_amplitude:.12g} km"
                )
            planarity_residual = float(np.max(np.abs(states[:, (2, 5)])))
            if planarity_residual > PERIODIC_SAMPLE_ABS_TOL:
                raise CrossValidationError(
                    f"{case_id} planarity residual={planarity_residual:.12g}"
                )
            relative_x = float(state[0] - moon[0])
            relative_y = float(state[1] - moon[1])
            relative_angular_momentum_z = (
                relative_x * float(state[4]) - relative_y * float(state[3])
            )
            if relative_angular_momentum_z >= 0.0:
                raise CrossValidationError(
                    f"{case_id} is not retrograde relative to the Moon: "
                    f"relative_angular_momentum_z={relative_angular_momentum_z:.12g}"
                )
        else:
            assert_halo_family_and_branch(case_id, state)
        print(
            f"E2M2E_FAMILY_CASE={case_id} closure={closure:.12g} "
            f"jacobi={drift:.12g} symmetry={symmetry:.12g}"
        )
    assert_halo_reflections(dict(generated))


def test_e2m2e_fixed_x_correction_matches_astrox_family_seeds() -> None:
    configure_astrox_from_env()
    dynamics = CR3BP_Dynamics(e2m2e_system())
    references = (
        ("l1", libration.earth_moon_l1_halo(z_amplitude=0.05, southern=False)),
        ("l2", libration.earth_moon_l2_halo(x_amplitude=0.10, southern=False)),
        ("dro", libration.earth_moon_dro(x_amplitude=0.1801)),
    )
    for family, reference in references:
        expected = barycentric_state(reference.corrected_state)
        seed = expected.copy()
        if family != "dro":
            seed[2] += 1.0e-5
        seed[4] += 1.0e-5
        guess = Orbit(states=seed, times=np.asarray((0.0,)), system=dynamics.system)
        guess.period = reference.period * 1.00001
        corrector = DifferentialCorrection(dynamics)
        if family == "dro":
            corrector.setup_2D_symmetric_x_fixed_x0(float(seed[0]))
        else:
            corrector.setup_3D_symmetric_xz_fixed_x0(float(seed[0]))
        result = corrector.iterate_correction(guess, verbose=False)
        if result.status is not ConvergenceState.CONVERGED or result.orbit is None:
            raise CrossValidationError(
                f"e2m2e {family} correction did not converge: {result.message}"
            )
        corrected = np.asarray(result.orbit.states[0], dtype=float)
        state_residual = maximum_absolute_residual(corrected, expected)
        period_residual = abs(float(result.orbit.period) - reference.period)
        closure, drift, symmetry = assert_periodic_state(
            case_id=f"fixed_x_{family}",
            initial_state=corrected,
            period=float(result.orbit.period),
        )
        print(
            f"E2M2E_CORRECTION_CASE={family} state={state_residual:.12g} "
            f"period={period_residual:.12g} closure={closure:.12g} "
            f"jacobi={drift:.12g} symmetry={symmetry:.12g}"
        )
        if max(state_residual, period_residual) > CORRECTION_ABS_TOL:
            raise CrossValidationError(
                f"e2m2e {family} correction disagreement: "
                f"state={state_residual:.12g}, period={period_residual:.12g}"
            )


def test_astrox_fixed_x_accepts_independently_generated_e2m2e_seeds() -> None:
    configure_astrox_from_env()
    for case_id, orbit in generated_orbits():
        if case_id.endswith("south"):
            continue
        if orbit.period is None:
            raise CrossValidationError(f"{case_id} did not return a period")
        seed_values = np.asarray(orbit.states[0], dtype=float)
        seed_values[0] += EARTH_MOON_MASS_RATIO
        seed = libration.crtbp_state(
            x=seed_values[0],
            y=seed_values[1],
            z=seed_values[2],
            vx=seed_values[3],
            vy=seed_values[4],
            vz=seed_values[5],
        )
        result = libration.correct_periodic_orbit_fixed_x(
            initial_state=seed,
            period_guess=orbit.period,
            mass_ratio=EARTH_MOON_MASS_RATIO,
            barycentric=False,
            output_step=0.05,
        )
        state_residual = maximum_absolute_residual(
            np.asarray(result.corrected_state.to_wire()),
            seed_values,
        )
        period_residual = abs(result.period - orbit.period)
        print(
            f"ASTROX_E2M2E_SEED_CASE={case_id} state={state_residual:.12g} "
            f"period={period_residual:.12g}"
        )
        if max(state_residual, period_residual) > CORRECTION_ABS_TOL:
            raise CrossValidationError(
                f"ASTROX changed the independently generated {case_id} seed"
            )


def main() -> int:
    checks = (
        test_e2m2e_equations_and_propagation_match_local_crtbp,
        test_e2m2e_stm_matches_finite_differences,
        test_e2m2e_halo_and_dro_generators_match_local_invariants,
        test_e2m2e_fixed_x_correction_matches_astrox_family_seeds,
        test_astrox_fixed_x_accepts_independently_generated_e2m2e_seeds,
    )
    try:
        for check in checks:
            check()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    checked = len(DYNAMICS_CASES) + 1 + 1 + 5 + 3 + 3
    print(f"CROSS_VALIDATION_CHECKED={checked}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
