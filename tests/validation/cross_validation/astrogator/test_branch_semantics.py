#!/usr/bin/env python3
"""Cross-validate RunMCS branch semantics with independent local derivations."""

# Coverage:
#   Branches:
#     - Epoch stopping condition: verified (UTC epoch arithmetic)
#     - Apoapsis stopping condition: verified (conic half-period from periapsis)
#     - Periapsis stopping condition: verified (conic half-period from apoapsis)
#     - Enabled top-level Stop: verified (sequence termination, no result objects)
#     - TargetSequence RunNominalSequence without profiles: verified (direct
#       same-sequence execution comparison plus local Kepler timing)
#     - Impulsive maneuver with UpdateMass=true and a registered constant engine:
#       verified (rocket equation and mass-difference accounting)
#   Fields:
#     - Propagate DurationSec and final epoch at the stop event: verified
#     - StoppingConditionName echo: verified
#     - FinalState Keplerian true anomaly at apsidal stops: verified
#     - SegmentResults absence after an enabled Stop: verified
#     - TargetSequenceResult operator_results and recursive segment_results: verified
#     - Impulsive UpdateMass/FuelUsed/final fuel mass/DeltaV_Mag: verified
#   Parameters:
#     - 600 s epoch trip; apoapsis/periapsis from exact apsides; 100 m/s
#       impulsive burn with a 500 N / 600 s / 9.80665 m/s^2 engine: verified
#   Comparison:
#     - Independent UTC epoch arithmetic, conic orbital-period computation,
#       local Kepler mean-anomaly solve, direct same-sequence execution, and
#       the Tsiolkovsky rocket equation
#     - Constants: MU=398600441500000 m^3/s^2; a=7000000 m; e=0.3;
#       dry/fuel mass 500 kg each; g=9.80665 m/s^2
#     - Tolerances: epoch 1e-6 s and exact UTCG string; duration 1e-4 s;
#       true anomaly 1e-4 deg; mass 1e-9 kg; delta-v 1e-6 m/s
#
# Calibration notes:
#   - With UpdateMass=true the engine collection is searched by the name in
#     PropulsionMethodValue; the literal name "Constant_Thrust_Isp" is not
#     found unless an engine is explicitly registered (DISCOVERY_LOG). The
#     registered EngineConstant "EngineA" is referenced by that name.
#   - The periapsis stop event boundary uses the configured event tolerance,
#     so its duration residual (~5e-6 s) is slightly larger than the apoapsis
#     case; both stay far below the 1e-4 s tolerance.

from __future__ import annotations

import math
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import astrogator, exceptions, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


MU = 398600441500000.0
START = "2026-01-01T00:00:00Z"
STEP_S = 0.1
SEMI_MAJOR_AXIS_M = 7_000_000.0
ECCENTRICITY = 0.3
DURATION_EPS_S = 1.0e-4
TRUE_ANOMALY_EPS_DEG = 1.0e-4
MASS_EPS_KG = 1.0e-9
DELTA_V_EPS_M_S = 1.0e-6


class CrossValidationError(Exception):
    """Raised when a RunMCS branch semantics comparison fails."""


def keplerian_state(true_anomaly_deg: float) -> astrogator.KeplerianState:
    return astrogator.keplerian_state(
        semi_major_axis_m=SEMI_MAJOR_AXIS_M,
        eccentricity=ECCENTRICITY,
        inclination_deg=45.0,
        raan_deg=30.0,
        argument_of_periapsis_deg=60.0,
        gravitational_parameter_m3_s2=MU,
        true_anomaly_deg=true_anomaly_deg,
    )


def two_body_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        name="PR15_Semantics_TwoBody",
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="PR15_Semantics_RKF",
            use_fixed_step=True,
            initial_step_s=STEP_S,
            max_step_s=STEP_S,
            min_step_s=STEP_S,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_two_body_gravity(
            name="PR15_Semantics_Gravity",
            gravitational_parameter_m3_s2=MU,
        ),
    )


def last_propagate(result: astrogator.RunMCSResult) -> astrogator.PropagateResult:
    segment = result.main_sequence_results[-1]
    if not isinstance(segment, astrogator.PropagateResult):
        raise CrossValidationError(f"expected PropagateResult, got {type(segment).__name__}")
    return segment


def utc_plus_seconds(epoch_utc: str, delta_s: float) -> str:
    """Independent UTC epoch arithmetic returning the server's UTCG format."""
    parsed = datetime.fromisoformat(epoch_utc.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    shifted = (parsed + timedelta(seconds=delta_s)).astimezone(UTC)
    return f"{shifted.strftime('%Y-%m-%dT%H:%M:%S')}.{shifted.microsecond // 1000:03d}Z"


def utc_seconds_between(first: str, second: str) -> float:
    """Independent UTC epoch difference in seconds."""
    return (
        datetime.fromisoformat(second.replace("Z", "+00:00"))
        - datetime.fromisoformat(first.replace("Z", "+00:00"))
    ).total_seconds()


def orbital_period_s() -> float:
    """Two-body orbital period for the fixed Keplerian case."""
    return 2.0 * math.pi * math.sqrt(SEMI_MAJOR_AXIS_M**3 / MU)


def true_anomaly_at_duration(duration_s: float, initial_true_anomaly_deg: float) -> float:
    """Independent Kepler solve: true anomaly after a duration on the fixed orbit."""
    mean_motion = math.sqrt(MU / SEMI_MAJOR_AXIS_M**3)
    nu = math.radians(initial_true_anomaly_deg)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 - ECCENTRICITY) * math.sin(nu / 2.0),
        math.sqrt(1.0 + ECCENTRICITY) * math.cos(nu / 2.0),
    )
    mean_anomaly = eccentric_anomaly - ECCENTRICITY * math.sin(eccentric_anomaly)
    mean_anomaly += mean_motion * duration_s
    eccentric_anomaly = mean_anomaly
    for _ in range(30):
        eccentric_anomaly -= (
            eccentric_anomaly - ECCENTRICITY * math.sin(eccentric_anomaly) - mean_anomaly
        ) / (1.0 - ECCENTRICITY * math.cos(eccentric_anomaly))
    return math.degrees(
        2.0
        * math.atan2(
            math.sqrt(1.0 + ECCENTRICITY) * math.sin(eccentric_anomaly / 2.0),
            math.sqrt(1.0 - ECCENTRICITY) * math.cos(eccentric_anomaly / 2.0),
        )
    ) % 360.0


def compare_epoch_stop() -> None:
    """Epoch stop at START + 600 s: final epoch and DurationSec from UTC arithmetic."""
    target_epoch = utc_plus_seconds(START, 600.0)
    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", keplerian_state(30.0), epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name="PR15_Semantics_TwoBody",
                stop_conditions=[astrogator.epoch_stop("EpochStop", target_epoch)],
            ),
        ],
        propagators=[two_body_config()],
    )
    segment = last_propagate(result)
    if abs(segment.duration_s - 600.0) > DURATION_EPS_S:
        raise CrossValidationError(f"Epoch stop DurationSec={segment.duration_s!r}, expected 600.0")
    if segment.final_state.epoch != target_epoch:
        raise CrossValidationError(
            f"Epoch stop final epoch {segment.final_state.epoch!r}, expected {target_epoch!r}"
        )
    epoch_delta = utc_seconds_between(START, segment.final_state.epoch)
    if abs(epoch_delta - segment.duration_s) > DURATION_EPS_S:
        raise CrossValidationError(
            f"Epoch stop DurationSec={segment.duration_s} disagrees with epoch "
            f"arithmetic delta {epoch_delta}"
        )
    if segment.stopping_condition_name != "EpochStop":
        raise CrossValidationError(
            f"Epoch stop StoppingConditionName={segment.stopping_condition_name!r}, "
            "expected 'EpochStop'"
        )


def compare_apoapsis_stop() -> None:
    """Apoapsis stop from periapsis (TA=0): half orbital period, TA ~ 180 deg."""
    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", keplerian_state(0.0), epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name="PR15_Semantics_TwoBody",
                stop_conditions=[
                    astrogator.apoapsis_stop("Apo", gravitational_parameter_m3_s2=MU)
                ],
            ),
        ],
        propagators=[two_body_config()],
    )
    segment = last_propagate(result)
    expected_duration = orbital_period_s() / 2.0
    if abs(segment.duration_s - expected_duration) > DURATION_EPS_S:
        raise CrossValidationError(
            f"Apoapsis stop DurationSec={segment.duration_s:.12g}, expected "
            f"half period {expected_duration:.12g}"
        )
    residual = abs(segment.final_state.keplerian.true_anomaly_deg - 180.0)
    if residual > TRUE_ANOMALY_EPS_DEG:
        raise CrossValidationError(
            f"Apoapsis stop true anomaly={segment.final_state.keplerian.true_anomaly_deg:.12g} "
            f"deg, expected 180 deg within {TRUE_ANOMALY_EPS_DEG:g}"
        )
    if segment.stopping_condition_name != "Apo":
        raise CrossValidationError(
            f"Apoapsis stop StoppingConditionName={segment.stopping_condition_name!r}, "
            "expected 'Apo'"
        )


def compare_periapsis_stop() -> None:
    """Periapsis stop from apoapsis (TA=180): half orbital period, TA ~ 0 deg."""
    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", keplerian_state(180.0), epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name="PR15_Semantics_TwoBody",
                stop_conditions=[
                    astrogator.periapsis_stop("Peri", gravitational_parameter_m3_s2=MU)
                ],
            ),
        ],
        propagators=[two_body_config()],
    )
    segment = last_propagate(result)
    expected_duration = orbital_period_s() / 2.0
    if abs(segment.duration_s - expected_duration) > DURATION_EPS_S:
        raise CrossValidationError(
            f"Periapsis stop DurationSec={segment.duration_s:.12g}, expected "
            f"half period {expected_duration:.12g}"
        )
    residual = abs(
        (segment.final_state.keplerian.true_anomaly_deg + 180.0) % 360.0 - 180.0
    )
    if residual > TRUE_ANOMALY_EPS_DEG:
        raise CrossValidationError(
            f"Periapsis stop true anomaly={segment.final_state.keplerian.true_anomaly_deg:.12g} "
            f"deg, expected 0 deg within {TRUE_ANOMALY_EPS_DEG:g}"
        )
    if segment.stopping_condition_name != "Peri":
        raise CrossValidationError(
            f"Periapsis stop StoppingConditionName={segment.stopping_condition_name!r}, "
            "expected 'Peri'"
        )


def compare_enabled_stop() -> None:
    """Enabled Stop after the initial segment terminates the sequence.

    The Stop segment itself and every later segment must produce no result
    object; the last returned state must be the unpropagated initial state.
    """
    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", keplerian_state(30.0), epoch=START),
            astrogator.stop("StopIt", enable=True),
            astrogator.propagate(
                "Prop",
                propagator_name="PR15_Semantics_TwoBody",
                stop_conditions=[astrogator.duration_stop("Duration", 10.0)],
            ),
        ],
        propagators=[two_body_config()],
    )
    results = result.main_sequence_results
    if len(results) != 1:
        raise CrossValidationError(
            f"Enabled Stop returned {len(results)} result objects "
            f"({[type(item).__name__ for item in results]}); expected only the "
            "InitialState result with no Stop or later-segment results"
        )
    initial = results[0]
    if not isinstance(initial, astrogator.InitialStateResult) or initial.name != "Init":
        raise CrossValidationError(
            f"Enabled Stop first result is {type(initial).__name__}:{initial.name}; "
            "expected InitialStateResult:Init"
        )
    if initial.final_state.epoch != "2026-01-01T00:00:00.000Z":
        raise CrossValidationError(
            f"Enabled Stop left the mission at epoch {initial.final_state.epoch!r}; "
            "no propagation may run after the stop"
        )


def compare_nominal_target_sequence() -> None:
    """RunNominalSequence without profiles matches directly executing the inner sequence.

    The same inner Propagate segment is executed twice: once inside a
    TargetSequence with Action=RunNominalSequence and no profiles, once at the
    top level. Result shape (empty OperatorResults, recursive child results,
    aggregate duration) and the FinalTA scalar must agree, and FinalTA must
    match the independent Kepler mean-anomaly solve.
    """
    inner_results = [
        astrogator.keplerian_scalar(
            "FinalTA", "TrueAnomaly",
            gravitational_parameter_m3_s2=MU,
            coord_system_name="Earth Inertial",
        )
    ]
    inner = astrogator.propagate(
        "Coast",
        propagator_name="PR15_Semantics_TwoBody",
        stop_conditions=[astrogator.duration_stop("Duration", 60.0)],
        results=inner_results,
    )
    targeted = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", keplerian_state(30.0), epoch=START),
            astrogator.target_sequence(
                "Tgt", [inner], action="RunNominalSequence",
            ),
        ],
        propagators=[two_body_config()],
    )
    direct = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", keplerian_state(30.0), epoch=START),
            inner,
        ],
        propagators=[two_body_config()],
    )
    target = targeted.main_sequence_results[-1]
    if not isinstance(target, astrogator.TargetSequenceResult):
        raise CrossValidationError(
            f"RunNominalSequence returned {type(target).__name__}; "
            "expected TargetSequenceResult"
        )
    if len(target.operator_results) != 0:
        raise CrossValidationError(
            f"RunNominalSequence without profiles returned {len(target.operator_results)} "
            "operator results; expected none"
        )
    if len(target.segment_results) != 1:
        raise CrossValidationError(
            f"RunNominalSequence returned {len(target.segment_results)} child results; "
            "expected the one inner Propagate result"
        )
    child = target.segment_results[0]
    direct_segment = direct.main_sequence_results[-1]
    if not isinstance(child, astrogator.PropagateResult):
        raise CrossValidationError(
            f"RunNominalSequence child is {type(child).__name__}; expected PropagateResult"
        )
    if abs(target.duration_s - 60.0) > DURATION_EPS_S:
        raise CrossValidationError(f"TargetSequence aggregate DurationSec={target.duration_s!r}")
    if abs(child.duration_s - 60.0) > DURATION_EPS_S:
        raise CrossValidationError(f"child Propagate DurationSec={child.duration_s!r}")
    if not isinstance(direct_segment, astrogator.PropagateResult):
        raise CrossValidationError(
            f"direct execution returned {type(direct_segment).__name__}; "
            "expected PropagateResult"
        )
    if abs(direct_segment.duration_s - target.duration_s) > DURATION_EPS_S:
        raise CrossValidationError(
            "TargetSequence aggregate duration differs from the direct execution "
            f"({target.duration_s} vs {direct_segment.duration_s})"
        )
    if child.final_state.epoch != direct_segment.final_state.epoch:
        raise CrossValidationError(
            "TargetSequence child final epoch differs from direct execution "
            f"({child.final_state.epoch!r} vs {direct_segment.final_state.epoch!r})"
        )
    observed_ta = child.scalar_results["FinalTA"]
    direct_ta = direct_segment.scalar_results["FinalTA"]
    if float(observed_ta) != float(direct_ta):
        raise CrossValidationError(
            f"RunNominalSequence FinalTA={observed_ta!r} differs from direct "
            f"execution FinalTA={direct_ta!r}"
        )
    expected_ta = true_anomaly_at_duration(60.0, 30.0)
    if abs(float(observed_ta) - expected_ta) > TRUE_ANOMALY_EPS_DEG:
        raise CrossValidationError(
            f"RunNominalSequence FinalTA={float(observed_ta):.12g}, independent "
            f"Kepler solve={expected_ta:.12g}"
        )


def compare_impulsive_update_mass() -> None:
    """Impulsive VelocityVector with UpdateMass=true and a registered engine.

    Independent checks: fuel mass difference equals FuelUsed; final fuel mass
    and FuelUsed match the Tsiolkovsky equation m1 = m0 * exp(-dv/(Isp*g));
    EstimatedFuelUsed equals FuelUsed; DeltaV_Mag equals the commanded 100 m/s.
    """
    thrust_n = 500.0
    isp_s = 600.0
    gravity_m_s2 = 9.80665
    delta_v_m_s = 100.0
    dry_mass_kg = 500.0
    fuel_mass_kg = 500.0
    result = astrogator.run_mcs(
        [
            astrogator.initial_state(
                "Init", keplerian_state(30.0), epoch=START,
                dry_mass_kg=dry_mass_kg, fuel_mass_kg=fuel_mass_kg,
            ),
            astrogator.impulsive_maneuver(
                "Burn",
                attitude_control=astrogator.impulsive_velocity_vector(delta_v_m_s),
                # Live discovery: with UpdateMass=true the engine collection is
                # searched by the name in PropulsionMethodValue; the literal
                # "Constant_Thrust_Isp" is not found unless an engine with that
                # name is registered. The real combination is the registered
                # EngineConstant name.
                propulsion_method_value="EngineA",
                update_mass=True,
            ),
        ],
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
    if not isinstance(segment, astrogator.ManeuverImpulsiveResult):
        raise CrossValidationError(
            f"expected ManeuverImpulsiveResult, got {type(segment).__name__}"
        )
    information = segment.maneuver_information
    if information.update_mass is not True:
        raise CrossValidationError(f"UpdateMass echo is {information.update_mass!r}, expected True")
    initial_fuel = segment.initial_state.fuel_mass_kg
    final_fuel = segment.final_state.fuel_mass_kg
    if segment.final_state.dry_mass_kg != dry_mass_kg:
        raise CrossValidationError(
            f"dry mass changed across the impulsive burn: {segment.final_state.dry_mass_kg!r}"
        )
    if abs(information.fuel_used_kg - (initial_fuel - final_fuel)) > MASS_EPS_KG:
        raise CrossValidationError(
            "FuelUsed does not equal the boundary fuel mass difference "
            f"({information.fuel_used_kg} vs {initial_fuel - final_fuel})"
        )
    initial_total = dry_mass_kg + initial_fuel
    expected_final_total = initial_total * math.exp(-delta_v_m_s / (isp_s * gravity_m_s2))
    expected_final_fuel = expected_final_total - dry_mass_kg
    if abs(final_fuel - expected_final_fuel) > MASS_EPS_KG:
        raise CrossValidationError(
            f"final fuel mass {final_fuel:.12g} does not match the rocket equation "
            f"value {expected_final_fuel:.12g}"
        )
    expected_fuel_used = initial_total - expected_final_total
    if abs(information.fuel_used_kg - expected_fuel_used) > MASS_EPS_KG:
        raise CrossValidationError(
            f"FuelUsed {information.fuel_used_kg:.12g} does not match the rocket "
            f"equation fuel {expected_fuel_used:.12g}"
        )
    if information.estimated_fuel_used_kg is None or (
        abs(information.estimated_fuel_used_kg - information.fuel_used_kg) > MASS_EPS_KG
    ):
        raise CrossValidationError(
            f"EstimatedFuelUsed {information.estimated_fuel_used_kg!r} differs from "
            f"FuelUsed {information.fuel_used_kg}"
        )
    observed_final_total = segment.final_state.dry_mass_kg + final_fuel
    rocket_delta_v = isp_s * gravity_m_s2 * math.log(initial_total / observed_final_total)
    if abs(information.delta_v_magnitude_m_s - delta_v_m_s) > DELTA_V_EPS_M_S:
        raise CrossValidationError(
            f"DeltaV_Mag {information.delta_v_magnitude_m_s!r} differs from the "
            f"commanded {delta_v_m_s} m/s"
        )
    if abs(rocket_delta_v - delta_v_m_s) > DELTA_V_EPS_M_S:
        raise CrossValidationError(
            f"rocket equation delta-v {rocket_delta_v:.12g} differs from the "
            f"commanded {delta_v_m_s} m/s"
        )


def test_epoch_stop_matches_utc_epoch_arithmetic() -> None:
    configure_astrox_from_env()
    compare_epoch_stop()


def test_apoapsis_stop_matches_half_orbital_period() -> None:
    configure_astrox_from_env()
    compare_apoapsis_stop()


def test_periapsis_stop_matches_half_orbital_period() -> None:
    configure_astrox_from_env()
    compare_periapsis_stop()


def test_enabled_stop_matches_sequence_termination() -> None:
    configure_astrox_from_env()
    compare_enabled_stop()


def test_nominal_target_sequence_matches_direct_sequence() -> None:
    configure_astrox_from_env()
    compare_nominal_target_sequence()


def test_impulsive_update_mass_matches_rocket_equation() -> None:
    configure_astrox_from_env()
    compare_impulsive_update_mass()


def main() -> int:
    try:
        test_epoch_stop_matches_utc_epoch_arithmetic()
        test_apoapsis_stop_matches_half_orbital_period()
        test_periapsis_stop_matches_half_orbital_period()
        test_enabled_stop_matches_sequence_termination()
        test_nominal_target_sequence_matches_direct_sequence()
        test_impulsive_update_mass_matches_rocket_equation()
    except (CrossValidationError, exceptions.AstroxError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=6")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
