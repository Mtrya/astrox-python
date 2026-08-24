#!/usr/bin/env python3
"""Cross-validation for the celestial Lambert transfer-window route.

``lamberthub`` is a dev-only validation dependency used as an independent
zero-revolution Lambert solver. The explicit MPC-element case also uses a
small local two-body derivation; its result remains unresolved until the
server's element convention is identified.
"""

# Coverage:
#   Branches:
#     - Earth -> Mars, ICRF, zero-revolution prograde transfer states: verified
#       for the maintained six-result sampling grid
#     - Earth -> Mars, server-owned MeanEclpJ2000 output frame: unresolved
#     - Earth -> 2015 XF261 with explicit MPC elements: unresolved; the
#       independent Kepler derivation does not yet identify the server's exact
#       element/frame/time convention
#   Fields:
#     - RV1/RV2 transfer velocities: verified against lamberthub for ICRF
#     - RV1/RV2 endpoint position directions: verified against independent
#       Skyfield heliocentric Earth/Mars directions for ICRF; state-model
#       precision and MeanEclpJ2000 semantics remain separate questions
#     - DV1_Mag/DV2_Mag: verified as Euclidean norms of DeltaV1/DeltaV2
#     - TimeOfFlightDays: verified as the exact day delta between ArrivalTime
#       and DepartureTime
#     - ArrivalLightAngle: verified as the angle in degrees between DeltaV2 and
#       the RV2 position vector
#     - DeltaV1/DeltaV2 physical body-velocity interpretation: unresolved
#   Parameters:
#     - departure and arrival sampling: verified for two departure dates and
#       three arrival dates in the maintained ICRF case
#     - MinTofDays: verified by exact timestamp-pair filtering on 2, 4, 12,
#       and 14 day transfer durations
#     - MaxTofDays: verified by exact timestamp-pair filtering against the
#       maintained ICRF grid
#     - MaxDepartureDV/MaxArrivalDV: verified as DV1_Mag/DV2_Mag upper-bound
#       filters against the maintained ICRF grid; since 2026-08-20 the server
#       defaults (10000 m/s departure, 10000 m/s arrival, 500 days TOF) filter
#       the maintained grid to zero results, so the maintained fixtures pass
#       explicit wide bounds
#     - SunFrameName=ICRF: verified for the Lambert-state comparison and the
#       independent axis-identification comparison
#     - omitted MeanEclpJ2000 frame: unresolved against fixed obliquity rotations
#     - explicit MPC elements: unresolved after independent element/time/frame
#       convention probes, including the 2026-08-20 ReferenceFrame option,
#       which does not change the route's arrival states
#   Comparison:
#     - External: lamberthub.izzo2015 with Sun mu, M=0, prograde=True
#     - External frame anchor: Skyfield DE421 heliocentric Earth/Mars position
#       directions at the returned UTC epochs
#     - Local: standard elliptic Kepler propagation for the supplied MPC values
#     - Tolerances: solver precision bounds, a 0.01-degree axis-identification
#       bound, and a 1-degree wrong-frame separation; none is a fitted envelope
#       for unexplained model differences

from __future__ import annotations

from datetime import UTC, datetime
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from astropy.time import Time
from lamberthub import izzo2015

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import celestial  # noqa: E402
from tests.validation._support import (  # noqa: E402
    configure_astrox_from_env,
    load_skyfield_ephemeris,
    skyfield_loader_from_env,
)


SUN_MU_M3_S2 = 1.3271244004193938e20
AU_M = 149597870700.0
MEAN_OBLIQUITY_DEG = 23.439291111
SOLVER_ABS_TOL_M_S = 1.0e-6
NORM_REL_TOL = 1.0e-12
NORM_ABS_TOL_M_S = 1.0e-9
FRAME_POSITION_DIAGNOSTIC_TOL_M = 1.0
FRAME_VELOCITY_DIAGNOSTIC_TOL_M_S = 1.0e-6
ELEMENT_POSITION_DIAGNOSTIC_TOL_M = 1.0
ICRF_AXIS_IDENTIFICATION_MAX_ANGLE_DEG = 0.01
WRONG_FRAME_MIN_SEPARATION_DEG = 1.0

DEPARTURE_START = "2028-06-01T00:00:00Z"
DEPARTURE_STOP = "2028-06-03T00:00:00Z"
ARRIVAL_START = "2029-04-01T00:00:00Z"
ARRIVAL_STOP = "2029-04-03T00:00:00Z"
EXPECTED_DEPARTURE_TIMES = (DEPARTURE_START, DEPARTURE_STOP)
EXPECTED_ARRIVAL_TIMES = (
    ARRIVAL_START,
    "2029-04-02T00:00:00Z",
    ARRIVAL_STOP,
)
FILTER_DEPARTURE_TIMES = ("2028-06-01T00:00:00Z", "2028-06-03T00:00:00Z")
FILTER_ARRIVAL_TIMES = ("2028-06-05T00:00:00Z", "2028-06-15T00:00:00Z")

# Since 2026-08-20 the server applies default MaxDepartureDV/MaxArrivalDV
# (10000 m/s) and MaxTofDays (500) filters. The maintained grids exercise
# transfers outside those defaults (the short-window fixture needs up to
# about 2e6 m/s), so every maintained fixture opts out with explicit wide
# bounds.
WIDE_MAX_DELTA_V_M_S = 10000000
WIDE_MAX_TOF_DAYS = 1000
WIDE_FILTER_KWARGS: dict[str, Any] = {
    "max_departure_delta_v_m_s": WIDE_MAX_DELTA_V_M_S,
    "max_arrival_delta_v_m_s": WIDE_MAX_DELTA_V_M_S,
    "max_time_of_flight_days": WIDE_MAX_TOF_DAYS,
}

EXPLICIT_ELEMENTS = celestial.mpc_orbital_elements(
    epoch_mjd_tdt=61000.0,
    periapsis_time_mjd_tdt=60900.0,
    periapsis_distance_au=0.6740515,
    semi_major_axis_au=0.9898367,
    eccentricity=0.3190276,
    inclination_deg=0.79379,
    raan_deg=209.81829,
    argument_of_periapsis_deg=100.88187,
    mean_anomaly_deg=120.0,
)


class CrossValidationError(Exception):
    """Raised when the independent comparison disagrees with ASTROX."""


class ResponseShapeError(Exception):
    """Raised when a maintained live transfer response is unusable."""


def _require_number(value: Any, *, field: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ResponseShapeError(f"{field} must be numeric")
    return float(value)


def _require_results(response: Any, *, expected_count: int) -> list[dict[str, Any]]:
    if not isinstance(response, dict):
        raise ResponseShapeError("transfer response must be an object")
    results = response.get("TransferResults")
    if not isinstance(results, list) or len(results) != expected_count:
        raise ResponseShapeError(
            f"TransferResults must contain {expected_count} result objects"
        )
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            raise ResponseShapeError(f"TransferResults[{index}] must be an object")
        for key in (
            "DepartureTime",
            "ArrivalTime",
            "DeltaV1",
            "DV1_Mag",
            "DeltaV2",
            "DV2_Mag",
            "RV1",
            "RV2",
            "TimeOfFlightDays",
            "ArrivalLightAngle",
        ):
            if key not in result:
                raise ResponseShapeError(f"TransferResults[{index}] missing {key}")
        for key in ("DepartureTime", "ArrivalTime"):
            if not isinstance(result[key], str):
                raise ResponseShapeError(f"TransferResults[{index}].{key} must be a string")
        for key in ("DeltaV1", "DeltaV2"):
            vector = result[key]
            if (
                not isinstance(vector, list)
                or len(vector) != 3
                or not all(
                    isinstance(item, int | float) and not isinstance(item, bool)
                    for item in vector
                )
            ):
                raise ResponseShapeError(
                    f"TransferResults[{index}].{key} must be a numeric 3-vector"
                )
        for key in ("RV1", "RV2"):
            state = result[key]
            if (
                not isinstance(state, list)
                or len(state) != 6
                or not all(
                    isinstance(item, int | float) and not isinstance(item, bool)
                    for item in state
                )
            ):
                raise ResponseShapeError(
                    f"TransferResults[{index}].{key} must be a numeric 6-vector"
                )
        for key in ("DV1_Mag", "DV2_Mag"):
            _require_number(result[key], field=f"TransferResults[{index}].{key}")
    return results


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _timestamp_pairs(results: list[dict[str, Any]]) -> list[tuple[datetime, datetime]]:
    return sorted(
        [
            (_time(result["DepartureTime"]), _time(result["ArrivalTime"]))
            for result in results
        ]
    )


def _assert_sampling_grid(results: list[dict[str, Any]]) -> None:
    expected_pairs = sorted(
        [
            (_time(departure), _time(arrival))
            for departure in EXPECTED_DEPARTURE_TIMES
            for arrival in EXPECTED_ARRIVAL_TIMES
        ]
    )
    if _timestamp_pairs(results) != expected_pairs:
        raise ResponseShapeError(
            "TransferResults timestamps do not match the maintained 2x3 sampling grid"
        )


def _astrox_transfer_results(*, frame: str | None, explicit_elements: bool) -> list[dict[str, Any]]:
    kwargs: dict[str, Any] = {
        "departure_body": "Earth",
        "arrival_body": "2015 XF261" if explicit_elements else "Mars",
        "departure_start": DEPARTURE_START,
        "departure_stop": DEPARTURE_STOP,
        "arrival_start": ARRIVAL_START,
        "arrival_stop": ARRIVAL_STOP,
        "min_time_of_flight_days": 10,
        "departure_step_days": 2.0,
        "arrival_step_days": 1.0,
        **WIDE_FILTER_KWARGS,
    }
    if frame is not None:
        kwargs["sun_frame"] = frame
    if explicit_elements:
        kwargs["arrival_elements"] = EXPLICIT_ELEMENTS
    results = _require_results(
        celestial.lambert_transfer_window(**kwargs),
        expected_count=6,
    )
    if not explicit_elements:
        _assert_sampling_grid(results)
    return results


def _state(result: dict[str, Any], key: str) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(result[key], dtype=float)
    return values[:3], values[3:]


def _solver_residual(result: dict[str, Any]) -> tuple[float, float]:
    departure_position, _ = _state(result, "RV1")
    arrival_position, _ = _state(result, "RV2")
    tof_s = (_time(result["ArrivalTime"]) - _time(result["DepartureTime"])).total_seconds()
    transfer_departure, transfer_arrival = izzo2015(
        SUN_MU_M3_S2,
        departure_position,
        arrival_position,
        tof_s,
        M=0,
        prograde=True,
        low_path=True,
    )
    _, actual_departure_velocity = _state(result, "RV1")
    _, actual_arrival_velocity = _state(result, "RV2")
    return (
        float(np.max(np.abs(actual_departure_velocity - transfer_departure))),
        float(np.max(np.abs(actual_arrival_velocity - transfer_arrival))),
    )


def test_transfer_states_match_lamberthub_zero_revolution_prograde() -> None:
    configure_astrox_from_env()
    results = _astrox_transfer_results(frame="ICRF", explicit_elements=False)
    residuals = [_solver_residual(result) for result in results]
    max_residual = max(max(pair) for pair in residuals)
    print(f"LAMBERT_ICRF_MAX_VELOCITY_RESIDUAL_M_S={max_residual:.12g}")
    if max_residual > SOLVER_ABS_TOL_M_S:
        raise CrossValidationError(
            "ASTROX ICRF transfer velocities no longer match the independent "
            f"zero-revolution prograde Lambert solver: max residual={max_residual:.12g} m/s, "
            f"threshold={SOLVER_ABS_TOL_M_S:g} m/s"
        )


def test_transfer_delta_v_magnitudes_match_vector_norms() -> None:
    configure_astrox_from_env()
    results = _astrox_transfer_results(frame="ICRF", explicit_elements=False)
    for index, result in enumerate(results):
        for vector_key, magnitude_key in (
            ("DeltaV1", "DV1_Mag"),
            ("DeltaV2", "DV2_Mag"),
        ):
            actual = _require_number(
                result[magnitude_key],
                field=f"TransferResults[{index}].{magnitude_key}",
            )
            expected = float(np.linalg.norm(np.asarray(result[vector_key], dtype=float)))
            if not math.isclose(
                actual,
                expected,
                rel_tol=NORM_REL_TOL,
                abs_tol=NORM_ABS_TOL_M_S,
            ):
                raise CrossValidationError(
                    f"TransferResults[{index}] {magnitude_key}={actual:.12g} "
                    f"does not match norm({vector_key})={expected:.12g}"
                )


def _short_window_results(*, min_tof_days: int) -> Any:
    return celestial.lambert_transfer_window(
        departure_body="Earth",
        arrival_body="Mars",
        departure_start=FILTER_DEPARTURE_TIMES[0],
        departure_stop=FILTER_DEPARTURE_TIMES[1],
        arrival_start=FILTER_ARRIVAL_TIMES[0],
        arrival_stop=FILTER_ARRIVAL_TIMES[1],
        sun_frame="ICRF",
        min_time_of_flight_days=min_tof_days,
        departure_step_days=2.0,
        arrival_step_days=10.0,
        **WIDE_FILTER_KWARGS,
    )


def test_min_time_of_flight_filters_short_sampling_pairs() -> None:
    configure_astrox_from_env()
    expected_all_pairs = sorted(
        [
            (_time(departure), _time(arrival))
            for departure in FILTER_DEPARTURE_TIMES
            for arrival in FILTER_ARRIVAL_TIMES
        ]
    )
    expected_long_pairs = [
        pair
        for pair in expected_all_pairs
        if (pair[1] - pair[0]).total_seconds() / 86400.0 >= 10.0
    ]
    unfiltered = _require_results(
        _short_window_results(min_tof_days=1),
        expected_count=len(expected_all_pairs),
    )
    filtered = _require_results(
        _short_window_results(min_tof_days=10),
        expected_count=len(expected_long_pairs),
    )
    if _timestamp_pairs(unfiltered) != expected_all_pairs:
        raise CrossValidationError(
            "the low-threshold Lambert case did not return the complete 2x2 grid"
        )
    if _timestamp_pairs(filtered) != expected_long_pairs:
        raise CrossValidationError(
            "MinTofDays=10 did not retain exactly the transfer pairs at least 10 days long"
        )
    print(
        "MIN_TOF_FILTERED_PAIRS="
        + ",".join(
            f"{departure.isoformat()}->{arrival.isoformat()}"
            for departure, arrival in expected_long_pairs
        )
    )


def test_time_of_flight_days_matches_timestamp_delta() -> None:
    configure_astrox_from_env()
    results = _astrox_transfer_results(frame="ICRF", explicit_elements=False)
    for index, result in enumerate(results):
        expected_days = (
            _time(result["ArrivalTime"]) - _time(result["DepartureTime"])
        ).total_seconds() / 86400.0
        actual_days = _require_number(
            result["TimeOfFlightDays"],
            field=f"TransferResults[{index}].TimeOfFlightDays",
        )
        if not math.isclose(actual_days, expected_days, rel_tol=0.0, abs_tol=1.0e-9):
            raise CrossValidationError(
                f"TransferResults[{index}].TimeOfFlightDays={actual_days:.12g} "
                f"does not match the timestamp delta {expected_days:.12g} days"
            )


def test_arrival_light_angle_matches_delta_v_geometry() -> None:
    configure_astrox_from_env()
    results = _astrox_transfer_results(frame="ICRF", explicit_elements=False)
    for index, result in enumerate(results):
        delta_v2 = np.asarray(result["DeltaV2"], dtype=float)
        arrival_position, _ = _state(result, "RV2")
        cosine = float(
            np.dot(delta_v2, arrival_position)
            / (np.linalg.norm(delta_v2) * np.linalg.norm(arrival_position))
        )
        expected_deg = math.degrees(math.acos(np.clip(cosine, -1.0, 1.0)))
        actual_deg = _require_number(
            result["ArrivalLightAngle"],
            field=f"TransferResults[{index}].ArrivalLightAngle",
        )
        if not math.isclose(actual_deg, expected_deg, rel_tol=0.0, abs_tol=1.0e-9):
            raise CrossValidationError(
                f"TransferResults[{index}].ArrivalLightAngle={actual_deg:.12g} "
                f"does not match the DeltaV2/RV2 angle {expected_deg:.12g} deg"
            )


def test_max_filters_retain_expected_pairs() -> None:
    configure_astrox_from_env()
    unfiltered = _astrox_transfer_results(frame="ICRF", explicit_elements=False)

    def _filtered(**overrides: Any) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "departure_body": "Earth",
            "arrival_body": "Mars",
            "departure_start": DEPARTURE_START,
            "departure_stop": DEPARTURE_STOP,
            "arrival_start": ARRIVAL_START,
            "arrival_stop": ARRIVAL_STOP,
            "sun_frame": "ICRF",
            "min_time_of_flight_days": 10,
            "departure_step_days": 2.0,
            "arrival_step_days": 1.0,
            **WIDE_FILTER_KWARGS,
            **overrides,
        }
        results = celestial.lambert_transfer_window(**kwargs)["TransferResults"]
        if not isinstance(results, list) or not results:
            raise ResponseShapeError("filtered transfer response must be a non-empty list")
        return results

    def _expected_subset(**overrides: Any) -> list[tuple[datetime, datetime]]:
        subset = []
        for result in unfiltered:
            if (
                "max_departure_delta_v_m_s" in overrides
                and result["DV1_Mag"] > overrides["max_departure_delta_v_m_s"]
            ):
                continue
            if (
                "max_arrival_delta_v_m_s" in overrides
                and result["DV2_Mag"] > overrides["max_arrival_delta_v_m_s"]
            ):
                continue
            if "max_time_of_flight_days" in overrides:
                tof_days = (
                    _time(result["ArrivalTime"]) - _time(result["DepartureTime"])
                ).total_seconds() / 86400.0
                if tof_days > overrides["max_time_of_flight_days"]:
                    continue
            subset.append((_time(result["DepartureTime"]), _time(result["ArrivalTime"])))
        return sorted(subset)

    for label, overrides in (
        ("max_departure_delta_v_m_s", {"max_departure_delta_v_m_s": 15000}),
        ("max_arrival_delta_v_m_s", {"max_arrival_delta_v_m_s": 5500}),
        ("max_time_of_flight_days", {"max_time_of_flight_days": 304}),
    ):
        expected_pairs = _expected_subset(**overrides)
        if len(expected_pairs) == len(unfiltered):
            raise CrossValidationError(
                f"{label} fixture no longer distinguishes: threshold retains every pair"
            )
        filtered = _filtered(**overrides)
        if _timestamp_pairs(filtered) != expected_pairs:
            raise CrossValidationError(
                f"{label}={next(iter(overrides.values()))} did not retain exactly the "
                "pairs whose maintained magnitudes satisfy the bound"
            )
        print(f"{label.upper()}_RETAINED_PAIRS={len(expected_pairs)}")


def _obliquity_rotation(sign: float) -> np.ndarray:
    angle = math.radians(sign * MEAN_OBLIQUITY_DEG)
    return np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, math.cos(angle), -math.sin(angle)],
            [0.0, math.sin(angle), math.cos(angle)],
        ]
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "ASTROX MeanEclpJ2000 versus ICRF transfer states remains unresolved "
        "after fixed-obliquity and independent rotation probes; do not widen "
        "the diagnostic threshold to absorb the residual."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_mean_ecliptic_frame_relation_remains_unresolved() -> None:
    configure_astrox_from_env()
    common = {
        "departure_body": "Earth",
        "arrival_body": "Mars",
        "departure_start": DEPARTURE_START,
        "departure_stop": DEPARTURE_START,
        "arrival_start": ARRIVAL_START,
        "arrival_stop": ARRIVAL_START,
        "min_time_of_flight_days": 10,
        "departure_step_days": 1.0,
        "arrival_step_days": 1.0,
        **WIDE_FILTER_KWARGS,
    }
    mean_ecliptic = _require_results(
        celestial.lambert_transfer_window(**common),
        expected_count=1,
    )[0]
    icrf = _require_results(
        celestial.lambert_transfer_window(**common, sun_frame="ICRF"),
        expected_count=1,
    )[0]
    icrf_state = np.concatenate((_state(icrf, "RV1")[0], _state(icrf, "RV1")[1]))
    icrf_arrival = np.concatenate((_state(icrf, "RV2")[0], _state(icrf, "RV2")[1]))
    mean_state = np.concatenate(
        (_state(mean_ecliptic, "RV1")[0], _state(mean_ecliptic, "RV1")[1])
    )
    mean_arrival = np.concatenate(
        (_state(mean_ecliptic, "RV2")[0], _state(mean_ecliptic, "RV2")[1])
    )
    candidates = [_obliquity_rotation(1.0), _obliquity_rotation(-1.0)]
    residuals: list[tuple[float, float]] = []
    for rotation in candidates:
        predicted_departure = np.concatenate(
            (rotation @ icrf_state[:3], rotation @ icrf_state[3:])
        )
        predicted_arrival = np.concatenate(
            (rotation @ icrf_arrival[:3], rotation @ icrf_arrival[3:])
        )
        residuals.append(
            (
                float(
                    max(
                        np.max(np.abs(mean_state[:3] - predicted_departure[:3])),
                        np.max(np.abs(mean_arrival[:3] - predicted_arrival[:3])),
                    )
                ),
                float(
                    max(
                        np.max(np.abs(mean_state[3:] - predicted_departure[3:])),
                        np.max(np.abs(mean_arrival[3:] - predicted_arrival[3:])),
                    )
                ),
            )
        )
    best_position, best_velocity = min(residuals, key=lambda pair: pair[0])
    print(
        "MEAN_ECLIPTIC_FRAME_DIAGNOSTIC="
        f"position={best_position:.12g} m velocity={best_velocity:.12g} m/s"
    )
    if (
        best_position > FRAME_POSITION_DIAGNOSTIC_TOL_M
        or best_velocity > FRAME_VELOCITY_DIAGNOSTIC_TOL_M_S
    ):
        raise CrossValidationError(
            "fixed mean-obliquity rotations do not explain MeanEclpJ2000 versus "
            f"ICRF transfer states: position={best_position:.12g} m, "
            f"velocity={best_velocity:.12g} m/s"
        )


def _body_state_from_skyfield(
    ephemeris: Any,
    *,
    body: str,
    timestamp: str,
) -> tuple[np.ndarray, np.ndarray]:
    loader = skyfield_loader_from_env()
    time = loader.timescale(builtin=True).from_datetime(_time(timestamp))
    body_state = ephemeris[body.lower()].at(time)
    sun_state = ephemeris["sun"].at(time)
    position_m = (np.asarray(body_state.position.km) - np.asarray(sun_state.position.km)) * 1000.0
    velocity_m_s = (np.asarray(body_state.velocity.km_per_s) - np.asarray(sun_state.velocity.km_per_s)) * 1000.0
    return position_m, velocity_m_s


def _body_velocity_from_skyfield(
    ephemeris: Any,
    *,
    body: str,
    timestamp: str,
) -> np.ndarray:
    return _body_state_from_skyfield(ephemeris, body=body, timestamp=timestamp)[1]


def _unit_vector(value: np.ndarray, *, field: str) -> np.ndarray:
    norm = float(np.linalg.norm(value))
    if norm == 0.0:
        raise ResponseShapeError(f"{field} must not be the zero vector")
    return value / norm


def _angular_separation_deg(left: np.ndarray, right: np.ndarray) -> float:
    left_unit = _unit_vector(left, field="left position")
    right_unit = _unit_vector(right, field="right position")
    cosine = float(np.clip(np.dot(left_unit, right_unit), -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def test_icrf_axes_match_independent_skyfield_orientation() -> None:
    configure_astrox_from_env()
    loader = skyfield_loader_from_env()
    ephemeris = load_skyfield_ephemeris(loader, "de421.bsp")
    results = _astrox_transfer_results(frame="ICRF", explicit_elements=False)
    comparisons: list[tuple[np.ndarray, np.ndarray]] = []
    for result in results:
        for body, state_key, timestamp_key in (
            ("earth", "RV1", "DepartureTime"),
            ("mars", "RV2", "ArrivalTime"),
        ):
            actual_position, _ = _state(result, state_key)
            expected_position, _ = _body_state_from_skyfield(
                ephemeris,
                body=body,
                timestamp=result[timestamp_key],
            )
            comparisons.append((actual_position, expected_position))

    direct_angles = [
        _angular_separation_deg(actual, expected)
        for actual, expected in comparisons
    ]
    wrong_frame_max_angles = [
        max(
            _angular_separation_deg(actual, rotation @ expected)
            for actual, expected in comparisons
        )
        for rotation in (_obliquity_rotation(1.0), _obliquity_rotation(-1.0))
    ]
    direct_max_angle = max(direct_angles)
    best_wrong_frame_max_angle = min(wrong_frame_max_angles)
    print(
        "ICRF_AXIS_DIAGNOSTIC="
        f"direct_max_deg={direct_max_angle:.12g} "
        f"best_wrong_frame_max_deg={best_wrong_frame_max_angle:.12g}"
    )
    if (
        direct_max_angle > ICRF_AXIS_IDENTIFICATION_MAX_ANGLE_DEG
        or best_wrong_frame_max_angle < WRONG_FRAME_MIN_SEPARATION_DEG
    ):
        raise CrossValidationError(
            "independent heliocentric directions do not identify the ASTROX ICRF axes: "
            f"direct max={direct_max_angle:.12g} deg, "
            f"best fixed-obliquity max={best_wrong_frame_max_angle:.12g} deg"
        )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "The physical meaning of DeltaV1/DeltaV2 remains unresolved because the "
        "route does not return the endpoint body's velocity convention; a Skyfield "
        "DE421 comparison is retained as a strict diagnostic."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_delta_v_vectors_match_skyfield_body_velocity_interpretation() -> None:
    configure_astrox_from_env()
    loader = skyfield_loader_from_env()
    ephemeris = load_skyfield_ephemeris(loader, "de421.bsp")
    results = _astrox_transfer_results(frame="ICRF", explicit_elements=False)
    residuals: list[float] = []
    for result in results:
        _, transfer_departure_velocity = _state(result, "RV1")
        _, transfer_arrival_velocity = _state(result, "RV2")
        expected_departure = transfer_departure_velocity - _body_velocity_from_skyfield(
            ephemeris,
            body="earth",
            timestamp=result["DepartureTime"],
        )
        expected_arrival = transfer_arrival_velocity - _body_velocity_from_skyfield(
            ephemeris,
            body="mars",
            timestamp=result["ArrivalTime"],
        )
        residuals.extend(
            [
                float(np.max(np.abs(np.asarray(result["DeltaV1"]) - expected_departure))),
                float(np.max(np.abs(np.asarray(result["DeltaV2"]) - expected_arrival))),
            ]
        )
    max_residual = max(residuals)
    print(f"DELTA_V_BODY_VELOCITY_DIAGNOSTIC_MAX_M_S={max_residual:.12g}")
    if max_residual > SOLVER_ABS_TOL_M_S:
        raise CrossValidationError(
            "Skyfield endpoint-body velocity interpretation retains an unexplained "
            f"DeltaV residual of {max_residual:.12g} m/s"
        )


def _mjd_tdt_from_utc(value: str) -> float:
    return float(Time(value, scale="utc").tt.mjd)


def _kepler_state_from_elements(
    *,
    elements: celestial.MpcOrbitalElements,
    timestamp: str,
    use_periapsis_time: bool,
) -> np.ndarray:
    values = elements
    if values.semi_major_axis_au is None or values.eccentricity is None:
        raise ResponseShapeError("explicit MPC elements need a and e for the local oracle")
    if (
        values.inclination_deg is None
        or values.raan_deg is None
        or values.argument_of_periapsis_deg is None
    ):
        raise ResponseShapeError("explicit MPC elements need orientation fields for the local oracle")
    a_m = values.semi_major_axis_au * AU_M
    eccentricity = values.eccentricity
    mean_motion_rad_s = math.sqrt(SUN_MU_M3_S2 / a_m**3)
    timestamp_mjd = _mjd_tdt_from_utc(timestamp)
    if use_periapsis_time:
        if values.periapsis_time_mjd_tdt is None:
            raise ResponseShapeError("explicit MPC elements have no periapsis epoch")
        mean_anomaly_rad = mean_motion_rad_s * (timestamp_mjd - values.periapsis_time_mjd_tdt) * 86400.0
    else:
        if values.epoch_mjd_tdt is None or values.mean_anomaly_deg is None:
            raise ResponseShapeError("explicit MPC elements need epoch and mean anomaly")
        mean_anomaly_rad = math.radians(values.mean_anomaly_deg) + mean_motion_rad_s * (
            timestamp_mjd - values.epoch_mjd_tdt
        ) * 86400.0
    mean_anomaly_rad %= 2.0 * math.pi
    eccentric_anomaly = mean_anomaly_rad
    for _ in range(50):
        eccentric_anomaly -= (
            eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly) - mean_anomaly_rad
        ) / (1.0 - eccentricity * math.cos(eccentric_anomaly))
    true_anomaly_rad = 2.0 * math.atan2(
        math.sqrt(1.0 + eccentricity) * math.sin(eccentric_anomaly / 2.0),
        math.sqrt(1.0 - eccentricity) * math.cos(eccentric_anomaly / 2.0),
    )
    radius_m = a_m * (1.0 - eccentricity * math.cos(eccentric_anomaly))
    semi_latus_rectum_m = a_m * (1.0 - eccentricity**2)
    position_perifocal = np.array(
        [radius_m * math.cos(true_anomaly_rad), radius_m * math.sin(true_anomaly_rad), 0.0]
    )
    velocity_perifocal = np.array(
        [
            -math.sqrt(SUN_MU_M3_S2 / semi_latus_rectum_m) * math.sin(true_anomaly_rad),
            math.sqrt(SUN_MU_M3_S2 / semi_latus_rectum_m)
            * (eccentricity + math.cos(true_anomaly_rad)),
            0.0,
        ]
    )
    raan = math.radians(values.raan_deg)
    inclination = math.radians(values.inclination_deg)
    argument = math.radians(values.argument_of_periapsis_deg)
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
    return np.concatenate(
        (rotation @ position_perifocal, rotation @ velocity_perifocal)
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Explicit MPC elements remain unresolved after independent Kepler probes "
        "for mean-anomaly and periapsis-time propagation; the 2026-08-20 "
        "ReferenceFrame option was probed and does not change the route's "
        "arrival states, so the server's exact element frame and time "
        "convention is still not identified."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_explicit_mpc_elements_match_independent_kepler_propagation() -> None:
    configure_astrox_from_env()
    results = _astrox_transfer_results(frame="ICRF", explicit_elements=True)
    residuals: list[float] = []
    for use_periapsis_time in (False, True):
        candidate_residuals = []
        for result in results:
            expected = _kepler_state_from_elements(
                elements=EXPLICIT_ELEMENTS,
                timestamp=result["ArrivalTime"],
                use_periapsis_time=use_periapsis_time,
            )
            actual_position, _ = _state(result, "RV2")
            candidate_residuals.append(float(np.max(np.abs(actual_position - expected[:3]))))
        residuals.append(max(candidate_residuals))
    best_residual = min(residuals)
    print(
        "EXPLICIT_MPC_ELEMENT_DIAGNOSTIC_MAX_POSITION_RESIDUAL_M="
        f"{best_residual:.12g}"
    )
    if best_residual > ELEMENT_POSITION_DIAGNOSTIC_TOL_M:
        raise CrossValidationError(
            "independent MPC-element propagation does not explain the ASTROX "
            f"arrival positions: best residual={best_residual:.12g} m"
        )


def main() -> int:
    try:
        test_transfer_states_match_lamberthub_zero_revolution_prograde()
        test_transfer_delta_v_magnitudes_match_vector_norms()
        test_min_time_of_flight_filters_short_sampling_pairs()
        test_time_of_flight_days_matches_timestamp_delta()
        test_arrival_light_angle_matches_delta_v_geometry()
        test_max_filters_retain_expected_pairs()
        test_icrf_axes_match_independent_skyfield_orientation()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=7")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
