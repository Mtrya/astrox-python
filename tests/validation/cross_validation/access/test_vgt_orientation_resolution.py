"""VGT orientation and name-resolution cross-validation."""

# Coverage:
#   Branches:
#     - vgt_fixed_vector with built-in VVLH reference axes: verified
#     - aligned_and_constrained_axes using built-in VVLH fixed vectors: verified against local TRIAD-style alignment for orthogonal, permuted-axis, and non-orthogonal-reference cases
#     - Vgt.Axes, Vgt.Vectors, Vgt.Angles, Vgt.Planes, and empty Vgt.Points/Systems provider collections: verified as pass-through containers that do not alter calibrated VVLH sensor access
#     - custom fixed-axes name resolution inside aligned_and_constrained_axes: verified against the same TRIAD oracle for no-space object and string reference styles
#     - custom fixed-axes names containing spaces inside aligned_and_constrained_axes: unresolved; object and string reference styles both report the named axes cannot be found
#     - non-empty Vgt.Points and Vgt.Systems provider collections: unresolved after SDK-callable name-only/description/combined provider probes and raw discriminator/default-name probes return HTTP 500 before semantic output
#   Fields:
#     - Passes.AccessStart/AccessStop: verified for built-in aligned/VGT container cases
#     - VGT custom-name semantic fields: verified for no-space names through AccessStart/AccessStop comparison; unresolved for names containing spaces
#     - VGT non-empty Points/Systems semantic fields: unresolved because live server returns errors before semantic output
#   Parameters:
#     - Principal, PrincipalAxis, Reference, ReferenceAxis: verified for +Z/+X, +X/+Y, and -Z/+X axis combinations, including a non-orthogonal reference-vector projection
#     - VGT collection fields Axes/Vectors/Angles/Planes and empty Points/Systems: verified for no semantic perturbation in the calibrated sensor case
#     - VGT custom axes name/reference fields: verified for no-space EntityAxes object references and string name references
#     - VGT non-empty collection fields Points/Systems: unresolved while server returns HTTP 500
#   Comparison:
#     - External: local TRIAD-style axes construction plus independent VVLH/FOV interval oracle
#     - Constants: controlled two-body orbit in _orientation.py
#     - Tolerances: ORIENTATION_INTERVAL_ABS_S=0.5 s

from __future__ import annotations

import sys

import numpy as np
import pytest

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


def test_aligned_axes_axis_permutations_match_triad_alignment_oracles() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    variants = [
        (
            "aligned_builtin_plus_x_plus_y",
            np.array([0.0, 0.0, 1.0]),
            "+X",
            np.array([1.0, 0.0, 0.0]),
            "+Y",
        ),
        (
            "aligned_builtin_minus_z_plus_x_nonorthogonal",
            np.array([0.0, 0.0, 1.0]),
            "-Z",
            np.array([1.0, 0.0, 0.5]),
            "+X",
        ),
    ]
    for case_id, principal_vector, principal_axis, reference_vector, reference_axis in variants:
        boresight = entities.vgt_fixed_vector(
            name=f"{case_id}_principal",
            reference_axes="VVLH",
            direction=entities.xyz_direction(
                x=float(principal_vector[0]),
                y=float(principal_vector[1]),
                z=float(principal_vector[2]),
            ),
        )
        hint = entities.vgt_fixed_vector(
            name=f"{case_id}_reference",
            reference_axes="VVLH",
            direction=entities.xyz_direction(
                x=float(reference_vector[0]),
                y=float(reference_vector[1]),
                z=float(reference_vector[2]),
            ),
        )
        aligned = entities.aligned_and_constrained_axes(
            name=f"{case_id}_axes",
            principal=boresight,
            principal_axis=principal_axis,
            reference=hint,
            reference_axis=reference_axis,
        )
        triad = triad_aligned_frame(
            principal_vector=principal_vector,
            principal_axis=principal_axis,
            reference_vector=reference_vector,
            reference_axis=reference_axis,
        )
        case = type("Case", (), {
            "id": case_id,
            "observer": observer_with_sensor(
                name=case_id,
                orientation=aligned,
                sensor=conic_sensor(20.0),
                vgt=entities.vgt(axes=[aligned], vectors=[boresight, hint]),
            ),
            "target": target,
            "expected": expected_site_intervals(
                site=target,
                frame=fixed_frame(vvlh_frame, triad),
                sensor_predicate=conic_predicate(20.0, np.array([0.0, 0.0, 1.0])),
            ),
        })()
        compare_sensor_case(case)


def test_vgt_provider_collections_do_not_perturb_calibrated_vvlh_sensor_access_when_live_callable() -> None:
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
    angle_from = entities.vgt_fixed_vector(
        name="AngleFrom",
        reference_axes="VVLH",
        direction=entities.xyz_direction(x=0.0, y=0.0, z=1.0),
    )
    angle_to = entities.vgt_fixed_vector(
        name="AngleTo",
        reference_axes="VVLH",
        direction=entities.xyz_direction(x=1.0, y=0.0, z=0.0),
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
            vectors=[angle_from, angle_to],
            angles=[
                entities.vgt_angle(
                    name="Angle",
                    from_vector=angle_from,
                    to_vector="AngleTo",
                )
            ],
        ),
        entities.vgt(
            axes=[entities.vvlh_axes(name="OnlyAxes")],
            planes=[entities.vgt_plane(name="Plane", plane_type="Fixed")],
        ),
        entities.vgt(
            axes=[entities.vvlh_axes(name="OnlyAxes")],
            points=[],
        ),
        entities.vgt(
            axes=[entities.vvlh_axes(name="OnlyAxes")],
            systems=[],
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


def test_custom_vgt_axes_name_resolution_matches_triad_oracle() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    for axes_name, reference_kind in (
        ("BodyFixedObject", "object"),
        ("BodyFixedString", "string"),
    ):
        body = entities.vvlh_axes(name=axes_name)
        reference_value = body if reference_kind == "object" else axes_name
        boresight = entities.vgt_fixed_vector(
            name=f"{axes_name} Boresight",
            reference_axes=reference_value,
            direction=entities.xyz_direction(x=0.0, y=0.0, z=1.0),
        )
        hint = entities.vgt_fixed_vector(
            name=f"{axes_name} Hint",
            reference_axes=reference_value,
            direction=entities.xyz_direction(x=1.0, y=0.0, z=0.0),
        )
        aligned = entities.aligned_and_constrained_axes(
            name=f"{axes_name} Aligned",
            principal=boresight,
            principal_axis="+Z",
            reference=hint,
            reference_axis="+X",
        )
        observer = observer_with_sensor(
            name=f"aligned_custom_{axes_name}",
            orientation=aligned,
            sensor=conic_sensor(8.0),
            vgt=entities.vgt(axes=[body, aligned], vectors=[boresight, hint]),
        )
        triad = triad_aligned_frame(
            principal_vector=np.array([0.0, 0.0, 1.0]),
            principal_axis="+Z",
            reference_vector=np.array([1.0, 0.0, 0.0]),
            reference_axis="+X",
        )
        case = type("Case", (), {
            "id": f"aligned_custom_{axes_name}",
            "observer": observer,
            "target": target,
            "expected": expected_site_intervals(
                site=target,
                frame=fixed_frame(vvlh_frame, triad),
                sensor_predicate=conic_predicate(8.0, np.array([0.0, 0.0, 1.0])),
            ),
        })()
        compare_sensor_case(case)


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "custom VGT axes names containing spaces remain unresolved: object and "
        "string reference styles both report the named axes cannot be found "
        "before semantic output."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_custom_vgt_axes_name_with_space_remains_unresolved() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    failures: list[str] = []
    successes: list[str] = []
    for reference_kind in ("object", "string"):
        body = entities.vvlh_axes(name="Body VVLH")
        reference_value = body if reference_kind == "object" else "Body VVLH"
        boresight = entities.vgt_fixed_vector(
            name=f"Body VVLH {reference_kind} Boresight",
            reference_axes=reference_value,
            direction=entities.xyz_direction(x=0.0, y=0.0, z=1.0),
        )
        hint = entities.vgt_fixed_vector(
            name=f"Body VVLH {reference_kind} Hint",
            reference_axes=reference_value,
            direction=entities.xyz_direction(x=1.0, y=0.0, z=0.0),
        )
        aligned = entities.aligned_and_constrained_axes(
            name=f"Body VVLH {reference_kind} Aligned",
            principal=boresight,
            principal_axis="+Z",
            reference=hint,
            reference_axis="+X",
        )
        observer = observer_with_sensor(
            name=f"aligned_custom_space_name_{reference_kind}",
            orientation=aligned,
            sensor=conic_sensor(8.0),
            vgt=entities.vgt(axes=[body, aligned], vectors=[boresight, hint]),
        )
        try:
            compute_sensor_access(observer, target)
        except AstroxAPIError as exc:
            failures.append(f"{reference_kind}: {exc}")
        else:
            successes.append(reference_kind)
    if successes:
        raise AssertionError(
            "space-containing custom VGT axes name partially resolved; reclassify "
            f"successful reference styles before keeping this xfail: {successes}"
        )
    raise CrossValidationError(
        "space-containing custom VGT axes name unresolved after object and string "
        "reference probes:\n" + "\n".join(failures)
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "non-empty VGT Points and Systems remain unresolved: bounded provider "
        "variants return HTTP 500 before semantic output."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_vgt_points_and_systems_remain_unresolved_after_named_provider_probes() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    # The SDK-callable probes below cover the checked-in CrdnPoint/CrdnSystem
    # schema shape. A bounded raw-wire live probe also tried {"$type": "Point"},
    # {"$type": "System"}, and default names Center, SubSatellitePoint, Fixed,
    # and ICRF; each returned HTTP 500 before semantic output.
    provider_cases = [
        (
            "point_name_only",
            entities.vgt(
                axes=[entities.vvlh_axes(name="OnlyAxes")],
                points=[entities.vgt_point(name="Point")],
            ),
        ),
        (
            "point_name_desc",
            entities.vgt(
                axes=[entities.vvlh_axes(name="OnlyAxes")],
                points=[
                    entities.vgt_point(
                        name="Point",
                        description="minimal named point probe",
                    )
                ],
            ),
        ),
        (
            "system_name_only",
            entities.vgt(
                axes=[entities.vvlh_axes(name="OnlyAxes")],
                systems=[entities.vgt_system(name="System")],
            ),
        ),
        (
            "system_name_desc",
            entities.vgt(
                axes=[entities.vvlh_axes(name="OnlyAxes")],
                systems=[
                    entities.vgt_system(
                        name="System",
                        description="minimal named system probe",
                    )
                ],
            ),
        ),
        (
            "point_system",
            entities.vgt(
                axes=[entities.vvlh_axes(name="OnlyAxes")],
                points=[entities.vgt_point(name="Point")],
                systems=[entities.vgt_system(name="System")],
            ),
        ),
    ]
    failures: list[str] = []
    successes: list[str] = []
    for case_id, provider in provider_cases:
        observer = observer_with_sensor(
            name=f"vgt_{case_id}",
            orientation=entities.vvlh_axes(),
            sensor=conic_sensor(8.0),
            rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
            vgt=provider,
        )
        try:
            compute_sensor_access(observer, target)
        except AstroxHTTPError as exc:
            failures.append(f"{case_id}: HTTP {exc.status_code} {exc}")
            continue
        successes.append(case_id)
    if successes:
        raise AssertionError(
            "non-empty VGT Points/Systems partially resolved; reclassify "
            f"successful provider cases before keeping this xfail: {successes}"
        )
    raise CrossValidationError(
        "VGT Points/Systems unresolved after bounded named provider probes:\n"
        + "\n".join(failures)
    )


def main() -> int:
    try:
        test_aligned_and_constrained_axes_match_triad_alignment_oracle()
        test_aligned_axes_axis_permutations_match_triad_alignment_oracles()
        test_vgt_provider_collections_do_not_perturb_calibrated_vvlh_sensor_access_when_live_callable()
        test_custom_vgt_axes_name_resolution_matches_triad_oracle()
    except (CrossValidationError, LiveConfigError, AstroxAPIError, AstroxHTTPError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=4")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
