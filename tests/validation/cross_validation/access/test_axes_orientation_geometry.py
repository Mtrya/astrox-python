"""Entity orbital-axes cross-validation through sensor-constrained access."""

# Coverage:
#   Branches:
#     - VVLH, VVLH(Earth), and VVLH(CBF): verified against local front/right/down frame for nadir, along-track, and cross-track targets
#     - VNC, VNC(Earth), and VNC(CBF): verified against local velocity/normal/co-normal frame for along-track, radial-out, and cross-track targets
#     - LVLH, LVLH(Earth), and LVLH(CBF): verified against local radial/along-track/angular-momentum frame for radial-out, along-track, and cross-track targets
#     - VVLH/LVLH/VNC Moon and Mars variants: unresolved after live central-body target probes and Skyfield body-vector candidate comparison; kept as strict calibration xfail
#     - VVLH/LVLH/VNC Sun variants: unresolved because live central-body target comparison returns Object reference not set before semantic output; kept as strict calibration xfail
#   Fields:
#     - Passes.AccessStart/AccessStop: verified for VVLH/VNC/LVLH branches listed above
#   Parameters:
#     - relative_to: verified for generic, Earth, and CBF where those live variants match the corresponding generic branch
#     - relative_to Moon/Mars: unresolved; no passing semantic comparison is claimed
#     - relative_to Sun: unresolved while the matching central-body target fails before semantic output
#     - sensor orientation: verified with Quaternion identity, AzEl(0,0), AzEl(90,0), and AzEl(0,90) probes
#   Comparison:
#     - External: independent two-body state sampling, local orbital-frame derivations, WGS84 obstruction, and conic FOV predicates
#     - Constants: controlled two-body orbit in _orientation.py, EARTH_MU from access cases
#     - Tolerances: ORIENTATION_INTERVAL_ABS_S=0.5 s
#   Unresolved:
#     - Skyfield DE421 body-vector candidates remain just outside the promoted tolerance for Moon/Mars: body-pointing VVLH matched interval counts but had 0.91-1.68 s boundary residuals; body-relative VNC(Moon) matched interval counts but had 1.36-1.77 s residuals; body-relative LVLH(Moon), VNC(Mars), and LVLH(Mars) matched empty interval counts, which is useful but not enough to promote a semantic branch

from __future__ import annotations

import sys

import pytest

from astrox import entities
from astrox.exceptions import AstroxAPIError
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import CrossValidationError
from tests.validation.cross_validation.access._geometry import compare_intervals
from tests.validation.cross_validation.access._orientation import (
    ORIENTATION_INTERVAL_ABS_S,
    az_el_boresight,
    body_lvlh_frame,
    body_vnc_frame,
    body_vvlh_frame,
    compare_sensor_case,
    compute_sensor_access,
    conic_predicate,
    conic_sensor,
    controlled_orbit,
    expected_intervals,
    expected_site_intervals,
    observer_with_sensor,
    quaternion_rotation,
    lvlh_frame,
    skyfield_body_state_function,
    state_function,
    subpoint_site,
    target_orbit_entity,
    target_satellite,
    vnc_frame,
    vvlh_frame,
)


def test_vvlh_generic_earth_and_cbf_match_local_vvlh_frame() -> None:
    configure_astrox_from_env()
    target = subpoint_site()
    rotation = entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0)
    boresight = quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0) @ [0.0, 0.0, 1.0]
    expected = expected_site_intervals(
        site=target,
        frame=vvlh_frame,
        sensor_predicate=conic_predicate(8.0, boresight),
    )
    for relative_to in (None, "Earth", "CBF"):
        case = case_for_axes(
            case_id=f"vvlh_{relative_to or 'generic'}_nadir",
            axes=entities.vvlh_axes(relative_to=relative_to),
            target=target,
            rotation=rotation,
            expected=expected,
        )
        compare_sensor_case(case)


def test_vvlh_and_vnc_along_track_branches_match_local_frame_candidates() -> None:
    configure_astrox_from_env()
    target = target_satellite(5.0)
    rotation = entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=0.0)
    expected_vvlh = expected_intervals(
        target_state=state_function(controlled_orbit(true_anomaly_offset_deg=5.0)),
        frame=vvlh_frame,
        sensor_predicate=conic_predicate(8.0, az_el_boresight(azimuth_deg=0.0, elevation_deg=0.0)),
    )
    expected_vnc = expected_intervals(
        target_state=state_function(controlled_orbit(true_anomaly_offset_deg=5.0)),
        frame=vnc_frame,
        sensor_predicate=conic_predicate(8.0, az_el_boresight(azimuth_deg=0.0, elevation_deg=0.0)),
    )
    for relative_to in (None, "Earth", "CBF"):
        compare_sensor_case(
            case_for_axes(
                case_id=f"vvlh_{relative_to or 'generic'}_along_track",
                axes=entities.vvlh_axes(relative_to=relative_to),
                target=target,
                rotation=rotation,
                expected=expected_vvlh,
            )
        )
        compare_sensor_case(
            case_for_axes(
                case_id=f"vnc_{relative_to or 'generic'}_along_track",
                axes=entities.vnc_axes(relative_to=relative_to),
                target=target,
                rotation=rotation,
                expected=expected_vnc,
            )
        )


def test_vvlh_vnc_and_lvlh_cross_axis_discriminators_match_local_frame_candidates() -> None:
    configure_astrox_from_env()
    cross_track = target_orbit_entity(name="AxesCrossTrackIncPlus2", inclination_delta_deg=2.0)
    radial = target_orbit_entity(name="AxesRadialOut", semi_major_delta_m=100000.0)
    vvlh_cross_expected = expected_intervals(
        target_state=state_function(controlled_orbit(inclination_delta_deg=2.0)),
        frame=vvlh_frame,
        sensor_predicate=conic_predicate(20.0, az_el_boresight(azimuth_deg=90.0, elevation_deg=0.0)),
    )
    vnc_radial_expected = expected_intervals(
        target_state=state_function(controlled_orbit(semi_major_delta_m=100000.0)),
        frame=vnc_frame,
        sensor_predicate=conic_predicate(20.0, az_el_boresight(azimuth_deg=0.0, elevation_deg=90.0)),
    )
    vnc_cross_expected = expected_intervals(
        target_state=state_function(controlled_orbit(inclination_delta_deg=2.0)),
        frame=vnc_frame,
        sensor_predicate=conic_predicate(20.0, az_el_boresight(azimuth_deg=90.0, elevation_deg=0.0)),
    )
    lvlh_cross_expected = expected_intervals(
        target_state=state_function(controlled_orbit(inclination_delta_deg=2.0)),
        frame=lvlh_frame,
        sensor_predicate=conic_predicate(20.0, az_el_boresight(azimuth_deg=0.0, elevation_deg=90.0)),
    )
    for relative_to in (None, "Earth", "CBF"):
        compare_sensor_case(
            case_for_axes(
                case_id=f"vvlh_{relative_to or 'generic'}_cross_track",
                axes=entities.vvlh_axes(relative_to=relative_to),
                target=cross_track,
                rotation=entities.az_el_rotation(azimuth_deg=90.0, elevation_deg=0.0),
                expected=vvlh_cross_expected,
                sensor=conic_sensor(20.0),
            )
        )
        compare_sensor_case(
            case_for_axes(
                case_id=f"vnc_{relative_to or 'generic'}_radial",
                axes=entities.vnc_axes(relative_to=relative_to),
                target=radial,
                rotation=entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=90.0),
                expected=vnc_radial_expected,
                sensor=conic_sensor(20.0),
            )
        )
        compare_sensor_case(
            case_for_axes(
                case_id=f"vnc_{relative_to or 'generic'}_cross_track",
                axes=entities.vnc_axes(relative_to=relative_to),
                target=cross_track,
                rotation=entities.az_el_rotation(azimuth_deg=90.0, elevation_deg=0.0),
                expected=vnc_cross_expected,
                sensor=conic_sensor(20.0),
            )
        )
        compare_sensor_case(
            case_for_axes(
                case_id=f"lvlh_{relative_to or 'generic'}_cross_track",
                axes=entities.lvlh_axes(relative_to=relative_to),
                target=cross_track,
                rotation=entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=90.0),
                expected=lvlh_cross_expected,
                sensor=conic_sensor(20.0),
            )
        )


def test_lvlh_branches_match_radial_and_along_track_frame_candidates() -> None:
    configure_astrox_from_env()
    radial_target = target_orbit_entity(name="RadialOut", semi_major_delta_m=100000.0)
    along_target = target_satellite(5.0)
    radial_rotation = entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=0.0)
    along_rotation = entities.az_el_rotation(azimuth_deg=90.0, elevation_deg=0.0)
    expected_radial = expected_intervals(
        target_state=state_function(controlled_orbit(semi_major_delta_m=100000.0)),
        frame=lvlh_frame,
        sensor_predicate=conic_predicate(8.0, az_el_boresight(azimuth_deg=0.0, elevation_deg=0.0)),
    )
    expected_along = expected_intervals(
        target_state=state_function(controlled_orbit(true_anomaly_offset_deg=5.0)),
        frame=lvlh_frame,
        sensor_predicate=conic_predicate(8.0, az_el_boresight(azimuth_deg=90.0, elevation_deg=0.0)),
    )
    for relative_to in (None, "Earth", "CBF"):
        compare_sensor_case(
            case_for_axes(
                case_id=f"lvlh_{relative_to or 'generic'}_radial",
                axes=entities.lvlh_axes(relative_to=relative_to),
                target=radial_target,
                rotation=radial_rotation,
                expected=expected_radial,
            )
        )
        compare_sensor_case(
            case_for_axes(
                case_id=f"lvlh_{relative_to or 'generic'}_along_track",
                axes=entities.lvlh_axes(relative_to=relative_to),
                target=along_target,
                rotation=along_rotation,
                expected=expected_along,
            )
        )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Moon/Mars axes remain unresolved: matching central-body target probes produced live passes, "
        "but Skyfield DE421 body-vector candidates either exceed the transition tolerance or only "
        "match empty interval controls."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_moon_mars_relative_axes_remain_unresolved_after_body_vector_probe() -> None:
    configure_astrox_from_env()
    # Bounded implementation probe, using Skyfield DE421 and the same local FOV
    # interval oracle. The local candidates below are intentionally simple:
    # body positions are geocentric DE421 vectors, and velocities use a central
    # finite difference around the UTC sample. These candidates test whether the
    # ASTROX relative_to body variants are just ordinary body-relative orbital
    # frames. Current live behavior says they are not calibrated enough to
    # promote.
    diagnostics: list[str] = []
    for body_name in ("Moon", "Mars"):
        body_state = skyfield_body_state_function(body_name)
        target_state = body_state
        target = entities.entity(name=body_name, position=entities.central_body_position(body_name))
        for axes_name, axes, rotation, frame, boresight in (
            (
                "VVLH",
                entities.vvlh_axes(relative_to=body_name),
                entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
                body_vvlh_frame(body_state),
                quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0) @ [0.0, 0.0, 1.0],
            ),
            (
                "VNC",
                entities.vnc_axes(relative_to=body_name),
                entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=0.0),
                body_vnc_frame(body_state),
                az_el_boresight(azimuth_deg=0.0, elevation_deg=0.0),
            ),
            (
                "LVLH",
                entities.lvlh_axes(relative_to=body_name),
                entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=0.0),
                body_lvlh_frame(body_state),
                az_el_boresight(azimuth_deg=0.0, elevation_deg=0.0),
            ),
        ):
            observer = observer_with_sensor(
                name=f"{axes_name}_{body_name}_probe",
                orientation=axes,
                sensor=conic_sensor(20.0),
                rotation=rotation,
            )
            actual = compute_sensor_access(observer, target)
            expected = expected_intervals(
                target_state=target_state,
                frame=frame,
                sensor_predicate=conic_predicate(20.0, boresight),
            )
            if not expected and not actual:
                diagnostics.append(
                    f"{axes_name}({body_name}): expected and actual are both empty; "
                    "empty-control agreement is not enough to promote body-relative axes"
                )
                continue
            try:
                compare_intervals(expected, actual, tolerance_s=ORIENTATION_INTERVAL_ABS_S)
            except CrossValidationError as exc:
                diagnostics.append(
                    f"{axes_name}({body_name}): expected {expected}, actual {actual}, residual {exc}"
                )
            else:
                raise AssertionError(
                    f"{axes_name}({body_name}) matched the Skyfield body-relative candidate; "
                    "reclassify this branch as verified"
                )
    raise CrossValidationError(
        "Moon/Mars body-relative axes unresolved after live probes. "
        "Skyfield DE421 body-vector candidates still do not explain the observed intervals:\n"
        + "\n".join(diagnostics)
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Sun relative axes remain unresolved: live central-body target comparison fails "
        "with Object reference not set before semantic output."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_sun_relative_axes_remain_unresolved_server_failure() -> None:
    configure_astrox_from_env()
    target = entities.entity(name="Sun", position=entities.central_body_position("Sun"))
    failures: list[str] = []
    successes: list[str] = []
    for axes_name, axes, rotation in (
        (
            "VVLH",
            entities.vvlh_axes(relative_to="Sun"),
            entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
        ),
        (
            "VNC",
            entities.vnc_axes(relative_to="Sun"),
            entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=0.0),
        ),
        (
            "LVLH",
            entities.lvlh_axes(relative_to="Sun"),
            entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=0.0),
        ),
    ):
        observer = observer_with_sensor(
            name=f"{axes_name}_sun_relative_axes",
            orientation=axes,
            sensor=conic_sensor(20.0),
            rotation=rotation,
        )
        try:
            intervals = compute_sensor_access(observer, target)
        except AstroxAPIError as exc:
            if "Object reference not set to an instance of an object" not in str(exc):
                raise
            failures.append(f"{axes_name}(Sun): {exc}")
        else:
            successes.append(f"{axes_name}(Sun): returned intervals {intervals}")
    if successes:
        raise AssertionError(
            "Sun relative axes partially resolved; reclassify successful cases before "
            "keeping this xfail:\n" + "\n".join(successes)
        )
    raise CrossValidationError(
        "Sun relative-axis central-body targets unresolved for every axes family:\n"
        + "\n".join(failures)
    )


def case_for_axes(*, case_id: str, axes, target, rotation, expected, sensor=None):
    sensor = conic_sensor(8.0) if sensor is None else sensor
    return type("Case", (), {
        "id": case_id,
        "observer": observer_with_sensor(
            name=case_id,
            orientation=axes,
            sensor=sensor,
            rotation=rotation,
        ),
        "target": target,
        "expected": expected,
    })()


def main() -> int:
    try:
        test_vvlh_generic_earth_and_cbf_match_local_vvlh_frame()
        test_vvlh_and_vnc_along_track_branches_match_local_frame_candidates()
        test_vvlh_vnc_and_lvlh_cross_axis_discriminators_match_local_frame_candidates()
        test_lvlh_branches_match_radial_and_along_track_frame_candidates()
    except (CrossValidationError, LiveConfigError, AstroxAPIError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=4")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
