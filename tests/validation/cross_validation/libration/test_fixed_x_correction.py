#!/usr/bin/env python3
"""Live cross-validation for ASTROX fixed-x periodic-orbit correction."""

# Coverage:
#   Branches:
#     - representative L1 Halo, L2 Halo, and planar DRO seeds: verified
#     - exact and boundedly perturbed z/vy or vy/period seeds: verified
#     - primary-centered inputs for all families and barycentric input for L1: verified
#     - invalid half-period guess and a 0.05 z/vy coarse perturbation: verified API-error behavior
#   Fields:
#     - InitialX0 echo, fixed corrected x, corrected state, Period, ListT, ListX, IsBarycentric: verified
#   Parameters:
#     - initial state, period guess, mass ratio, origin, and output step: verified
#   Comparison:
#     - independent full-period DOP853 propagation, closure, Jacobi drift, and half-period symmetry
#     - comparison to the separately generated family member is supporting cross-endpoint evidence only
#   Tolerances:
#     - 2e-8 absolute for propagated residuals; 5e-10 for Jacobi drift; 2e-8 for correction recovery

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import exceptions, libration  # noqa: E402
from tests.validation._support import configure_astrox_from_env  # noqa: E402
from tests.validation.cross_validation.libration._support import (  # noqa: E402
    EARTH_MOON_MASS_RATIO,
    PERIODIC_SAMPLE_ABS_TOL,
    CrossValidationError,
    assert_periodic_metrics,
    maximum_absolute_residual,
    validate_periodic_orbit,
)


CORRECTION_RECOVERY_ABS_TOL = PERIODIC_SAMPLE_ABS_TOL


@dataclass(frozen=True, kw_only=True)
class CorrectionCase:
    """One fixed-x correction comparison."""

    id: str
    family: str
    barycentric: bool
    perturbed: bool


CASES = (
    CorrectionCase(id="l1_primary_exact", family="l1", barycentric=False, perturbed=False),
    CorrectionCase(id="l1_primary_perturbed", family="l1", barycentric=False, perturbed=True),
    CorrectionCase(id="l1_barycentric_perturbed", family="l1", barycentric=True, perturbed=True),
    CorrectionCase(id="l2_primary_exact", family="l2", barycentric=False, perturbed=False),
    CorrectionCase(id="l2_primary_perturbed", family="l2", barycentric=False, perturbed=True),
    CorrectionCase(id="dro_primary_exact", family="dro", barycentric=False, perturbed=False),
    CorrectionCase(id="dro_primary_perturbed", family="dro", barycentric=False, perturbed=True),
)


def family_orbit(family: str) -> libration.PeriodicOrbit:
    if family == "l1":
        return libration.earth_moon_l1_halo(z_amplitude=0.05, southern=False)
    if family == "l2":
        return libration.earth_moon_l2_halo(x_amplitude=0.10, southern=False)
    if family == "dro":
        return libration.earth_moon_dro(x_amplitude=0.1801)
    raise ValueError(f"unsupported correction family: {family!r}")


def shifted_state(
    state: libration.CrtbpState,
    *,
    barycentric: bool,
) -> libration.CrtbpState:
    return libration.crtbp_state(
        x=state.x - EARTH_MOON_MASS_RATIO if barycentric else state.x,
        y=state.y,
        z=state.z,
        vx=state.vx,
        vy=state.vy,
        vz=state.vz,
    )


def perturbed_state(
    state: libration.CrtbpState,
    *,
    family: str,
) -> libration.CrtbpState:
    return libration.crtbp_state(
        x=state.x,
        y=state.y,
        z=state.z + (0.0 if family == "dro" else 1.0e-5),
        vx=state.vx,
        vy=state.vy + 1.0e-5,
        vz=state.vz,
    )


def compare_case(case: CorrectionCase) -> None:
    reference = family_orbit(case.family)
    seed = shifted_state(reference.corrected_state, barycentric=case.barycentric)
    if case.perturbed:
        seed = perturbed_state(seed, family=case.family)
    period_guess = reference.period * (1.00001 if case.perturbed else 1.0)
    result = libration.correct_periodic_orbit_fixed_x(
        initial_state=seed,
        period_guess=period_guess,
        mass_ratio=EARTH_MOON_MASS_RATIO,
        barycentric=case.barycentric,
        output_step=0.05,
    )
    if result.is_barycentric is not case.barycentric:
        raise CrossValidationError(
            f"{case.id} response origin={result.is_barycentric}, requested={case.barycentric}"
        )
    echo_residual = maximum_absolute_residual(
        np.asarray(result.initial_state.to_wire()),
        np.asarray(seed.to_wire()),
    )
    fixed_x_residual = abs(result.corrected_state.x - seed.x)
    expected_corrected = shifted_state(
        reference.corrected_state,
        barycentric=case.barycentric,
    )
    recovery_residual = maximum_absolute_residual(
        np.asarray(result.corrected_state.to_wire()),
        np.asarray(expected_corrected.to_wire()),
    )
    period_residual = abs(result.period - reference.period)
    metrics = validate_periodic_orbit(result)
    print(
        f"FIXED_X_CASE={case.id} echo={echo_residual:.12g} "
        f"fixed_x={fixed_x_residual:.12g} recovery={recovery_residual:.12g} "
        f"period={period_residual:.12g} closure={metrics.closure_residual:.12g} "
        f"jacobi_drift={metrics.jacobi_drift:.12g}"
    )
    if echo_residual != 0.0:
        raise CrossValidationError(f"{case.id} InitialX0 echo residual={echo_residual:.12g}")
    if fixed_x_residual != 0.0:
        raise CrossValidationError(f"{case.id} fixed-x residual={fixed_x_residual:.12g}")
    if recovery_residual > CORRECTION_RECOVERY_ABS_TOL:
        raise CrossValidationError(
            f"{case.id} recovery residual={recovery_residual:.12g}, "
            f"tolerance={CORRECTION_RECOVERY_ABS_TOL:.12g}"
        )
    if period_residual > CORRECTION_RECOVERY_ABS_TOL:
        raise CrossValidationError(
            f"{case.id} period residual={period_residual:.12g}, "
            f"tolerance={CORRECTION_RECOVERY_ABS_TOL:.12g}"
        )
    assert_periodic_metrics(metrics, case_id=case.id)


def test_fixed_x_correction_matches_independent_periodic_residuals() -> None:
    configure_astrox_from_env()
    for case in CASES:
        compare_case(case)


@pytest.mark.parametrize(
    "seed_kind",
    ("half_period", "coarse_perturbation"),
)
def test_fixed_x_nonconvergence_remains_visible(seed_kind: str) -> None:
    configure_astrox_from_env()
    reference = family_orbit("l1")
    if seed_kind == "half_period":
        seed = reference.corrected_state
        period_guess = reference.period / 2.0
    else:
        state = reference.corrected_state
        seed = libration.crtbp_state(
            x=state.x,
            y=state.y,
            z=state.z + 5.0e-2,
            vx=state.vx,
            vy=state.vy - 5.0e-2,
            vz=state.vz,
        )
        period_guess = reference.period
    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        libration.correct_periodic_orbit_fixed_x(
            initial_state=seed,
            period_guess=period_guess,
            mass_ratio=EARTH_MOON_MASS_RATIO,
            barycentric=False,
            output_step=0.05,
        )
    if exc_info.value.endpoint != "/libration/crtbp-period-orbit-fixed-x":
        raise CrossValidationError(
            f"{seed_kind} failed at unexpected endpoint {exc_info.value.endpoint!r}"
        )


def main() -> int:
    try:
        test_fixed_x_correction_matches_independent_periodic_residuals()
        for seed_kind in ("half_period", "coarse_perturbation"):
            test_fixed_x_nonconvergence_remains_visible(seed_kind)
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"CROSS_VALIDATION_CHECKED={len(CASES) + 2}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
