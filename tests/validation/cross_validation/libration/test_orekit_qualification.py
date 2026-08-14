#!/usr/bin/env python3
"""Cross-validate ASTROX libration semantics with Orekit 13.1."""

# Coverage:
#   Verified roles:
#     - analytical L4/L5 points, CR3BP force propagation, and STM: verified
#     - Richardson northern/southern L1 and L2 Halo seeds plus differential correction: partial
#     - ASTROX fixed-x refinement of Orekit-corrected Halo states: verified
#   Constrained roles:
#     - Orekit L1-L3 roots: partial; use a 1 mm absolute solver tolerance in a normalized problem
#       and differ from bracketed roots by up to 1.8e-7, so they are diagnostic only
#     - Orekit L2 correction: partial; treated as a seed because local full-period closure is ~3e-7
#   Parameters:
#     - Earth-Moon mass ratio, L1/L2 point, north/south family, and one propagation arc: partial
#   Reconciliation:
#     - both use barycentric rotating coordinates and nondimensional states
#     - Orekit's factory mass ratio differs from ASTROX defaults, so it is supplied explicitly
#     - Orekit factory dimensional scales are ephemeris-derived and are not used as ASTROX unit evidence
#   Tolerances:
#     - 5e-13 equilibrium coordinates; 2e-11 propagation; 1e-8 STM finite differences
#     - 1e-12 STM determinant
#     - 2e-8 accepted periodic closure and ASTROX correction residual

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import libration  # noqa: E402
from tests.validation._support import (  # noqa: E402
    configure_astrox_from_env,
    ensure_orekit_data,
)
from tests.validation.cross_validation.libration._support import (  # noqa: E402
    JACOBI_DRIFT_ABS_TOL,
    PERIODIC_CLOSURE_ABS_TOL,
    PERIODIC_SAMPLE_ABS_TOL,
    ROOT_ABS_TOL,
    SYMMETRY_ABS_TOL,
    CrossValidationError,
    jacobi_drift,
    maximum_absolute_residual,
    propagate_local,
)


OREKIT_PROPAGATION_ABS_TOL = 2.0e-11
OREKIT_STM_FINITE_DIFFERENCE_ABS_TOL = 1.0e-8
OREKIT_STM_DETERMINANT_ABS_TOL = 1.0e-12
OREKIT_COLLINEAR_ROOT_RESIDUAL_MIN = 1.0e-8
OREKIT_COLLINEAR_ROOT_RESIDUAL_MAX = 1.0e-6
OREKIT_L2_SEED_CLOSURE_MIN = 1.0e-8
OREKIT_L2_SEED_CLOSURE_MAX = 1.0e-6
HALO_AMPLITUDE_FRACTION = 0.05


@dataclass(frozen=True, kw_only=True)
class HaloCase:
    id: str
    point: int
    southern: bool


HALO_CASES = tuple(
    HaloCase(
        id=f"l{point}_{'south' if southern else 'north'}",
        point=point,
        southern=southern,
    )
    for point in (1, 2)
    for southern in (False, True)
)


class OrekitContext:
    """Initialize Orekit once and expose only the CRTBP operations used here."""

    def __init__(self) -> None:
        import jpype
        import orekit_jpype as orekit

        if not jpype.isJVMStarted():
            orekit.initVM(vmargs="--enable-native-access=ALL-UNNAMED")

        from orekit_jpype.pyhelpers import setup_orekit_data
        from org.hipparchus.geometry.euclidean.threed import Vector3D
        from org.hipparchus.ode.nonstiff import DormandPrince853Integrator
        from org.orekit.attitudes import FrameAlignedProvider
        from org.orekit.bodies import CR3BPFactory
        from org.orekit.orbits import HaloOrbit, LibrationOrbitFamily, RichardsonExpansion
        from org.orekit.propagation import SpacecraftState
        from org.orekit.propagation.numerical import NumericalPropagator
        from org.orekit.propagation.numerical.cr3bp import CR3BPForceModel, STMEquations
        from org.orekit.time import AbsoluteDate
        from org.orekit.utils import AbsolutePVCoordinates, LagrangianPoints, PVCoordinates

        setup_orekit_data(str(ensure_orekit_data()), from_pip_library=False)
        self.Vector3D = Vector3D
        self.DormandPrince853Integrator = DormandPrince853Integrator
        self.FrameAlignedProvider = FrameAlignedProvider
        self.HaloOrbit = HaloOrbit
        self.LibrationOrbitFamily = LibrationOrbitFamily
        self.RichardsonExpansion = RichardsonExpansion
        self.SpacecraftState = SpacecraftState
        self.NumericalPropagator = NumericalPropagator
        self.CR3BPForceModel = CR3BPForceModel
        self.STMEquations = STMEquations
        self.AbsoluteDate = AbsoluteDate
        self.AbsolutePVCoordinates = AbsolutePVCoordinates
        self.LagrangianPoints = LagrangianPoints
        self.PVCoordinates = PVCoordinates
        self.system = CR3BPFactory.getEarthMoonCR3BP()
        self.mass_ratio = float(self.system.getMassRatio())

    def state_from_pv(self, pv: Any) -> np.ndarray:
        return np.asarray(
            (*pv.getPosition().toArray(), *pv.getVelocity().toArray()),
            dtype=float,
        )

    def propagate_with_stm(
        self,
        initial_state: np.ndarray,
        final_time: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        integrator = self.DormandPrince853Integrator(
            1.0e-12,
            0.001,
            1.0e-13,
            1.0e-13,
        )
        frame = self.system.getRotatingFrame()
        propagator = self.NumericalPropagator(
            integrator,
            self.FrameAlignedProvider(frame),
        )
        propagator.setOrbitType(None)
        propagator.setIgnoreCentralAttraction(True)
        propagator.addForceModel(self.CR3BPForceModel(self.system))
        stm_equations = self.STMEquations(self.system)
        propagator.addAdditionalDerivativesProvider(stm_equations)
        pv = self.PVCoordinates(
            self.Vector3D(*initial_state[:3]),
            self.Vector3D(*initial_state[3:]),
        )
        initial = self.SpacecraftState(
            self.AbsolutePVCoordinates(
                frame,
                self.AbsoluteDate.ARBITRARY_EPOCH,
                pv,
            )
        )
        propagator.setInitialState(stm_equations.setInitialPhi(initial))
        final = propagator.propagate(
            self.AbsoluteDate.ARBITRARY_EPOCH.shiftedBy(final_time)
        )
        final_state = np.asarray(
            (*final.getPosition().toArray(), *final.getVelocity().toArray()),
            dtype=float,
        )
        java_stm = stm_equations.getStateTransitionMatrix(final)
        stm = np.asarray(
            [
                [float(java_stm.getEntry(row, column)) for column in range(6)]
                for row in range(6)
            ],
            dtype=float,
        )
        return final_state, stm

    def corrected_halo(self, case: HaloCase) -> tuple[np.ndarray, float]:
        point = self.LagrangianPoints.L1 if case.point == 1 else self.LagrangianPoints.L2
        family = (
            self.LibrationOrbitFamily.SOUTHERN
            if case.southern
            else self.LibrationOrbitFamily.NORTHERN
        )
        expansion = self.RichardsonExpansion(self.system, point)
        amplitude_m = HALO_AMPLITUDE_FRACTION * float(self.system.getDdim())
        halo = self.HaloOrbit(expansion, amplitude_m, family)
        halo.applyDifferentialCorrection()
        return self.state_from_pv(halo.getInitialPV()), float(halo.getOrbitalPeriod())


def test_orekit_points_are_classified_against_astrox_and_bracketed_roots() -> None:
    configure_astrox_from_env()
    orekit = OrekitContext()
    result = libration.positions(mass_ratio=orekit.mass_ratio)
    orekit_points = tuple(
        orekit.system.getLPosition(point)
        for point in (
            orekit.LagrangianPoints.L1,
            orekit.LagrangianPoints.L2,
            orekit.LagrangianPoints.L3,
            orekit.LagrangianPoints.L4,
            orekit.LagrangianPoints.L5,
        )
    )
    astrox_points = (result.l1, result.l2, result.l3, result.l4, result.l5)
    residuals = tuple(
        max(abs(astrox.x - float(orekit_point.getX())), abs(astrox.y - float(orekit_point.getY())))
        for astrox, orekit_point in zip(astrox_points, orekit_points, strict=True)
    )
    collinear_residual = max(residuals[:3])
    triangular_residual = max(residuals[3:])
    print(
        "OREKIT_POSITIONS_CASE=earth_moon disposition=collinear_constrained "
        f"collinear={collinear_residual:.12g} triangular={triangular_residual:.12g}"
    )
    if not OREKIT_COLLINEAR_ROOT_RESIDUAL_MIN < collinear_residual < OREKIT_COLLINEAR_ROOT_RESIDUAL_MAX:
        raise CrossValidationError(
            f"Orekit collinear-point residual changed to {collinear_residual:.12g}"
        )
    if triangular_residual > ROOT_ABS_TOL:
        raise CrossValidationError(
            f"Orekit triangular-point residual={triangular_residual:.12g}"
        )


def test_orekit_crtbp_propagation_and_stm_match_local_equations() -> None:
    orekit = OrekitContext()
    state = np.asarray((0.823844660756625, 0.0, 0.05, 0.0, 0.159703975128827, 0.0))
    final_time = 0.3
    actual, stm = orekit.propagate_with_stm(state, final_time)
    expected = propagate_local(
        mass_ratio=orekit.mass_ratio,
        initial_state=state,
        times=(0.0, final_time),
        is_barycentric=True,
    )[-1]
    state_residual = maximum_absolute_residual(actual, expected)

    epsilon = 1.0e-6
    finite_difference = np.empty((6, 6))
    for column in range(6):
        positive = state.copy()
        negative = state.copy()
        positive[column] += epsilon
        negative[column] -= epsilon
        positive_final = propagate_local(
            mass_ratio=orekit.mass_ratio,
            initial_state=positive,
            times=(0.0, final_time),
            is_barycentric=True,
        )[-1]
        negative_final = propagate_local(
            mass_ratio=orekit.mass_ratio,
            initial_state=negative,
            times=(0.0, final_time),
            is_barycentric=True,
        )[-1]
        finite_difference[:, column] = (positive_final - negative_final) / (2.0 * epsilon)
    stm_residual = maximum_absolute_residual(stm, finite_difference)
    determinant_residual = abs(float(np.linalg.det(stm)) - 1.0)
    print(
        f"OREKIT_PROPAGATION_CASE=earth_moon_0_3 state={state_residual:.12g} "
        f"stm={stm_residual:.12g} determinant={determinant_residual:.12g}"
    )
    if state_residual > OREKIT_PROPAGATION_ABS_TOL:
        raise CrossValidationError(f"Orekit propagation residual={state_residual:.12g}")
    if stm_residual > OREKIT_STM_FINITE_DIFFERENCE_ABS_TOL:
        raise CrossValidationError(f"Orekit STM residual={stm_residual:.12g}")
    if determinant_residual > OREKIT_STM_DETERMINANT_ABS_TOL:
        raise CrossValidationError(
            f"Orekit STM determinant residual={determinant_residual:.12g}"
        )


def test_orekit_halo_correction_is_independently_classified_and_refined_by_astrox() -> None:
    configure_astrox_from_env()
    orekit = OrekitContext()
    for case in HALO_CASES:
        state, period = orekit.corrected_halo(case)
        times = np.linspace(0.0, period, 501)
        states = propagate_local(
            mass_ratio=orekit.mass_ratio,
            initial_state=state,
            times=times,
            is_barycentric=True,
        )
        closure = maximum_absolute_residual(states[-1], states[0])
        drift = jacobi_drift(
            states,
            mass_ratio=orekit.mass_ratio,
            is_barycentric=True,
        )
        half_state = states[len(states) // 2]
        symmetry = max(abs(float(half_state[index])) for index in (1, 3, 5))
        expected_sign = -1.0 if case.southern else 1.0
        if np.sign(state[2]) != expected_sign:
            raise CrossValidationError(f"{case.id} branch sign={state[2]:.12g}")
        if drift > JACOBI_DRIFT_ABS_TOL:
            raise CrossValidationError(f"{case.id} Jacobi drift={drift:.12g}")
        if case.point == 1:
            if closure > PERIODIC_CLOSURE_ABS_TOL or symmetry > SYMMETRY_ABS_TOL:
                raise CrossValidationError(
                    f"{case.id} Orekit correction residuals: closure={closure:.12g}, "
                    f"symmetry={symmetry:.12g}"
                )
            disposition = "accepted"
        else:
            if not OREKIT_L2_SEED_CLOSURE_MIN < closure < OREKIT_L2_SEED_CLOSURE_MAX:
                raise CrossValidationError(
                    f"{case.id} Orekit L2 seed closure changed to {closure:.12g}"
                )
            disposition = "constrained_seed"

        seed = libration.crtbp_state(
            x=state[0],
            y=state[1],
            z=state[2],
            vx=state[3],
            vy=state[4],
            vz=state[5],
        )
        astrox = libration.correct_periodic_orbit_fixed_x(
            initial_state=seed,
            period_guess=period,
            mass_ratio=orekit.mass_ratio,
            barycentric=True,
            output_step=0.05,
        )
        corrected = np.asarray(astrox.corrected_state.to_wire(), dtype=float)
        correction_residual = maximum_absolute_residual(corrected, state)
        period_residual = abs(astrox.period - period)
        corrected_states = propagate_local(
            mass_ratio=orekit.mass_ratio,
            initial_state=corrected,
            times=np.linspace(0.0, astrox.period, 501),
            is_barycentric=True,
        )
        corrected_closure = maximum_absolute_residual(
            corrected_states[-1],
            corrected_states[0],
        )
        print(
            f"OREKIT_HALO_CASE={case.id} disposition={disposition} "
            f"orekit_closure={closure:.12g} astrox_delta={correction_residual:.12g} "
            f"period_delta={period_residual:.12g} astrox_closure={corrected_closure:.12g}"
        )
        if case.point == 1 and max(correction_residual, period_residual) > PERIODIC_SAMPLE_ABS_TOL:
            raise CrossValidationError(f"{case.id} ASTROX/Orekit residual too large")
        if corrected_closure > PERIODIC_CLOSURE_ABS_TOL:
            raise CrossValidationError(f"{case.id} ASTROX-refined closure={corrected_closure:.12g}")


def main() -> int:
    checks = (
        test_orekit_points_are_classified_against_astrox_and_bracketed_roots,
        test_orekit_crtbp_propagation_and_stm_match_local_equations,
        test_orekit_halo_correction_is_independently_classified_and_refined_by_astrox,
    )
    try:
        for check in checks:
            check()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"CROSS_VALIDATION_CHECKED={2 + len(HALO_CASES)}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
