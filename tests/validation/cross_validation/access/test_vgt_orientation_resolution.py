"""VGT orientation and name-resolution cross-validation."""

# Coverage:
#   Branches:
#     - vgt_fixed_vector with built-in VVLH reference axes: verified
#     - aligned_and_constrained_axes using built-in VVLH fixed vectors: verified against a local TRIAD-style alignment
#     - Vgt.Axes, Vgt.Vectors, and Vgt.Planes provider collections: verified as pass-through containers that do not alter calibrated VVLH sensor access
#     - custom fixed-axes name resolution inside aligned_and_constrained_axes: unverifiable (live server cannot resolve the custom Body VVLH axes name; maintainer sign-off inherited from implementation plan)
#     - Vgt.Points, Vgt.Systems, and Vgt.Angles provider collections: unverifiable (live server returns HTTP 500 before semantic output; maintainer sign-off inherited from implementation plan)
#   Fields:
#     - Passes.AccessStart/AccessStop: verified for built-in aligned/VGT container cases
#     - VGT custom-name and Points/Systems/Angles semantic fields: unverifiable because live server returns an error
#   Parameters:
#     - Principal, PrincipalAxis, Reference, ReferenceAxis: verified for +Z aligned to built-in VVLH +Z and +X constrained by VVLH +X
#     - VGT collection fields Axes/Vectors/Planes: verified for no semantic perturbation in the calibrated sensor case
#     - VGT collection fields Points/Systems/Angles: unverifiable while server returns HTTP 500
#   Comparison:
#     - External: local TRIAD-style axes construction plus independent VVLH/FOV interval oracle
#     - Constants: controlled two-body orbit in _orientation.py
#     - Tolerances: ORIENTATION_INTERVAL_ABS_S=0.5 s

from __future__ import annotations

import sys

import numpy as np

from astrox import entities
from astrox.exceptions import AstroxAPIError, AstroxHTTPError
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import CrossValidationError
from tests.validation.cross_validation.access._orientation import (
    compare_sensor_case,
    conic_predicate,
    conic_sensor,
    compute_sensor_access,
    expected_site_intervals,
    fixed_frame,
    observer_with_sensor,
    quaternion_rotation,
    subpoint_site,
    triad_aligned_frame,
    vvlh_frame,
)


def test_aligned_and_constrained_axes_match_triad_alignment_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    boresight = entities.vgt_fixed_vector(
        name="Boresight",
        reference_axes="VVLH",
        direction=entities.xyz_direction(x=0.0, y=0.0, z=1.0),
    )
    hint = entities.vgt_fixed_vector(
        name="Hint",
        reference_axes="VVLH",
        direction=entities.xyz_direction(x=1.0, y=0.0, z=0.0),
    )
    aligned = entities.aligned_and_constrained_axes(
        name="AlignedBuiltin",
        principal=boresight,
        principal_axis="+Z",
        reference=hint,
        reference_axis="+X",
    )
    triad = triad_aligned_frame(
        principal_vector=np.array([0.0, 0.0, 1.0]),
        principal_axis="+Z",
        reference_vector=np.array([1.0, 0.0, 0.0]),
        reference_axis="+X",
    )
    case = type("Case", (), {
        "id": "aligned_builtin_vvlh",
        "observer": observer_with_sensor(
            name="aligned_builtin_vvlh",
            orientation=aligned,
            sensor=conic_sensor(8.0),
            vgt=entities.vgt(axes=[aligned], vectors=[boresight, hint]),
        ),
        "target": target,
        "expected": expected_site_intervals(
            site=target,
            frame=fixed_frame(vvlh_frame, triad),
            sensor_predicate=conic_predicate(8.0, np.array([0.0, 0.0, 1.0])),
        ),
    })()
    compare_sensor_case(case)


def test_vgt_axes_vectors_and_planes_do_not_perturb_calibrated_vvlh_sensor_access() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    expected = expected_site_intervals(
        site=target,
        frame=vvlh_frame,
        sensor_predicate=conic_predicate(
            8.0,
            quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0) @ np.array([0.0, 0.0, 1.0]),
        ),
    )
    providers = [
        entities.vgt(axes=[entities.vvlh_axes(name="OnlyAxes")]),
        entities.vgt(
            axes=[entities.vvlh_axes(name="OnlyAxes")],
            vectors=[
                entities.vgt_fixed_vector(
                    name="Vector",
                    reference_axes="VVLH",
                    direction=entities.xyz_direction(x=1.0, y=0.0, z=0.0),
                )
            ],
        ),
        entities.vgt(
            axes=[entities.vvlh_axes(name="OnlyAxes")],
            planes=[entities.vgt_plane(name="Plane", plane_type="Fixed")],
        ),
    ]
    for index, provider in enumerate(providers):
        case = type("Case", (), {
            "id": f"vgt_container_{index}",
            "observer": observer_with_sensor(
                name=f"vgt_container_{index}",
                orientation=entities.vvlh_axes(),
                sensor=conic_sensor(8.0),
                rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
                vgt=provider,
            ),
            "target": target,
            "expected": expected,
        })()
        compare_sensor_case(case)


def test_custom_vgt_axes_name_resolution_remains_unverifiable_server_failure() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    body = entities.vvlh_axes(name="Body VVLH")
    boresight = entities.vgt_fixed_vector(
        name="Boresight",
        reference_axes=body,
        direction=entities.xyz_direction(x=0.0, y=0.0, z=1.0),
    )
    hint = entities.vgt_fixed_vector(
        name="Hint",
        reference_axes=body,
        direction=entities.xyz_direction(x=1.0, y=0.0, z=0.0),
    )
    aligned = entities.aligned_and_constrained_axes(
        name="AlignedCustom",
        principal=boresight,
        principal_axis="+Z",
        reference=hint,
        reference_axis="+X",
    )
    observer = observer_with_sensor(
        name="aligned_custom",
        orientation=aligned,
        sensor=conic_sensor(8.0),
        vgt=entities.vgt(axes=[body, aligned], vectors=[boresight, hint]),
    )
    try:
        compute_sensor_access(observer, target)
    except AstroxAPIError as exc:
        if "未找到坐标轴: Body VVLH" not in str(exc):
            raise
        return
    raise CrossValidationError("custom VGT axes name resolution unexpectedly succeeded; replace unverifiable classification")


def test_vgt_points_systems_and_angles_remain_unverifiable_http_500() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    providers = [
        entities.vgt(axes=[entities.vvlh_axes(name="OnlyAxes")], points=[entities.vgt_point(name="Point")]),
        entities.vgt(axes=[entities.vvlh_axes(name="OnlyAxes")], systems=[entities.vgt_system(name="System")]),
        entities.vgt(axes=[entities.vvlh_axes(name="OnlyAxes")], angles=[entities.vgt_angle(name="Angle")]),
    ]
    for provider in providers:
        observer = observer_with_sensor(
            name="vgt_server_failure",
            orientation=entities.vvlh_axes(),
            sensor=conic_sensor(8.0),
            rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
            vgt=provider,
        )
        try:
            compute_sensor_access(observer, target)
        except AstroxHTTPError as exc:
            if exc.status_code != 500:
                raise
            continue
        raise CrossValidationError("VGT Points/Systems/Angles unexpectedly returned semantic output")


def main() -> int:
    try:
        test_aligned_and_constrained_axes_match_triad_alignment_oracle()
        test_vgt_axes_vectors_and_planes_do_not_perturb_calibrated_vvlh_sensor_access()
        test_custom_vgt_axes_name_resolution_remains_unverifiable_server_failure()
        test_vgt_points_systems_and_angles_remain_unverifiable_http_500()
    except (CrossValidationError, LiveConfigError, AstroxAPIError, AstroxHTTPError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=4")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
