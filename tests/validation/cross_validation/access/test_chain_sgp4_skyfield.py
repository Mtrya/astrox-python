"""Access chain cross-validation against Skyfield SGP4 geometry."""

# Coverage:
#   Branches:
#     - direct site -> SGP4 chain with Connections omitted: verified
#     - explicit site -> SGP4 -> SGP4 chain with two satellite participants: verified against independent Skyfield/WGS84 link-visibility intersection
#     - serial site -> SGP4 relay -> site chain with explicit connections: unresolved
#     - explicit site -> SGP4 -> SGP4 -> site chain: unresolved server no-path calibration
#   Fields:
#     - CompleteChainAccess.Start/Stop: partial (direct and two-satellite routes verified; serial relay chain residual and full two-relay route unresolved)
#     - ComputedStrands: partial (checked for direct/two-satellite/serial route topology, but topology enumeration variants live in live snapshot tests)
#     - IndividualStrandAccess and IndividualObjectAccess: partial (two-satellite route verified; serial route consistency remains behind calibration xfail)
#   Parameters:
#     - participants: verified for fixed-site and SGP4 entity participants in the covered routes
#     - connections: verified for omitted direct chain, a two-link satellite route, and a single explicit serial route
#     - use_light_time_delay: partial (two-link satellite chain delay matches range-over-c on the limiting ground-to-satellite link; satellite-pair link is not boundary-limiting in this case)
#   Comparison:
#     - External: Skyfield SGP4 states plus WGS84 segment-obstruction line-of-sight oracle
#     - Constants: TLE_A, WGS84 ellipsoid from Skyfield, ASTROX fixed-site coordinates from access cases
#     - Tolerances: INTERVAL_ABS_S for external oracle intervals, CHAIN_INTERVAL_ABS_S for exact ASTROX chain object consistency
#   Unresolved:
#     - relay -> GroundB link intervals differ from the undirected Skyfield/WGS84 obstruction oracle by about 15-20 s for later passes
#     - full GroundA -> RelayA -> RelayB -> GroundB route returns a server no-path error even though all direct links, both two-link subroutes, and the direct-link intersection are non-empty

from __future__ import annotations

import sys

import pytest

from astrox import access, entities
from astrox.exceptions import AstroxAPIError
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._aer import compare_light_time_interval_shift
from tests.validation.cross_validation.access._cases import (
    CHAIN_INTERVAL_ABS_S,
    DAY_STOP,
    INTERVAL_ABS_S,
    SPEED_OF_LIGHT_M_S,
    SITE_HEIGHT_M,
    SITE_LATITUDE_DEG,
    SITE_LONGITUDE_DEG,
    START,
    STOP,
    TLE_A,
    TLE_B,
    CrossValidationError,
    compute_access,
    direct_chain_sgp4,
    is_server_no_path_error,
    relay_chain,
    sgp4_entity,
    site,
)
from tests.validation.cross_validation.access._geometry import (
    Interval,
    compare_intervals,
    intersect_intervals,
    intervals_from_access_passes,
    intervals_from_chain,
    sampled_satellite_visibility_intervals,
    sgp4_state_ecef_for,
    sgp4_site_visibility_intervals,
    skyfield_satellite,
    skyfield_site,
)


def target_site(name: str = "GroundB") -> entities.Entity:
    return entities.entity(
        name=name,
        position=entities.site_position(
            longitude_deg=-150.0,
            latitude_deg=22.0,
            height_m=0.0,
        ),
    )


def two_satellite_chain(
    *,
    use_light_time_delay: bool | None = None,
) -> tuple[dict[str, object], entities.Entity, entities.Entity, entities.Entity]:
    ground = site("GroundA")
    relay_a = sgp4_entity("RelayA", TLE_A)
    relay_b = sgp4_entity("RelayB", TLE_B)
    result = access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, relay_a, relay_b],
        start_participant=ground,
        end_participant=relay_b,
        connections=[
            access.connection(ground, relay_a),
            access.connection(relay_a, relay_b),
        ],
        use_light_time_delay=use_light_time_delay,
    )
    return result, ground, relay_a, relay_b


def full_two_relay_ground_chain(
    *,
    use_light_time_delay: bool | None = None,
) -> tuple[dict[str, object], entities.Entity, entities.Entity, entities.Entity, entities.Entity]:
    ground = site("GroundA")
    relay_a = sgp4_entity("RelayA", TLE_A)
    relay_b = sgp4_entity("RelayB", TLE_B)
    target = target_site("GroundB")
    result = access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, relay_a, relay_b, target],
        start_participant=ground,
        end_participant=target,
        connections=[
            access.connection(ground, relay_a),
            access.connection(relay_a, relay_b),
            access.connection(relay_b, target),
        ],
        use_light_time_delay=use_light_time_delay,
    )
    return result, ground, relay_a, relay_b, target


def direct_link_intersection(
    links: list[dict[str, object]],
) -> list[object]:
    expected = intervals_from_access_passes(links[0]["Passes"])
    for link in links[1:]:
        expected = intersect_intervals(expected, intervals_from_access_passes(link["Passes"]))
    return expected


def two_satellite_chain_oracle_intervals() -> list[Interval]:
    first_link = sgp4_site_visibility_intervals(
        start=START,
        stop=DAY_STOP,
        satellite=skyfield_satellite(TLE_A, "RelayA"),
        site_position=skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M),
    )
    second_link = sampled_satellite_visibility_intervals(
        start=START,
        stop=DAY_STOP,
        left_state=lambda offset_s: sgp4_state_ecef_for(
            TLE_A,
            "RelayA",
            offset_s,
        ),
        right_state=lambda offset_s: sgp4_state_ecef_for(
            TLE_B,
            "RelayB",
            offset_s,
        ),
    )
    return intersect_intervals(first_link, second_link)


def compare_two_satellite_chain_to_direct_links(
    *,
    use_light_time_delay: bool | None,
    compute_aer: bool | None = None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    chain_result, ground, relay_a, relay_b = two_satellite_chain(
        use_light_time_delay=use_light_time_delay
    )
    links = [
        compute_access(
            ground,
            relay_a,
            start=START,
            stop=DAY_STOP,
            compute_aer=compute_aer,
            use_light_time_delay=use_light_time_delay,
        ),
        compute_access(
            relay_a,
            relay_b,
            start=START,
            stop=DAY_STOP,
            compute_aer=compute_aer,
            use_light_time_delay=use_light_time_delay,
        ),
    ]
    expected = direct_link_intersection(links)
    actual = intervals_from_chain(chain_result["CompleteChainAccess"])
    compare_intervals(expected, actual, tolerance_s=CHAIN_INTERVAL_ABS_S)
    if chain_result["ComputedStrands"] != [["GroundA", "RelayA", "RelayB"]]:
        raise CrossValidationError(
            f"unexpected ComputedStrands: {chain_result['ComputedStrands']!r}"
        )
    strand_access = chain_result["IndividualStrandAccess"]["GroundA>RelayA>RelayB"]
    compare_intervals(actual, intervals_from_chain(strand_access), tolerance_s=CHAIN_INTERVAL_ABS_S)
    object_access = chain_result["IndividualObjectAccess"]
    for object_name in ("GroundA", "RelayA", "RelayB"):
        compare_intervals(
            actual,
            intervals_from_chain(object_access[object_name]),
            tolerance_s=CHAIN_INTERVAL_ABS_S,
        )
    return chain_result, links


def compare_two_satellite_chain_to_oracle(
    *,
    use_light_time_delay: bool | None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    chain_result, links = compare_two_satellite_chain_to_direct_links(
        use_light_time_delay=use_light_time_delay,
        compute_aer=True,
    )
    if use_light_time_delay:
        return chain_result, links
    expected = two_satellite_chain_oracle_intervals()
    actual = intervals_from_chain(chain_result["CompleteChainAccess"])
    compare_intervals(expected, actual, tolerance_s=INTERVAL_ABS_S)
    return chain_result, links


def compare_two_satellite_chain_light_time_shift(
    plain_chain: dict[str, object],
    delayed_chain: dict[str, object],
    limiting_plain_link: dict[str, object],
) -> None:
    plain_chain_intervals = intervals_from_chain(plain_chain["CompleteChainAccess"])
    delayed_chain_intervals = intervals_from_chain(delayed_chain["CompleteChainAccess"])
    plain_link_intervals = intervals_from_access_passes(limiting_plain_link["Passes"])
    if len(plain_chain_intervals) != len(delayed_chain_intervals):
        raise CrossValidationError(
            f"chain light-time interval count mismatch: plain={len(plain_chain_intervals)} delayed={len(delayed_chain_intervals)}"
        )

    failures: list[str] = []
    for index, (plain_interval, delayed_interval) in enumerate(
        zip(plain_chain_intervals, delayed_chain_intervals, strict=True)
    ):
        plain_link_pass = matching_access_pass_for_interval(
            plain_interval,
            limiting_plain_link["Passes"],
        )
        start_shift_s = delayed_interval.start_s - plain_interval.start_s
        stop_shift_s = delayed_interval.stop_s - plain_interval.stop_s
        expected_start_shift_s = -float(plain_link_pass["AccessBeginData"]["Range"]) / SPEED_OF_LIGHT_M_S
        expected_stop_shift_s = -float(plain_link_pass["AccessEndData"]["Range"]) / SPEED_OF_LIGHT_M_S
        start_error_s = abs(start_shift_s - expected_start_shift_s)
        stop_error_s = abs(stop_shift_s - expected_stop_shift_s)
        if start_error_s > 3.0e-3:
            failures.append(
                f"interval {index} start light-time shift error {start_error_s:.12g} s exceeds 0.003 s"
            )
        if stop_error_s > 3.0e-3:
            failures.append(
                f"interval {index} stop light-time shift error {stop_error_s:.12g} s exceeds 0.003 s"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def matching_access_pass_for_interval(
    interval: Interval,
    passes: list[dict[str, object]],
) -> dict[str, object]:
    for access_pass, pass_interval in zip(
        passes,
        intervals_from_access_passes(passes),
        strict=True,
    ):
        start_error_s = abs(interval.start_s - pass_interval.start_s)
        stop_error_s = abs(interval.stop_s - pass_interval.stop_s)
        if start_error_s <= CHAIN_INTERVAL_ABS_S and stop_error_s <= CHAIN_INTERVAL_ABS_S:
            return access_pass
    raise CrossValidationError(
        f"no limiting ground-to-satellite pass matches chain interval {interval!r}"
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


def test_two_satellite_chain_matches_direct_link_intersection() -> None:
    configure_astrox_from_env()
    compare_two_satellite_chain_to_oracle(use_light_time_delay=False)


def test_two_satellite_chain_light_time_matches_delayed_direct_link_intersection() -> None:
    configure_astrox_from_env()
    plain_chain, plain_links = compare_two_satellite_chain_to_oracle(
        use_light_time_delay=False,
    )
    delayed_chain, delayed_links = compare_two_satellite_chain_to_oracle(
        use_light_time_delay=True,
    )
    compare_light_time_interval_shift(plain_links[0]["Passes"], delayed_links[0]["Passes"])
    compare_two_satellite_chain_light_time_shift(
        plain_chain,
        delayed_chain,
        plain_links[0],
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Serial relay chain exposes an unresolved relay-to-ground interval residual against "
        "the undirected Skyfield/WGS84 obstruction oracle for later passes."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_relay_chain_matches_sgp4_skyfield_link_intersection_calibration() -> None:
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


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Full GroundA -> RelayA -> RelayB -> GroundB ChainCompute returns no-path even though "
        "all direct links, both two-link subroutes, and the direct-link intersection are non-empty."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_full_two_relay_ground_chain_expected_server_no_path_calibration() -> None:
    configure_astrox_from_env()
    ground = site("GroundA")
    relay_a = sgp4_entity("RelayA", TLE_A)
    relay_b = sgp4_entity("RelayB", TLE_B)
    target = target_site("GroundB")
    direct_links = [
        compute_access(ground, relay_a, start=START, stop=DAY_STOP),
        compute_access(relay_a, relay_b, start=START, stop=DAY_STOP),
        compute_access(relay_b, target, start=START, stop=DAY_STOP),
    ]
    expected = direct_link_intersection(direct_links)
    if not expected:
        raise CrossValidationError("direct-link intersection is empty before full two-relay chain probe")

    first_subroute = access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, relay_a, relay_b],
        start_participant=ground,
        end_participant=relay_b,
        connections=[
            access.connection(ground, relay_a),
            access.connection(relay_a, relay_b),
        ],
    )
    second_subroute = access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[relay_a, relay_b, target],
        start_participant=relay_a,
        end_participant=target,
        connections=[
            access.connection(relay_a, relay_b),
            access.connection(relay_b, target),
        ],
    )
    if not first_subroute["CompleteChainAccess"] or not second_subroute["CompleteChainAccess"]:
        raise CrossValidationError("two-link subroutes must work before full two-relay chain probe")

    try:
        full_two_relay_ground_chain()
    except AstroxAPIError as exc:
        if is_server_no_path_error(exc):
            raise CrossValidationError(
                "full two-relay ground-terminal chain failed with server no-path despite non-empty direct-link and subroute evidence"
            ) from exc
        raise


def main() -> int:
    try:
        test_direct_chain_matches_sgp4_skyfield_obstruction_oracle()
        test_two_satellite_chain_matches_direct_link_intersection()
        test_two_satellite_chain_light_time_matches_delayed_direct_link_intersection()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=3")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
