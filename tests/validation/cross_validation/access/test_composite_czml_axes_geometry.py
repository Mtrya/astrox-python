"""Fixed, frozen, composite, and CZML axes cross-validation."""

# Coverage:
#   Branches:
#     - Fixed axes relative to built-in VVLH and LVLH: verified with Euler and quaternion rotations
#     - FixedAtEpoch axes from VVLH into ICRF at start epoch and +60 s: verified against frozen-at-epoch local frame derivations
#     - Composite axes with identity first interval and off-nadir second interval: verified for two switch points against piecewise local FOV intervals
#     - CZML axes sampled identity quaternions over short sample spans: verified against inertial-frame oracle for 30 s and 60 s spans, with and without CentralBody
#     - CZML axes constant, long-span sampled, and non-identity sampled quaternions: unresolved after live probes of constant vs sampled arrays, xyzw/wxyz order, sign, non-identity rotation, interpolation options, CentralBody, and full-span sampling; kept as strict calibration xfail
#   Fields:
#     - Passes.AccessStart/AccessStop: verified for Fixed, FixedAtEpoch, and Composite branches
#     - CZML sampled-identity AccessStart/AccessStop over short spans: verified
#     - CZML constant, long-span, and non-identity semantic fields: unresolved because constant variants fail and other sampled variants return unexplained interval residuals or component/sign behavior
#   Parameters:
#     - reference_axes, FixedOrientation, SourceAxesName, ReferenceAxesName, Epoch, Intervals, Start/Stop: verified for covered Fixed/FixedAtEpoch/Composite branches
#     - unitQuaternion identity samples, interpolationAlgorithm=LINEAR, interpolationDegree=1, CentralBody omission/Earth: verified for short-span CZML sampled identity
#     - unitQuaternion constant arrays, non-identity samples, and longer sampled spans: unresolved after server failures and sampled-array residuals
#   Comparison:
#     - External: independent VVLH frame, Euler rotation, frozen source/reference transform, and piecewise composite interval derivation
#     - Constants: controlled two-body orbit in _orientation.py, COMPOSITE_SWITCH_S=20 s
#     - Tolerances: ORIENTATION_INTERVAL_ABS_S=0.5 s

from __future__ import annotations

import sys

import numpy as np
import pytest

from astrox import entities
from astrox.exceptions import AstroxAPIError
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import CrossValidationError, START, STOP
from tests.validation.cross_validation.access._geometry import compare_intervals
from tests.validation.cross_validation.access._orientation import (
    COMPOSITE_SWITCH_S,
    ORIENTATION_INTERVAL_ABS_S,
    compare_sensor_case,
    composite_frame,
    conic_predicate,
    conic_sensor,
    compute_sensor_access,
    euler_321_rotation,
    expected_site_intervals,
    expected_intervals,
    fixed_frame,
    frozen_at_epoch_frame,
    inertial_frame,
    lvlh_frame,
    observer_with_sensor,
    quaternion_rotation,
    controlled_orbit,
    state_function,
    subpoint_site,
    target_orbit_entity,
    vvlh_frame,
)


def test_fixed_axes_relative_to_vvlh_matches_fixed_rotation_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    rotation = euler_321_rotation(a_deg=0.0, b_deg=-20.0, c_deg=0.0)
    fixed_axes = entities.fixed_axes(
        reference_axes="VVLH",
        rotation=entities.euler_rotation(sequence="321", a_deg=0.0, b_deg=-20.0, c_deg=0.0),
    )
    case = case_for_orientation(
        case_id="fixed_vvlh_euler_b_minus_20",
        orientation=fixed_axes,
        target=target,
        expected=expected_site_intervals(
            site=target,
            frame=fixed_frame(vvlh_frame, rotation),
            sensor_predicate=conic_predicate(8.0, np.array([0.0, 0.0, 1.0])),
        ),
    )
    compare_sensor_case(case)


def test_fixed_axes_relative_to_lvlh_matches_fixed_rotation_oracle() -> None:
    configure_astrox_from_env()
    target = target_orbit_entity(
        name="FixedLvlhPositive",
        semi_major_delta_m=100000.0,
    )
    fixed_axes = entities.fixed_axes(
        reference_axes="LVLH",
        rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
    )
    case = case_for_orientation(
        case_id="fixed_lvlh_identity_positive",
        orientation=fixed_axes,
        target=target,
        rotation=entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=0.0),
        expected=expected_intervals(
            target_state=state_function(
                controlled_orbit(
                    semi_major_delta_m=100000.0,
                )
            ),
            frame=fixed_frame(
                lvlh_frame,
                quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
            ),
            sensor_predicate=conic_predicate(
                8.0,
                np.array([1.0, 0.0, 0.0]),
            ),
        ),
    )
    compare_sensor_case(case)


def test_fixed_at_epoch_axes_match_frozen_vvlh_inertial_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    frozen = entities.fixed_at_epoch_axes(
        source_axes="VVLH",
        reference_axes="ICRF",
        epoch=START,
    )
    case = case_for_orientation(
        case_id="fixed_at_epoch_vvlh_icrf",
        orientation=frozen,
        target=target,
        expected=expected_site_intervals(
            site=target,
            frame=frozen_at_epoch_frame(vvlh_frame, inertial_frame),
            sensor_predicate=conic_predicate(
                8.0,
                quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0)
                @ np.array([0.0, 0.0, 1.0]),
            ),
        ),
    )
    compare_sensor_case(case)


def test_fixed_at_epoch_axes_match_later_epoch_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    frozen = entities.fixed_at_epoch_axes(
        source_axes="VVLH",
        reference_axes="ICRF",
        epoch="2024-01-01T00:01:00.000Z",
    )
    case = case_for_orientation(
        case_id="fixed_at_epoch_vvlh_icrf_plus_60",
        orientation=frozen,
        target=target,
        expected=expected_site_intervals(
            site=target,
            frame=frozen_at_epoch_frame(vvlh_frame, inertial_frame, epoch_s=60.0),
            sensor_predicate=conic_predicate(
                8.0,
                quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0)
                @ np.array([0.0, 0.0, 1.0]),
            ),
        ),
    )
    compare_sensor_case(case)


def test_composite_axes_match_piecewise_interval_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    identity = entities.fixed_axes(
        reference_axes="VVLH",
        rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
        start=START,
        stop="2024-01-01T00:00:20.000Z",
    )
    off_nadir = entities.fixed_axes(
        reference_axes="VVLH",
        rotation=entities.euler_rotation(sequence="321", a_deg=0.0, b_deg=-20.0, c_deg=0.0),
        start="2024-01-01T00:00:20.000Z",
        stop=STOP,
    )
    composite = entities.composite_axes(intervals=[identity, off_nadir])
    frame = composite_frame(
        first=fixed_frame(
            vvlh_frame,
            quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
        ),
        second=fixed_frame(
            vvlh_frame,
            euler_321_rotation(a_deg=0.0, b_deg=-20.0, c_deg=0.0),
        ),
        switch_s=COMPOSITE_SWITCH_S,
    )
    case = case_for_orientation(
        case_id="composite_identity_then_off_nadir",
        orientation=composite,
        target=target,
        expected=expected_site_intervals(
            site=target,
            frame=frame,
            sensor_predicate=conic_predicate(8.0, np.array([0.0, 0.0, 1.0])),
        ),
    )
    compare_sensor_case(case)


def test_composite_axes_match_second_switch_point_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    identity = entities.fixed_axes(
        reference_axes="VVLH",
        rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
        start=START,
        stop="2024-01-01T00:00:30.000Z",
    )
    off_nadir = entities.fixed_axes(
        reference_axes="VVLH",
        rotation=entities.euler_rotation(sequence="321", a_deg=0.0, b_deg=-20.0, c_deg=0.0),
        start="2024-01-01T00:00:30.000Z",
        stop=STOP,
    )
    composite = entities.composite_axes(intervals=[identity, off_nadir])
    frame = composite_frame(
        first=fixed_frame(
            vvlh_frame,
            quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
        ),
        second=fixed_frame(
            vvlh_frame,
            euler_321_rotation(a_deg=0.0, b_deg=-20.0, c_deg=0.0),
        ),
        switch_s=30.0,
    )
    case = case_for_orientation(
        case_id="composite_identity_then_off_nadir_switch_30",
        orientation=composite,
        target=target,
        expected=expected_site_intervals(
            site=target,
            frame=frame,
            sensor_predicate=conic_predicate(8.0, np.array([0.0, 0.0, 1.0])),
        ),
    )
    compare_sensor_case(case)


def test_czml_sampled_identity_short_spans_match_inertial_oracle() -> None:
    configure_astrox_from_env()
    target = target_orbit_entity(
        name="CzmlSampledIdentityPositive",
        inclination_delta_deg=-20.0,
        raan_delta_deg=-60.0,
        true_anomaly_offset_deg=60.0,
    )
    variants = [
        ("czml_identity_span_30_earth", 30.0, "Earth"),
        ("czml_identity_span_60_earth", 60.0, "Earth"),
        ("czml_identity_span_60_no_central_body", 60.0, None),
    ]
    for case_id, span_s, central_body in variants:
        czml = entities.czml_axes(
            epoch=START,
            unit_quaternion_xyzw=[
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                span_s,
                0.0,
                0.0,
                0.0,
                1.0,
            ],
            central_body=central_body,
            interpolation_algorithm="LINEAR",
            interpolation_degree=1,
        )
        case = case_for_orientation(
            case_id=case_id,
            orientation=czml,
            target=target,
            sensor=conic_sensor(20.0),
            rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
            expected=expected_intervals(
                target_state=state_function(
                    controlled_orbit(
                        inclination_delta_deg=-20.0,
                        raan_delta_deg=-60.0,
                        true_anomaly_offset_deg=60.0,
                    )
                ),
                frame=inertial_frame,
                sensor_predicate=conic_predicate(20.0, np.array([0.0, 0.0, 1.0])),
                stop_s=span_s,
            ),
        )
        compare_sensor_case(case)


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "CZML axes remain partially unresolved: constant quaternion variants fail before semantic output, "
        "long-span sampled identity has boundary residuals, and non-identity sampled quaternion "
        "component/sign behavior does not match the local inertial-frame candidate."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_czml_axes_remain_unresolved_after_variant_probe_matrix() -> None:
    configure_astrox_from_env()
    site_target = subpoint_site()
    positive_target = target_orbit_entity(
        name="CzmlUnresolvedPositive",
        inclination_delta_deg=-20.0,
        raan_delta_deg=-60.0,
        true_anomaly_offset_deg=60.0,
    )
    constant_variants = [
        (
            "constant_xyzw_identity_with_central_body",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[0.0, 0.0, 0.0, 1.0],
                central_body="Earth",
            ),
        ),
        (
            "constant_wxyz_identity_probe",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[1.0, 0.0, 0.0, 0.0],
                central_body="Earth",
            ),
        ),
        (
            "constant_xyzw_negative_identity_probe",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[0.0, 0.0, 0.0, -1.0],
                central_body="Earth",
            ),
        ),
        (
            "constant_xyzw_y_minus_20_probe",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[
                    0.0,
                    -0.17364817766693033,
                    0.0,
                    0.984807753012208,
                ],
                central_body="Earth",
            ),
        ),
    ]
    sampled_variants = [
        (
            "sampled_identity_positive_span_600",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[0.0, 0.0, 0.0, 0.0, 1.0, 600.0, 0.0, 0.0, 0.0, 1.0],
                central_body="Earth",
                interpolation_algorithm="LINEAR",
                interpolation_degree=1,
            ),
            inertial_frame,
            600.0,
        ),
        (
            "sampled_identity_positive_span_7200",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    7200.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                ],
                central_body="Earth",
                interpolation_algorithm="LINEAR",
                interpolation_degree=1,
            ),
            inertial_frame,
            7200.0,
        ),
        (
            "sampled_xyzw_y_minus_20_span_60",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[
                    0.0,
                    0.0,
                    -0.17364817766693033,
                    0.0,
                    0.984807753012208,
                    60.0,
                    0.0,
                    -0.17364817766693033,
                    0.0,
                    0.984807753012208,
                ],
                central_body="Earth",
                interpolation_algorithm="LINEAR",
                interpolation_degree=1,
            ),
            fixed_frame(
                inertial_frame,
                quaternion_rotation(
                    scalar=0.984807753012208,
                    x=0.0,
                    y=-0.17364817766693033,
                    z=0.0,
                ),
            ),
            60.0,
        ),
        (
            "sampled_xyzw_x_minus_20_span_60",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[
                    0.0,
                    -0.17364817766693033,
                    0.0,
                    0.0,
                    0.984807753012208,
                    60.0,
                    -0.17364817766693033,
                    0.0,
                    0.0,
                    0.984807753012208,
                ],
                central_body="Earth",
                interpolation_algorithm="LINEAR",
                interpolation_degree=1,
            ),
            fixed_frame(
                inertial_frame,
                quaternion_rotation(
                    scalar=0.984807753012208,
                    x=-0.17364817766693033,
                    y=0.0,
                    z=0.0,
                ),
            ),
            60.0,
        ),
        (
            "sampled_wxyz_order_probe_span_7200",
            entities.czml_axes(
                epoch=START,
                unit_quaternion_xyzw=[
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                    7200.0,
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                central_body="Earth",
                interpolation_algorithm="LINEAR",
                interpolation_degree=1,
            ),
            inertial_frame,
            7200.0,
        ),
    ]
    failures: list[str] = []
    successes: list[str] = []
    for case_id, czml in constant_variants:
        observer = observer_with_sensor(
            name=case_id,
            orientation=czml,
            sensor=conic_sensor(8.0),
            rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
        )
        try:
            actual = compute_sensor_access(observer, site_target)
        except AstroxAPIError as exc:
            failures.append(f"{case_id}: {exc}")
            continue
        successes.append(f"{case_id}: returned intervals {actual}")
    for case_id, czml, frame, stop_s in sampled_variants:
        observer = observer_with_sensor(
            name=case_id,
            orientation=czml,
            sensor=conic_sensor(20.0),
            rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
        )
        actual = compute_sensor_access(observer, positive_target)
        expected = expected_intervals(
            target_state=state_function(
                controlled_orbit(
                    inclination_delta_deg=-20.0,
                    raan_delta_deg=-60.0,
                    true_anomaly_offset_deg=60.0,
                )
            ),
            frame=frame,
            sensor_predicate=conic_predicate(20.0, np.array([0.0, 0.0, 1.0])),
            stop_s=stop_s,
        )
        try:
            compare_intervals(expected, actual, tolerance_s=ORIENTATION_INTERVAL_ABS_S)
        except CrossValidationError as exc:
            failures.append(
                f"{case_id}: expected {expected}, actual {actual}, residual {exc}"
            )
        else:
            successes.append(f"{case_id}: matched local candidate {expected}")
    if successes:
        raise AssertionError(
            "CZML unresolved matrix partially resolved; reclassify successful "
            "cases before keeping this xfail:\n" + "\n".join(successes)
        )
    raise CrossValidationError("CZML axes unresolved after variant probes:\n" + "\n".join(failures))


def case_for_orientation(*, case_id: str, orientation, target, expected, sensor=None, rotation=None):
    sensor = conic_sensor(8.0) if sensor is None else sensor
    return type("Case", (), {
        "id": case_id,
        "observer": observer_with_sensor(
            name=case_id,
            orientation=orientation,
            sensor=sensor,
            rotation=rotation,
        ),
        "target": target,
        "expected": expected,
    })()


def main() -> int:
    try:
        test_fixed_axes_relative_to_vvlh_matches_fixed_rotation_oracle()
        test_fixed_axes_relative_to_lvlh_matches_fixed_rotation_oracle()
        test_fixed_at_epoch_axes_match_frozen_vvlh_inertial_oracle()
        test_fixed_at_epoch_axes_match_later_epoch_oracle()
        test_composite_axes_match_piecewise_interval_oracle()
        test_composite_axes_match_second_switch_point_oracle()
        test_czml_sampled_identity_short_spans_match_inertial_oracle()
    except (CrossValidationError, LiveConfigError, AstroxAPIError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=7")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
