"""Access chain cross-validation against Skyfield SGP4 geometry."""

# Coverage:
#   Branches:
#     - direct site -> SGP4 chain with Connections omitted: verified
#     - serial site -> SGP4 relay -> site chain with explicit connections: verified
#   Fields:
#     - CompleteChainAccess.Start/Stop: verified (compared with independent WGS84 segment-obstruction intervals)
#     - ComputedStrands: partial (checked for the verified route topology, but topology enumeration variants live in live snapshot tests)
#     - IndividualStrandAccess and IndividualObjectAccess: partial (checked for serial route consistency after independent link calibration)
#   Parameters:
#     - participants: verified for fixed-site and SGP4 entity participants in the covered routes
#     - connections: verified for omitted direct chain and a single explicit serial route
#     - use_light_time_delay: partial (serial chain uses the option, but range-over-c route behavior remains covered in compute cross-validation)
#   Comparison:
#     - External: Skyfield SGP4 states plus WGS84 segment-obstruction line-of-sight oracle
#     - Constants: TLE_A, WGS84 ellipsoid from Skyfield, ASTROX fixed-site coordinates from access cases
#     - Tolerances: INTERVAL_ABS_S for external oracle intervals, CHAIN_INTERVAL_ABS_S for exact ASTROX chain object consistency

from __future__ import annotations

import sys

from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import (
    CHAIN_INTERVAL_ABS_S,
    DAY_STOP,
    INTERVAL_ABS_S,
    SITE_HEIGHT_M,
    SITE_LATITUDE_DEG,
    SITE_LONGITUDE_DEG,
    START,
    STOP,
    TLE_A,
    CrossValidationError,
    compute_access,
    direct_chain_sgp4,
    relay_chain,
    sgp4_entity,
    site,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    intersect_intervals,
    intervals_from_access_passes,
    intervals_from_chain,
    sgp4_site_visibility_intervals,
    skyfield_satellite,
    skyfield_site,
)


def test_direct_chain_matches_sgp4_skyfield_obstruction_oracle() -> None:
    configure_astrox_from_env()
    compute_result = compute_access(site(), sgp4_entity())
    chain_result = direct_chain_sgp4()
    oracle_intervals = sgp4_site_visibility_intervals(
        start=START,
        stop=STOP,
        satellite=skyfield_satellite(TLE_A, "ISS"),
        site_position=skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M),
    )
    compute_intervals = intervals_from_access_passes(compute_result["Passes"])
    chain_intervals = intervals_from_chain(chain_result["CompleteChainAccess"])

    compare_intervals(oracle_intervals, compute_intervals, tolerance_s=INTERVAL_ABS_S)
    compare_intervals(oracle_intervals, chain_intervals, tolerance_s=INTERVAL_ABS_S)
    compare_intervals(compute_intervals, chain_intervals, tolerance_s=CHAIN_INTERVAL_ABS_S)


def test_relay_chain_matches_sgp4_skyfield_link_intersection() -> None:
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

    satellite = skyfield_satellite(TLE_A, "Relay")
    first_oracle = sgp4_site_visibility_intervals(
        start=START,
        stop=DAY_STOP,
        satellite=satellite,
        site_position=skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M),
    )
    second_oracle = sgp4_site_visibility_intervals(
        start=START,
        stop=DAY_STOP,
        satellite=satellite,
        site_position=skyfield_site(22.0, -150.0, 0.0),
    )
    expected_chain = intersect_intervals(first_oracle, second_oracle)

    compare_intervals(first_oracle, intervals_from_access_passes(first_link["Passes"]), tolerance_s=INTERVAL_ABS_S)
    compare_intervals(second_oracle, intervals_from_access_passes(second_link["Passes"]), tolerance_s=INTERVAL_ABS_S)
    actual_chain = intervals_from_chain(chain_result["CompleteChainAccess"])
    compare_intervals(expected_chain, actual_chain, tolerance_s=INTERVAL_ABS_S)

    computed_strands = chain_result["ComputedStrands"]
    if computed_strands != [["GroundA", "Relay", "GroundB"]]:
        raise CrossValidationError(f"unexpected ComputedStrands: {computed_strands!r}")
    strand_access = chain_result["IndividualStrandAccess"]["GroundA>Relay>GroundB"]
    compare_intervals(actual_chain, intervals_from_chain(strand_access), tolerance_s=CHAIN_INTERVAL_ABS_S)
    object_access = chain_result["IndividualObjectAccess"]
    for object_name in ("GroundA", "Relay", "GroundB"):
        compare_intervals(
            actual_chain,
            intervals_from_chain(object_access[object_name]),
            tolerance_s=CHAIN_INTERVAL_ABS_S,
        )


def main() -> int:
    try:
        test_direct_chain_matches_sgp4_skyfield_obstruction_oracle()
        test_relay_chain_matches_sgp4_skyfield_link_intersection()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=2")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
