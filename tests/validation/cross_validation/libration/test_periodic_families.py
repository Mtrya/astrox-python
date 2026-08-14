#!/usr/bin/env python3
"""Live cross-validation for Earth-Moon Halo and DRO periodic families."""

# Coverage:
#   Branches:
#     - L1 Halo and L2 Halo low/middle/high amplitudes, northern and southern: verified
#     - planar DRO low/middle/high x amplitudes: verified
#     - exact advertised rounded lower bounds: verified rejection behavior
#   Fields:
#     - amplitude definition, origin, corrected state, period, every ListT/ListX sample: verified
#     - full-period closure, Jacobi drift, and half-period XZ-plane symmetry residuals: verified
#   Parameters:
#     - amplitude, north/south branch, and all three family routes: verified
#   Comparison:
#     - independent DOP853 integration of explicitly written CRTBP equations
#     - northern/southern Halo reflection is checked as (z,vz)->(-z,-vz)
#   Tolerances:
#     - 2e-8 absolute for samples, closure, and symmetry; 5e-10 for Jacobi drift

from __future__ import annotations

import math
import sys
from collections.abc import Callable
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
    PERIODIC_SAMPLE_ABS_TOL,
    CrossValidationError,
    assert_periodic_metrics,
    maximum_absolute_residual,
    periodic_arrays,
    validate_periodic_orbit,
)


AMPLITUDE_ABS_TOL = 5.0e-10
REFLECTION_ABS_TOL = PERIODIC_SAMPLE_ABS_TOL
L2_FIRST_AVAILABLE_AMPLITUDE = 0.026000000000018453
DRO_FIRST_AVAILABLE_AMPLITUDE = 0.0780437044745057


@dataclass(frozen=True, kw_only=True)
class HaloCase:
    """One Earth-Moon Halo family member."""

    id: str
    point: int
    amplitude: float
    southern: bool


@dataclass(frozen=True, kw_only=True)
class DroCase:
    """One Earth-Moon DRO family member."""

    id: str
    amplitude: float


HALO_CASES = tuple(
    HaloCase(
        id=f"l{point}_{position}_{hemisphere}",
        point=point,
        amplitude=amplitude,
        southern=southern,
    )
    for point, amplitudes in (
        (1, (("low", 0.022), ("middle", 0.10), ("high", 0.199))),
        (
            2,
            (
                ("low", L2_FIRST_AVAILABLE_AMPLITUDE),
                ("middle", 0.10),
                ("high", 0.1928),
            ),
        ),
    )
    for position, amplitude in amplitudes
    for hemisphere, southern in (("north", False), ("south", True))
)
DRO_CASES = (
    DroCase(id="dro_low", amplitude=DRO_FIRST_AVAILABLE_AMPLITUDE),
    DroCase(id="dro_middle", amplitude=0.30),
    DroCase(id="dro_high", amplitude=0.520),
)


def halo(case: HaloCase) -> libration.PeriodicOrbit:
    if case.point == 1:
        return libration.earth_moon_l1_halo(
            z_amplitude=case.amplitude,
            southern=case.southern,
        )
    if case.point == 2:
        return libration.earth_moon_l2_halo(
            x_amplitude=case.amplitude,
            southern=case.southern,
        )
    raise ValueError(f"unsupported Halo point: {case.point}")


def compare_halo(case: HaloCase) -> None:
    result = halo(case)
    if result.is_barycentric:
        raise CrossValidationError(f"{case.id} unexpectedly returned barycentric states")
    if case.point == 1:
        expected_z = -case.amplitude if case.southern else case.amplitude
        amplitude_residual = abs(result.corrected_state.z - expected_z)
    else:
        amplitude_residual = abs((result.corrected_state.x - 1.0) - case.amplitude)
        expected_z_sign = -1.0 if case.southern else 1.0
        if math.copysign(1.0, result.corrected_state.z) != expected_z_sign:
            raise CrossValidationError(
                f"{case.id} z sign={result.corrected_state.z:.12g} contradicts branch"
            )
    if amplitude_residual > AMPLITUDE_ABS_TOL:
        raise CrossValidationError(
            f"{case.id} amplitude residual={amplitude_residual:.12g}, "
            f"tolerance={AMPLITUDE_ABS_TOL:.12g}"
        )
    if any(
        abs(value) > AMPLITUDE_ABS_TOL
        for value in (
            result.corrected_state.y,
            result.corrected_state.vx,
            result.corrected_state.vz,
        )
    ):
        raise CrossValidationError(f"{case.id} corrected state is not an XZ-plane crossing")
    metrics = validate_periodic_orbit(result)
    print(
        f"PERIODIC_FAMILY_CASE={case.id} period={result.period:.12g} "
        f"sample_residual={metrics.max_sample_residual:.12g} "
        f"closure={metrics.closure_residual:.12g} "
        f"jacobi_drift={metrics.jacobi_drift:.12g}"
    )
    assert_periodic_metrics(metrics, case_id=case.id)


def compare_dro(case: DroCase) -> None:
    result = libration.earth_moon_dro(x_amplitude=case.amplitude)
    if result.is_barycentric:
        raise CrossValidationError(f"{case.id} unexpectedly returned barycentric states")
    amplitude_residual = abs((result.corrected_state.x - 1.0) - case.amplitude)
    if amplitude_residual > AMPLITUDE_ABS_TOL:
        raise CrossValidationError(
            f"{case.id} amplitude residual={amplitude_residual:.12g}, "
            f"tolerance={AMPLITUDE_ABS_TOL:.12g}"
        )
    if result.corrected_state.vy >= 0.0:
        raise CrossValidationError(f"{case.id} vy={result.corrected_state.vy:.12g}, expected < 0")
    if any(
        abs(value) > AMPLITUDE_ABS_TOL
        for value in (
            result.corrected_state.y,
            result.corrected_state.z,
            result.corrected_state.vx,
            result.corrected_state.vz,
        )
    ):
        raise CrossValidationError(f"{case.id} corrected state is not planar at +X crossing")
    metrics = validate_periodic_orbit(result)
    print(
        f"PERIODIC_FAMILY_CASE={case.id} period={result.period:.12g} "
        f"sample_residual={metrics.max_sample_residual:.12g} "
        f"closure={metrics.closure_residual:.12g} "
        f"jacobi_drift={metrics.jacobi_drift:.12g}"
    )
    assert_periodic_metrics(metrics, case_id=case.id)


def compare_reflection(*, point: int, amplitude: float) -> None:
    north = halo(
        HaloCase(
            id=f"l{point}_reflection_north",
            point=point,
            amplitude=amplitude,
            southern=False,
        )
    )
    south = halo(
        HaloCase(
            id=f"l{point}_reflection_south",
            point=point,
            amplitude=amplitude,
            southern=True,
        )
    )
    north_times, north_states = periodic_arrays(north)
    south_times, south_states = periodic_arrays(south)
    reflected_states = north_states.copy()
    reflected_states[:, 2] *= -1.0
    reflected_states[:, 5] *= -1.0
    time_residual = maximum_absolute_residual(north_times, south_times)
    state_residual = maximum_absolute_residual(reflected_states, south_states)
    period_residual = abs(north.period - south.period)
    print(
        f"HALO_REFLECTION_CASE=l{point}/amplitude={amplitude:.12g} "
        f"time_residual={time_residual:.12g} state_residual={state_residual:.12g} "
        f"period_residual={period_residual:.12g}"
    )
    if max(time_residual, state_residual, period_residual) > REFLECTION_ABS_TOL:
        raise CrossValidationError(
            f"L{point} amplitude={amplitude} reflection residuals: "
            f"time={time_residual:.12g}, state={state_residual:.12g}, "
            f"period={period_residual:.12g}"
        )


def test_halo_families_match_independent_propagation() -> None:
    configure_astrox_from_env()
    for case in HALO_CASES:
        compare_halo(case)


def test_dro_family_matches_independent_propagation() -> None:
    configure_astrox_from_env()
    for case in DRO_CASES:
        compare_dro(case)


def test_halo_north_south_reflection_at_low_middle_high_amplitudes() -> None:
    configure_astrox_from_env()
    for point, amplitudes in (
        (1, (0.022, 0.10, 0.199)),
        (2, (L2_FIRST_AVAILABLE_AMPLITUDE, 0.10, 0.1928)),
    ):
        for amplitude in amplitudes:
            compare_reflection(point=point, amplitude=amplitude)


@pytest.mark.parametrize(
    ("function", "message"),
    [
        (
            lambda: libration.earth_moon_l2_halo(
                x_amplitude=0.026,
                southern=False,
            ),
            "0.026000000000018453",
        ),
        (
            lambda: libration.earth_moon_dro(x_amplitude=0.078),
            "0.0780437044745057",
        ),
    ],
)
def test_advertised_rounded_low_boundaries_are_rejected(
    function: Callable[[], libration.PeriodicOrbit],
    message: str,
) -> None:
    configure_astrox_from_env()
    with pytest.raises(exceptions.AstroxAPIError, match=message):
        function()


def main() -> int:
    try:
        test_halo_families_match_independent_propagation()
        test_dro_family_matches_independent_propagation()
        test_halo_north_south_reflection_at_low_middle_high_amplitudes()
        for function, _message in (
            (
                lambda: libration.earth_moon_l2_halo(
                    x_amplitude=0.026,
                    southern=False,
                ),
                "",
            ),
            (lambda: libration.earth_moon_dro(x_amplitude=0.078), ""),
        ):
            try:
                function()
            except exceptions.AstroxAPIError:
                pass
            else:
                raise CrossValidationError(
                    "advertised rounded low boundary unexpectedly became accepted"
                )
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    checked = len(HALO_CASES) + len(DRO_CASES) + 6 + 2
    print(f"CROSS_VALIDATION_CHECKED={checked}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
