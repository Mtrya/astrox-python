#!/usr/bin/env python3
"""Live snapshots for OrbitSystem frame and libration helpers."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import _samples, entities, orbits
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("orbit_system.snap.json")
EPOCH = "2024-01-01T00:00:00Z"
ORBIT_RADIUS_M = 7000000.0


def sample_inertial_position() -> entities.CzmlPosition:
    return entities.czml_position(
        epoch=EPOCH,
        central_body="Earth",
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=_samples.circular_leo_samples(radius_m=ORBIT_RADIUS_M),
    )


def central_body_frame_to_earth_fixed() -> tuple[float, entities.CzmlPosition]:
    return orbits.central_body_frame(
        sample_inertial_position(),
        to_central_body="Earth",
        target_reference_frame="FIXED",
    )


def earth_moon_libration_frame() -> entities.CzmlPositionSTM:
    return orbits.earth_moon_libration(sample_inertial_position())


CASES = [
    LiveSnapshotCase(
        id="central_body_frame_to_earth_fixed",
        description="Transform an Earth inertial CZML sample to the Earth fixed frame.",
        run=central_body_frame_to_earth_fixed,
    ),
    LiveSnapshotCase(
        id="earth_moon_libration_frame",
        description="Transform an Earth inertial CZML sample to the Earth-Moon libration frame.",
        run=earth_moon_libration_frame,
    ),
]


def test_orbit_system_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
