"""Entity orbital-axes cross-validation through sensor-constrained access."""

# Coverage:
#   Branches:
#     - VVLH, VVLH(Earth), and VVLH(CBF): verified against local front/right/down frame for nadir and along-track targets
#     - VNC, VNC(Earth), and VNC(CBF): verified against local velocity/normal/co-normal frame for along-track target
#     - LVLH, LVLH(Earth), and LVLH(CBF): verified against local radial/along-track/angular-momentum frame for radial-out and along-track targets
#     - VVLH/LVLH/VNC Moon and Mars variants: unresolved after matching central-body target probes and Skyfield body-vector candidate comparison; kept as strict calibration xfail
#     - VVLH/LVLH/VNC Sun variants: unverifiable for central-body target comparison while live ASTROX returns Object reference not set; maintainer sign-off inherited from implementation plan
#   Fields:
#     - Passes.AccessStart/AccessStop: verified for VVLH/VNC/LVLH branches listed above
#   Parameters:
#     - relative_to: verified for generic, Earth, and CBF where those live variants match the corresponding generic branch
#     - relative_to Moon/Mars: unresolved; no passing semantic comparison is claimed
#     - relative_to Sun: unverifiable while the matching central-body target fails before semantic output
#     - sensor orientation: verified with Quaternion identity, AzEl(0,0), and AzEl(90,0) probes
#   Comparison:
#     - External: independent two-body state sampling, local orbital-frame derivations, WGS84 obstruction, and conic FOV predicates
#     - Constants: controlled two-body orbit in _orientation.py, EARTH_MU from access cases
#     - Tolerances: ORIENTATION_INTERVAL_ABS_S=0.5 s
#   Unresolved:
#     - Skyfield DE421 body-vector candidate did not match Moon/Mars: VVLH(Moon/Mars) returned central-body-target passes when the Skyfield +Z body-vector FOV oracle predicted none, VNC(Moon) was shifted by about 90-137 s for the +X candidate, and VNC(Mars) selected a different boresight branch

from __future__ import annotations

import sys

import pytest

from astrox import entities
from astrox.exceptions import AstroxAPIError
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import CrossValidationError
from tests.validation.cross_validation.access._orientation import (
    az_el_boresight,
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
        "but the Skyfield DE421 body-vector candidate did not match interval counts or transition times."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_moon_mars_relative_axes_remain_unresolved_after_body_vector_probe() -> None:
    raise CrossValidationError(
        "Moon/Mars body-relative axes unresolved: VVLH body-target intervals contradict the Skyfield +Z body-vector FOV candidate, VNC(Moon) +X transitions differ by about 90-137 s, and VNC(Mars) selects -Z rather than the Skyfield +X candidate"
    )


def test_sun_relative_axes_remain_unverifiable_server_failure() -> None:
    configure_astrox_from_env()
    observer = observer_with_sensor(
        name="sun_relative_axes",
        orientation=entities.vvlh_axes(relative_to="Sun"),
        sensor=conic_sensor(20.0),
        rotation=entities.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0),
    )
    target = entities.entity(name="Sun", position=entities.central_body_position("Sun"))
    try:
        compute_sensor_access(observer, target)
    except AstroxAPIError as exc:
        if "Object reference not set to an instance of an object" not in str(exc):
            raise
        return
    raise CrossValidationError("Sun relative-axis central-body target unexpectedly returned semantic output")


def case_for_axes(*, case_id: str, axes, target, rotation, expected):
    return type("Case", (), {
        "id": case_id,
        "observer": observer_with_sensor(
            name=case_id,
            orientation=axes,
            sensor=conic_sensor(8.0),
            rotation=rotation,
        ),
        "target": target,
        "expected": expected,
    })()


def main() -> int:
    try:
        test_vvlh_generic_earth_and_cbf_match_local_vvlh_frame()
        test_vvlh_and_vnc_along_track_branches_match_local_frame_candidates()
        test_lvlh_branches_match_radial_and_along_track_frame_candidates()
        test_sun_relative_axes_remain_unverifiable_server_failure()
    except (CrossValidationError, LiveConfigError, AstroxAPIError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=4")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
