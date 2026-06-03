#!/usr/bin/env python3
"""Live SDK contract snapshot for the SGP4 propagator."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import propagator
from tests.validation._support import ContractCase, main


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
STEP_S = 300.0
SATELLITE_NUMBER = "25544"
TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def iss_tle() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.sgp4(
        start=START,
        stop=STOP,
        step_s=STEP_S,
        satellite_number=SATELLITE_NUMBER,
        tle_lines=TLE_LINES,
    )


CASES = [
    ContractCase(
        id="iss_tle",
        description="Short ISS TLE propagation through the public SGP4 SDK function.",
        run=iss_tle,
    )
]


if __name__ == "__main__":
    raise SystemExit(
        main(
            cases=CASES,
            snapshot_path=Path(__file__).with_suffix(".snap.json"),
        )
    )
