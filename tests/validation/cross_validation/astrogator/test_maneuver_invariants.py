#!/usr/bin/env python3
"""Cross-validate RunMCS maneuver outputs against local invariants."""

# Coverage:
#   Branches:
#     - impulsive VelocityVector: verified
#     - impulsive AntiVelocityVector: verified
#     - finite VelocityVector with constant engine and TwoBody propagator: verified
#   Fields:
#     - impulsive velocity jump and VNC direction: verified
#     - finite total inertial/VNC delta-v arrays: verified
#     - finite thrust-only DeltaV_Mag: verified by rocket equation
#     - FuelUsed and final fuel mass: verified by constant mass-flow equation
#   Parameters:
#     - positive/negative along-velocity direction: verified
#     - 100 m/s impulsive magnitude and 500 N / 600 s / 1 s finite burn: verified
#   Comparison:
#     - Independent local vectors, VNC basis, spherical conversion, and Tsiolkovsky equation
#     - Constants: initial dry/fuel mass 500 kg each, g=9.80665 m/s^2
#     - Tolerances: vector 1e-8 m/s; mass 1e-10 kg; scalar 1e-10 m/s
#
# Calibration notes:
#   - DeltaV_Mag matches the rocket-equation exhaust delta-v from the actual fuel
#     change, while the first three values in DeltaV_Inertial/VNC are the total
#     boundary velocity change including gravity.
#   - The last three values of each six-value array are azimuth, elevation, and
#     magnitude of that array's first three values.

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import astrogator, exceptions, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


MU = 398600441500000.0
START = "2026-01-01T00:00:00Z"
MASS_EPS = 1.0e-10
VECTOR_EPS = 1.0e-8
SCALAR_EPS = 1.0e-10


class CrossValidationError(Exception):
    """Raised when a maneuver invariant fails."""


def initial_state() -> astrogator.KeplerianState:
    return astrogator.keplerian_state(
        semi_major_axis_m=7_000_000.0,
        eccentricity=0.3,
        inclination_deg=45.0,
        raan_deg=30.0,
        argument_of_periapsis_deg=60.0,
        gravitational_parameter_m3_s2=MU,
        true_anomaly_deg=30.0,
    )


def two_body_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        name="PR15_Maneuver_TwoBody",
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="PR15_Maneuver_RKF",
            use_fixed_step=True,
            initial_step_s=0.1,
            max_step_s=0.1,
            min_step_s=0.1,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_two_body_gravity(
            name="PR15_Maneuver_Gravity",
            gravitational_parameter_m3_s2=MU,
        ),
    )


def vector_angles(values: np.ndarray) -> tuple[float, float, float]:
    magnitude = float(np.linalg.norm(values))
    return (
        math.degrees(math.atan2(float(values[1]), float(values[0]))),
        math.degrees(math.asin(float(values[2]) / magnitude)),
        magnitude,
    )


def vnc_basis(position: np.ndarray, velocity: np.ndarray) -> np.ndarray:
    v_axis = velocity / np.linalg.norm(velocity)
    n_axis = np.cross(position, velocity)
    n_axis = n_axis / np.linalg.norm(n_axis)
    c_axis = np.cross(v_axis, n_axis)
    return np.vstack((v_axis, n_axis, c_axis))


def run_impulsive(control: astrogator.ImpulsiveAttitudeControl) -> astrogator.ManeuverImpulsiveResult:
    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", initial_state(), epoch=START),
            astrogator.impulsive_maneuver(
                "Burn",
                attitude_control=control,
                propulsion_method_value="Constant_Thrust_Isp",
                update_mass=False,
            ),
        ]
    )
    segment = result.main_sequence_results[-1]
    if not isinstance(segment, astrogator.ManeuverImpulsiveResult):
        raise CrossValidationError(f"expected impulsive result, got {type(segment).__name__}")
    return segment


def compare_impulsive(control: astrogator.ImpulsiveAttitudeControl, sign: float) -> None:
    segment = run_impulsive(control)
    initial = np.asarray(segment.initial_state.cartesian.to_wire())
    final = np.asarray(segment.final_state.cartesian.to_wire())
    velocity = initial[3:]
    observed_jump = final[3:] - velocity
    expected_jump = sign * 100.0 * velocity / np.linalg.norm(velocity)
    information = segment.maneuver_information
    if np.max(np.abs(observed_jump - expected_jump)) > VECTOR_EPS:
        raise CrossValidationError(f"impulsive velocity jump mismatch: {observed_jump} vs {expected_jump}")
    if np.max(np.abs(np.asarray(information.delta_v_inertial[:3]) - expected_jump)) > VECTOR_EPS:
        raise CrossValidationError("impulsive DeltaV_Inertial does not equal boundary velocity jump")
    expected_vnc = np.array([sign * 100.0, 0.0, 0.0])
    if np.max(np.abs(np.asarray(information.delta_v_vnc[:3]) - expected_vnc)) > VECTOR_EPS:
        raise CrossValidationError("impulsive DeltaV_VNC does not preserve along-velocity sign")
    if abs(information.delta_v_magnitude_m_s - 100.0) > SCALAR_EPS:
        raise CrossValidationError("impulsive DeltaV_Mag mismatch")
    if information.fuel_used_kg != 0.0 or segment.final_state.fuel_mass_kg != segment.initial_state.fuel_mass_kg:
        raise CrossValidationError("UpdateMass=false changed impulsive fuel")


def compare_finite() -> None:
    thrust_n = 500.0
    isp_s = 600.0
    gravity_m_s2 = 9.80665
    duration_s = 1.0
    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", initial_state(), epoch=START),
            astrogator.finite_maneuver(
                "Burn",
                attitude_control=astrogator.finite_velocity_vector(),
                propagator_name="PR15_Maneuver_TwoBody",
                stop_conditions=[astrogator.duration_stop("Duration", duration_s)],
                propulsion_method_value="EngineA",
            ),
        ],
        propagators=[two_body_config()],
        engine_models=[
            astrogator.constant_engine(
                name="EngineA",
                thrust_n=thrust_n,
                isp_s=isp_s,
                gravitational_acceleration_m_s2=gravity_m_s2,
            )
        ],
    )
    segment = result.main_sequence_results[-1]
    if not isinstance(segment, astrogator.ManeuverFiniteResult):
        raise CrossValidationError(f"expected finite result, got {type(segment).__name__}")
    information = segment.maneuver_information
    initial = np.asarray(segment.initial_state.cartesian.to_wire())
    final = np.asarray(segment.final_state.cartesian.to_wire())
    total_delta_v = final[3:] - initial[3:]
    inertial = np.asarray(information.delta_v_inertial[:3])
    if np.max(np.abs(total_delta_v - inertial)) > VECTOR_EPS:
        raise CrossValidationError("finite DeltaV_Inertial first three values mismatch final velocity jump")

    vnc = vnc_basis(initial[:3], initial[3:]) @ total_delta_v
    observed_vnc = np.asarray(information.delta_v_vnc[:3])
    if np.max(np.abs(vnc - observed_vnc)) > VECTOR_EPS:
        raise CrossValidationError(f"finite VNC mismatch: {vnc} vs {observed_vnc}")
    if np.max(np.abs(np.asarray(information.delta_v_inertial[3:]) - vector_angles(inertial))) > VECTOR_EPS:
        raise CrossValidationError("finite inertial spherical delta-v values mismatch")
    if np.max(np.abs(np.asarray(information.delta_v_vnc[3:]) - vector_angles(vnc))) > VECTOR_EPS:
        raise CrossValidationError("finite VNC spherical delta-v values mismatch")

    expected_fuel = thrust_n / (isp_s * gravity_m_s2) * duration_s
    if abs(information.fuel_used_kg - expected_fuel) > MASS_EPS:
        raise CrossValidationError("finite FuelUsed does not match constant mass flow")
    if abs(segment.initial_state.fuel_mass_kg - segment.final_state.fuel_mass_kg - expected_fuel) > MASS_EPS:
        raise CrossValidationError("finite fuel boundary masses do not match FuelUsed")
    expected_delta_v = isp_s * gravity_m_s2 * math.log(
        (segment.initial_state.dry_mass_kg + segment.initial_state.fuel_mass_kg)
        / (segment.final_state.dry_mass_kg + segment.final_state.fuel_mass_kg)
    )
    if abs(information.delta_v_magnitude_m_s - expected_delta_v) > SCALAR_EPS:
        raise CrossValidationError("finite DeltaV_Mag does not match rocket equation")


def test_maneuver_outputs_match_invariants() -> None:
    configure_astrox_from_env()
    compare_impulsive(astrogator.impulsive_velocity_vector(100.0), 1.0)
    compare_impulsive(astrogator.impulsive_anti_velocity_vector(100.0), -1.0)
    compare_finite()


def main() -> int:
    try:
        test_maneuver_outputs_match_invariants()
    except (CrossValidationError, exceptions.AstroxError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=3")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
