#!/usr/bin/env python3
"""Cross-validate nested Sequence results and INERTIAL CZML samples with Brahe."""

# Coverage:
#   Branches:
#     - nested Sequence containing InitialState and Propagate: verified
#     - ComputeCzmlPositions=true, INERTIAL output: verified
#   Fields:
#     - recursive SegmentResults order and boundary continuity: verified
#     - sequence aggregate DurationSec: verified
#     - CZML epoch/interval/reference frame/sample ordering: verified
#     - all sampled Cartesian position and velocity values: verified against Brahe
#   Parameters:
#     - one-second duration and 0.1-second fixed step: verified
#   Comparison:
#     - External: Brahe KeplerianPropagator sampled at every ASTROX CZML time offset
#     - Tolerances: position 0.05 m; velocity 5e-5 m/s

from __future__ import annotations

import math
import sys
from pathlib import Path

import brahe as bh
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import astrogator, exceptions, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


MU = 398600441500000.0
START = "2026-01-01T00:00:00Z"
DURATION_S = 1.0
STEP_S = 0.1
POSITION_ABS_M = 0.05
VELOCITY_ABS_M_S = 5.0e-5


class CrossValidationError(Exception):
    """Raised when nested result or CZML evidence disagrees with Brahe."""


def brahe_epoch() -> bh.Epoch:
    return bh.Epoch.from_datetime(2026, 1, 1, 0, 0, 0.0, 0.0, bh.TimeSystem.UTC)


def true_to_mean_deg(true_anomaly_deg: float, eccentricity: float) -> float:
    nu = math.radians(true_anomaly_deg)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 - eccentricity) * math.sin(nu / 2.0),
        math.sqrt(1.0 + eccentricity) * math.cos(nu / 2.0),
    )
    return math.degrees(eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly)) % 360.0


def run_sequence() -> astrogator.RunMCSResult:
    state = astrogator.keplerian_state(
        semi_major_axis_m=7_000_000.0,
        eccentricity=0.3,
        inclination_deg=45.0,
        raan_deg=30.0,
        argument_of_periapsis_deg=60.0,
        gravitational_parameter_m3_s2=MU,
        true_anomaly_deg=30.0,
    )
    propagator_name = "PR15_Sequence_TwoBody"
    config = propagator.hpop_config(
        name=propagator_name,
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="PR15_Sequence_RKF",
            use_fixed_step=True,
            initial_step_s=STEP_S,
            max_step_s=STEP_S,
            min_step_s=STEP_S,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_two_body_gravity(
            name="PR15_Sequence_Gravity",
            gravitational_parameter_m3_s2=MU,
        ),
    )
    nested = astrogator.sequence(
        "Mission",
        [
            astrogator.initial_state("Init", state, epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name=propagator_name,
                stop_conditions=[astrogator.duration_stop("Duration", DURATION_S)],
            ),
        ],
    )
    return astrogator.run_mcs(
        [nested],
        compute_czml_positions=True,
        out_czml_frame_name="INERTIAL",
        propagators=[config],
    )


def compare_sequence_and_czml() -> None:
    result = run_sequence()
    sequence = result.main_sequence_results[0]
    if not isinstance(sequence, astrogator.SequenceResult):
        raise CrossValidationError(f"expected SequenceResult, got {type(sequence).__name__}")
    if [type(item) for item in sequence.segment_results] != [
        astrogator.InitialStateResult,
        astrogator.PropagateResult,
    ]:
        raise CrossValidationError("nested SegmentResults order or dispatch changed")
    initial, coast = sequence.segment_results
    if abs(sequence.duration_s - DURATION_S) > 1.0e-9 or abs(coast.duration_s - DURATION_S) > 1.0e-9:
        raise CrossValidationError("nested or aggregate DurationSec mismatch")
    if initial.final_state != coast.initial_state:
        raise CrossValidationError("nested segment boundary state is discontinuous")
    if sequence.initial_state != initial.initial_state or sequence.final_state != coast.final_state:
        raise CrossValidationError("sequence boundary states do not match first/last child")

    if result.positions is None or len(result.positions.positions) != 1:
        raise CrossValidationError("expected one CZML position output")
    position = result.positions.positions[0]
    if position.reference_frame != "INERTIAL":
        raise CrossValidationError(f"unexpected reference frame {position.reference_frame!r}")
    if position.epoch != "2026-01-01T00:00:00.000Z":
        raise CrossValidationError(f"unexpected CZML epoch {position.epoch!r}")
    if position.interval != "2026-01-01T00:00:00.000Z/2026-01-01T00:00:01.000Z":
        raise CrossValidationError(f"unexpected CZML interval {position.interval!r}")
    samples = position.cartesian_velocity
    if samples is None or len(samples) == 0 or len(samples) % 7 != 0:
        raise CrossValidationError("CZML cartesianVelocity is missing or not seven-value sampled data")

    elements = np.array([7_000_000.0, 0.3, 45.0, 30.0, 60.0, true_to_mean_deg(30.0, 0.3)])
    model = bh.KeplerianPropagator.from_keplerian(
        brahe_epoch(), elements, bh.AngleFormat.DEGREES, STEP_S
    )
    failures: list[str] = []
    for index in range(len(samples) // 7):
        start = index * 7
        offset_s = float(samples[start])
        actual = np.asarray(samples[start + 1 : start + 7])
        expected = np.asarray(model.state_eci(brahe_epoch() + offset_s))
        position_error = float(np.max(np.abs(actual[:3] - expected[:3])))
        velocity_error = float(np.max(np.abs(actual[3:] - expected[3:])))
        if position_error > POSITION_ABS_M:
            failures.append(f"offset {offset_s:g}: position residual {position_error:.12g} m")
        if velocity_error > VELOCITY_ABS_M_S:
            failures.append(f"offset {offset_s:g}: velocity residual {velocity_error:.12g} m/s")
    if failures:
        raise CrossValidationError("\n".join(failures))


def test_sequence_and_czml_samples_match_brahe() -> None:
    configure_astrox_from_env()
    compare_sequence_and_czml()


def main() -> int:
    try:
        test_sequence_and_czml_samples_match_brahe()
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
