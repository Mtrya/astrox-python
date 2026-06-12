#!/usr/bin/env python3
"""Live snapshots for rocket.landing_zone."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import rocket
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("landing_zone.snap.json")
LANDING_ZONE_ABS_TOL = 1.0e-9
LANDING_ZONE_REL_TOL = 1.0e-9


def diagonal_launch_to_impact() -> dict[str, Any]:
    return rocket.landing_zone(
        launch_longitude_deg=100.0,
        launch_latitude_deg=30.0,
        launch_height_m=0.0,
        impact_longitude_deg=101.0,
        impact_latitude_deg=30.5,
        impact_height_m=100.0,
        zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
    )


def north_south_launch_to_impact() -> dict[str, Any]:
    return rocket.landing_zone(
        launch_longitude_deg=100.0,
        launch_latitude_deg=31.0,
        launch_height_m=0.0,
        impact_longitude_deg=100.0,
        impact_latitude_deg=30.0,
        impact_height_m=0.0,
        zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
    )


def small_offset_single_vertex() -> dict[str, Any]:
    return rocket.landing_zone(
        launch_longitude_deg=100.0,
        launch_latitude_deg=30.0,
        launch_height_m=0.0,
        impact_longitude_deg=101.0,
        impact_latitude_deg=30.5,
        impact_height_m=100.0,
        zone_xys_km=[0.0, 0.0],
    )


CASES = [
    LiveSnapshotCase(
        id="diagonal_launch_to_impact",
        description="Landing zone for a diagonal launch-to-impact track.",
        run=diagonal_launch_to_impact,
    ),
    LiveSnapshotCase(
        id="north_south_launch_to_impact",
        description="Landing zone for a pure north-south launch-to-impact track.",
        run=north_south_launch_to_impact,
    ),
    LiveSnapshotCase(
        id="small_offset_single_vertex",
        description="Landing zone with a single zero-offset vertex at the impact point.",
        run=small_offset_single_vertex,
    ),
]


def test_landing_zone_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(
        cases=CASES,
        snapshot_path=SNAPSHOT_PATH,
        abs_tol=LANDING_ZONE_ABS_TOL,
        rel_tol=LANDING_ZONE_REL_TOL,
    )


if __name__ == "__main__":
    raise SystemExit(
        main(
            cases=CASES,
            snapshot_path=SNAPSHOT_PATH,
            abs_tol=LANDING_ZONE_ABS_TOL,
            rel_tol=LANDING_ZONE_REL_TOL,
        )
    )
