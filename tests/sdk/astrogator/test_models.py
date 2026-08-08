"""Behavior tests for Astrogator RunMCS request fragments."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from astrox import astrogator, propagator
from tests.sdk.helpers import assert_canonical_equal


MU = 3.986004415e14


@pytest.fixture
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


def test_initial_state_lowers_exactly_and_is_frozen(state: astrogator.KeplerianState) -> None:
    fragment = astrogator.initial_state(
        "Init",
        state,
        epoch="2026-01-01T00:00:00Z",
        description="description",
        user_comment="comment",
    )

    assert is_dataclass(fragment)
    assert_canonical_equal(
        fragment.to_wire(),
        {
            "$type": "InitialState",
            "Name": "Init",
            "Description": "description",
            "UserComment": "comment",
            "InitialState": {
                "Epoch": "2026-01-01T00:00:00Z",
                "CoordSystemName": "Earth Inertial",
                "Element": {
                    "$type": "Keplerian",
                    "ElementType": "Osculating",
                    "GravitationalParameter": MU,
                    "SemiMajorAxis": 7_000_000.0,
                    "Eccentricity": 0.3,
                    "Inclination": 45.0,
                    "RAAN": 30.0,
                    "ArgOfPeriapsis": 60.0,
                    "AnomalyType": "True",
                    "TrueAnomaly": 30.0,
                },
                "DryMass": 500.0,
                "FuelMass": 500.0,
            },
        },
    )

    with pytest.raises(FrozenInstanceError):
        fragment.name = "changed"


def test_initial_state_exposes_coordinate_system_and_omits_optional_values(
    state: astrogator.KeplerianState,
) -> None:
    fragment = astrogator.initial_state(
        "Init",
        state,
        epoch="2026-01-01T00:00:00Z",
        coord_system_name="Earth Fixed",
        coefficient_of_drag=None,
        coefficient_of_srp=None,
        drag_area_m2=None,
        srp_area_m2=None,
    )

    wire = fragment.to_wire()
    assert wire["InitialState"]["CoordSystemName"] == "Earth Fixed"
    assert "Cd" not in wire["InitialState"]
    assert "Cr" not in wire["InitialState"]
    assert "DragArea" not in wire["InitialState"]
    assert "SRPArea" not in wire["InitialState"]


def test_all_state_discriminators_lower_to_distinct_wire_shapes() -> None:
    assert astrogator.cartesian_state(
        x_m=1.0, y_m=2.0, z_m=3.0, vx_m_s=4.0, vy_m_s=5.0, vz_m_s=6.0
    ).to_wire() == {
        "$type": "Cartesian", "X": 1.0, "Y": 2.0, "Z": 3.0,
        "Vx": 4.0, "Vy": 5.0, "Vz": 6.0,
    }
    assert astrogator.spherical_state(
        right_ascension_deg=1.0,
        declination_deg=2.0,
        radius_m=3.0,
        horizontal_fpa_deg=4.0,
        velocity_azimuth_deg=5.0,
        velocity_magnitude_m_s=6.0,
    ).to_wire() == {
        "$type": "Spherical",
        "RightAscension": 1.0,
        "Declination": 2.0,
        "RadiusMagnitude": 3.0,
        "HorizFPA": 4.0,
        "VelocityAzimuth": 5.0,
        "VelocityMagnitude": 6.0,
    }
    assert astrogator.target_vector_out_state(
        radius_of_periapsis_km=7000.0,
        c3_km2_s2=2.0,
        asymptote_ra_deg=10.0,
        asymptote_dec_deg=20.0,
        gravitational_parameter_m3_s2=MU,
    ).to_wire() == {
        "$type": "TargetVecOut",
        "GravitationalParameter": MU,
        "RadiusOfPeriapsis": 7000.0,
        "C3": 2.0,
        "AsympRA": 10.0,
        "AsympDec": 20.0,
        "VelAzAtPeriapsis": 0.0,
        "TrueAnomaly": 0.0,
    }


def test_scalar_constructors_lower_to_exact_wire_shapes() -> None:
    assert astrogator.duration_scalar("DurationScalar").to_wire() == {
        "$type": "Duration", "Name": "DurationScalar",
    }
    assert astrogator.epoch_scalar("EpochScalar").to_wire() == {
        "$type": "Epoch", "Name": "EpochScalar",
    }
    assert astrogator.keplerian_scalar(
        "KeplerianScalar",
        "TrueAnomaly",
        gravitational_parameter_m3_s2=MU,
        coord_system_name="Earth Inertial",
    ).to_wire() == {
        "$type": "KeplerianElement",
        "Name": "KeplerianScalar",
        "ComponentName": "TrueAnomaly",
        "Mu": MU,
        "CoordSystemName": "Earth Inertial",
        "ElementType": "Osculating",
    }
    assert astrogator.modified_keplerian_scalar(
        "ModifiedKeplerianScalar",
        "SemimajorAxis",
        gravitational_parameter_m3_s2=MU,
        coord_system_name="Earth Inertial",
    ).to_wire() == {
        "$type": "ModifiedKeplerianElement",
        "Name": "ModifiedKeplerianScalar",
        "ComponentName": "SemimajorAxis",
        "Mu": MU,
        "CoordSystemName": "Earth Inertial",
    }
    assert astrogator.cartographic_scalar(
        "CartographicScalar", "Latitude", central_body_name="Earth"
    ).to_wire() == {
        "$type": "Cartographic",
        "Name": "CartographicScalar",
        "ComponentName": "Latitude",
        "CentralBodyName": "Earth",
    }
    assert astrogator.point_scalar(
        "PointScalar", "X", coord_system_name="Earth Inertial"
    ).to_wire() == {
        "$type": "PointElement",
        "Name": "PointScalar",
        "ComponentName": "X",
        "CoordSystemName": "Earth Inertial",
    }
    assert astrogator.spherical_scalar(
        "SphericalScalar", "Radius", coord_system_name="Earth Inertial"
    ).to_wire() == {
        "$type": "SphericalElement",
        "Name": "SphericalScalar",
        "ComponentName": "Radius",
        "CoordSystemName": "Earth Inertial",
    }
    assert astrogator.delta_spherical_scalar(
        "DeltaSphericalScalar", "Radius", central_body_name="Earth",
        parent_central_body_name="Moon",
    ).to_wire() == {
        "$type": "DeltaSpherical",
        "Name": "DeltaSphericalScalar",
        "ComponentName": "Radius",
        "CentralBodyName": "Earth",
        "ParentCbName": "Moon",
    }
    assert astrogator.b_plane_scalar(
        "BPlaneScalar",
        "BVectorDotR",
        gravitational_parameter_m3_s2=MU,
        central_body_name="Earth",
    ).to_wire() == {
        "$type": "BPlane",
        "Name": "BPlaneScalar",
        "ComponentName": "BVectorDotR",
        "Mu": MU,
        "CentralBodyName": "Earth",
    }


def test_scalar_tree_lowers_nested_relative_branch() -> None:
    scalar = astrogator.relative_scalar(
        "RelativeTA",
        astrogator.keplerian_scalar(
            "TA",
            "TrueAnomaly",
            gravitational_parameter_m3_s2=MU,
            coord_system_name="Earth Inertial",
        ),
        reference_name="Init",
    )
    assert_canonical_equal(
        scalar.to_wire(),
        {
            "$type": "Relative",
            "Name": "RelativeTA",
            "ReferenceName": "Init",
            "CalcObject": {
                "$type": "KeplerianElement",
                "Name": "TA",
                "ComponentName": "TrueAnomaly",
                "Mu": MU,
                "CoordSystemName": "Earth Inertial",
                "ElementType": "Osculating",
            },
        },
    )


def test_attitude_control_families_lower_exactly() -> None:
    assert astrogator.impulsive_velocity_vector(10.0).to_wire() == {
        "$type": "VelocityVector", "DeltaVMagnitude": 10.0
    }
    assert astrogator.impulsive_anti_velocity_vector(10.0).to_wire() == {
        "$type": "AntiVelocityVector", "DeltaVMagnitude": 10.0
    }
    assert astrogator.impulsive_thrust_vector_cartesian(1.0, 2.0, 3.0).to_wire() == {
        "$type": "ThrustVector", "CoordType": "Cartesian",
        "ThrustAxesName": "VNC(Earth)", "X": 1.0, "Y": 2.0, "Z": 3.0,
    }
    assert astrogator.impulsive_thrust_vector_spherical(1.0, 2.0, 3.0).to_wire() == {
        "$type": "ThrustVector", "CoordType": "Spherical",
        "ThrustAxesName": "VNC(Earth)", "Azimuth": 1.0,
        "Elevation": 2.0, "Magnitude": 3.0,
    }
    assert astrogator.impulsive_attitude_quaternion(10.0).to_wire() == {
        "$type": "Attitude", "DeltaVMagnitude": 10.0,
        "CoordType": "Quaternion", "RefAxesName": "VNC(Earth)",
        "QX": 0.0, "QY": 0.0, "QZ": 0.0, "QS": 1.0,
    }
    assert astrogator.impulsive_attitude_euler(10.0, 1.0, 2.0, 3.0).to_wire() == {
        "$type": "Attitude", "DeltaVMagnitude": 10.0,
        "CoordType": "EulerAngles", "RefAxesName": "VNC(Earth)",
        "A": 1.0, "B": 2.0, "C": 3.0, "Sequence": "313",
    }
    assert astrogator.finite_velocity_vector().to_wire() == {
        "$type": "VelocityVector", "AttitudeUpdate": "DuringBurn"
    }
    assert astrogator.finite_anti_velocity_vector().to_wire() == {
        "$type": "AntiVelocityVector", "AttitudeUpdate": "DuringBurn"
    }
    assert astrogator.finite_thrust_vector_cartesian(1.0, 2.0, 3.0).to_wire() == {
        "$type": "ThrustVector", "AttitudeUpdate": "DuringBurn",
        "CoordType": "Cartesian", "ThrustAxesName": "VNC(Earth)",
        "X": 1.0, "Y": 2.0, "Z": 3.0,
    }
    assert astrogator.finite_thrust_vector_spherical(1.0, 2.0, 3.0).to_wire() == {
        "$type": "ThrustVector", "AttitudeUpdate": "DuringBurn",
        "CoordType": "Spherical", "ThrustAxesName": "VNC(Earth)",
        "Azimuth": 1.0, "Elevation": 2.0, "Magnitude": 3.0,
    }
    assert astrogator.finite_attitude_quaternion().to_wire() == {
        "$type": "Attitude", "AttitudeUpdate": "DuringBurn",
        "CoordType": "Quaternion", "RefAxesName": "VNC(Earth)",
        "QX": 0.0, "QY": 0.0, "QZ": 0.0, "QS": 1.0,
    }
    assert astrogator.finite_attitude_euler(1.0, 2.0, 3.0).to_wire() == {
        "$type": "Attitude", "AttitudeUpdate": "DuringBurn",
        "CoordType": "EulerAngles", "RefAxesName": "VNC(Earth)",
        "A": 1.0, "B": 2.0, "C": 3.0, "Sequence": "313",
    }


def test_engine_constant_lowers_exactly() -> None:
    assert astrogator.constant_engine(
        name="EngineA", thrust_n=500.0, isp_s=600.0
    ).to_wire() == {
        "$type": "EngineConstant", "Name": "EngineA",
        "Thrust": 500.0, "Isp": 600.0, "g": 9.80665,
    }


def test_differential_corrector_lowers_control_constraint_and_profile_exactly() -> None:
    control = astrogator.differential_corrector_control(
        "StopConditions.Duration", 10.0, parent_name="Coast"
    )
    assert control.to_wire() == {
        "Enable": True,
        "Name": "StopConditions.Duration",
        "ParentName": "Coast",
        "InitialValue": "10.0",
        "Perturbation": 1.0,
        "MaxStep": 600.0,
        "Tolerance": 1.0e-4,
    }
    constraint = astrogator.differential_corrector_constraint(
        "FinalTA", 36.0, parent_name="Coast"
    )
    assert constraint.to_wire() == {
        "Enable": True,
        "Name": "FinalTA",
        "DesiredValue": "36.0",
        "ParentName": "Coast",
        "Tolerance": 0.1,
    }
    assert astrogator.differential_corrector(
        "DC1", controls=[control], results=[constraint]
    ).to_wire() == {
        "$type": "DifferentialCorrector",
        "Name": "DC1",
        "Active": True,
        "MaximumIterations": 50,
        "ControlParameters": [control.to_wire()],
        "Results": [constraint.to_wire()],
    }


def test_maneuver_segments_lower_exactly() -> None:
    assert astrogator.impulsive_maneuver(
        "Impulse",
        attitude_control=astrogator.impulsive_velocity_vector(10.0),
        propulsion_method_value="0",
    ).to_wire() == {
        "$type": "ManeuverImpulsive",
        "Name": "Impulse",
        "AttitudeControl": {"$type": "VelocityVector", "DeltaVMagnitude": 10.0},
        "PropulsionMethodValue": "0",
        "UpdateMass": False,
    }
    assert astrogator.finite_maneuver(
        "Burn",
        attitude_control=astrogator.finite_velocity_vector(),
        propagator_name="Earth_TwoBody",
        stop_conditions=[astrogator.duration_stop("BurnStop", 10.0)],
        propulsion_method_value="0",
    ).to_wire() == {
        "$type": "ManeuverFinite",
        "Name": "Burn",
        "AttitudeControl": {"$type": "VelocityVector", "AttitudeUpdate": "DuringBurn"},
        "PropagatorName": "Earth_TwoBody",
        "StopConditions": [
            {
                "$type": "Duration", "Name": "BurnStop", "Trip": 10.0,
                "Tolerance": 1.0e-6, "Active": True,
            }
        ],
        "PropulsionMethodValue": "0",
        "ThrustEfficiency": 1.0,
    }


def test_sequence_and_target_sequence_lower_exactly(state: astrogator.KeplerianState) -> None:
    initial = astrogator.initial_state("Init", state, epoch="2026-01-01T00:00:00Z")
    coast = astrogator.propagate(
        "Coast",
        propagator_name="Earth_TwoBody",
        stop_conditions=[astrogator.duration_stop("Duration", 10.0)],
        variable_names="StopConditions.Duration",
    )
    assert astrogator.sequence("Seq", [initial, coast]).to_wire() == {
        "$type": "Sequence",
        "Name": "Seq",
        "Segments": [
            {
                "$type": "InitialState",
                "Name": "Init",
                "InitialState": {
                    "Epoch": "2026-01-01T00:00:00Z",
                    "CoordSystemName": "Earth Inertial",
                    "Element": {
                        "$type": "Keplerian",
                        "ElementType": "Osculating",
                        "GravitationalParameter": MU,
                        "SemiMajorAxis": 7_000_000.0,
                        "Eccentricity": 0.3,
                        "Inclination": 45.0,
                        "RAAN": 30.0,
                        "ArgOfPeriapsis": 60.0,
                        "AnomalyType": "True",
                        "TrueAnomaly": 30.0,
                    },
                    "DryMass": 500.0,
                    "FuelMass": 500.0,
                },
            },
            {
                "$type": "Propagate",
                "Name": "Coast",
                "PropagatorName": "Earth_TwoBody",
                "StopConditions": [
                    {
                        "$type": "Duration", "Name": "Duration", "Trip": 10.0,
                        "Tolerance": 1.0e-6, "Active": True,
                    }
                ],
                "VariableNames": "StopConditions.Duration",
            },
        ],
    }
    control = astrogator.differential_corrector_control(
        "StopConditions.Duration", 10.0, parent_name="Coast"
    )
    constraint = astrogator.differential_corrector_constraint(
        "FinalTA", 36.0, parent_name="Coast"
    )
    profile = astrogator.differential_corrector(
        "DC1", controls=[control], results=[constraint]
    )
    assert astrogator.target_sequence(
        "Target", [initial, coast], profiles=[profile]
    ).to_wire() == {
        "$type": "TargetSequence",
        "Name": "Target",
        "Action": "RunNominalSequence",
        "Segments": [initial.to_wire(), coast.to_wire()],
        "Profiles": [profile.to_wire()],
    }


def test_mission_position_and_entity_path_lower_exactly(
    state: astrogator.KeplerianState,
) -> None:
    initial = astrogator.initial_state("Init", state, epoch="2026-01-01T00:00:00Z")
    coast = astrogator.propagate(
        "Coast",
        propagator_name="Earth_TwoBody",
        stop_conditions=[astrogator.duration_stop("Duration", 10.0)],
        variable_names="StopConditions.Duration",
    )
    config = propagator.hpop_config(
        name="Earth_TwoBody",
        central_body="Earth",
        integrator=propagator.hpop_rkf78(name="RKF7th8th"),
        gravity=propagator.hpop_two_body_gravity(
            gravitational_parameter_m3_s2=MU,
        ),
    )
    engine = astrogator.constant_engine(name="EngineA", thrust_n=500.0, isp_s=600.0)
    mission = astrogator.mission_position(
        main_sequence=[initial, coast],
        compute_czml_positions=True,
        propagators=[config],
        engine_models=[engine],
    )
    assert mission.to_wire() == {
        "$type": "AstrogatorMCS",
        "CentralBody": "Earth",
        "OutCzmlFrameName": "INERTIAL",
        "MainSequence": [initial.to_wire(), coast.to_wire()],
        "ComputeCzmlPositions": True,
        "Propagators": [
            {
                "Name": "Earth_TwoBody",
                "CentralBodyName": "Earth",
                "NumericalIntegrator": {"$type": "RKF7th8th", "Name": "RKF7th8th"},
                "GravityModel": {"$type": "TwoBody", "Mu": MU},
            }
        ],
        "EngineModels": [engine.to_wire()],
    }
    assert astrogator.entity_path("Leader", position=mission).to_wire() == {
        "$type": "EntityPath",
        "Name": "Leader",
        "Position": mission.to_wire(),
    }


def test_curated_constructors_reject_raw_dicts() -> None:
    with pytest.raises(TypeError):
        astrogator.initial_state("Init", {}, epoch="2026-01-01T00:00:00Z")
    with pytest.raises(TypeError):
        astrogator.propagate(
            "Prop", propagator_name="P", stop_conditions=[{}]
        )
    with pytest.raises(TypeError):
        astrogator.sequence("Seq", [{}])
    with pytest.raises(TypeError):
        astrogator.entity_path("Entity", position={})


def test_propagate_rejects_fractional_maximum_propagation_time() -> None:
    with pytest.raises(TypeError, match="max_propagation_time_s must be an integer"):
        astrogator.propagate(
            "Prop",
            propagator_name="P",
            stop_conditions=[],
            max_propagation_time_s=1.5,
        )

    fragment = astrogator.propagate(
        "Prop",
        propagator_name="P",
        stop_conditions=[],
        max_propagation_time_s=2,
    )
    assert fragment.to_wire()["MaxPropagationTime"] == 2


def test_stop_conditions_and_follow_lower_all_server_branches() -> None:
    assert astrogator.duration_stop("Duration", 10.0).to_wire() == {
        "$type": "Duration", "Name": "Duration", "Trip": 10.0,
        "Tolerance": 1.0e-6, "Active": True,
    }
    assert astrogator.epoch_stop("Epoch", "2026-01-01T00:00:10Z").to_wire() == {
        "$type": "Epoch", "Name": "Epoch", "Trip": "2026-01-01T00:00:10Z", "Active": True,
    }
    assert astrogator.periapsis_stop(
        "Peri", gravitational_parameter_m3_s2=MU, repeat_count=2
    ).to_wire() == {
        "$type": "Periapsis", "Name": "Peri", "CentralBodyName": "Earth",
        "Mu": MU, "RepeatCount": 2, "Tolerance": 1.0e-6, "Active": True,
    }
    assert astrogator.apoapsis_stop(
        "Apo", gravitational_parameter_m3_s2=MU, repeat_count=2
    ).to_wire() == {
        "$type": "Apoapsis", "Name": "Apo", "CentralBodyName": "Earth",
        "Mu": MU, "RepeatCount": 2, "Tolerance": 1.0e-6, "Active": True,
    }
    assert astrogator.stop(
        "Stop",
        enable=False,
        description="description",
        user_comment="comment",
        results=[astrogator.duration_scalar("Elapsed")],
    ).to_wire() == {
        "$type": "Stop", "Name": "Stop", "Description": "description",
        "UserComment": "comment", "Enable": False,
        "Results": [{"$type": "Duration", "Name": "Elapsed"}],
    }
    assert astrogator.follow(
        "Follow",
        leader_name="Leader",
        joining="Specify",
        separation="Specify",
        joining_conditions=[astrogator.duration_stop("Join", 5.0)],
        separation_conditions=[astrogator.duration_stop("Separate", 10.0)],
        x_offset_m=1.0,
        y_offset_m=2.0,
        z_offset_m=3.0,
        variable_names="StopConditions.Duration",
    ).to_wire() == {
        "$type": "Follow",
        "Name": "Follow",
        "LeaderName": "Leader",
        "Joining": "Specify",
        "Separation": "Specify",
        "JoiningConditions": [
            {
                "$type": "Duration", "Name": "Join", "Trip": 5.0,
                "Tolerance": 1.0e-6, "Active": True,
            }
        ],
        "SeparationConditions": [
            {
                "$type": "Duration", "Name": "Separate", "Trip": 10.0,
                "Tolerance": 1.0e-6, "Active": True,
            }
        ],
        "XOffset": 1.0,
        "YOffset": 2.0,
        "ZOffset": 3.0,
        "VariableNames": "StopConditions.Duration",
    }


def test_mission_position_omits_compute_czml_positions_when_unsupplied() -> None:
    mission = astrogator.mission_position(
        main_sequence=[
            astrogator.initial_state(
                "Init",
                astrogator.cartesian_state(
                    x_m=1.0, y_m=2.0, z_m=3.0, vx_m_s=4.0, vy_m_s=5.0, vz_m_s=6.0
                ),
                epoch="2026-01-01T00:00:00Z",
            )
        ]
    )
    assert_canonical_equal(
        mission.to_wire(),
        {
            "$type": "AstrogatorMCS",
            "CentralBody": "Earth",
            "OutCzmlFrameName": "INERTIAL",
            "MainSequence": [
                {
                    "$type": "InitialState",
                    "Name": "Init",
                    "InitialState": {
                        "Epoch": "2026-01-01T00:00:00Z",
                        "CoordSystemName": "Earth Inertial",
                        "Element": {
                            "$type": "Cartesian",
                            "X": 1.0, "Y": 2.0, "Z": 3.0,
                            "Vx": 4.0, "Vy": 5.0, "Vz": 6.0,
                        },
                        "DryMass": 500.0,
                        "FuelMass": 500.0,
                    },
                }
            ],
        },
    )
