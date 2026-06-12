#!/usr/bin/env python3
"""Live snapshots for OrbitSystem frame and libration helpers."""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import entities, orbits
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("orbit_system.snap.json")
EPOCH = "2024-01-01T00:00:00Z"
EARTH_MU_M3_S2 = 398600441500000.0
ORBIT_RADIUS_M = 7000000.0


def circular_leo_samples() -> list[float]:
    """Build an 8-sample LEO cartesian array for CZML interpolation."""
    velocity_m_s = math.sqrt(EARTH_MU_M3_S2 / ORBIT_RADIUS_M)
    period_s = 2 * math.pi * math.sqrt(ORBIT_RADIUS_M**3 / EARTH_MU_M3_S2)
    n_samples = 8
    dt_s = period_s / (n_samples - 1)
    samples: list[float] = []
    for index in range(n_samples):
        t_s = index * dt_s
        angle = velocity_m_s / ORBIT_RADIUS_M * t_s
        samples += [
            t_s,
            ORBIT_RADIUS_M * math.cos(angle),
            ORBIT_RADIUS_M * math.sin(angle),
            0.0,
        ]
    return samples


def sample_inertial_position() -> entities.CzmlPosition:
    return entities.czml_position(
        epoch=EPOCH,
        central_body="Earth",
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=circular_leo_samples(),
    )


def transform_frame_to_earth_fixed() -> tuple[float, entities.CzmlPosition]:
    return orbits.transform_frame(
        sample_inertial_position(),
        to_central_body="Earth",
        target_reference_frame="FIXED",
    )


def earth_moon_libration_frame() -> entities.CzmlPositionSTM:
    return orbits.earth_moon_libration(sample_inertial_position())


CASES = [
    LiveSnapshotCase(
        id="transform_frame_to_earth_fixed",
        description="Transform an Earth inertial CZML sample to the Earth fixed frame.",
        run=transform_frame_to_earth_fixed,
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
