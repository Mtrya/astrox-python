#!/usr/bin/env python3
"""Cross-validate a RunMCS differential-corrector target with a local solver."""

# Coverage:
#   Branches:
#     - TargetSequence RunActiveOperators: verified
#     - DifferentialCorrector control path StopConditions.Duration: verified
#     - KeplerianElement(TrueAnomaly) target result: verified
#   Fields:
#     - Converged and TotalIterations: verified
#     - control FinalValue/Correction/Values: verified
#     - constraint CurrentValue/Difference/Values: verified
#     - nested Propagate DurationSec and FinalTA: verified
#   Parameters:
#     - initial control 10 s, perturbation 1 s, desired true anomaly 36 deg: verified
#     - tolerance, max step, and explicit Mu: verified
#   Comparison:
#     - Independent local Keplerian mean-anomaly propagation and one-step finite-difference Newton solve
#     - Constants: a=7000000 m, e=0.3, Mu=398600441500000 m^3/s^2
#     - Tolerances: solver trace 1e-7 s/deg; residual identity 1e-10

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import astrogator, exceptions, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


MU = 398600441500000.0
A_M = 7_000_000.0
E = 0.3
INITIAL_TRUE_ANOMALY_DEG = 30.0
INITIAL_CONTROL_S = 10.0
PERTURBATION_S = 1.0
DESIRED_TRUE_ANOMALY_DEG = 36.0


class CrossValidationError(Exception):
    """Raised when ASTROX and the local target solver disagree."""


def mean_anomaly_from_true(true_anomaly_deg: float) -> float:
    nu = math.radians(true_anomaly_deg)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 - E) * math.sin(nu / 2.0),
        math.sqrt(1.0 + E) * math.cos(nu / 2.0),
    )
    return eccentric_anomaly - E * math.sin(eccentric_anomaly)


def true_anomaly_at_duration(duration_s: float) -> float:
    mean_anomaly = mean_anomaly_from_true(INITIAL_TRUE_ANOMALY_DEG)
    mean_anomaly += math.sqrt(MU / A_M**3) * duration_s
    eccentric_anomaly = mean_anomaly
    for _ in range(30):
        eccentric_anomaly -= (
            eccentric_anomaly - E * math.sin(eccentric_anomaly) - mean_anomaly
        ) / (1.0 - E * math.cos(eccentric_anomaly))
    true_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 + E) * math.sin(eccentric_anomaly / 2.0),
        math.sqrt(1.0 - E) * math.cos(eccentric_anomaly / 2.0),
    )
    return math.degrees(true_anomaly) % 360.0


def local_newton_duration() -> tuple[float, float, float]:
    f0 = true_anomaly_at_duration(INITIAL_CONTROL_S)
    f1 = true_anomaly_at_duration(INITIAL_CONTROL_S + PERTURBATION_S)
    correction = (DESIRED_TRUE_ANOMALY_DEG - f0) / (f1 - f0) * PERTURBATION_S
    final_duration = INITIAL_CONTROL_S + correction
    final_true_anomaly = true_anomaly_at_duration(final_duration)
    return final_duration, final_true_anomaly, correction


def two_body_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        name="PR15_Target_TwoBody",
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="PR15_Target_RKF",
            use_fixed_step=True,
            initial_step_s=0.1,
            max_step_s=0.1,
            min_step_s=0.1,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_two_body_gravity(
            name="PR15_Target_Gravity",
            gravitational_parameter_m3_s2=MU,
        ),
    )


def run_target() -> astrogator.TargetSequenceResult:
    state = astrogator.keplerian_state(
        semi_major_axis_m=A_M,
        eccentricity=E,
        inclination_deg=45.0,
        raan_deg=30.0,
        argument_of_periapsis_deg=60.0,
        gravitational_parameter_m3_s2=MU,
        true_anomaly_deg=INITIAL_TRUE_ANOMALY_DEG,
    )
    coast = astrogator.propagate(
        "Coast",
        propagator_name="PR15_Target_TwoBody",
        stop_conditions=[astrogator.duration_stop("Duration", 60.0)],
        variable_names="StopConditions.Duration",
        results=[
            astrogator.keplerian_scalar(
                "FinalTA",
                "TrueAnomaly",
                gravitational_parameter_m3_s2=MU,
                coord_system_name="Earth Inertial",
            )
        ],
    )
    profile = astrogator.differential_corrector(
        "DC1",
        controls=[
            astrogator.differential_corrector_control(
                "StopConditions.Duration",
                INITIAL_CONTROL_S,
                parent_name="Coast",
                perturbation=PERTURBATION_S,
                max_step=600.0,
                tolerance=0.0001,
            )
        ],
        results=[
            astrogator.differential_corrector_constraint(
                "FinalTA",
                DESIRED_TRUE_ANOMALY_DEG,
                parent_name="Coast",
                tolerance=0.1,
            )
        ],
        maximum_iterations=50,
    )
    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state, epoch="2026-01-01T00:00:00Z"),
            astrogator.target_sequence(
                "Target",
                [coast],
                action="RunActiveOperators",
                profiles=[profile],
            ),
        ],
        propagators=[two_body_config()],
    )
    target = result.main_sequence_results[-1]
    if not isinstance(target, astrogator.TargetSequenceResult):
        raise CrossValidationError(f"expected TargetSequenceResult, got {type(target).__name__}")
    return target


def compare_target() -> None:
    target = run_target()
    if len(target.operator_results) != 1:
        raise CrossValidationError(f"expected one operator result, got {len(target.operator_results)}")
    operator = target.operator_results[0]
    if not isinstance(operator, astrogator.DifferentialCorrectorResult):
        raise CrossValidationError(f"expected DifferentialCorrectorResult, got {type(operator).__name__}")
    if not operator.converged or operator.total_iterations != 1:
        raise CrossValidationError("ASTROX target operator did not report one-step convergence")
    if len(operator.control_parameters) != 1 or len(operator.results) != 1:
        raise CrossValidationError("ASTROX target trace shape changed")

    expected_duration, expected_true_anomaly, expected_correction = local_newton_duration()
    control = operator.control_parameters[0]
    constraint = operator.results[0]
    child = target.segment_results[0]
    if not isinstance(child, astrogator.PropagateResult):
        raise CrossValidationError(f"expected nested PropagateResult, got {type(child).__name__}")
    observed_duration = child.duration_s
    observed_true_anomaly = child.scalar_results["FinalTA"]
    checks = (
        ("duration", observed_duration, expected_duration, 1.0e-7),
        ("control final value", float(control.final_value), expected_duration, 1.0e-7),
        ("control correction", control.correction, expected_correction, 1.0e-7),
        ("FinalTA", observed_true_anomaly, expected_true_anomaly, 1.0e-7),
        ("constraint current value", float(constraint.current_value), expected_true_anomaly, 1.0e-7),
        ("constraint difference", constraint.difference, expected_true_anomaly - DESIRED_TRUE_ANOMALY_DEG, 1.0e-10),
    )
    for name, observed, expected, tolerance in checks:
        if abs(float(observed) - float(expected)) > tolerance:
            raise CrossValidationError(f"{name}: observed={observed:.12g}, expected={expected:.12g}")
    if abs(float(control.values[-1]) - expected_duration) > 1.0e-7:
        raise CrossValidationError("control Values history does not contain the final duration")
    if abs(float(constraint.values[-1]) - expected_true_anomaly) > 1.0e-7:
        raise CrossValidationError("constraint Values history does not contain the final value")


def test_target_sequence_matches_local_newton_solver() -> None:
    configure_astrox_from_env()
    compare_target()


def main() -> int:
    try:
        test_target_sequence_matches_local_newton_solver()
    except (CrossValidationError, exceptions.AstroxError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
