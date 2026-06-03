#!/usr/bin/env python3
"""Live SDK contract snapshot for the two-body propagator."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import propagator
from tests.validation._support import ContractCase, main
from tests.validation.sdk_contract.propagator import _common


def sso() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.two_body(
        start=_common.J2_START,
        stop=_common.J2_STOP,
        orbit_epoch=_common.J2_ORBIT_EPOCH,
        orbit=_common.sso_orbit(),
        step_s=_common.J2_STEP_S,
        coord_system=_common.J2_COORD_SYSTEM,
        gravitational_parameter_m3_s2=_common.J2_GRAVITATIONAL_PARAMETER_M3_S2,
    )


CASES = [
    ContractCase(
        id="sso",
        description="Short two-body propagation from a low Earth orbit using explicit Earth constants.",
        run=sso,
    )
]


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=Path(__file__).with_suffix(".snap.json")))
