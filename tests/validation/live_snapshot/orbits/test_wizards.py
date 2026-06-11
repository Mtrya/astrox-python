#!/usr/bin/env python3
"""Live snapshots for orbit wizard helpers."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("wizards.snap.json")
ORBIT_EPOCH = "2024-01-01T00:00:00.000Z"


def seed_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=53.0,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=0.0,
    )


def geo() -> tuple[orbits.KeplerianElements, orbits.KeplerianElements]:
    return orbits.geo(
        orbit_epoch=ORBIT_EPOCH,
        inclination_deg=10.0,
        subsatellite_longitude_deg=120.0,
    )


def molniya() -> tuple[orbits.KeplerianElements, orbits.KeplerianElements]:
    return orbits.molniya(
        orbit_epoch=ORBIT_EPOCH,
        perigee_altitude_km=600.0,
        apogee_longitude_deg=100.0,
        argument_of_periapsis_deg=270.0,
    )


def sso() -> tuple[orbits.KeplerianElements, orbits.KeplerianElements]:
    return orbits.sso(
        orbit_epoch=ORBIT_EPOCH,
        altitude_km=600.0,
        local_time_of_descending_node_hours=14.5,
    )


def walker_delta() -> tuple[tuple[orbits.KeplerianElements, ...], ...]:
    return orbits.walker_delta(
        seed_orbit=seed_orbit(),
        num_planes=3,
        num_sats_per_plane=2,
        inter_plane_phase_increment=1,
    )


def walker_star() -> tuple[tuple[orbits.KeplerianElements, ...], ...]:
    return orbits.walker_star(
        seed_orbit=seed_orbit(),
        num_planes=3,
        num_sats_per_plane=2,
        inter_plane_phase_increment=1,
    )


def walker_custom() -> tuple[tuple[orbits.KeplerianElements, ...], ...]:
    return orbits.walker_custom(
        seed_orbit=seed_orbit(),
        num_planes=3,
        num_sats_per_plane=2,
        inter_plane_true_anomaly_increment_deg=30.0,
        raan_increment_deg=60.0,
    )


CASES = [
    LiveSnapshotCase(
        id="geo",
        description="GEO wizard returned as TOD and inertial Keplerian elements.",
        run=geo,
    ),
    LiveSnapshotCase(
        id="molniya",
        description="Molniya wizard returned as TOD and inertial Keplerian elements.",
        run=molniya,
    ),
    LiveSnapshotCase(
        id="sso",
        description="SSO wizard returned as TOD and inertial Keplerian elements.",
        run=sso,
    ),
    LiveSnapshotCase(
        id="walker_delta",
        description="Walker Delta constellation returned as nested plane and satellite tuples.",
        run=walker_delta,
    ),
    LiveSnapshotCase(
        id="walker_star",
        description="Walker Star constellation returned as nested plane and satellite tuples.",
        run=walker_star,
    ),
    LiveSnapshotCase(
        id="walker_custom",
        description="Custom Walker constellation returned as nested plane and satellite tuples.",
        run=walker_custom,
    ),
]


def test_orbit_wizard_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
