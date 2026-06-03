#!/usr/bin/env python3
"""Live SDK contract snapshot for the SGP4 propagator."""

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


SNAPSHOT_PATH = Path(__file__).with_name("sgp4.snap.json")


def iss_tle() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.sgp4(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        step_s=300.0,
        satellite_number="25544",
        tle_lines=(
            "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
            "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
        ),
    )


CASES = [
    ContractCase(
        id="iss_tle",
        description="Short ISS TLE propagation through the public SGP4 SDK function.",
        run=iss_tle,
    )
]


def test_sgp4_sdk_contract() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(
        main(
            cases=CASES,
            snapshot_path=SNAPSHOT_PATH,
        )
    )
