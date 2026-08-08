#!/usr/bin/env python3
"""Live snapshot validation for CAT functions."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import cat, orbits  # noqa: E402
from tests.validation._support import (  # noqa: E402
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("cat.snap.json")
START = "2024-01-01T00:00:00.000Z"
LINE1 = "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995"
LINE2 = "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456"


def primary_tle() -> orbits.Tle:
    return orbits.tle(
        line1=LINE1,
        line2=LINE2,
        name="ISS",
        catalog_number="25544",
    )


def generate_tle() -> orbits.Tle:
    return cat.generate_tle(
        name="probe",
        catalog_number="25544",
        epoch=START,
        bstar=0.00004142,
        semi_major_axis_km=6794.0,
        eccentricity=0.0001882,
        inclination_deg=51.6461,
        argument_of_perigee_deg=64.8995,
        raan_deg=339.8014,
        true_anomaly_deg=295.2305,
    )


def estimate_tle_lifetime() -> cat.TleLifetimeResult:
    return cat.estimate_tle_lifetime(
        epoch=START,
        tle=primary_tle(),
        sm=0.01,
        mass=100.0,
    )


def simulate_debris_breakup_simple() -> cat.DebrisBreakupResult:
    return cat.simulate_debris_breakup_simple(
        mother_tle=primary_tle(),
        epoch=START,
        count=2,
        ssc_prefix="AF",
        delta_v_m_s=10.0,
        area_to_mass_ratio_m2_kg=0.002,
        min_azimuth_deg=40.0,
        max_azimuth_deg=180.0,
        min_elevation_deg=0.0,
        max_elevation_deg=2.0,
        compute_lifetime=False,
    )


def simulate_debris_breakup() -> cat.DebrisBreakupResult:
    return cat.simulate_debris_breakup(
        mother_tle=primary_tle(),
        epoch=START,
        impulses=[
            cat.DebrisImpulse(
                azimuth_deg=0.0,
                elevation_deg=0.0,
                delta_v_m_s=10.0,
                area_to_mass_ratio_m2_kg=0.002,
            ),
            cat.DebrisImpulse(
                azimuth_deg=180.0,
                elevation_deg=0.0,
                delta_v_m_s=10.0,
                area_to_mass_ratio_m2_kg=0.002,
            ),
        ],
        ssc_prefix="AF",
        area_to_mass_ratio_m2_kg=0.002,
        compute_lifetime=False,
    )


def simulate_debris_breakup_nasa() -> cat.DebrisBreakupResult:
    return cat.simulate_debris_breakup_nasa(
        mother_tle=primary_tle(),
        epoch=START,
        ssc_prefix="AF",
        total_mass=100.0,
        minimum_characteristic_length=0.1,
    )


CASES = [
    LiveSnapshotCase(
        id="generate_tle",
        description="TLE generation through the public CAT SDK function.",
        run=generate_tle,
    ),
    LiveSnapshotCase(
        id="estimate_tle_lifetime",
        description="TLE lifetime calculation through the public CAT SDK function.",
        run=estimate_tle_lifetime,
    ),
    LiveSnapshotCase(
        id="debris_breakup_simple",
        description="Simple debris breakup through the public CAT SDK function.",
        run=simulate_debris_breakup_simple,
    ),
    LiveSnapshotCase(
        id="debris_breakup",
        description="Explicit-impulse debris breakup through the public CAT SDK function.",
        run=simulate_debris_breakup,
    ),
    LiveSnapshotCase(
        id="debris_breakup_nasa",
        description="NASA debris breakup through the public CAT SDK function.",
        run=simulate_debris_breakup_nasa,
    ),
]


def test_cat_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
