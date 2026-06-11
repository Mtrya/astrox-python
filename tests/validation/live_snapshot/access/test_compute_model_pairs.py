"""Live access behavior checks for satellite model pair branches."""

from __future__ import annotations

import pytest

from astrox import orbits
from tests.validation._support import configure_astrox_from_env
from tests.validation.cross_validation.access._cases import (
    CHAIN_INTERVAL_ABS_S,
    CrossValidationError,
    access_orbit,
    branch_probe,
    compute_access,
    distinct_access_orbit,
    hpop_entity,
    is_server_worker_thread_message,
    site,
    two_body_entity,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    intervals_from_access_passes,
)


def slightly_offset_access_orbit() -> orbits.KeplerianElements:
    base = access_orbit()
    return orbits.keplerian(
        semi_major_axis_m=base.semi_major_axis_m,
        eccentricity=base.eccentricity,
        inclination_deg=base.inclination_deg,
        argument_of_periapsis_deg=base.argument_of_periapsis_deg,
        raan_deg=base.raan_deg,
        true_anomaly_deg=base.true_anomaly_deg + 1.0e-6,
    )


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


def test_hpop_two_body_near_coincident_satellite_pair_is_callable_and_symmetric() -> None:
    configure_astrox_from_env()
    left_orbit = access_orbit()
    right_orbit = slightly_offset_access_orbit()
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


@pytest.mark.xfail(
    reason=(
        "Satellite access with coincident initial orbits is isolated to a server worker error, "
        "including same-model and mixed HPOP/two-body pairs; tiny orbital offsets are callable."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_coincident_satellite_orbit_pair_expected_server_worker_error() -> None:
    configure_astrox_from_env()
    probes = [
        branch_probe(
            "two_body->two_body",
            two_body_entity(access_orbit(), name="TwoBodyA"),
            two_body_entity(access_orbit(), name="TwoBodyB"),
        ),
        branch_probe(
            "HPOP->HPOP",
            hpop_entity(access_orbit(), name="HpopA"),
            hpop_entity(access_orbit(), name="HpopB"),
        ),
        branch_probe("two_body->HPOP", two_body_entity(), hpop_entity()),
        branch_probe("HPOP->two_body", hpop_entity(), two_body_entity()),
    ]
    failures = [
        f"{probe.label}: expected isolated server worker error, got {probe.message}"
        for probe in probes
        if probe.success or not is_server_worker_thread_message(probe.message)
    ]
    if failures:
        return
    raise CrossValidationError(
        "coincident satellite orbit pairs still produce the isolated server worker error"
    )
