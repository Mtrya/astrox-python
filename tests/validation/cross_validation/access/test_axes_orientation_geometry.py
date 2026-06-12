"""Entity orbital-axes cross-validation through sensor-constrained access."""

# Coverage:
#   Branches:
#     - VVLH, VVLH(Earth), and VVLH(CBF): verified against local front/right/down frame for nadir and along-track targets
#     - VNC, VNC(Earth), and VNC(CBF): verified against local velocity/normal/co-normal frame for along-track target
#     - LVLH, LVLH(Earth), and LVLH(CBF): partial (live calls are stable no-access for the two calibrated targets; local LVLH candidate does not yet identify a positive discriminator case)
#     - VVLH/LVLH/VNC Moon, Mars, and Sun variants: unresolved after bounded body-vector candidate probing; kept as strict calibration xfail
#   Fields:
#     - Passes.AccessStart/AccessStop: verified for VVLH/VNC branches listed above
#     - Empty Passes for LVLH checks: partial (verified as stable blocking checks, not a full positive convention calibration)
#   Parameters:
#     - relative_to: verified for generic, Earth, and CBF where those live variants match the corresponding generic branch
#     - relative_to Moon/Mars/Sun: unresolved; no passing semantic comparison is claimed
#     - sensor orientation: verified with Quaternion identity and AzEl(0,0) probes
#   Comparison:
#     - External: independent two-body state sampling, local orbital-frame derivations, WGS84 obstruction, and conic FOV predicates
#     - Constants: controlled two-body orbit in _orientation.py, EARTH_MU from access cases
#     - Tolerances: ORIENTATION_INTERVAL_ABS_S=0.5 s
#   Unresolved:
#     - LVLH positive convention discriminator remains pending; current target matrix only proves the two obvious VVLH/VNC target families are excluded
#     - Moon/Mars/Sun relative variants need a body-vector ephemeris comparison path before promotion

from __future__ import annotations

import sys

import pytest

from astrox import entities
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
    state_function,
    subpoint_site,
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


def test_lvh_branches_remain_visible_partial_no_access_checks() -> None:
    configure_astrox_from_env()
    target = target_satellite(5.0)
    rotation = entities.az_el_rotation(azimuth_deg=0.0, elevation_deg=0.0)
    for relative_to in (None, "Earth", "CBF"):
        observer = observer_with_sensor(
            name=f"lvlh_{relative_to or 'generic'}",
            orientation=entities.lvlh_axes(relative_to=relative_to),
            sensor=conic_sensor(8.0),
            rotation=rotation,
        )
        actual = compute_sensor_access(observer, target)
        if actual:
            raise CrossValidationError(
                f"LVLH {relative_to or 'generic'} target unexpectedly became positive; add a local frame discriminator"
            )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Moon/Mars/Sun axes need an ephemeris body-vector comparison path; bounded probes did not "
        "produce a matched convention, so the variants stay unresolved instead of being promoted."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_moon_mars_sun_relative_axes_remain_unresolved() -> None:
    raise CrossValidationError(
        "VVLH/LVLH/VNC Moon/Mars/Sun relative axes are unresolved after body-vector candidate probing"
    )


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
        test_lvh_branches_remain_visible_partial_no_access_checks()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=3")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
