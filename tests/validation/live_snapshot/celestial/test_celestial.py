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
    main as snapshot_main,
)


SNAPSHOT_PATH = Path(__file__).with_name("celestial.snap.json")
START = "2026-01-01T00:00:00.000Z"
STOP = "2026-01-02T00:00:00.000Z"


def _keys(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, dict):
        raise SnapshotError(f"{field} must be an object")
    return sorted(str(key) for key in value)


def ephemeris_shape() -> dict[str, Any]:
    response = celestial.ephemeris(
        target_name="Moon",
        start=START,
        stop=STOP,
        step_s=86400.0,
    )
    if not isinstance(response, dict):
        raise SnapshotError("ephemeris response must be an object")
    for key in ("IsSuccess", "Message", "Position", "Period"):
        if key not in response:
            raise SnapshotError(f"ephemeris response missing {key}")
    if not isinstance(response["IsSuccess"], bool):
        raise SnapshotError("ephemeris IsSuccess must be a boolean")
    if not isinstance(response["Message"], str):
        raise SnapshotError("ephemeris Message must be a string")
    return {
        "response_keys": _keys(response, field="ephemeris response"),
        "IsSuccess": response["IsSuccess"],
        "Message": response["Message"],
        "Period_type": type(response["Period"]).__name__,
        "Position_keys": _keys(response["Position"], field="Position"),
    }


def rotation_shape(order: int) -> dict[str, Any]:
    response = celestial.cb_axes_rotation(
        from_central_body="Earth",
        to_central_body="Moon",
        epoch=START,
        order=order,
    )
    if not isinstance(response, dict):
        raise SnapshotError("rotation response must be an object")
    for key in ("IsSuccess", "Message", "Rotation"):
        if key not in response:
            raise SnapshotError(f"rotation response missing {key}")
    rotation = response["Rotation"]
    if not isinstance(rotation, list):
        raise SnapshotError("Rotation must be an array")
    if not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in rotation):
        raise SnapshotError("Rotation must contain numeric values")
    return {
        "response_keys": _keys(response, field="rotation response"),
        "IsSuccess": response["IsSuccess"],
        "Message": response["Message"],
        "rotation_length": len(rotation),
        "rotation_item_type": "number",
    }


def mpc_shape() -> dict[str, Any]:
    response = celestial.mpc_ephemeris(
        target_name="Ceres",
        start=START,
        stop=STOP,
    )
    if not isinstance(response, dict):
        raise SnapshotError("MPC response must be an object")
    for key in ("IsSuccess", "Message", "OrbitElements", "Position"):
        if key not in response:
            raise SnapshotError(f"MPC response missing {key}")
    return {
        "response_keys": _keys(response, field="MPC response"),
        "IsSuccess": response["IsSuccess"],
        "Message": response["Message"],
        "OrbitElements_keys": _keys(response["OrbitElements"], field="OrbitElements"),
        "Position_keys": _keys(response["Position"], field="Position"),
    }


CASES = [
    LiveSnapshotCase(
        id="ephemeris_moon_explicit_window",
        description="CZML-like ephemeris response shape for an explicit Moon window.",
        run=ephemeris_shape,
    ),
    LiveSnapshotCase(
        id="cb_axes_rotation_order_0",
        description="Quaternion-only rotation response shape.",
        run=lambda: rotation_shape(0),
    ),
    LiveSnapshotCase(
        id="cb_axes_rotation_order_1",
        description="Quaternion-plus-angular-velocity response shape.",
        run=lambda: rotation_shape(1),
    ),
    LiveSnapshotCase(
        id="mpc_ceres_explicit_window",
        description="MPC-backed response keys for a current valid orbital window; numeric orbital values remain external-data-owned.",
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
