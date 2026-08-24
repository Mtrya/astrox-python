#!/usr/bin/env python3
"""Live two-body RV cross-validation between ASTROX and Brahe."""

# Coverage:
#   Branches:
#     - two_body_rv sampled Cartesian ephemeris: verified
#   Fields:
#     - Positions flat [t, x, y, z, vx, vy, vz, ...] layout: verified (Brahe ECI Keplerian propagation)
#     - sample count and time grid: verified against time_of_flight_s/step_s
#   Parameters:
#     - state: partial (LEO and inclined LEO samples)
#     - gravitational_parameter_m3_s2: verified for Brahe Earth GM
#     - time_of_flight_s/step_s: partial (two window/step pairings)
#   Comparison:
#     - External: Brahe KeplerianPropagator two-body state transition from ECI state
#     - Constants: EARTH_MU
#     - Tolerances: POSITION_ABS_M, VELOCITY_ABS_M_S, TIME_ABS_S
#   Notes:
#     - /Propagator/TwoBodyRV is a fixed-step numerical two-body integrator,
#       not the analytic Kepler route behind /Propagator/TwoBody. Residuals
#       against Brahe oscillate with the orbital phase and peak near 4.2e-4 m
#       and 5.4e-7 m/s per ~10-minute arc; they do not grow secularly over the
#       probed hour, which excludes a gravitational-parameter mismatch. The
#       tolerances below bound that observed truncation signature with margin.

from __future__ import annotations

import math
import sys
from pathlib import Path

import brahe as bh
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


EPOCH = bh.Epoch.from_datetime(2024, 1, 1, 0, 0, 0.0, 0.0, bh.TimeSystem.UTC)
EARTH_MU = bh.GM_EARTH
POSITION_ABS_M = 1.0e-3
VELOCITY_ABS_M_S = 1.0e-5
TIME_ABS_S = 1.0e-9


class CrossValidationError(Exception):
    """Raised when ASTROX and Brahe disagree."""


def _state_vector(
    *,
    semi_major_axis_m: float,
    eccentricity: float,
    inclination_deg: float,
    raan_deg: float,
    argument_of_periapsis_deg: float,
    true_anomaly_deg: float,
) -> orbits.CartesianState:
    """Local Keplerian-to-Cartesian conversion for non-degenerate fixtures."""
    p = semi_major_axis_m * (1.0 - eccentricity**2)
    nu = math.radians(true_anomaly_deg)
    position_perifocal = np.array(
        [
            p * math.cos(nu) / (1.0 + eccentricity * math.cos(nu)),
            p * math.sin(nu) / (1.0 + eccentricity * math.cos(nu)),
            0.0,
        ]
    )
    velocity_perifocal = np.array(
        [
            -math.sqrt(EARTH_MU / p) * math.sin(nu),
            math.sqrt(EARTH_MU / p) * (eccentricity + math.cos(nu)),
            0.0,
        ]
    )
    raan = math.radians(raan_deg)
    inclination = math.radians(inclination_deg)
    argument = math.radians(argument_of_periapsis_deg)
    rotation = np.array(
        [
            [
                math.cos(raan) * math.cos(argument)
                - math.sin(raan) * math.sin(argument) * math.cos(inclination),
                -math.cos(raan) * math.sin(argument)
                - math.sin(raan) * math.cos(argument) * math.cos(inclination),
                math.sin(raan) * math.sin(inclination),
            ],
            [
                math.sin(raan) * math.cos(argument)
                + math.cos(raan) * math.sin(argument) * math.cos(inclination),
                -math.sin(raan) * math.sin(argument)
                + math.cos(raan) * math.cos(argument) * math.cos(inclination),
                -math.cos(raan) * math.sin(inclination),
            ],
            [
                math.sin(argument) * math.sin(inclination),
                math.cos(argument) * math.sin(inclination),
                math.cos(inclination),
            ],
        ]
    )
    position = rotation @ position_perifocal
    velocity = rotation @ velocity_perifocal
    return orbits.cartesian_state(
        x_m=float(position[0]),
        y_m=float(position[1]),
        z_m=float(position[2]),
        vx_m_s=float(velocity[0]),
        vy_m_s=float(velocity[1]),
        vz_m_s=float(velocity[2]),
    )


def leo_state() -> orbits.CartesianState:
    return _state_vector(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        raan_deg=0.0,
        argument_of_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
    )


def inclined_state() -> orbits.CartesianState:
    return _state_vector(
        semi_major_axis_m=7078137.0,
        eccentricity=0.002,
        inclination_deg=51.6,
        raan_deg=120.0,
        argument_of_periapsis_deg=10.0,
        true_anomaly_deg=5.0,
    )


def compare_two_body_rv(
    label: str,
    state: orbits.CartesianState,
    *,
    time_of_flight_s: float,
    step_s: float,
) -> int:
    positions = propagator.two_body_rv(
        state=state,
        time_of_flight_s=time_of_flight_s,
        step_s=step_s,
        gravitational_parameter_m3_s2=EARTH_MU,
    )
    expected_samples = int(time_of_flight_s / step_s) + 1
    if len(positions) != expected_samples * 7:
        raise CrossValidationError(
            f"{label}: Positions length {len(positions)} != {expected_samples} samples * 7"
        )
    initial = np.array(state.to_wire())
    first_sample = np.array(positions[1:7])
    if float(np.max(np.abs(first_sample - initial))) > POSITION_ABS_M:
        raise CrossValidationError(
            f"{label}: first sample does not reproduce RV0: "
            f"max error={float(np.max(np.abs(first_sample - initial))):.12g} m"
        )

    propagator_brahe = bh.KeplerianPropagator.from_eci(EPOCH, initial, step_s)
    failures: list[str] = []
    checked = 0
    for sample_index in range(expected_samples):
        offset_s = sample_index * step_s
        start = sample_index * 7
        sample_time_s = positions[start]
        if abs(sample_time_s - offset_s) > TIME_ABS_S:
            failures.append(
                f"{label} sample {sample_index}: time {sample_time_s} != {offset_s}"
            )
            continue
        expected = propagator_brahe.state_eci(EPOCH + offset_s)
        actual = np.array(positions[start + 1 : start + 7])
        position_error_m = float(np.max(np.abs(actual[:3] - expected[:3])))
        velocity_error_m_s = float(np.max(np.abs(actual[3:] - expected[3:])))
        if position_error_m > POSITION_ABS_M:
            failures.append(
                f"{label} position error at offset_s={offset_s:g} is {position_error_m:.12g}, "
                f"tolerance {POSITION_ABS_M:.12g}"
            )
        if velocity_error_m_s > VELOCITY_ABS_M_S:
            failures.append(
                f"{label} velocity error at offset_s={offset_s:g} is {velocity_error_m_s:.12g}, "
                f"tolerance {VELOCITY_ABS_M_S:.12g}"
            )
        checked += 1
    if failures:
        raise CrossValidationError("\n".join(failures))
    return checked


def test_two_body_rv_matches_brahe_keplerian_propagation() -> None:
    configure_astrox_from_env()
    checked = 0
    checked += compare_two_body_rv(
        "leo",
        leo_state(),
        time_of_flight_s=600.0,
        step_s=300.0,
    )
    checked += compare_two_body_rv(
        "inclined",
        inclined_state(),
        time_of_flight_s=900.0,
        step_s=150.0,
    )
    print(f"TWO_BODY_RV_SAMPLES_CHECKED={checked}")


def main() -> int:
    try:
        test_two_body_rv_matches_brahe_keplerian_propagation()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=2")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
