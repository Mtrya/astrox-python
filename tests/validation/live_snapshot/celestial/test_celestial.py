#!/usr/bin/env python3
"""Live snapshot validation for read-like celestial functions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import celestial  # noqa: E402
from tests.validation._support import (  # noqa: E402
    LiveSnapshotCase,
    SnapshotError,
    check_snapshot,
    configure_astrox_from_env,
    describe_json_shape,
    main as snapshot_main,
)


SNAPSHOT_PATH = Path(__file__).with_name("celestial.snap.json")
START = "2026-01-01T00:00:00.000Z"
STOP = "2026-01-02T00:00:00.000Z"


def _require_response(response: Any, *, field: str, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise SnapshotError(f"{field} response must be an object")
    for key in keys:
        if key not in response:
            raise SnapshotError(f"{field} response missing {key}")
    return response


def _numeric_series_shape(
    value: Any,
    *,
    field: str,
    group_size: int,
    exact_length: int | None = None,
) -> dict[str, Any]:
    if not isinstance(value, list) or not value or len(value) % group_size != 0:
        raise SnapshotError(f"{field} must be a non-empty numeric list grouped by {group_size}")
    if not all(isinstance(item, int | float) and not isinstance(item, bool) for item in value):
        raise SnapshotError(f"{field} must contain numeric values")
    shape: dict[str, Any] = {
        "kind": "array",
        "item": {"kind": "number"},
        "group_size": group_size,
    }
    if exact_length is not None:
        shape["length"] = exact_length
    return shape


def _response_snapshot(shape: dict[str, Any]) -> dict[str, Any]:
    return {"shape": shape}


def ephemeris_shape() -> dict[str, Any]:
    response = _require_response(
        celestial.ephemeris(
            target_name="Moon",
            start=START,
            stop=STOP,
            step_s=86400.0,
        ),
        field="ephemeris",
        keys=("Position", "Period"),
    )
    if not isinstance(response["Position"], dict):
        raise SnapshotError("ephemeris Position must be an object")
    if not isinstance(response["Period"], int | float) or isinstance(response["Period"], bool):
        raise SnapshotError("ephemeris Period must be numeric")
    shape = describe_json_shape(response, field="ephemeris response")
    position_shape = shape["fields"]["Position"]["fields"]
    position_shape["cartesianVelocity"] = _numeric_series_shape(
        response["Position"].get("cartesianVelocity"),
        field="ephemeris Position.cartesianVelocity",
        group_size=7,
        exact_length=14,
    )
    return _response_snapshot(shape)


def rotation_shape(order: int) -> dict[str, Any]:
    response = _require_response(
        celestial.cb_axes_rotation(
            from_central_body="Earth",
            to_central_body="Moon",
            epoch=START,
            order=order,
        ),
        field="rotation",
        keys=("Rotation",),
    )
    rotation = response["Rotation"]
    if not isinstance(rotation, list):
        raise SnapshotError("Rotation must be an array")
    expected_length = 4 if order == 0 else 7
    if len(rotation) != expected_length:
        raise SnapshotError(f"Rotation length={len(rotation)}, expected {expected_length}")
    if not all(isinstance(item, int | float) and not isinstance(item, bool) for item in rotation):
        raise SnapshotError("Rotation must contain numeric values")
    shape = describe_json_shape(response, field="rotation response")
    shape["fields"]["Rotation"] = {
        "kind": "array",
        "length": expected_length,
        "item": {"kind": "number"},
    }
    return _response_snapshot(shape)


def mpc_shape() -> dict[str, Any]:
    response = _require_response(
        celestial.mpc_ephemeris(target_name="Ceres"),
        field="MPC",
        keys=("OrbitElements", "Position"),
    )
    if not isinstance(response["OrbitElements"], dict):
        raise SnapshotError("MPC OrbitElements must be an object")
    if not isinstance(response["Position"], dict):
        raise SnapshotError("MPC Position must be an object")
    shape = describe_json_shape(response, field="MPC response")
    position_shape = shape["fields"]["Position"]["fields"]
    position_shape["cartesianVelocity"] = _numeric_series_shape(
        response["Position"].get("cartesianVelocity"),
        field="MPC Position.cartesianVelocity",
        group_size=7,
    )
    return _response_snapshot(shape)


def _transfer_result_shape(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SnapshotError(f"{field} must be an object")
    required = (
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
    )
    for key in required:
        if key not in value:
            raise SnapshotError(f"{field} missing {key}")
    for key in ("DepartureTime", "ArrivalTime"):
        if not isinstance(value[key], str):
            raise SnapshotError(f"{field}.{key} must be a string")
    for key in ("DV1_Mag", "DV2_Mag", "TimeOfFlightDays", "ArrivalLightAngle"):
        if not isinstance(value[key], int | float) or isinstance(value[key], bool):
            raise SnapshotError(f"{field}.{key} must be numeric")
    for key, expected_length in (("DeltaV1", 3), ("DeltaV2", 3), ("RV1", 6), ("RV2", 6)):
        series = value[key]
        if (
            not isinstance(series, list)
            or len(series) != expected_length
            or not all(isinstance(item, int | float) and not isinstance(item, bool) for item in series)
        ):
            raise SnapshotError(f"{field}.{key} must be a numeric array of length {expected_length}")
    return {
        "kind": "object",
        "fields": {
            "ArrivalTime": {"kind": "string"},
            "DV1_Mag": {"kind": "number"},
            "DV2_Mag": {"kind": "number"},
            "DeltaV1": {"kind": "array", "length": 3, "item": {"kind": "number"}},
            "DeltaV2": {"kind": "array", "length": 3, "item": {"kind": "number"}},
            "DepartureTime": {"kind": "string"},
            "RV1": {"kind": "array", "length": 6, "item": {"kind": "number"}},
            "RV2": {"kind": "array", "length": 6, "item": {"kind": "number"}},
        },
    }


def transfer_shape(*, frame: str | None, explicit_elements: bool) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "departure_body": "Earth",
        "arrival_body": "2015 XF261" if explicit_elements else "Mars",
        "departure_start": "2028-06-01T00:00:00Z",
        "departure_stop": "2028-06-03T00:00:00Z",
        "arrival_start": "2029-04-01T00:00:00Z",
        "arrival_stop": "2029-04-03T00:00:00Z",
        "departure_step_days": 2.0,
        "arrival_step_days": 1.0,
        # Since 2026-08-20 the server defaults MaxDepartureDV/MaxArrivalDV to
        # 10000 m/s and MaxTofDays to 500, which would filter this maintained
        # grid to zero results; opt out with explicit wide bounds.
        "max_departure_delta_v_m_s": 10000000,
        "max_arrival_delta_v_m_s": 10000000,
        "max_time_of_flight_days": 1000,
    }
    if frame is not None:
        kwargs["sun_frame"] = frame
    if explicit_elements:
        kwargs["arrival_elements"] = celestial.mpc_orbital_elements(
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
    response = _require_response(
        celestial.lambert_transfer_window(**kwargs),
        field="transfer",
        keys=("TransferResults",),
    )
    results = response["TransferResults"]
    if not isinstance(results, list) or not results:
        raise SnapshotError("transfer TransferResults must be a non-empty list")
    shape = describe_json_shape(response, field="transfer response")
    transfer_shape = shape["fields"]["TransferResults"]
    transfer_shape["length"] = len(results)
    item_fields = transfer_shape["item"]["fields"]
    for key, expected_length in (
        ("DeltaV1", 3),
        ("DeltaV2", 3),
        ("RV1", 6),
        ("RV2", 6),
    ):
        item_fields[key]["length"] = expected_length
    for index, result in enumerate(results):
        _transfer_result_shape(result, field=f"TransferResults[{index}]")
    return _response_snapshot(shape)


CASES = [
    LiveSnapshotCase(
        id="ephemeris_moon_explicit_window",
        description="Nested CZML-like ephemeris types and 7-value sample layout for an explicit Moon window.",
        run=ephemeris_shape,
    ),
    LiveSnapshotCase(
        id="cb_axes_rotation_order_0",
        description="Nested quaternion response shape with the order-0 length contract.",
        run=lambda: rotation_shape(0),
    ),
    LiveSnapshotCase(
        id="cb_axes_rotation_order_1",
        description="Nested quaternion-plus-angular-velocity response shape with the order-1 length contract.",
        run=lambda: rotation_shape(1),
    ),
    LiveSnapshotCase(
        id="mpc_ceres_server_default_window",
        description="Nested MPC response shape using the server-owned orbital-epoch default window; external numeric values are not frozen.",
        run=mpc_shape,
    ),
    LiveSnapshotCase(
        id="lambert_transfer_earth_mars_default_eclp_j2000_icrf",
        description="Transfer-window result grid and six-state vector layout for the server-default EclpJ2000ICRF Earth-to-Mars case.",
        run=lambda: transfer_shape(frame=None, explicit_elements=False),
    ),
    LiveSnapshotCase(
        id="lambert_transfer_asteroid_explicit_elements_icrf",
        description="Transfer-window result grid using explicit MPC elements and the ICRF output branch.",
        run=lambda: transfer_shape(frame="ICRF", explicit_elements=True),
    ),
]


def test_celestial_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


def _main() -> int:
    try:
        return snapshot_main(cases=CASES, snapshot_path=SNAPSHOT_PATH)
    except Exception as exc:
        print(f"LIVE_SNAPSHOT_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
