#!/usr/bin/env python3
"""Live snapshots for the multi-SGP4 propagator."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits, propagator
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("multi_sgp4.snap.json")
ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
HUBBLE_TLE = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)


def two_tle_sets() -> tuple[orbits.KeplerianElements, ...]:
    return propagator.multi_sgp4(
        epoch="2024-01-01T00:10:00.000Z",
        tle_sets=[
            ISS_TLE,
            HUBBLE_TLE,
        ],
    )


def empty() -> tuple[orbits.KeplerianElements, ...]:
    return propagator.multi_sgp4(
        epoch="2024-01-01T00:10:00.000Z",
        tle_sets=[],
    )


CASES = [
    LiveSnapshotCase(
        id="two_tle_sets",
        description="Two TLE sets propagated to one target epoch.",
        run=two_tle_sets,
    ),
    LiveSnapshotCase(
        id="empty",
        description="Server-supported empty batch returns an empty tuple.",
        run=empty,
    ),
]


def test_multi_sgp4_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
