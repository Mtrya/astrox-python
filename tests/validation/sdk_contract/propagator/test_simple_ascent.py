#!/usr/bin/env python3
"""Live SDK contract snapshot for the simple-ascent propagator."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import propagator
from tests.validation._support import (
    ContractCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("simple_ascent.snap.json")


def launch_to_burnout() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.simple_ascent(
        start="2024-01-01T03:00:00.000Z",
        stop="2024-01-01T03:02:00.000Z",
        step_s=30.0,
        central_body="Earth",
        launch_latitude_deg=40.9575,
        launch_longitude_deg=100.2912,
        launch_altitude_m=1000.0,
        burnout_velocity_m_s=7800.0,
        burnout_latitude_deg=41.3,
        burnout_longitude_deg=101.0,
        burnout_altitude_m=200000.0,
    )


CASES = [
    ContractCase(
        id="launch_to_burnout",
        description="Simple ascent from launch point to burnout point using explicit scalar inputs.",
        run=launch_to_burnout,
    )
]


def test_simple_ascent_sdk_contract() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
