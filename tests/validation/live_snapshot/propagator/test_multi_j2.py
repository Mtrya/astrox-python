#!/usr/bin/env python3
"""Live snapshots for the multi-J2 propagator."""

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


SNAPSHOT_PATH = Path(__file__).with_name("multi_j2.snap.json")


def leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )


def inclined_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=7078137.0,
        eccentricity=0.002,
        inclination_deg=51.6,
        argument_of_periapsis_deg=10.0,
        raan_deg=120.0,
        true_anomaly_deg=5.0,
    )


def two_states() -> tuple[orbits.KeplerianElements, ...]:
    return propagator.multi_j2(
        epoch="2024-01-01T00:10:00.000Z",
        gravitational_parameter_m3_s2=398600441500000.0,
        states=[
            ("2024-01-01T00:00:00.000Z", leo_orbit()),
            ("2024-01-01T00:03:00.000Z", inclined_orbit()),
        ],
    )


def empty() -> tuple[orbits.KeplerianElements, ...]:
    return propagator.multi_j2(
        epoch="2024-01-01T00:10:00.000Z",
        states=[],
    )


CASES = [
    ContractCase(
        id="two_states",
        description="Two Classical states with different source epochs propagated to one target epoch.",
        run=two_states,
    ),
    ContractCase(
        id="empty",
        description="Server-supported empty batch returns an empty tuple.",
        run=empty,
    ),
]


def test_multi_j2_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
