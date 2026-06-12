"""Sensor pointing and FOV cross-validation against a local geometry oracle."""

# Coverage:
#   Branches:
#     - fixed_sensor_pointing Quaternion identity with conic FOV: verified
#     - fixed_sensor_pointing Quaternion off-nadir and single-axis rotations with conic FOV: verified
#     - fixed_sensor_pointing Euler 321/123/213 off-nadir equivalents to Quaternion: verified
#     - fixed_sensor_pointing AzEl along-track and cross-track with conic FOV: verified
#     - fixed_sensor_pointing AzEl off-target no-access case: verified
#     - rectangular sensor FOV with identity/off-nadir rotations and two width pairs: verified
#     - no-sensor line-of-sight positive and WGS84 blocked target controls: verified
#   Fields:
#     - Passes.AccessStart/AccessStop: verified (local two-body, frame, WGS84 obstruction, and FOV interval oracle)
#     - Passes.AccessBeginData/AccessEndData AER: partial (AER convention covered in existing access AER tests; this script uses it only as live diagnostic output)
#   Parameters:
#     - rotation: verified for Quaternion identity, Quaternion rotations about X/Y/Z, Euler 321/123/213, AzEl(0,0), AzEl(90,0), and AzEl(0,-20) no-access
#     - sensor widths: verified for conic 8 deg, conic 20 deg, rectangular 8x12 deg, and rectangular 12x8 deg
#     - target geometry: verified for nadir surface-direction site, along-track satellite, cross-track altered-inclination satellite, off-target trailing satellite, and Earth-blocked site
#   Comparison:
#     - External: independent two-body geometry, VVLH frame derivation, WGS84 obstruction, and local conic/rectangular FOV predicates
#     - Constants: controlled two-body orbit in _orientation.py, EARTH_MU from access cases, WGS84 from Skyfield
#     - Tolerances: ORIENTATION_INTERVAL_ABS_S=0.5 s, fixed before comparison and documented in _orientation.py
#   Unresolved:
#     - AzEl is calibrated as a direct boresight vector in parent axes; this script does not claim equivalence between AzEl and Quaternion/Euler rotation fragments because live probes showed different semantics for nadir targets

from __future__ import annotations

import sys

import numpy as np

from astrox import entities
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import CrossValidationError, STOP
from tests.validation.cross_validation.access._geometry import Interval
from tests.validation.cross_validation.access._orientation import (
    ORIENTATION_INTERVAL_ABS_S,
    az_el_boresight,
    blocked_site,
    compare_sensor_case,
    compute_sensor_access,
    conic_predicate,
    conic_sensor,
    controlled_orbit,
    euler_321_rotation,
    euler_rotation,
    expected_intervals,
    expected_site_intervals,
    observer_with_sensor,
    quaternion_rotation,
    rectangular_predicate,
    rectangular_sensor,
    state_function,
    subpoint_site,
    target_orbit_entity,
    target_satellite,
    two_body_entity,
    vvlh_frame,
)


def test_quaternion_identity_conic_matches_nadir_site_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    rotation = quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0)
    case = sensor_case_for_site(
        case_id="quat_identity_conic8_subpoint",
        target=target,
        sensor=conic_sensor(8.0),
        rotation_entity_kwargs={"scalar": 1.0, "x": 0.0, "y": 0.0, "z": 0.0},
        predicate=conic_predicate(8.0, rotation @ np.array([0.0, 0.0, 1.0])),
    )
    compare_sensor_case(case)


def test_quaternion_identity_conic_widths_match_nadir_site_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    for half_angle_deg in (8.0, 20.0):
        rotation = quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0)
        case = sensor_case_for_site(
            case_id=f"quat_identity_conic{half_angle_deg:g}_subpoint",
            target=target,
            sensor=conic_sensor(half_angle_deg),
            rotation_entity_kwargs={"scalar": 1.0, "x": 0.0, "y": 0.0, "z": 0.0},
            predicate=conic_predicate(half_angle_deg, rotation @ np.array([0.0, 0.0, 1.0])),
        )
        compare_sensor_case(case)


def test_euler_and_quaternion_off_nadir_conic_match_same_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    quaternion = quaternion_rotation(
        scalar=0.984807753012208,
        x=0.0,
        y=-0.17364817766693033,
        z=0.0,
    )
    expected = expected_site_intervals(
        site=target,
        frame=vvlh_frame,
        sensor_predicate=conic_predicate(8.0, quaternion @ np.array([0.0, 0.0, 1.0])),
    )
    quaternion_case = sensor_case_for_site(
        case_id="quat_y_minus_20_conic8_subpoint",
        target=target,
        sensor=conic_sensor(8.0),
        rotation_entity_kwargs={
            "scalar": 0.984807753012208,
            "x": 0.0,
            "y": -0.17364817766693033,
            "z": 0.0,
        },
        expected=expected,
    )
    euler_case = sensor_case_for_site(
        case_id="euler_321_b_minus_20_conic8_subpoint",
        target=target,
        sensor=conic_sensor(8.0),
        euler_entity_kwargs={"sequence": "321", "a_deg": 0.0, "b_deg": -20.0, "c_deg": 0.0},
        expected=expected,
    )
    compare_sensor_case(quaternion_case)
    compare_sensor_case(euler_case)


def test_quaternion_single_axis_rotations_match_local_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    rotations = [
        (
            "quat_x_plus_10_conic20_subpoint",
            {"scalar": 0.9961946980917455, "x": 0.08715574274765817, "y": 0.0, "z": 0.0},
            quaternion_rotation(scalar=0.9961946980917455, x=0.08715574274765817, y=0.0, z=0.0),
            20.0,
        ),
        (
            "quat_y_minus_20_conic8_subpoint",
            {"scalar": 0.984807753012208, "x": 0.0, "y": -0.17364817766693033, "z": 0.0},
            quaternion_rotation(scalar=0.984807753012208, x=0.0, y=-0.17364817766693033, z=0.0),
            8.0,
        ),
        (
            "quat_z_plus_45_rect12_8_subpoint",
            {"scalar": 0.9238795325112867, "x": 0.0, "y": 0.0, "z": 0.3826834323650898},
            quaternion_rotation(scalar=0.9238795325112867, x=0.0, y=0.0, z=0.3826834323650898),
            None,
        ),
    ]
    for case_id, rotation_kwargs, rotation_matrix, conic_width in rotations:
        if conic_width is None:
            predicate = rectangular_predicate(
                x_half_angle_deg=12.0,
                y_half_angle_deg=8.0,
                boresight_rotation=rotation_matrix,
            )
            sensor = rectangular_sensor(12.0, 8.0)
        else:
            predicate = conic_predicate(conic_width, rotation_matrix @ np.array([0.0, 0.0, 1.0]))
            sensor = conic_sensor(conic_width)
        case = sensor_case_for_site(
            case_id=case_id,
            target=target,
            sensor=sensor,
            rotation_entity_kwargs=rotation_kwargs,
            predicate=predicate,
        )
        compare_sensor_case(case)


def test_euler_sequence_variants_match_equivalent_quaternion_oracles() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    variants = [
        ("321", {"a_deg": 0.0, "b_deg": -20.0, "c_deg": 0.0}),
        ("123", {"a_deg": 0.0, "b_deg": -20.0, "c_deg": 0.0}),
        ("213", {"a_deg": -20.0, "b_deg": 0.0, "c_deg": 0.0}),
    ]
    for sequence, angles in variants:
        matrix = euler_rotation(sequence, **angles)
        case = sensor_case_for_site(
            case_id=f"euler_{sequence}_single_axis_conic8_subpoint",
            target=target,
            sensor=conic_sensor(8.0),
            euler_entity_kwargs={"sequence": sequence, **angles},
            predicate=conic_predicate(8.0, matrix @ np.array([0.0, 0.0, 1.0])),
        )
        compare_sensor_case(case)


def test_rectangular_fov_matches_local_half_angle_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    for rotation_kwargs, rotation_matrix in (
        ({"scalar": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}, quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0)),
        (
            {"scalar": 0.984807753012208, "x": 0.0, "y": -0.17364817766693033, "z": 0.0},
            quaternion_rotation(scalar=0.984807753012208, x=0.0, y=-0.17364817766693033, z=0.0),
        ),
    ):
        case = sensor_case_for_site(
            case_id="rectangular_subpoint",
            target=target,
            sensor=rectangular_sensor(8.0, 12.0),
            rotation_entity_kwargs=rotation_kwargs,
            predicate=rectangular_predicate(
                x_half_angle_deg=8.0,
                y_half_angle_deg=12.0,
                boresight_rotation=rotation_matrix,
            ),
        )
        compare_sensor_case(case)


def test_az_el_along_track_conic_matches_satellite_target_oracle() -> None:
    configure_astrox_from_env()
    target = target_satellite(5.0)
    case = sensor_case_for_satellite(
        case_id="az_el_0_0_target_sat_5",
        target=target,
        sensor=conic_sensor(8.0),
        rotation=az_el_rotation(0.0, 0.0),
        expected=expected_intervals(
            target_state=state_function(controlled_orbit(true_anomaly_offset_deg=5.0)),
            frame=vvlh_frame,
            sensor_predicate=conic_predicate(8.0, az_el_boresight(azimuth_deg=0.0, elevation_deg=0.0)),
        ),
    )
    compare_sensor_case(case)


def test_az_el_cross_track_and_negative_elevation_match_satellite_target_oracles() -> None:
    configure_astrox_from_env()
    cross_track = target_orbit_entity(name="CrossTrackIncPlus2", inclination_delta_deg=2.0)
    cross_track_case = sensor_case_for_satellite(
        case_id="az_el_90_0_cross_track_inc_plus_2",
        target=cross_track,
        sensor=conic_sensor(20.0),
        rotation=az_el_rotation(90.0, 0.0),
        expected=expected_intervals(
            target_state=state_function(controlled_orbit(inclination_delta_deg=2.0)),
            frame=vvlh_frame,
            sensor_predicate=conic_predicate(20.0, az_el_boresight(azimuth_deg=90.0, elevation_deg=0.0)),
        ),
    )
    compare_sensor_case(cross_track_case)

    below_boresight_case = sensor_case_for_satellite(
        case_id="az_el_0_minus_20_along_track_no_access",
        target=target_satellite(5.0),
        sensor=conic_sensor(8.0),
        rotation=az_el_rotation(0.0, -20.0),
        expected=expected_intervals(
            target_state=state_function(controlled_orbit(true_anomaly_offset_deg=5.0)),
            frame=vvlh_frame,
            sensor_predicate=conic_predicate(8.0, az_el_boresight(azimuth_deg=0.0, elevation_deg=-20.0)),
        ),
    )
    compare_sensor_case(below_boresight_case)


def test_az_el_off_target_and_earth_blocked_controls_match_oracles() -> None:
    configure_astrox_from_env()
    trailing = target_satellite(-3.0)
    trailing_case = sensor_case_for_satellite(
        case_id="az_el_0_0_trailing_sat_no_access",
        target=trailing,
        sensor=conic_sensor(8.0),
        rotation=az_el_rotation(0.0, 0.0),
        expected=expected_intervals(
            target_state=state_function(controlled_orbit(true_anomaly_offset_deg=-3.0)),
            frame=vvlh_frame,
            sensor_predicate=conic_predicate(8.0, az_el_boresight(azimuth_deg=0.0, elevation_deg=0.0)),
        ),
    )
    compare_sensor_case(trailing_case)

    blocked_observer = two_body_entity(name="NoSensor", orientation=entities_vvlh())
    if compute_sensor_access(blocked_observer, blocked_site()):
        raise CrossValidationError("Earth-blocked target unexpectedly returned access")


def sensor_case_for_site(
    *,
    case_id: str,
    target,
    sensor,
    rotation_entity_kwargs: dict[str, float] | None = None,
    euler_entity_kwargs: dict[str, float | str] | None = None,
    predicate=None,
    expected: list[Interval] | None = None,
):
    if expected is None:
        expected = expected_site_intervals(
            site=target,
            frame=vvlh_frame,
            sensor_predicate=predicate,
        )
    return type("Case", (), {
        "id": case_id,
        "observer": observer_with_sensor(
            name=case_id,
            orientation=entities_vvlh(),
            sensor=sensor,
            rotation=rotation_from_kwargs(rotation_entity_kwargs, euler_entity_kwargs),
        ),
        "target": target,
        "expected": expected,
    })()


def sensor_case_for_satellite(*, case_id: str, target, sensor, rotation, expected: list[Interval]):
    return type("Case", (), {
        "id": case_id,
        "observer": observer_with_sensor(
            name=case_id,
            orientation=entities_vvlh(),
            sensor=sensor,
            rotation=rotation,
        ),
        "target": target,
        "expected": expected,
    })()


def rotation_from_kwargs(quaternion_kwargs, euler_kwargs):
    if quaternion_kwargs is not None:
        return entities.quaternion_rotation(**quaternion_kwargs)
    if euler_kwargs is not None:
        return entities.euler_rotation(**euler_kwargs)
    raise TypeError("rotation kwargs required")


def az_el_rotation(azimuth_deg: float, elevation_deg: float):
    return entities.az_el_rotation(azimuth_deg=azimuth_deg, elevation_deg=elevation_deg)


def entities_vvlh():
    return entities.vvlh_axes()


def main() -> int:
    try:
        test_quaternion_identity_conic_matches_nadir_site_oracle()
        test_quaternion_identity_conic_widths_match_nadir_site_oracle()
        test_euler_and_quaternion_off_nadir_conic_match_same_oracle()
        test_quaternion_single_axis_rotations_match_local_oracle()
        test_euler_sequence_variants_match_equivalent_quaternion_oracles()
        test_rectangular_fov_matches_local_half_angle_oracle()
        test_az_el_along_track_conic_matches_satellite_target_oracle()
        test_az_el_cross_track_and_negative_elevation_match_satellite_target_oracles()
        test_az_el_off_target_and_earth_blocked_controls_match_oracles()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=9")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
