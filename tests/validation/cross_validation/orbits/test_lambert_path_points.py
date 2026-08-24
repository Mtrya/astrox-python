#!/usr/bin/env python3
"""Live cross-validation for the ASTROX Lambert transfer path-point output.

The ``GetPathPoints`` branch of ``/orbit/lambert`` returns the sampled
transfer-orbit positions. The checks below pin the branch to three independent
anchors: the endpoint positions must reproduce the input RV1/RV2 position
triples, the sample count must follow ``NumberOfPathPoints``, and the
intermediate samples must lie on the two-body transfer orbit whose departure
velocity is the input velocity plus the returned departure delta-v (propagated
independently with Brahe).
"""

# Coverage:
#   Branches:
#     - lambert_delta_v get_path_points=True path-point output: verified
#   Fields:
#     - LambertResult.positions endpoint triples: verified against RV1/RV2 positions
#     - LambertResult.positions intermediate samples: verified against Brahe
#       two-body propagation of the post-maneuver departure state
#   Parameters:
#     - path_point_count: verified for an explicit count of 5
#     - omitted path_point_count: verified for the server default of 100
#   Comparison:
#     - External: Brahe KeplerianPropagator from the departure state with the
#       returned departure delta-v applied
#     - Constants: EARTH_MU, TIME_OF_FLIGHT_S
#     - Tolerances: ENDPOINT_ABS_M, PATH_POSITION_ABS_M
#   Notes:
#     - Path samples come from the server's own transfer interpolation, which
#       carries the same per-orbit truncation signature as the numerical
#       two-body RV integrator; PATH_POSITION_ABS_M bounds the observed
#       sub-millimeter residual with margin instead of the analytic-route
#       tolerance.

from __future__ import annotations

import sys
from pathlib import Path

import brahe as bh
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits
from tests.validation._support import LiveConfigError, configure_astrox_from_env


EPOCH = bh.Epoch.from_datetime(2024, 1, 1, 0, 0, 0.0, 0.0, bh.TimeSystem.UTC)
EARTH_MU = 398600441500000.0
TIME_OF_FLIGHT_S = 3600.0
PATH_POINT_COUNT = 5
ENDPOINT_ABS_M = 1.0e-3
PATH_POSITION_ABS_M = 1.0e-3


class CrossValidationError(Exception):
    """Raised when the path-point output disagrees with the independent anchors."""


def departure_state() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=42164000.0,
        y_m=0.0,
        z_m=0.0,
        vx_m_s=0.0,
        vy_m_s=3074.659412716,
        vz_m_s=0.0,
    )


def arrival_state() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=23948974.391427755,
        y_m=34471026.142188683,
        z_m=0.0,
        vx_m_s=-2512.657650119,
        vy_m_s=1746.125055794,
        vz_m_s=100.0,
    )


def _check_path_points(
    label: str,
    *,
    path_point_count: int | None,
    expected_count: int,
) -> None:
    departure = departure_state()
    arrival = arrival_state()
    kwargs: dict[str, object] = {
        "departure_state": departure,
        "arrival_state": arrival,
        "time_of_flight_s": TIME_OF_FLIGHT_S,
        "gravitational_parameter_m3_s2": EARTH_MU,
        "get_path_points": True,
    }
    if path_point_count is not None:
        kwargs["path_point_count"] = path_point_count
    result = orbits.lambert_delta_v(**kwargs)
    if not isinstance(result, orbits.LambertResult):
        raise CrossValidationError(f"{label}: expected LambertResult, got {type(result).__name__}")

    positions = result.positions
    if len(positions) != expected_count * 3:
        raise CrossValidationError(
            f"{label}: positions length {len(positions)} != {expected_count} samples * 3"
        )

    departure_position = np.array(departure.to_wire()[:3])
    arrival_position = np.array(arrival.to_wire()[:3])
    first = np.array(positions[:3])
    last = np.array(positions[-3:])
    if float(np.max(np.abs(first - departure_position))) > ENDPOINT_ABS_M:
        raise CrossValidationError(
            f"{label}: first path point does not reproduce the RV1 position triple: "
            f"max error={float(np.max(np.abs(first - departure_position))):.12g} m"
        )
    if float(np.max(np.abs(last - arrival_position))) > ENDPOINT_ABS_M:
        raise CrossValidationError(
            f"{label}: last path point does not reproduce the RV2 position triple: "
            f"max error={float(np.max(np.abs(last - arrival_position))):.12g} m"
        )

    transfer_state = np.array(departure.to_wire())
    transfer_state[3:] += np.array(result.departure_delta_v_m_s)
    propagator = bh.KeplerianPropagator.from_eci(
        EPOCH,
        transfer_state,
        TIME_OF_FLIGHT_S / (expected_count - 1),
    )
    failures: list[str] = []
    for index in range(1, expected_count - 1):
        offset_s = TIME_OF_FLIGHT_S * index / (expected_count - 1)
        expected = propagator.state_eci(EPOCH + offset_s)[:3]
        actual = np.array(positions[index * 3 : index * 3 + 3])
        error_m = float(np.max(np.abs(actual - expected)))
        if error_m > PATH_POSITION_ABS_M:
            failures.append(
                f"{label} sample {index}: transfer-orbit position error {error_m:.12g} m, "
                f"tolerance {PATH_POSITION_ABS_M:.12g}"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))
    print(f"{label}: {expected_count} path points verified")


def test_lambert_path_points_match_transfer_orbit() -> None:
    configure_astrox_from_env()
    _check_path_points(
        "explicit_count",
        path_point_count=PATH_POINT_COUNT,
        expected_count=PATH_POINT_COUNT,
    )
    _check_path_points("server_default_count", path_point_count=None, expected_count=100)


def main() -> int:
    try:
        test_lambert_path_points_match_transfer_orbit()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=2")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
