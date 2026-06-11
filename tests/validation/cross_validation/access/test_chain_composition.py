"""Access chain cross-validation against direct links and interval composition."""

from __future__ import annotations

from tests.validation._support import configure_astrox_from_env
from tests.validation.cross_validation.access._cases import (
    CHAIN_INTERVAL_ABS_S,
    CrossValidationError,
    DAY_STOP,
    INTERVAL_ABS_S,
    SITE_HEIGHT_M,
    SITE_LATITUDE_DEG,
    SITE_LONGITUDE_DEG,
    START,
    STOP,
    TLE_A,
    compute_access,
    direct_chain_sgp4,
    group_chain_anyof,
    relay_chain,
    sgp4_entity,
    site,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    intersect_intervals,
    intervals_from_access_passes,
    intervals_from_chain,
    merge_intervals,
    sgp4_site_visibility_intervals,
    skyfield_satellite,
    skyfield_site,
)


def test_direct_chain_matches_compute_and_obstruction_oracle() -> None:
    configure_astrox_from_env()
    compute_result = compute_access(site(), sgp4_entity())
    chain_result = direct_chain_sgp4()
    compute_intervals = intervals_from_access_passes(compute_result["Passes"])
    chain_intervals = intervals_from_chain(chain_result["CompleteChainAccess"])
    oracle_intervals = sgp4_site_visibility_intervals(
        start=START,
        stop=STOP,
        satellite=skyfield_satellite(TLE_A, "ISS"),
        site_position=skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M),
    )
    compare_intervals(compute_intervals, chain_intervals, tolerance_s=CHAIN_INTERVAL_ABS_S)
    compare_intervals(oracle_intervals, compute_intervals, tolerance_s=INTERVAL_ABS_S)


def test_entity_group_anyof_complete_access_is_union_of_member_strands() -> None:
    configure_astrox_from_env()
    result = group_chain_anyof()
    strand_access = result["IndividualStrandAccess"]
    member_intervals = []
    for strand_name in ("Ground>ISS", "Ground>Hubble"):
        member_intervals.extend(intervals_from_chain(strand_access[strand_name]))
    expected = merge_intervals(member_intervals)
    actual = intervals_from_chain(result["CompleteChainAccess"])
    compare_intervals(expected, actual, tolerance_s=CHAIN_INTERVAL_ABS_S)


def test_ground_relay_ground_chain_is_intersection_of_links() -> None:
    configure_astrox_from_env()
    chain_result, ground_a, relay, ground_b = relay_chain()
    first_link = compute_access(
        ground_a,
        relay,
        start=START,
        stop=DAY_STOP,
        use_light_time_delay=True,
    )
    second_link = compute_access(
        relay,
        ground_b,
        start=START,
        stop=DAY_STOP,
        use_light_time_delay=True,
    )
    first_intervals = intervals_from_access_passes(first_link["Passes"])
    second_intervals = intervals_from_access_passes(second_link["Passes"])
    expected = intersect_intervals(first_intervals, second_intervals)
    actual = intervals_from_chain(chain_result["CompleteChainAccess"])
    compare_intervals(expected, actual, tolerance_s=CHAIN_INTERVAL_ABS_S)

    computed_strands = chain_result["ComputedStrands"]
    if computed_strands != [["GroundA", "Relay", "GroundB"]]:
        raise CrossValidationError(f"unexpected ComputedStrands: {computed_strands!r}")
    strand_access = chain_result["IndividualStrandAccess"]["GroundA>Relay>GroundB"]
    compare_intervals(actual, intervals_from_chain(strand_access), tolerance_s=CHAIN_INTERVAL_ABS_S)
    object_access = chain_result["IndividualObjectAccess"]
    for object_name in ("GroundA", "Relay", "GroundB"):
        compare_intervals(
            actual,
            intervals_from_chain(object_access[object_name]),
            tolerance_s=CHAIN_INTERVAL_ABS_S,
        )
