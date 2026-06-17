#!/usr/bin/env python3
"""Live snapshots for orbit conversion helpers."""

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


SNAPSHOT_PATH = Path(__file__).with_name("conversions.snap.json")
# Live runners have observed tiny angle/value drift from the same ASTROX route.
# This snapshot remains a response-shape drift guard, not a semantic precision
# proof.
ORBIT_CONVERSIONS_SNAPSHOT_ABS_TOL = 1.0e-4
EARTH_MU = 398600441500000.0
ORBIT_EPOCH = "2024-01-01T00:00:00.000Z"


def leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def geo_platform_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=42164000.0,
        eccentricity=0.0001,
        inclination_deg=0.2,
        argument_of_periapsis_deg=0.0,
        raan_deg=30.0,
        true_anomaly_deg=20.0,
    )


def lambert_target_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=42164000.0,
        eccentricity=0.001,
        inclination_deg=1.0,
        argument_of_periapsis_deg=10.0,
        raan_deg=80.0,
        true_anomaly_deg=95.0,
    )


def cartesian_state() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=6114454.0,
        y_m=2870352.0,
        z_m=3308542.0,
        vx_m_s=-3548.0,
        vy_m_s=6463.0,
        vz_m_s=1830.0,
    )


def lambert_arrival_state() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=-4963330.5,
        y_m=4154175.2,
        z_m=1301603.0,
        vx_m_s=-5569.688,
        vy_m_s=-5716.8755,
        vz_m_s=323.9083,
    )


def keplerian_to_cartesian() -> orbits.CartesianState:
    return orbits.keplerian_to_cartesian(
        leo_orbit(),
        gravitational_parameter_m3_s2=EARTH_MU,
    )


def cartesian_to_keplerian() -> orbits.KeplerianElements:
    return orbits.cartesian_to_keplerian(cartesian_state())


def lla_at_ascending_node() -> tuple[float, float, float]:
    return orbits.lla_at_ascending_node(
        leo_orbit(),
        orbit_epoch=ORBIT_EPOCH,
    )


def kozai_izsak_mean_elements() -> orbits.MeanKeplerianElements:
    return orbits.kozai_izsak_mean_elements(leo_orbit())


def lambert_delta_v_with_platform_mu() -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
]:
    return orbits.geo_ym_lambert_delta_v(
        platform_orbit=geo_platform_orbit(),
        target_orbit=lambert_target_orbit(),
        time_of_flight_s=3600.0,
        platform_gravitational_parameter_m3_s2=EARTH_MU,
    )


def lambert_delta_v_cartesian() -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
]:
    return orbits.lambert_delta_v(
        departure_state=cartesian_state(),
        arrival_state=lambert_arrival_state(),
        time_of_flight_s=817.4257,
        gravitational_parameter_m3_s2=EARTH_MU,
    )


def lambert_delta_v_server_default_mu() -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
]:
    return orbits.geo_ym_lambert_delta_v(
        platform_orbit=geo_platform_orbit(),
        target_orbit=lambert_target_orbit(),
        time_of_flight_s=3600.0,
    )


CASES = [
    LiveSnapshotCase(
        id="keplerian_to_cartesian",
        description="Classical Keplerian elements converted to Cartesian position and velocity with explicit Earth mu.",
        run=keplerian_to_cartesian,
    ),
    LiveSnapshotCase(
        id="cartesian_to_keplerian",
        description="Cartesian position and velocity converted to Classical Keplerian elements.",
        run=cartesian_to_keplerian,
    ),
    LiveSnapshotCase(
        id="lla_at_ascending_node",
        description="Ascending-node location returned as longitude, latitude, and height.",
        run=lla_at_ascending_node,
    ),
    LiveSnapshotCase(
        id="kozai_izsak_mean_elements",
        description="Osculating Classical elements converted to Kozai-Izsak mean elements.",
        run=kozai_izsak_mean_elements,
    ),
    LiveSnapshotCase(
        id="lambert_delta_v_with_platform_mu",
        description="GEO-YM Lambert delta-v with explicit platform gravitational parameter.",
        run=lambert_delta_v_with_platform_mu,
    ),
    LiveSnapshotCase(
        id="lambert_delta_v_cartesian",
        description="Single-revolution Lambert delta-v between two Cartesian states.",
        run=lambert_delta_v_cartesian,
    ),
    LiveSnapshotCase(
        id="lambert_delta_v_server_default_mu",
        description="GEO-YM Lambert delta-v with server-owned platform gravitational parameter.",
        run=lambert_delta_v_server_default_mu,
    ),
]


def test_orbit_conversion_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(
        cases=CASES,
        snapshot_path=SNAPSHOT_PATH,
        abs_tol=ORBIT_CONVERSIONS_SNAPSHOT_ABS_TOL,
        datetime_abs_tol_s=ORBIT_CONVERSIONS_SNAPSHOT_ABS_TOL,
    )


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
