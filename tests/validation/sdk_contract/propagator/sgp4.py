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
from tests.validation.sdk_contract.propagator import _common


def iss_tle() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.sgp4(
        start=_common.SGP4_START,
        stop=_common.SGP4_STOP,
        step_s=_common.SGP4_STEP_S,
        satellite_number=_common.SGP4_SATELLITE_NUMBER,
        tle_lines=_common.SGP4_TLE_LINES,
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
