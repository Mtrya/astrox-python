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


def _require_success(response: Any, *, field: str, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise SnapshotError(f"{field} response must be an object")
    for key in keys:
        if key not in response:
            raise SnapshotError(f"{field} response missing {key}")
    if not isinstance(response["IsSuccess"], bool):
        raise SnapshotError(f"{field} IsSuccess must be a boolean")
    if not isinstance(response["Message"], str):
        raise SnapshotError(f"{field} Message must be a string")
    if response["IsSuccess"] is not True:
        raise SnapshotError(f"{field} returned IsSuccess={response['IsSuccess']!r}: {response['Message']!r}")
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


def _response_snapshot(
    response: dict[str, Any],
    *,
    field: str,
    shape: dict[str, Any],
) -> dict[str, Any]:
    return {
        "IsSuccess": response["IsSuccess"],
        "Message": response["Message"],
        "shape": shape,
    }


def ephemeris_shape() -> dict[str, Any]:
    response = _require_success(
        celestial.ephemeris(
            target_name="Moon",
            start=START,
            stop=STOP,
            step_s=86400.0,
        ),
        field="ephemeris",
        keys=("IsSuccess", "Message", "Position", "Period"),
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
    return _response_snapshot(response, field="ephemeris", shape=shape)


def rotation_shape(order: int) -> dict[str, Any]:
    response = _require_success(
        celestial.cb_axes_rotation(
            from_central_body="Earth",
            to_central_body="Moon",
            epoch=START,
            order=order,
        ),
        field="rotation",
        keys=("IsSuccess", "Message", "Rotation"),
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
    return _response_snapshot(response, field="rotation", shape=shape)


def mpc_shape() -> dict[str, Any]:
    response = _require_success(
        celestial.mpc_ephemeris(target_name="Ceres"),
        field="MPC",
        keys=("IsSuccess", "Message", "OrbitElements", "Position"),
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
    return _response_snapshot(response, field="MPC", shape=shape)


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
