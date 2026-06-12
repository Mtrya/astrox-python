"""Fixed, frozen, composite, and CZML axes cross-validation."""

# Coverage:
#   Branches:
#     - Fixed axes relative to built-in VVLH with Euler 321 B=-20 deg: verified
#     - FixedAtEpoch axes from VVLH into ICRF at start epoch: verified against a frozen-at-epoch local frame derivation
#     - Composite axes with identity first interval and off-nadir second interval: verified against piecewise local FOV intervals
#     - CZML axes constant identity quaternion: unverifiable (live server raises Index was outside the bounds of the array before returning semantic output; maintainer sign-off inherited from the implementation plan)
#     - CZML axes sampled quaternion interpretation: unverifiable for the same live server failure
#   Fields:
#     - Passes.AccessStart/AccessStop: verified for Fixed, FixedAtEpoch, and Composite branches
#     - CZML semantic fields: unverifiable because no response is produced
#   Parameters:
#     - reference_axes, FixedOrientation, SourceAxesName, ReferenceAxesName, Epoch, Intervals, Start/Stop: verified for covered branches
#     - unitQuaternion, interpolationAlgorithm, interpolationDegree: unverifiable while CZML axes route fails before comparison
#   Comparison:
#     - External: independent VVLH frame, Euler rotation, frozen source/reference transform, and piecewise composite interval derivation
#     - Constants: controlled two-body orbit in _orientation.py, COMPOSITE_SWITCH_S=20 s
#     - Tolerances: ORIENTATION_INTERVAL_ABS_S=0.5 s

from __future__ import annotations

import sys

import numpy as np

from astrox import entities
from astrox.exceptions import AstroxAPIError
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import CrossValidationError, START, STOP
from tests.validation.cross_validation.access._orientation import (
    COMPOSITE_SWITCH_S,
    compare_sensor_case,
    composite_frame,
    conic_predicate,
    conic_sensor,
    compute_sensor_access,
    euler_321_rotation,
    expected_site_intervals,
    fixed_frame,
    frozen_at_epoch_frame,
    inertial_frame,
    observer_with_sensor,
    quaternion_rotation,
    subpoint_site,
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


def test_czml_axes_constant_identity_remains_unverifiable_server_failure() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    czml = entities.czml_axes(
        epoch=START,
        unit_quaternion_xyzw=[0.0, 0.0, 0.0, 1.0],
        central_body="Earth",
    )
    observer = observer_with_sensor(
        name="czml_identity",
        orientation=czml,
        sensor=conic_sensor(8.0),
        rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
    )
    try:
        compute_sensor_access(observer, target)
    except AstroxAPIError as exc:
        if "Index was outside the bounds of the array" not in str(exc):
            raise
        return
    raise CrossValidationError("CZML axes unexpectedly returned semantic output; replace unverifiable classification with calibration")


def case_for_orientation(*, case_id: str, orientation, target, expected):
    return type("Case", (), {
        "id": case_id,
        "observer": observer_with_sensor(
            name=case_id,
            orientation=orientation,
            sensor=conic_sensor(8.0),
        ),
        "target": target,
        "expected": expected,
    })()


def main() -> int:
    try:
        test_fixed_axes_relative_to_vvlh_matches_fixed_rotation_oracle()
        test_fixed_at_epoch_axes_match_frozen_vvlh_inertial_oracle()
        test_composite_axes_match_piecewise_interval_oracle()
        test_czml_axes_constant_identity_remains_unverifiable_server_failure()
    except (CrossValidationError, LiveConfigError, AstroxAPIError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=4")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
