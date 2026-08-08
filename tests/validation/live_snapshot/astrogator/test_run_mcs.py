#!/usr/bin/env python3
"""Live snapshots for the public Astrogator RunMCS surface."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import astrogator, propagator
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("run_mcs.snap.json")
START = "2026-01-01T00:00:00Z"
MU = 398600441500000.0


def state() -> astrogator.KeplerianState:
    return astrogator.keplerian_state(
        semi_major_axis_m=7_000_000.0,
        eccentricity=0.3,
        inclination_deg=45.0,
        raan_deg=30.0,
        argument_of_periapsis_deg=60.0,
        gravitational_parameter_m3_s2=MU,
        true_anomaly_deg=30.0,
    )


def hpop_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        name="Earth_HPOP_PR15",
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="RKF7th8th",
            use_fixed_step=True,
            initial_step_s=0.1,
            max_step_s=0.1,
            min_step_s=0.1,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_gravity_field(
            name="EGM2008",
            gravity_file_name="EGM2008.grv",
            degree=4,
            order=4,
            use_secular_variations=False,
            solid_tide_type="Permanent tide only",
            eop_file_path="EOP-v1.1.txt",
        ),
    )


def all_force_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        name="Earth_AllForces_PR15",
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="AllForces_RKF7th8th",
            use_fixed_step=True,
            initial_step_s=0.1,
            max_step_s=0.1,
            min_step_s=0.1,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_gravity_field(
            name="EGM2008_AllForces",
            gravity_file_name="EGM2008.grv",
            degree=4,
            order=4,
            use_secular_variations=False,
            solid_tide_type="Permanent tide only",
            eop_file_path="EOP-v1.1.txt",
        ),
        atmosphere=propagator.hpop_jacchia_roberts(
            name="JacchiaRoberts_AllForces",
            drag_model_type="Spherical",
            atmos_data_source="Constant Values",
            f10p7=150.0,
            f10p7_avg=150.0,
            kp=3.0,
        ),
        srp=propagator.hpop_srp_spherical(
            name="SRP_AllForces",
            shadow_model="DualCone",
            sun_position="Apparent",
            eclipsing_bodies=["Earth", "Moon"],
        ),
        third_bodies=[
            propagator.hpop_third_body(
                "Sun",
                name="Sun_AllForces",
                mode_type="PointMass",
                ephem_source="DeFile",
                grav_source="DeFile",
            ),
            propagator.hpop_third_body(
                "Moon",
                name="Moon_AllForces",
                mode_type="PointMass",
                ephem_source="DeFile",
                grav_source="DeFile",
            ),
        ],
    )


def initial_state_case() -> astrogator.RunMCSResult:
    return astrogator.run_mcs(
        [astrogator.initial_state("Init", state(), epoch=START)],
    )


def propagate_case() -> astrogator.RunMCSResult:
    return astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state(), epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name="Earth_HPOP_PR15",
                stop_conditions=[astrogator.duration_stop("Duration", 1.0)],
            ),
        ],
        propagators=[hpop_config()],
    )


def propagate_czml_case() -> astrogator.RunMCSResult:
    return astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state(), epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name="Earth_HPOP_PR15",
                stop_conditions=[astrogator.duration_stop("Duration", 1.0)],
            ),
        ],
        compute_czml_positions=True,
        propagators=[hpop_config()],
    )


def impulsive_case() -> astrogator.RunMCSResult:
    return astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state(), epoch=START),
            astrogator.impulsive_maneuver(
                "Burn",
                attitude_control=astrogator.impulsive_velocity_vector(100.0),
                propulsion_method_value="Constant_Thrust_Isp",
                update_mass=False,
            ),
        ],
    )


def finite_case() -> astrogator.RunMCSResult:
    return astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state(), epoch=START),
            astrogator.finite_maneuver(
                "Burn",
                attitude_control=astrogator.finite_velocity_vector(),
                propagator_name="Earth_HPOP_PR15",
                stop_conditions=[astrogator.duration_stop("Duration", 1.0)],
                propulsion_method_value="EngineA",
            ),
        ],
        propagators=[hpop_config()],
        engine_models=[
            astrogator.constant_engine(name="EngineA", thrust_n=500.0, isp_s=600.0)
        ],
    )


def all_force_case() -> astrogator.RunMCSResult:
    return astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state(), epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name="Earth_AllForces_PR15",
                stop_conditions=[astrogator.duration_stop("Duration", 1.0)],
            ),
        ],
        propagators=[all_force_config()],
    )


def sequence_case() -> astrogator.RunMCSResult:
    mission = astrogator.sequence(
        "Mission",
        [
            astrogator.initial_state("Init", state(), epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name="Earth_HPOP_PR15",
                stop_conditions=[astrogator.duration_stop("Duration", 1.0)],
            ),
        ],
    )
    return astrogator.run_mcs([mission], propagators=[hpop_config()])


def scalar_case() -> astrogator.RunMCSResult:
    return astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state(), epoch=START),
            astrogator.propagate(
                "Prop",
                propagator_name="Earth_HPOP_PR15",
                stop_conditions=[astrogator.duration_stop("Duration", 1.0)],
                results=[
                    astrogator.duration_scalar("Elapsed"),
                    astrogator.epoch_scalar("EpochValue"),
                    astrogator.keplerian_scalar(
                        "FinalTA",
                        "TrueAnomaly",
                        gravitational_parameter_m3_s2=MU,
                        coord_system_name="Earth Inertial",
                    ),
                    astrogator.modified_keplerian_scalar(
                        "ModifiedTA",
                        "TrueAnomaly",
                        gravitational_parameter_m3_s2=MU,
                        coord_system_name="Earth Inertial",
                    ),
                    astrogator.cartographic_scalar("Latitude", "Latitude", central_body_name="Earth"),
                    astrogator.point_scalar("PointX", "X", coord_system_name="Earth Inertial"),
                    astrogator.spherical_scalar(
                        "SphericalRA", "RightAscension", coord_system_name="Earth Inertial"
                    ),
                ],
            ),
        ],
        propagators=[hpop_config()],
    )


def target_case() -> astrogator.RunMCSResult:
    coast = astrogator.propagate(
        "Coast",
        propagator_name="Earth_HPOP_PR15",
        stop_conditions=[astrogator.duration_stop("Duration", 60.0)],
        variable_names="StopConditions.Duration",
        results=[
            astrogator.keplerian_scalar(
                "FinalTA",
                "TrueAnomaly",
                gravitational_parameter_m3_s2=MU,
                coord_system_name="Earth Inertial",
            )
        ],
    )
    profile = astrogator.differential_corrector(
        "DC1",
        controls=[
            astrogator.differential_corrector_control(
                "StopConditions.Duration",
                10.0,
                parent_name="Coast",
                perturbation=1.0,
                max_step=600.0,
                tolerance=0.0001,
            )
        ],
        results=[
            astrogator.differential_corrector_constraint(
                "FinalTA", 36.0, parent_name="Coast", tolerance=0.1
            )
        ],
    )
    return astrogator.run_mcs(
        [
            astrogator.initial_state("Init", state(), epoch=START),
            astrogator.target_sequence(
                "Target", [coast], action="RunActiveOperators", profiles=[profile]
            ),
        ],
        propagators=[hpop_config()],
    )


CASES = [
    LiveSnapshotCase(
        id="initial_state",
        description="Keplerian InitialState result and returned state views.",
        run=initial_state_case,
    ),
    LiveSnapshotCase(
        id="propagate",
        description="One-second propagation with a registered custom HPOP model.",
        run=propagate_case,
    ),
    LiveSnapshotCase(
        id="propagate_czml",
        description="One-second propagation with sampled CZML positions enabled.",
        run=propagate_czml_case,
    ),
    LiveSnapshotCase(
        id="impulsive",
        description="Impulsive velocity-vector maneuver result.",
        run=impulsive_case,
    ),
    LiveSnapshotCase(
        id="finite",
        description="One-second finite velocity-vector maneuver with a constant engine.",
        run=finite_case,
    ),
    LiveSnapshotCase(
        id="all_force_models",
        description="Custom gravity, atmosphere, SRP, and third-body model collection.",
        run=all_force_case,
    ),
    LiveSnapshotCase(
        id="sequence",
        description="Nested Sequence result with recursive child results.",
        run=sequence_case,
    ),
    LiveSnapshotCase(
        id="scalar_results",
        description="Duration, epoch, orbital, cartographic, point, and spherical scalar results.",
        run=scalar_case,
    ),
    LiveSnapshotCase(
        id="target_sequence",
        description="Active differential-corrector TargetSequence result and operator trace.",
        run=target_case,
    ),
]


def test_run_mcs_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
