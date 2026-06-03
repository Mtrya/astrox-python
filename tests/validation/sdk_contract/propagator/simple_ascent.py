#!/usr/bin/env python3
"""Live SDK contract snapshot for the simple-ascent propagator."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import propagator
from tests.validation._support import ContractCase, main
from tests.validation.sdk_contract.propagator import _common


def launch_to_burnout() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.simple_ascent(
        start=_common.SIMPLE_ASCENT_START,
        stop=_common.SIMPLE_ASCENT_STOP,
        step_s=_common.SIMPLE_ASCENT_STEP_S,
        central_body=_common.SIMPLE_ASCENT_CENTRAL_BODY,
        launch_latitude_deg=_common.SIMPLE_ASCENT_LAUNCH_LATITUDE_DEG,
        launch_longitude_deg=_common.SIMPLE_ASCENT_LAUNCH_LONGITUDE_DEG,
        launch_altitude_m=_common.SIMPLE_ASCENT_LAUNCH_ALTITUDE_M,
        burnout_velocity_m_s=_common.SIMPLE_ASCENT_BURNOUT_VELOCITY_M_S,
        burnout_latitude_deg=_common.SIMPLE_ASCENT_BURNOUT_LATITUDE_DEG,
        burnout_longitude_deg=_common.SIMPLE_ASCENT_BURNOUT_LONGITUDE_DEG,
        burnout_altitude_m=_common.SIMPLE_ASCENT_BURNOUT_ALTITUDE_M,
    )


CASES = [
    ContractCase(
        id="launch_to_burnout",
        description="Simple ascent from launch point to burnout point using explicit scalar inputs.",
        run=launch_to_burnout,
    )
]


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=Path(__file__).with_suffix(".snap.json")))
