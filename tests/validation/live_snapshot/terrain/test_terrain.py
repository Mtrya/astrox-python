#!/usr/bin/env python3
"""Live snapshot validation for terrain-mask functions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import components, terrain  # noqa: E402
from tests.validation._support import (  # noqa: E402
    LiveSnapshotCase,
    SnapshotError,
    check_snapshot,
    configure_astrox_from_env,
    describe_json_shape,
    main as snapshot_main,
)


SNAPSHOT_PATH = Path(__file__).with_name("terrain.snap.json")
SITE = components.site_position(
    longitude_deg=0.0,
    latitude_deg=-89.0,
    height_m=0.0,
    central_body="Moon",
)
CONFIG = terrain.TerrainMaskConfig(
    text="live snapshot",
    terrain_server_url="",
    flag_pole=1,
    polar_dem_file_name="Moon_LDEM_80s_20m",
    terrain_zoom_level=-1,
    step_size_m=30.0,
    max_search_range_km=15.0,
)


def _shape(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, list):
        raise SnapshotError(f"{field} must be a list")
    if not value:
        return {"kind": "array", "item": None}
    if all(isinstance(item, dict) for item in value):
        return describe_json_shape(value, field=field)
    if all(isinstance(item, int | float) and not isinstance(item, bool) for item in value):
        if len(value) % 2 != 0:
            raise SnapshotError(f"{field} numeric values must form azimuth/elevation pairs")
        return {
            "kind": "array",
            "item": {"kind": "number"},
            "pair_size": 2,
        }
    raise SnapshotError(f"{field} has an unsupported item shape")


def _mask_shape(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise SnapshotError("terrain response must be an object")
    for key in ("sitePosition", "AzElMaskData"):
        if key not in response:
            raise SnapshotError(f"terrain response missing {key}")
    if not isinstance(response["sitePosition"], dict):
        raise SnapshotError("terrain sitePosition must be an object")
    shape = describe_json_shape(response, field="terrain response")
    shape["fields"]["AzElMaskData"] = _shape(response["AzElMaskData"], field="AzElMaskData")
    return {"shape": shape}


def full_mask_shape() -> dict[str, Any]:
    return _mask_shape(
        terrain.azimuth_elevation_mask(site_position=SITE, config=CONFIG),
    )


def simple_mask_shape() -> dict[str, Any]:
    return _mask_shape(
        terrain.azimuth_elevation_mask_simple(site_position=SITE, config=CONFIG),
    )


CASES = [
    LiveSnapshotCase(
        id="azimuth_elevation_mask_explicit_polar_config",
        description="Full terrain mask structure using the documented Moon polar DEM configuration.",
        run=full_mask_shape,
    ),
    LiveSnapshotCase(
        id="azimuth_elevation_mask_simple_explicit_polar_config",
        description="Simplified terrain mask pair structure using the documented Moon polar DEM configuration.",
        run=simple_mask_shape,
    ),
]


def test_terrain_live_snapshot() -> None:
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
