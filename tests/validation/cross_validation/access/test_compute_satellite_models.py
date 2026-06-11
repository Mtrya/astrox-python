"""Access cross-validation for satellite model pair branches."""

from __future__ import annotations

import pytest

from tests.validation._support import configure_astrox_from_env
from tests.validation.cross_validation.access._aer import first_aer_rows
from tests.validation.cross_validation.access._cases import (
    CHAIN_INTERVAL_ABS_S,
    CrossValidationError,
    INTERVAL_ABS_S,
    START,
    STOP,
    access_orbit,
    branch_probe,
    compute_access,
    distinct_access_orbit,
    hpop_entity,
    j2_entity,
    sgp4_entity,
    site,
    two_body_entity,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    intervals_from_access_passes,
    j2_state_ecef,
    sampled_satellite_visibility_intervals,
    sgp4_state_ecef,
)


def test_sgp4_to_j2_no_access_matches_segment_obstruction_oracle() -> None:
    configure_astrox_from_env()
    result = compute_access(
        sgp4_entity(),
        j2_entity(),
        compute_aer=True,
        step_s=300.0,
    )
    actual = intervals_from_access_passes(result["Passes"])
    expected = sampled_satellite_visibility_intervals(
        start=START,
        stop=STOP,
        left_state=sgp4_state_ecef,
        right_state=lambda offset_s: j2_state_ecef(access_orbit(), offset_s),
    )
    compare_intervals(expected, actual, tolerance_s=INTERVAL_ABS_S)
    if actual:
        rows = list(first_aer_rows(result, max_passes=1))
        if not rows:
            raise CrossValidationError("ASTROX returned SGP4-to-J2 passes without AER samples")


def test_hpop_two_body_site_companion_branches_are_callable() -> None:
    configure_astrox_from_env()
    probes = [
        branch_probe("site->HPOP", site(), hpop_entity()),
        branch_probe("HPOP->site", hpop_entity(), site()),
        branch_probe("site->two_body", site(), two_body_entity()),
        branch_probe("two_body->site", two_body_entity(), site()),
    ]
    failures = [
        f"{probe.label}: {probe.message}"
        for probe in probes
        if not probe.success
    ]
    if failures:
        raise CrossValidationError(
            "HPOP/two-body mixed-model checks require callable site companion branches:\n"
            + "\n".join(failures)
        )


def test_hpop_two_body_distinct_satellite_pair_is_callable_and_symmetric() -> None:
    configure_astrox_from_env()
    left_orbit = access_orbit()
    right_orbit = distinct_access_orbit()
    forward = compute_access(
        two_body_entity(left_orbit, name="TwoBodyA"),
        hpop_entity(right_orbit, name="HpopB"),
    )
    reverse = compute_access(
        hpop_entity(right_orbit, name="HpopB"),
        two_body_entity(left_orbit, name="TwoBodyA"),
    )
    compare_intervals(
        intervals_from_access_passes(forward["Passes"]),
        intervals_from_access_passes(reverse["Passes"]),
        tolerance_s=CHAIN_INTERVAL_ABS_S,
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "HPOP/two-body access with coincident initial orbits is isolated to a server worker error, "
        "while site-paired branches and distinct mixed-model satellite pairs are callable."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_hpop_two_body_coincident_orbit_server_error_calibration() -> None:
    configure_astrox_from_env()
    probes = [
        branch_probe("two_body->HPOP", two_body_entity(), hpop_entity()),
        branch_probe("HPOP->two_body", hpop_entity(), two_body_entity()),
    ]
    failures = [
        f"{probe.label}: expected isolated server worker error, got {probe.message}"
        for probe in probes
        if probe.success or "worker thread" not in probe.message
    ]
    if failures:
        raise CrossValidationError("\n".join(failures))
    raise CrossValidationError(
        "both coincident-orbit HPOP/two-body directions still produce the isolated server worker error"
    )
