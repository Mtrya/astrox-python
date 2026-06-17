#!/usr/bin/env python3
"""Live snapshots for lighting helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import components, lighting, orbits
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("lighting.snap.json")
START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:30:00.000Z"
EARTH_MU = 398600441500000.0
# SolarAER live snapshots can vary at the same sub-arcsecond scale already
# accepted by the Skyfield SolarAER cross-validation.
LIGHTING_SNAPSHOT_ABS_TOL = 1.0e-4
LIGHTING_SNAPSHOT_REL_TOL = 5.0e-11
TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def site_position() -> components.SitePosition:
    return components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    )


def orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def sgp4_position() -> components.Sgp4Position:
    return components.sgp4_position(tle_lines=TLE_LINES)


def j2_position() -> components.J2Position:
    return components.j2_position(
        orbit_epoch=START,
        orbit=orbit(),
        gravitational_parameter_m3_s2=EARTH_MU,
    )


def two_body_position() -> components.TwoBodyPosition:
    return components.two_body_position(
        orbit_epoch=START,
        orbit=orbit(),
        gravitational_parameter_m3_s2=EARTH_MU,
    )


def czml_position() -> components.CzmlPosition:
    return components.czml_position(
        epoch=START,
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=5,
        cartesian_velocity=[
            0.0,
            6114454.0,
            2870352.0,
            3308542.0,
            -3548.0,
            6463.0,
            1830.0,
            900.0,
            1200000.0,
            6500000.0,
            2500000.0,
            -7200.0,
            1500.0,
            1200.0,
            1800.0,
            -5751150.0,
            3715517.0,
            1150000.0,
            -6060.0,
            -5250.0,
            410.0,
            2700.0,
            -5000000.0,
            -4000000.0,
            -2000000.0,
            4500.0,
            -5600.0,
            -1500.0,
            3600.0,
            1000000.0,
            -6500000.0,
            -2500000.0,
            7200.0,
            1100.0,
            -900.0,
        ],
    )


def lighting_times_for_site() -> dict[str, Any]:
    return lighting.lighting_times(
        start=START,
        stop=STOP,
        position=site_position(),
    )


def lighting_times_for_sgp4() -> dict[str, Any]:
    return lighting.lighting_times(
        start=START,
        stop=STOP,
        position=sgp4_position(),
        occultation_bodies=["Earth", "Moon"],
    )


def solar_intensity_for_j2() -> dict[str, Any]:
    return lighting.solar_intensity(
        start=START,
        stop=STOP,
        position=j2_position(),
        step_s=900.0,
    )


def solar_intensity_for_two_body() -> dict[str, Any]:
    return lighting.solar_intensity(
        start=START,
        stop=STOP,
        position=two_body_position(),
        step_s=900.0,
    )


def solar_intensity_for_czml() -> dict[str, Any]:
    return lighting.solar_intensity(
        start=START,
        stop=STOP,
        position=czml_position(),
        step_s=900.0,
    )


def solar_aer_for_site() -> dict[str, Any]:
    return lighting.solar_aer(
        start=START,
        stop=STOP,
        position=site_position(),
        step_s=900,
    )


def solar_aer_for_sgp4() -> dict[str, Any]:
    return lighting.solar_aer(
        start=START,
        stop=STOP,
        position=sgp4_position(),
        step_s=900,
    )


CASES = [
    LiveSnapshotCase(
        id="lighting_times_site",
        description="Lighting intervals for a fixed geodetic site position.",
        run=lighting_times_for_site,
    ),
    LiveSnapshotCase(
        id="lighting_times_sgp4",
        description="Lighting intervals for an SGP4 TLE position.",
        run=lighting_times_for_sgp4,
    ),
    LiveSnapshotCase(
        id="solar_intensity_j2",
        description="Solar intensity samples for a J2 Keplerian position.",
        run=solar_intensity_for_j2,
    ),
    LiveSnapshotCase(
        id="solar_intensity_two_body",
        description="Solar intensity samples for a two-body Keplerian position.",
        run=solar_intensity_for_two_body,
    ),
    LiveSnapshotCase(
        id="solar_intensity_czml",
        description="Solar intensity samples for a CZML-like sampled position.",
        run=solar_intensity_for_czml,
    ),
    LiveSnapshotCase(
        id="solar_aer_site",
        description="Solar azimuth/elevation/range samples for a fixed geodetic site position.",
        run=solar_aer_for_site,
    ),
    LiveSnapshotCase(
        id="solar_aer_sgp4",
        description="Solar azimuth/elevation/range samples for an SGP4 TLE position.",
        run=solar_aer_for_sgp4,
    ),
]


def test_lighting_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(
        cases=CASES,
        snapshot_path=SNAPSHOT_PATH,
        abs_tol=LIGHTING_SNAPSHOT_ABS_TOL,
        rel_tol=LIGHTING_SNAPSHOT_REL_TOL,
    )


if __name__ == "__main__":
    raise SystemExit(
        main(
            cases=CASES,
            snapshot_path=SNAPSHOT_PATH,
            abs_tol=LIGHTING_SNAPSHOT_ABS_TOL,
            rel_tol=LIGHTING_SNAPSHOT_REL_TOL,
        )
    )
