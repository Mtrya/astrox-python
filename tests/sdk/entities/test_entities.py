"""Focused tests for entity and position-source constructors."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from astrox import entities, orbits, propagator
from tests.sdk.helpers import assert_canonical_equal


TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

ORBIT_WIRE = [6778137.0, 0.001, 28.5, 0.0, 15.0, 45.0]


def sample_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def sample_state() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=7000000.0,
        y_m=1000.0,
        z_m=2000.0,
        vx_m_s=-1.0,
        vy_m_s=7500.0,
        vz_m_s=10.0,
    )


def test_public_entity_names_are_exported() -> None:
    assert "AlignedAndConstrainedAxes" in entities.__all__
    assert "AzElMaskConstraint" in entities.__all__
    assert "AzElRotation" in entities.__all__
    assert "CompositeAxes" in entities.__all__
    assert "Constraint" in entities.__all__
    assert "CzmlAxes" in entities.__all__
    assert "Entity" in entities.__all__
    assert "EntityAxes" in entities.__all__
    assert "EntityGroup" in entities.__all__
    assert "ElevationConstraint" in entities.__all__
    assert "EulerRotation" in entities.__all__
    assert "FixedAtEpochAxes" in entities.__all__
    assert "FixedAxes" in entities.__all__
    assert "FixedSensorPointing" in entities.__all__
    assert "LvlhAxes" in entities.__all__
    assert "QuaternionRotation" in entities.__all__
    assert "RangeConstraint" in entities.__all__
    assert "Rotation" in entities.__all__
    assert "RaDecDirection" in entities.__all__
    assert "SensorPointing" in entities.__all__
    assert "SitePosition" in entities.__all__
    assert "CentralBodyPosition" in entities.__all__
    assert "J2Position" in entities.__all__
    assert "TwoBodyPosition" in entities.__all__
    assert "Sgp4Position" in entities.__all__
    assert "CzmlPosition" in entities.__all__
    assert "CzmlPositions" in entities.__all__
    assert "HpopPosition" in entities.__all__
    assert "SimpleAscentPosition" in entities.__all__
    assert "BallisticPosition" in entities.__all__
    assert "ConicSensor" in entities.__all__
    assert "RectangularSensor" in entities.__all__
    assert "VgtAngle" in entities.__all__
    assert "VgtDirection" in entities.__all__
    assert "VgtFixedVector" in entities.__all__
    assert "VgtPlane" in entities.__all__
    assert "VgtPoint" in entities.__all__
    assert "VgtProvider" in entities.__all__
    assert "VgtSystem" in entities.__all__
    assert "VgtVector" in entities.__all__
    assert "VncAxes" in entities.__all__
    assert "VvlhAxes" in entities.__all__
    assert "XyzDirection" in entities.__all__
    assert "az_el_mask_constraint" in entities.__all__
    assert "elevation_constraint" in entities.__all__
    assert "range_constraint" in entities.__all__


def test_site_position_has_typed_and_site_only_wire_forms() -> None:
    position = entities.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
        central_body="Earth",
        clamp_to_ground=False,
        height_above_ground_m=10.0,
    )

    assert is_dataclass(position)
    assert isinstance(position, entities.SitePosition)
    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "SitePosition",
            "CentralBody": "Earth",
            "cartographicDegrees": [-155.468, 19.821, 4205.0],
            "clampToGround": False,
            "HeightAboveGround": 10.0,
        },
    )
    assert_canonical_equal(
        position.to_site_wire(),
        {
            "CentralBody": "Earth",
            "cartographicDegrees": [-155.468, 19.821, 4205.0],
            "clampToGround": False,
            "HeightAboveGround": 10.0,
        },
    )

    with pytest.raises(FrozenInstanceError):
        position.height_m = 0.0


def test_site_position_omits_server_owned_defaults() -> None:
    position = entities.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    )

    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "SitePosition",
            "cartographicDegrees": [-155.468, 19.821, 4205.0],
        },
    )


def test_czml_position_lowers_supplied_samples_without_defaults() -> None:
    position = entities.czml_position(
        epoch="2024-01-01T00:00:00.000Z",
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=5,
        cartesian_velocity=[0.0, 7000000.0, 0.0, 0.0, 0.0, 7500.0, 0.0],
    )

    assert isinstance(position, entities.CzmlPosition)
    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "CzmlPosition",
            "epoch": "2024-01-01T00:00:00.000Z",
            "referenceFrame": "INERTIAL",
            "interpolationAlgorithm": "LAGRANGE",
            "interpolationDegree": 5,
            "cartesianVelocity": [0.0, 7000000.0, 0.0, 0.0, 0.0, 7500.0, 0.0],
        },
    )


def test_czml_positions_lowers_composite_samples_without_item_discriminators() -> None:
    first = entities.czml_position(
        epoch="2024-01-01T00:00:00.000Z",
        cartesian=[0.0, 7000000.0, 0.0, 0.0],
    )
    second = entities.czml_position(
        epoch="2024-01-01T00:01:00.000Z",
        cartesian=[60.0, 6990000.0, 1000.0, 0.0],
    )

    position = entities.czml_positions([first, second], central_body="Earth")

    assert isinstance(position, entities.CzmlPositions)
    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "CzmlPositions",
            "CentralBody": "Earth",
            "CzmlPositions": [
                {
                    "epoch": "2024-01-01T00:00:00.000Z",
                    "cartesian": [0.0, 7000000.0, 0.0, 0.0],
                },
                {
                    "epoch": "2024-01-01T00:01:00.000Z",
                    "cartesian": [60.0, 6990000.0, 1000.0, 0.0],
                },
            ],
        },
    )


def test_central_body_position_lowers_named_body() -> None:
    position = entities.central_body_position("Sun")

    assert isinstance(position, entities.CentralBodyPosition)
    assert_canonical_equal(position.to_wire(), {"$type": "CentralBody", "Name": "Sun"})


def test_j2_position_lowers_keplerian_source_and_explicit_options() -> None:
    position = entities.j2_position(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=sample_orbit(),
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        step_s=300.0,
        central_body="Earth",
        gravitational_parameter_m3_s2=398600441500000.0,
        coord_system="Inertial",
        j2_normalized_value=0.000484165143790815,
        ref_distance_m=6378136.3,
    )

    assert isinstance(position, entities.J2Position)
    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "J2",
            "OrbitEpoch": "2024-01-01T00:00:00.000Z",
            "CoordType": "Classical",
            "OrbitalElements": ORBIT_WIRE,
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T00:10:00.000Z",
            "Step": 300.0,
            "CentralBody": "Earth",
            "GravitationalParameter": 398600441500000.0,
            "CoordSystem": "Inertial",
            "J2NormalizedValue": 0.000484165143790815,
            "RefDistance": 6378136.3,
        },
    )


def test_two_body_position_lowers_keplerian_source_without_optional_defaults() -> None:
    position = entities.two_body_position(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=sample_orbit(),
    )

    assert isinstance(position, entities.TwoBodyPosition)
    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "TwoBody",
            "OrbitEpoch": "2024-01-01T00:00:00.000Z",
            "CoordType": "Classical",
            "OrbitalElements": ORBIT_WIRE,
        },
    )


def test_sgp4_position_lowers_tle_lines_and_supplied_options() -> None:
    position = entities.sgp4_position(
        tle_lines=list(TLE_LINES),
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        step_s=300.0,
        satellite_number="25544",
    )

    assert isinstance(position, entities.Sgp4Position)
    assert position.tle_lines == TLE_LINES
    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "SGP4",
            "TLEs": list(TLE_LINES),
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T00:10:00.000Z",
            "Step": 300.0,
            "SatelliteNumber": "25544",
        },
    )


def test_hpop_position_lowers_classical_or_cartesian_source() -> None:
    config = propagator.hpop_config(
        central_body="Earth",
        gravity=propagator.hpop_two_body_gravity(),
    )

    classical = entities.hpop_position(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=sample_orbit(),
        config=config,
        coord_system="GCRF",
        gravitational_parameter_m3_s2=398600441500000.0,
    )
    cartesian = entities.hpop_position(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        state=sample_state(),
    )

    assert isinstance(classical, entities.HpopPosition)
    assert_canonical_equal(
        classical.to_wire(),
        {
            "$type": "HPOP",
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T00:10:00.000Z",
            "OrbitEpoch": "2024-01-01T00:00:00.000Z",
            "CoordType": "Classical",
            "OrbitalElements": ORBIT_WIRE,
            "CoordSystem": "GCRF",
            "GravitationalParameter": 398600441500000.0,
            "HpopPropagator": {
                "CentralBodyName": "Earth",
                "GravityModel": {"$type": "TwoBody"},
            },
        },
    )
    assert_canonical_equal(
        cartesian.to_wire(),
        {
            "$type": "HPOP",
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T00:10:00.000Z",
            "OrbitEpoch": "2024-01-01T00:00:00.000Z",
            "CoordType": "Cartesian",
            "OrbitalElements": [7000000.0, 1000.0, 2000.0, -1.0, 7500.0, 10.0],
        },
    )


def test_simple_ascent_position_lowers_required_inputs_and_supplied_options() -> None:
    position = entities.simple_ascent_position(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:30:00.000Z",
        launch_latitude_deg=40.0,
        launch_longitude_deg=100.0,
        launch_altitude_m=1000.0,
        burnout_velocity_m_s=7800.0,
        burnout_latitude_deg=41.0,
        burnout_longitude_deg=101.0,
        burnout_altitude_m=200000.0,
        step_s=30.0,
        central_body="Earth",
    )

    assert isinstance(position, entities.SimpleAscentPosition)
    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "SimpleAscent",
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T00:30:00.000Z",
            "LaunchLatitude": 40.0,
            "LaunchLongitude": 100.0,
            "LaunchAltitude": 1000.0,
            "BurnoutVelocity": 7800.0,
            "BurnoutLatitude": 41.0,
            "BurnoutLongitude": 101.0,
            "BurnoutAltitude": 200000.0,
            "Step": 30.0,
            "CentralBody": "Earth",
        },
    )


def test_ballistic_position_lowers_branch_inputs_and_supplied_options() -> None:
    position = entities.ballistic_position(
        start="2024-01-01T00:00:00.000Z",
        ballistic_type="DeltaV",
        ballistic_type_value=5000.0,
        step_s=60.0,
        central_body="Earth",
        launch_latitude_deg=40.0,
        launch_longitude_deg=100.0,
        impact_latitude_deg=42.0,
        impact_longitude_deg=102.0,
    )

    assert isinstance(position, entities.BallisticPosition)
    assert_canonical_equal(
        position.to_wire(),
        {
            "$type": "Ballistic",
            "Start": "2024-01-01T00:00:00.000Z",
            "BallisticType": "DeltaV",
            "BallisticTypeValue": 5000.0,
            "Step": 60.0,
            "CentralBody": "Earth",
            "LaunchLatitude": 40.0,
            "LaunchLongitude": 100.0,
            "ImpactLatitude": 42.0,
            "ImpactLongitude": 102.0,
        },
    )


def test_sensor_constructors_lower_discriminated_fragments() -> None:
    assert_canonical_equal(
        entities.conic_sensor(
            inner_half_angle_deg=1.0,
            outer_half_angle_deg=30.0,
            minimum_clock_angle_deg=10.0,
            maximum_clock_angle_deg=350.0,
            text="camera",
        ).to_wire(),
        {
            "$type": "Conic",
            "innerHalfAngle": 1.0,
            "outerHalfAngle": 30.0,
            "minimumClockAngle": 10.0,
            "maximumClockAngle": 350.0,
            "Text": "camera",
        },
    )
    assert_canonical_equal(
        entities.rectangular_sensor(
            x_half_angle_deg=5.0,
            y_half_angle_deg=10.0,
            text="rect-camera",
        ).to_wire(),
        {
            "$type": "Rectangular",
            "xHalfAngle": 5.0,
            "yHalfAngle": 10.0,
            "Text": "rect-camera",
        },
    )


def test_constraint_constructors_lower_discriminated_fragments() -> None:
    assert_canonical_equal(
        entities.elevation_constraint(
            minimum_deg=10.0,
            maximum_deg=80.0,
            maximum_enabled=True,
            text="minimum elevation",
        ).to_wire(),
        {
            "$type": "ElevationAngle",
            "MinimumValue": 10.0,
            "MaximumValue": 80.0,
            "IsMaximumEnabled": True,
            "Text": "minimum elevation",
        },
    )
    assert_canonical_equal(
        entities.range_constraint(
            minimum_km=100.0,
            maximum_km=2500.0,
            maximum_enabled=True,
            text="range gate",
        ).to_wire(),
        {
            "$type": "Range",
            "MinimumValue": 100.0,
            "MaximumValue": 2500.0,
            "IsMaximumEnabled": True,
            "Text": "range gate",
        },
    )
    assert_canonical_equal(
        entities.az_el_mask_constraint(
            az_el_mask_rad=[0.0, 0.1, 1.57079632679, 0.2],
            max_range_km=5000.0,
            text="terrain mask",
        ).to_wire(),
        {
            "$type": "AzElMask",
            "AzElMaskData": [0.0, 0.1, 1.57079632679, 0.2],
            "MaxRange": 5000.0,
            "Text": "terrain mask",
        },
    )


def test_entity_composes_position_and_sensor_metadata() -> None:
    sat = entities.entity(
        name="ISS",
        description="Representative spacecraft",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
        sensor=entities.conic_sensor(outer_half_angle_deg=30.0),
    )

    assert is_dataclass(sat)
    assert isinstance(sat, entities.Entity)
    assert_canonical_equal(
        sat.to_wire(),
        {
            "Name": "ISS",
            "Description": "Representative spacecraft",
            "Position": {
                "$type": "SGP4",
                "TLEs": list(TLE_LINES),
            },
            "Sensor": {
                "$type": "Conic",
                "outerHalfAngle": 30.0,
            },
        },
    )


def test_entity_composes_constraints_metadata() -> None:
    site = entities.entity(
        name="Ground",
        position=entities.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
        constraints=[
            entities.elevation_constraint(minimum_deg=5.0),
            entities.range_constraint(maximum_km=3000.0, maximum_enabled=True),
        ],
    )

    assert site.constraints == (
        entities.elevation_constraint(minimum_deg=5.0),
        entities.range_constraint(maximum_km=3000.0, maximum_enabled=True),
    )
    assert_canonical_equal(
        site.to_wire(),
        {
            "Name": "Ground",
            "Position": {
                "$type": "SitePosition",
                "cartographicDegrees": [-155.468, 19.821, 4205.0],
            },
            "Constraints": [
                {
                    "$type": "ElevationAngle",
                    "MinimumValue": 5.0,
                },
                {
                    "$type": "Range",
                    "MaximumValue": 3000.0,
                    "IsMaximumEnabled": True,
                },
            ],
        },
    )


def test_rotation_fragments_lower_to_inner_orientation_wire_shapes() -> None:
    assert_canonical_equal(
        entities.az_el_rotation(azimuth_deg=10.0, elevation_deg=-20.0).to_wire(),
        {"$type": "AzEl", "Azimuth": 10.0, "Elevation": -20.0},
    )
    assert_canonical_equal(
        entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0).to_wire(),
        {"$type": "Quaternion", "QS": 1.0, "QX": 0.0, "QY": 0.0, "QZ": 0.0},
    )
    assert_canonical_equal(
        entities.euler_rotation(
            sequence="321",
            a_deg=1.0,
            b_deg=2.0,
            c_deg=3.0,
        ).to_wire(),
        {"$type": "EulerAngles", "Sequence": "321", "A": 1.0, "B": 2.0, "C": 3.0},
    )


def test_orbital_axes_lower_generic_and_relative_variants() -> None:
    assert_canonical_equal(
        entities.vvlh_axes(
            name="Body VVLH",
            description="body frame",
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T00:10:00.000Z",
        ).to_wire(),
        {
            "$type": "VVLH",
            "Name": "Body VVLH",
            "Description": "body frame",
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T00:10:00.000Z",
        },
    )
    assert_canonical_equal(
        entities.vvlh_axes(relative_to="Earth").to_wire(),
        {"$type": "VVLH(Earth)"},
    )
    assert_canonical_equal(
        entities.lvlh_axes(relative_to="CBF").to_wire(),
        {"$type": "LVLH(CBF)"},
    )
    assert_canonical_equal(
        entities.vnc_axes(relative_to="Sun").to_wire(),
        {"$type": "VNC(Sun)"},
    )


def test_fixed_and_fixed_at_epoch_axes_lower_named_references() -> None:
    body_axes = entities.vvlh_axes(name="Body VVLH")
    fixed = entities.fixed_axes(
        name="Camera Axes",
        reference_axes=body_axes,
        rotation=entities.euler_rotation(
            sequence="321",
            a_deg=0.0,
            b_deg=20.0,
            c_deg=0.0,
        ),
    )
    frozen = entities.fixed_at_epoch_axes(
        source_axes=fixed,
        reference_axes="ICRF",
        epoch="2024-01-01T00:00:00.000Z",
    )

    assert_canonical_equal(
        fixed.to_wire(),
        {
            "$type": "Fixed",
            "Name": "Camera Axes",
            "ReferenceAxesName": "Body VVLH",
            "FixedOrientation": {
                "$type": "EulerAngles",
                "Sequence": "321",
                "A": 0.0,
                "B": 20.0,
                "C": 0.0,
            },
        },
    )
    assert_canonical_equal(
        frozen.to_wire(),
        {
            "$type": "FixedAtEpoch",
            "SourceAxesName": "Camera Axes",
            "ReferenceAxesName": "ICRF",
            "Epoch": "2024-01-01T00:00:00.000Z",
        },
    )


def test_aligned_composite_and_czml_axes_lower_complete_wire_shapes() -> None:
    body_axes = entities.vvlh_axes(name="Body VVLH")
    boresight = entities.vgt_fixed_vector(
        name="Boresight",
        reference_axes=body_axes,
        direction=entities.xyz_direction(x=0.0, y=0.0, z=1.0),
    )
    sun_hint = entities.vgt_fixed_vector(
        name="Sun Hint",
        reference_axes="Body VVLH",
        direction=entities.ra_dec_direction(
            ra_deg=15.0,
            dec_deg=-5.0,
            magnitude=1.0,
        ),
    )
    aligned = entities.aligned_and_constrained_axes(
        name="Aligned Camera",
        principal=boresight,
        principal_axis="+Z",
        reference=sun_hint,
        reference_axis="+X",
    )
    czml = entities.czml_axes(
        epoch="2024-01-01T00:00:00.000Z",
        unit_quaternion_xyzw=[0.0, 0.0, 0.0, 1.0],
        central_body="Earth",
        interpolation_algorithm="LINEAR",
        interpolation_degree=1,
    )
    composite = entities.composite_axes(intervals=[body_axes, aligned, czml])

    assert_canonical_equal(
        aligned.to_wire(),
        {
            "$type": "AlignedAndConstrained",
            "Name": "Aligned Camera",
            "Principal": "Boresight",
            "PrincipalAxis": "+Z",
            "Reference": "Sun Hint",
            "ReferenceAxis": "+X",
        },
    )
    assert_canonical_equal(
        czml.to_wire(),
        {
            "$type": "CzmlOrientation",
            "epoch": "2024-01-01T00:00:00.000Z",
            "unitQuaternion": [0.0, 0.0, 0.0, 1.0],
            "CentralBody": "Earth",
            "interpolationAlgorithm": "LINEAR",
            "interpolationDegree": 1,
        },
    )
    assert_canonical_equal(
        composite.to_wire(),
        {
            "$type": "Composite",
            "Intervals": [body_axes.to_wire(), aligned.to_wire(), czml.to_wire()],
        },
    )


def test_vgt_provider_lowers_named_geometry_collections() -> None:
    body_axes = entities.vvlh_axes(name="Body VVLH")
    vector = entities.vgt_fixed_vector(
        name="Boresight",
        reference_axes=body_axes,
        direction=entities.xyz_direction(x=0.0, y=0.0, z=1.0),
        description="sensor boresight",
    )
    provider = entities.vgt(
        axes=[body_axes],
        vectors=[vector],
        points=[entities.vgt_point(name="Target Point", description="point")],
        systems=[entities.vgt_system(name="Body System")],
        angles=[
            entities.vgt_angle(
                name="Look Angle",
                from_vector=vector,
                to_vector="Boresight",
            )
        ],
        planes=[entities.vgt_plane(name="Local Plane", plane_type="Fixed")],
    )

    assert_canonical_equal(
        provider.to_wire(),
        {
            "Axes": [{"$type": "VVLH", "Name": "Body VVLH"}],
            "Vectors": [
                {
                    "$type": "FixedInAxes",
                    "Name": "Boresight",
                    "Description": "sensor boresight",
                    "ReferenceAxesName": "Body VVLH",
                    "Direction": {"$type": "XYZ", "X": 0.0, "Y": 0.0, "Z": 1.0},
                }
            ],
            "Points": [{"Name": "Target Point", "Description": "point"}],
            "Systems": [{"Name": "Body System"}],
            "Angles": [
                {
                    "$type": "BetweenVectors",
                    "Name": "Look Angle",
                    "FromVectorName": "Boresight",
                    "ToVectorName": "Boresight",
                }
            ],
            "Planes": [{"Name": "Local Plane", "Type": "Fixed"}],
        },
    )


def test_fixed_sensor_pointing_lowers_rotation_without_requiring_sensor() -> None:
    sat = entities.entity(
        name="Observer",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
        orientation=entities.vvlh_axes(),
        sensor_pointing=entities.fixed_sensor_pointing(
            rotation=entities.az_el_rotation(
                azimuth_deg=0.0,
                elevation_deg=-20.0,
            ),
            text="off-nadir pointing",
        ),
    )

    assert_canonical_equal(
        sat.to_wire(),
        {
            "Name": "Observer",
            "Position": {
                "$type": "SGP4",
                "TLEs": list(TLE_LINES),
            },
            "Orientation": {"$type": "VVLH"},
            "SensorPointing": {
                "$type": "Fixed",
                "Orientation": {
                    "$type": "AzEl",
                    "Azimuth": 0.0,
                    "Elevation": -20.0,
                },
                "Text": "off-nadir pointing",
            },
        },
    )


def test_entity_composes_vgt_orientation_sensor_and_pointing_metadata() -> None:
    body_axes = entities.vvlh_axes(name="Body VVLH")
    camera_axes = entities.fixed_axes(
        name="Camera Axes",
        reference_axes=body_axes,
        rotation=entities.euler_rotation(
            sequence="321",
            a_deg=0.0,
            b_deg=20.0,
            c_deg=0.0,
        ),
    )
    sat = entities.entity(
        name="Observer",
        description="Representative sensor platform",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
        vgt=entities.vgt(axes=[body_axes, camera_axes]),
        orientation=camera_axes,
        sensor=entities.conic_sensor(outer_half_angle_deg=8.0),
        sensor_pointing=entities.fixed_sensor_pointing(
            rotation=entities.quaternion_rotation(
                scalar=1.0,
                x=0.0,
                y=0.0,
                z=0.0,
            ),
        ),
    )

    assert_canonical_equal(
        sat.to_wire(),
        {
            "Name": "Observer",
            "Description": "Representative sensor platform",
            "Vgt": {
                "Axes": [body_axes.to_wire(), camera_axes.to_wire()],
            },
            "Position": {
                "$type": "SGP4",
                "TLEs": list(TLE_LINES),
            },
            "Orientation": camera_axes.to_wire(),
            "Sensor": {
                "$type": "Conic",
                "outerHalfAngle": 8.0,
            },
            "SensorPointing": {
                "$type": "Fixed",
                "Orientation": {
                    "$type": "Quaternion",
                    "QS": 1.0,
                    "QX": 0.0,
                    "QY": 0.0,
                    "QZ": 0.0,
                },
            },
        },
    )


def test_entity_group_lowers_grouped_entities() -> None:
    iss = entities.entity(name="ISS", position=entities.sgp4_position(tle_lines=TLE_LINES))
    hubble = entities.entity(
        name="Hubble",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
    )

    group = entities.entity_group(
        name="Targets",
        members=[iss, hubble],
        from_restriction="AnyOf",
        to_restriction="AtLeastN",
        to_number=2,
    )

    assert is_dataclass(group)
    assert isinstance(group, entities.EntityGroup)
    assert group.members == (iss, hubble)
    assert_canonical_equal(
        group.to_wire(),
        {
            "$type": "EntityPathGroup",
            "Name": "Targets",
            "AssignedObjects": [iss.to_wire(), hubble.to_wire()],
            "FromAccess_Restriction": "AnyOf",
            "ToAccess_Restriction": "AtLeastN",
            "ToAccess_Number": 2,
        },
    )


@pytest.mark.parametrize(
    ("factory", "kwargs", "match"),
    [
        (
            entities.j2_position,
            {"orbit_epoch": "2024-01-01T00:00:00.000Z", "orbit": ORBIT_WIRE},
            "orbit must be a KeplerianElements instance",
        ),
        (
            entities.two_body_position,
            {"orbit_epoch": "2024-01-01T00:00:00.000Z", "orbit": ORBIT_WIRE},
            "orbit must be a KeplerianElements instance",
        ),
        (
            entities.sgp4_position,
            {"tle_lines": ["not enough"]},
            "tle_lines must be a two-item sequence of TLE strings",
        ),
        (
            entities.czml_positions,
            {"positions": [{"epoch": "2024-01-01T00:00:00.000Z"}]},
            "positions must be a sequence of CzmlPosition values",
        ),
        (
            entities.czml_position,
            {"epoch": "2024-01-01T00:00:00.000Z", "cartesian": "1,2,3"},
            "cartesian must be a sequence of numbers",
        ),
        (
            entities.czml_position,
            {"epoch": "2024-01-01T00:00:00.000Z", "cartesian": [0.0, "1.0", 2.0]},
            "cartesian must be a sequence of numbers",
        ),
        (
            entities.czml_position,
            {"epoch": "2024-01-01T00:00:00.000Z", "cartesian_velocity": [0.0, True]},
            "cartesian_velocity must be a sequence of numbers",
        ),
        (
            entities.az_el_rotation,
            {"azimuth_deg": "0", "elevation_deg": 0.0},
            "azimuth_deg must be a number",
        ),
        (
            entities.euler_rotation,
            {"sequence": 321, "a_deg": 0.0, "b_deg": 0.0, "c_deg": 0.0},
            "sequence must be a string",
        ),
        (
            entities.fixed_axes,
            {
                "reference_axes": entities.vvlh_axes(),
                "rotation": entities.euler_rotation(
                    sequence="321",
                    a_deg=0.0,
                    b_deg=0.0,
                    c_deg=0.0,
                ),
            },
            "reference_axes object must have a name",
        ),
        (
            entities.fixed_sensor_pointing,
            {
                "rotation": {
                    "$type": "AzEl",
                    "Azimuth": 0.0,
                    "Elevation": 0.0,
                },
            },
            "rotation must be an astrox.entities rotation value",
        ),
        (
            entities.czml_axes,
            {
                "epoch": "2024-01-01T00:00:00.000Z",
                "unit_quaternion_xyzw": [0.0, "0.0", 0.0, 1.0],
            },
            "unit_quaternion_xyzw must be a sequence of numbers",
        ),
        (
            entities.az_el_mask_constraint,
            {"az_el_mask_rad": [0.0, "0.1"]},
            "az_el_mask_rad must be a sequence of numbers",
        ),
        (
            entities.vgt,
            {"axes": [entities.vgt_point(name="not axes")]},
            "axes contains unsupported item values",
        ),
        (
            entities.entity,
            {"name": "bad", "position": {"$type": "SitePosition"}},
            "position must be an astrox.entities position value",
        ),
        (
            entities.entity,
            {
                "name": "bad",
                "position": entities.sgp4_position(tle_lines=TLE_LINES),
                "orientation": entities.az_el_rotation(
                    azimuth_deg=0.0,
                    elevation_deg=0.0,
                ),
            },
            "orientation must be an astrox.entities axes value",
        ),
        (
            entities.entity,
            {
                "name": "bad",
                "position": entities.sgp4_position(tle_lines=TLE_LINES),
                "constraints": [{"$type": "ElevationAngle"}],
            },
            "constraints contains unsupported item values",
        ),
        (
            entities.entity,
            {
                "name": "bad",
                "position": entities.sgp4_position(tle_lines=TLE_LINES),
                "sensor_pointing": entities.az_el_rotation(
                    azimuth_deg=0.0,
                    elevation_deg=0.0,
                ),
            },
            "sensor_pointing must be an astrox.entities sensor-pointing value",
        ),
        (
            entities.entity_group,
            {"name": "bad", "members": [{"Name": "ISS"}]},
            "members must be a sequence of Entity values",
        ),
    ],
)
def test_constructors_reject_unsupported_shapes(factory: object, kwargs: dict[str, object], match: str) -> None:
    with pytest.raises(TypeError, match=match):
        factory(**kwargs)


def test_entity_group_rejects_unknown_restriction() -> None:
    with pytest.raises(ValueError, match="to_restriction must be one of"):
        entities.entity_group(
            name="bad",
            members=[
                entities.entity(
                    name="ISS",
                    position=entities.sgp4_position(tle_lines=TLE_LINES),
                )
            ],
            to_restriction="AllOf",
        )


def test_axes_reject_unknown_relative_to_variant() -> None:
    with pytest.raises(ValueError, match="relative_to must be one of"):
        entities.vvlh_axes(relative_to="earth")


def test_aligned_axes_reject_unknown_axis_direction() -> None:
    with pytest.raises(ValueError, match="principal_axis must be one of"):
        entities.aligned_and_constrained_axes(
            principal="Boresight",
            principal_axis="X",
            reference="Sun Hint",
            reference_axis="+Z",
        )
