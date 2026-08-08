#!/usr/bin/env python3
"""Cross-validate RunMCS two-body propagation against Brahe."""

# Coverage:
#   Branches:
#     - Keplerian InitialState plus registered TwoBody Propagate: verified
#     - three orbit regimes and three durations: verified
#   Fields:
#     - InitialState and FinalState Cartesian values: verified
#     - FinalState osculating Keplerian values: verified
#     - Propagate DurationSec: verified
#   Parameters:
#     - semi-major axis/eccentricity/inclination/anomaly: verified across three cases
#     - explicit gravitational parameter: verified
#     - fixed RKF7(8) step: verified as a numerical accuracy control
#   Comparison:
#     - External: Brahe KeplerianPropagator with the same Earth GM and true-to-mean conversion
#     - Constants: MU=398600441500000 m^3/s^2; fixed 0.1 s RKF step
#     - Tolerances: position 0.05 m; velocity 5e-5 m/s; elements 1e-5 in native units
#
# Calibration notes:
#   - The naive public HpopTwoBodyGravity() fragment omits Mu and live ASTROX then
#     returns a constant-velocity-like result. Adding the explicit Mu field made the
#     residual agree with Brahe within the tolerances below.
#   - No frame adjustment was needed: both paths are Earth-centered inertial ECI.

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
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
STEP_S = 0.1
POSITION_ABS_M = 0.05
VELOCITY_ABS_M_S = 5.0e-5
ELEMENT_ABS = 1.0e-5


@dataclass(frozen=True, kw_only=True)
class Case:
    name: str
    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    raan_deg: float
    argument_of_periapsis_deg: float
    true_anomaly_deg: float
    duration_s: float


CASES = (
    Case(
        name="leo_eccentric",
        semi_major_axis_m=7_000_000.0,
        eccentricity=0.3,
        inclination_deg=45.0,
        raan_deg=30.0,
        argument_of_periapsis_deg=60.0,
        true_anomaly_deg=30.0,
        duration_s=1.0,
    ),
    Case(
        name="high_inclination",
        semi_major_axis_m=7_500_000.0,
        eccentricity=0.1,
        inclination_deg=98.0,
        raan_deg=120.0,
        argument_of_periapsis_deg=15.0,
        true_anomaly_deg=5.0,
        duration_s=10.0,
    ),
    Case(
        name="near_circular_orbit_scale",
        semi_major_axis_m=6_800_000.0,
        eccentricity=0.01,
        inclination_deg=10.0,
        raan_deg=20.0,
        argument_of_periapsis_deg=40.0,
        true_anomaly_deg=200.0,
        duration_s=60.0,
    ),
)


class CrossValidationError(Exception):
    """Raised when the independent two-body comparison fails."""


def brahe_epoch(value: str) -> bh.Epoch:
    date, time = value.replace("Z", "").split("T")
    year, month, day = (int(part) for part in date.split("-"))
    hour, minute, second = time.split(":")
    return bh.Epoch.from_datetime(
        year,
        month,
        day,
        int(hour),
        int(minute),
        float(second),
        0.0,
        bh.TimeSystem.UTC,
    )


def true_to_mean_deg(true_anomaly_deg: float, eccentricity: float) -> float:
    nu = math.radians(true_anomaly_deg)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 - eccentricity) * math.sin(nu / 2.0),
        math.sqrt(1.0 + eccentricity) * math.cos(nu / 2.0),
    )
    return math.degrees(eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly)) % 360.0


def mean_to_true_deg(mean_anomaly_deg: float, eccentricity: float) -> float:
    mean_anomaly = math.radians(mean_anomaly_deg)
    eccentric_anomaly = mean_anomaly
    for _ in range(30):
        eccentric_anomaly -= (
            eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly) - mean_anomaly
        ) / (1.0 - eccentricity * math.cos(eccentric_anomaly))
    return math.degrees(
        2.0
        * math.atan2(
            math.sqrt(1.0 + eccentricity) * math.sin(eccentric_anomaly / 2.0),
            math.sqrt(1.0 - eccentricity) * math.cos(eccentric_anomaly / 2.0),
        )
    ) % 360.0


def run_case(case: Case) -> astrogator.PropagateResult:
    state = astrogator.keplerian_state(
        semi_major_axis_m=case.semi_major_axis_m,
        eccentricity=case.eccentricity,
        inclination_deg=case.inclination_deg,
        raan_deg=case.raan_deg,
        argument_of_periapsis_deg=case.argument_of_periapsis_deg,
        gravitational_parameter_m3_s2=MU,
        true_anomaly_deg=case.true_anomaly_deg,
    )
    propagator_name = f"PR15_TwoBody_{case.name}"
    config = propagator.hpop_config(
        name=propagator_name,
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name=f"RKF7th8th_{case.name}",
            use_fixed_step=True,
            initial_step_s=STEP_S,
            max_step_s=STEP_S,
            min_step_s=STEP_S,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_two_body_gravity(
            name=f"TwoBody_{case.name}",
            gravitational_parameter_m3_s2=MU,
        ),
    )
    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state, epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name=propagator_name,
                stop_conditions=[astrogator.duration_stop("Duration", case.duration_s)],
            ),
        ],
        propagators=[config],
    )
    segment = result.main_sequence_results[-1]
    if not isinstance(segment, astrogator.PropagateResult):
        raise CrossValidationError(f"{case.name}: expected PropagateResult, got {type(segment).__name__}")
    return segment


def compare_case(case: Case, segment: astrogator.PropagateResult) -> list[str]:
    elements = np.array(
        [
            case.semi_major_axis_m,
            case.eccentricity,
            case.inclination_deg,
            case.raan_deg,
            case.argument_of_periapsis_deg,
            true_to_mean_deg(case.true_anomaly_deg, case.eccentricity),
        ]
    )
    propagator_model = bh.KeplerianPropagator.from_keplerian(
        brahe_epoch(START), elements, bh.AngleFormat.DEGREES, STEP_S
    )
    expected_cartesian = np.asarray(
        propagator_model.state_eci(brahe_epoch(START) + case.duration_s)
    )
    actual_cartesian = np.asarray(segment.final_state.cartesian.to_wire())
    errors: list[str] = []
    position_error = float(np.max(np.abs(actual_cartesian[:3] - expected_cartesian[:3])))
    velocity_error = float(np.max(np.abs(actual_cartesian[3:] - expected_cartesian[3:])))
    if position_error > POSITION_ABS_M:
        errors.append(f"{case.name}: position residual {position_error:.12g} m")
    if velocity_error > VELOCITY_ABS_M_S:
        errors.append(f"{case.name}: velocity residual {velocity_error:.12g} m/s")

    expected_elements = propagator_model.state_koe_osc(
        brahe_epoch(START) + case.duration_s, bh.AngleFormat.DEGREES
    )
    expected_true_anomaly = mean_to_true_deg(float(expected_elements[5]), case.eccentricity)
    actual = segment.final_state.keplerian
    element_checks = (
        ("semi_major_axis_m", float(expected_elements[0]), actual.semi_major_axis_m),
        ("eccentricity", float(expected_elements[1]), actual.eccentricity),
        ("inclination_deg", float(expected_elements[2]), actual.inclination_deg),
        ("raan_deg", float(expected_elements[3]), actual.raan_deg),
        ("argument_of_periapsis_deg", float(expected_elements[4]), actual.argument_of_periapsis_deg),
        ("true_anomaly_deg", expected_true_anomaly, actual.true_anomaly_deg),
    )
    for field, expected, observed in element_checks:
        residual = abs(expected - observed)
        if field.endswith("_deg"):
            residual = abs((expected - observed + 180.0) % 360.0 - 180.0)
        if residual > ELEMENT_ABS:
            errors.append(f"{case.name}: {field} residual {residual:.12g}")
    if abs(segment.duration_s - case.duration_s) > 1.0e-9:
        errors.append(f"{case.name}: DurationSec={segment.duration_s!r}")
    return errors


def test_run_mcs_two_body_matches_brahe() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in CASES:
        try:
            failures.extend(compare_case(case, run_case(case)))
        except Exception as exc:
            failures.append(f"{case.name}: {type(exc).__name__}: {exc}")
    if failures:
        raise CrossValidationError("\n".join(failures))


def main() -> int:
    try:
        test_run_mcs_two_body_matches_brahe()
    except (CrossValidationError, exceptions.AstroxError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"CROSS_VALIDATION_CHECKED={len(CASES)}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
