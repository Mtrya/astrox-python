#!/usr/bin/env python3
"""Live snapshots for the HPOP propagator."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits, propagator
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("hpop.snap.json")
START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
ORBIT_EPOCH = START
EARTH_MU = 398600441500000.0


def leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )


def leo_cartesian_state() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=7000000.0,
        y_m=1000.0,
        z_m=2000.0,
        vx_m_s=-1.0,
        vy_m_s=7500.0,
        vz_m_s=10.0,
    )


def two_body_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        central_body="Earth",
        gravity=propagator.hpop_two_body_gravity(),
    )


def gravity_field_integrator_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            use_fixed_step=False,
            initial_step_s=30.0,
            max_step_s=120.0,
            min_step_s=0.001,
            max_abs_error=1e-10,
            max_rel_error=1e-12,
            max_iterations=50,
        ),
        gravity=propagator.hpop_gravity_field(
            gravity_file_name="EGM2008.grv",
            degree=4,
            order=4,
            use_secular_variations=False,
            solid_tide_type="Permanent tide only",
            eop_file_path="EOP-v1.1.txt",
        ),
    )


def full_branch_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            use_fixed_step=False,
            initial_step_s=30.0,
            max_step_s=120.0,
            min_step_s=0.001,
            max_abs_error=1e-10,
            max_rel_error=1e-12,
            max_iterations=50,
        ),
        gravity=propagator.hpop_gravity_field(
            gravity_file_name="EGM2008.grv",
            degree=4,
            order=4,
            use_secular_variations=False,
            solid_tide_type="Permanent tide only",
            eop_file_path="EOP-v1.1.txt",
        ),
        atmosphere=propagator.hpop_jacchia_roberts(
            drag_model_type="Spherical",
            atmos_data_source="Constant Values",
            f10p7=150.0,
            f10p7_avg=150.0,
            kp=3.0,
        ),
        srp=propagator.hpop_srp_spherical(
            shadow_model="DualCone",
            sun_position="Apparent",
            eclipsing_bodies=["Earth", "Moon"],
        ),
        third_bodies=[
            propagator.hpop_third_body(
                "Sun",
                mode_type="PointMass",
                ephem_source="DeFile",
                grav_source="DeFile",
            ),
            propagator.hpop_third_body(
                "Moon",
                mode_type="PointMass",
                ephem_source="DeFile",
                grav_source="DeFile",
            ),
        ],
    )


def classical_two_body() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.hpop(
        start=START,
        stop=STOP,
        orbit_epoch=ORBIT_EPOCH,
        orbit=leo_orbit(),
        config=two_body_config(),
        coord_system="Inertial",
        coord_epoch="2000-01-01T11:58:55.816Z",
    )


def cartesian_two_body() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.hpop(
        start=START,
        stop=STOP,
        orbit_epoch=ORBIT_EPOCH,
        state=leo_cartesian_state(),
        config=two_body_config(),
        coord_system="Inertial",
    )


def gravity_field_integrator() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.hpop(
        start=START,
        stop=STOP,
        orbit_epoch=ORBIT_EPOCH,
        orbit=leo_orbit(),
        config=gravity_field_integrator_config(),
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU,
    )


def full_branch_surface() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.hpop(
        start=START,
        stop=STOP,
        orbit_epoch=ORBIT_EPOCH,
        orbit=leo_orbit(),
        config=full_branch_config(),
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU,
        coefficient_of_drag=2.2,
        area_mass_ratio_drag_m2_kg=0.02,
        coefficient_of_srp=1.0,
        area_mass_ratio_srp_m2_kg=0.02,
    )


CASES = [
    LiveSnapshotCase(
        id="classical_two_body",
        description="Classical HPOP propagation with explicit two-body gravity config.",
        run=classical_two_body,
    ),
    LiveSnapshotCase(
        id="cartesian_two_body",
        description="Cartesian HPOP propagation with explicit two-body gravity config.",
        run=cartesian_two_body,
    ),
    LiveSnapshotCase(
        id="gravity_field_integrator",
        description="Classical HPOP propagation with gravity-field config and explicit RKF78 knobs.",
        run=gravity_field_integrator,
    ),
    LiveSnapshotCase(
        id="full_branch_surface",
        description="Classical HPOP propagation exercising gravity field, Jacchia-Roberts, SRP spherical, third-body, and spacecraft scalar branches.",
        run=full_branch_surface,
    ),
]


def test_hpop_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
