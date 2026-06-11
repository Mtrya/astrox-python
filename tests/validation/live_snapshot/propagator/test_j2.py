#!/usr/bin/env python3
"""Live snapshot validation for the J2 propagator."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits, propagator
from tests.validation._support import (
    ContractCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("j2.snap.json")


def sso_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )


def sso() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.j2(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=sso_orbit(),
        step_s=300.0,
        coord_system="Inertial",
        gravitational_parameter_m3_s2=398600441500000.0,
        j2_normalized_value=0.000484165143790815,
        ref_distance_m=6378137.0,
    )


CASES = [
    ContractCase(
        id="sso",
        description="Short J2 propagation from a low Earth orbit using explicit Earth constants.",
        run=sso,
    )
]


def test_j2_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
