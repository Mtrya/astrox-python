"""Live access chain topology behavior checks."""

from __future__ import annotations

import pytest

from astrox import access, components
from astrox.exceptions import AstroxAPIError
from tests.validation._support import configure_astrox_from_env
from tests.validation.cross_validation.access._cases import (
    CHAIN_INTERVAL_ABS_S,
    CrossValidationError,
    DAY_STOP,
    START,
    STOP,
    TLE_A,
    TLE_B,
    compute_access,
    direct_chain_sgp4,
    group_chain_anyof,
    is_server_index_error,
    is_server_no_path_error,
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
)


def _target_site(name: str = "G2") -> components.Entity:
    return components.entity(
        name=name,
        position=components.site_position(
            longitude_deg=-150.0,
            latitude_deg=22.0,
            height_m=0.0,
        ),
    )


def _serial_chain(
    ground: components.Entity,
    relay: components.Entity,
    target: components.Entity,
    *,
    participants: list[components.Entity] | None = None,
    connections: list[access.Connection] | None = None,
    start_participant: components.Entity | None = None,
    end_participant: components.Entity | None = None,
    use_light_time_delay: bool | None = None,
) -> dict[str, object]:
    route_connections = (
        connections
        if connections is not None
        else [
            access.connection(ground, relay),
            access.connection(relay, target),
        ]
    )
    return access.chain(
        start=START,
        stop=DAY_STOP,
        participants=participants if participants is not None else [ground, relay, target],
        start_participant=start_participant or ground,
        end_participant=end_participant or target,
        connections=route_connections,
        use_light_time_delay=use_light_time_delay,
    )


def test_empty_connections_matches_direct_chain_semantics() -> None:
    configure_astrox_from_env()
    ground = site()
    target = sgp4_entity()
    null_connections = direct_chain_sgp4()
    empty_connections = access.chain(
        start=START,
        stop=STOP,
        participants=[ground, target],
        start_participant=ground,
        end_participant=target,
        connections=[],
    )
    compare_intervals(
        intervals_from_chain(null_connections["CompleteChainAccess"]),
        intervals_from_chain(empty_connections["CompleteChainAccess"]),
        tolerance_s=CHAIN_INTERVAL_ABS_S,
    )
    if empty_connections["ComputedStrands"] != [["Ground", "ISS"]]:
        raise CrossValidationError(
            f"unexpected empty-connections ComputedStrands: {empty_connections['ComputedStrands']!r}"
        )


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


def test_entity_group_atleastn_complete_access_is_intersection_of_member_strands() -> None:
    configure_astrox_from_env()
    ground = site()
    targets = components.entity_group(
        name="TargetsAtLeast2",
        members=[
            sgp4_entity("ISS", TLE_A),
            sgp4_entity("Hubble", TLE_B),
        ],
        to_restriction="AtLeastN",
        to_number=2,
    )
    result = access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, targets],
        start_participant=ground,
        end_participant=targets,
    )
    strand_access = result["IndividualStrandAccess"]
    iss_intervals = intervals_from_chain(strand_access["Ground>ISS"])
    hubble_intervals = intervals_from_chain(strand_access["Ground>Hubble"])
    expected = intersect_intervals(iss_intervals, hubble_intervals)
    actual = intervals_from_chain(result["CompleteChainAccess"])
    compare_intervals(expected, actual, tolerance_s=CHAIN_INTERVAL_ABS_S)


def test_single_explicit_route_allows_unused_participants() -> None:
    configure_astrox_from_env()
    ground = site("G")
    relay = sgp4_entity("A", TLE_A)
    unused_relay = sgp4_entity("B", TLE_B)
    target = _target_site()
    baseline = _serial_chain(ground, relay, target)
    with_unused_participant = _serial_chain(
        ground,
        relay,
        target,
        participants=[ground, relay, unused_relay, target],
    )
    compare_intervals(
        intervals_from_chain(baseline["CompleteChainAccess"]),
        intervals_from_chain(with_unused_participant["CompleteChainAccess"]),
        tolerance_s=CHAIN_INTERVAL_ABS_S,
    )
    if with_unused_participant["ComputedStrands"] != [["G", "A", "G2"]]:
        raise CrossValidationError(
            f"unused participant changed computed strands: {with_unused_participant['ComputedStrands']!r}"
        )


def test_explicit_connections_are_directional() -> None:
    configure_astrox_from_env()
    ground = site("G")
    relay = sgp4_entity("A", TLE_A)
    target = _target_site()
    forward = _serial_chain(ground, relay, target)
    try:
        _serial_chain(
            ground,
            relay,
            target,
            connections=[
                access.connection(relay, ground),
                access.connection(target, relay),
            ],
        )
    except AstroxAPIError as exc:
        if not is_server_no_path_error(exc):
            raise
    else:
        raise CrossValidationError("reversed link directions unexpectedly produced a forward chain")

    backward = _serial_chain(
        ground,
        relay,
        target,
        start_participant=target,
        end_participant=ground,
        connections=[
            access.connection(target, relay),
            access.connection(relay, ground),
        ],
    )
    compare_intervals(
        intervals_from_chain(forward["CompleteChainAccess"]),
        intervals_from_chain(backward["CompleteChainAccess"]),
        tolerance_s=CHAIN_INTERVAL_ABS_S,
    )
    if backward["ComputedStrands"] != [["G2", "A", "G"]]:
        raise CrossValidationError(f"unexpected backward ComputedStrands: {backward['ComputedStrands']!r}")


def test_serial_chain_light_time_delay_matches_direct_link_composition() -> None:
    configure_astrox_from_env()
    ground = site("G")
    relay = sgp4_entity("A", TLE_A)
    target = _target_site()
    chain_without_light_time = _serial_chain(
        ground,
        relay,
        target,
        use_light_time_delay=False,
    )
    chain_with_light_time = _serial_chain(
        ground,
        relay,
        target,
        use_light_time_delay=True,
    )

    first_without_light_time = compute_access(
        ground,
        relay,
        start=START,
        stop=DAY_STOP,
        use_light_time_delay=False,
    )
    second_without_light_time = compute_access(
        relay,
        target,
        start=START,
        stop=DAY_STOP,
        use_light_time_delay=False,
    )
    first_with_light_time = compute_access(
        ground,
        relay,
        start=START,
        stop=DAY_STOP,
        use_light_time_delay=True,
    )
    second_with_light_time = compute_access(
        relay,
        target,
        start=START,
        stop=DAY_STOP,
        use_light_time_delay=True,
    )
    expected_without_light_time = intersect_intervals(
        intervals_from_access_passes(first_without_light_time["Passes"]),
        intervals_from_access_passes(second_without_light_time["Passes"]),
    )
    expected_with_light_time = intersect_intervals(
        intervals_from_access_passes(first_with_light_time["Passes"]),
        intervals_from_access_passes(second_with_light_time["Passes"]),
    )
    actual_without_light_time = intervals_from_chain(chain_without_light_time["CompleteChainAccess"])
    actual_with_light_time = intervals_from_chain(chain_with_light_time["CompleteChainAccess"])
    compare_intervals(expected_without_light_time, actual_without_light_time, tolerance_s=CHAIN_INTERVAL_ABS_S)
    compare_intervals(expected_with_light_time, actual_with_light_time, tolerance_s=CHAIN_INTERVAL_ABS_S)
    try:
        compare_intervals(actual_without_light_time, actual_with_light_time, tolerance_s=CHAIN_INTERVAL_ABS_S)
    except CrossValidationError:
        return
    raise CrossValidationError("serial chain light-time option did not change complete access intervals")


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "ChainCompute rejects one request containing multiple explicit relay routes even though each route works separately."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_multiple_explicit_relay_routes_expected_server_no_path() -> None:
    configure_astrox_from_env()
    ground = site("G")
    relay_a = sgp4_entity("A", TLE_A)
    relay_b = sgp4_entity("B", TLE_B)
    target = _target_site()
    first = _serial_chain(ground, relay_a, target)
    second = _serial_chain(
        ground,
        relay_b,
        target,
        connections=[
            access.connection(ground, relay_b),
            access.connection(relay_b, target),
        ],
    )
    if not first["CompleteChainAccess"] or not second["CompleteChainAccess"]:
        raise CrossValidationError("individual relay routes must work before testing the combined request")
    try:
        access.chain(
            start=START,
            stop=DAY_STOP,
            participants=[ground, relay_a, relay_b, target],
            start_participant=ground,
            end_participant=target,
            connections=[
                access.connection(ground, relay_a),
                access.connection(relay_a, target),
                access.connection(ground, relay_b),
                access.connection(relay_b, target),
            ],
        )
    except AstroxAPIError as exc:
        if is_server_no_path_error(exc):
            raise CrossValidationError(
                "combined explicit relay routes failed with no-path error despite both routes working separately"
            ) from exc
        raise


@pytest.mark.calibration
@pytest.mark.xfail(
    reason="ChainCompute rejects duplicate explicit links with no-path even when the unique serial route works.",
    raises=CrossValidationError,
    strict=True,
)
def test_duplicate_explicit_link_expected_server_no_path() -> None:
    configure_astrox_from_env()
    ground = site("G")
    relay = sgp4_entity("A", TLE_A)
    target = _target_site()
    baseline = _serial_chain(ground, relay, target)
    if not baseline["CompleteChainAccess"]:
        raise CrossValidationError("unique serial route must work before testing duplicate links")
    try:
        _serial_chain(
            ground,
            relay,
            target,
            connections=[
                access.connection(ground, relay),
                access.connection(ground, relay),
                access.connection(relay, target),
            ],
        )
    except AstroxAPIError as exc:
        if is_server_no_path_error(exc):
            raise CrossValidationError(
                "duplicate explicit link failed with no-path error despite the unique route working"
            ) from exc
        raise


@pytest.mark.calibration
@pytest.mark.xfail(
    reason="ChainCompute rejects a single working explicit route when an extra branch connection is also present.",
    raises=CrossValidationError,
    strict=True,
)
def test_extra_branch_connection_expected_server_no_path() -> None:
    configure_astrox_from_env()
    ground = site("G")
    relay = sgp4_entity("A", TLE_A)
    extra_relay = sgp4_entity("B", TLE_B)
    target = _target_site()
    working = _serial_chain(
        ground,
        relay,
        target,
        participants=[ground, relay, extra_relay, target],
    )
    if not working["CompleteChainAccess"]:
        raise CrossValidationError("single explicit route must work before testing the extra branch")
    try:
        _serial_chain(
            ground,
            relay,
            target,
            participants=[ground, relay, extra_relay, target],
            connections=[
                access.connection(ground, relay),
                access.connection(relay, target),
                access.connection(ground, extra_relay),
            ],
        )
    except AstroxAPIError as exc:
        if is_server_no_path_error(exc):
            raise CrossValidationError(
                "extra branch connection failed with no-path error despite the original route still being present"
            ) from exc
        raise


@pytest.mark.calibration
@pytest.mark.xfail(
    reason="ChainCompute raises an index error when an EntityGroup is used as the chain start object.",
    raises=CrossValidationError,
    strict=True,
)
def test_start_entity_group_expected_server_index_error() -> None:
    configure_astrox_from_env()
    ground = site("Ground")
    sources = components.entity_group(
        name="Sources",
        members=[
            sgp4_entity("ISS", TLE_A),
            sgp4_entity("Hubble", TLE_B),
        ],
        from_restriction="AnyOf",
    )
    try:
        access.chain(
            start=START,
            stop=DAY_STOP,
            participants=[sources, ground],
            start_participant=sources,
            end_participant=ground,
        )
    except AstroxAPIError as exc:
        if is_server_index_error(exc):
            raise CrossValidationError(
                "start EntityGroup failed with server index error"
            ) from exc
        raise


@pytest.mark.calibration
@pytest.mark.xfail(
    reason="ChainCompute currently returns the same single-strand intervals when a required link has MaxUses=0.",
    raises=CrossValidationError,
    strict=True,
)
def test_connection_max_uses_zero_expected_to_change_intervals() -> None:
    configure_astrox_from_env()
    chain_result, ground, relay, target = relay_chain()
    constrained = access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, relay, target],
        start_participant=ground,
        end_participant=target,
        connections=[
            access.connection(ground, relay, max_uses=0),
            access.connection(relay, target, max_uses=0),
        ],
        use_light_time_delay=True,
    )
    try:
        compare_intervals(
            intervals_from_chain(chain_result["CompleteChainAccess"]),
            intervals_from_chain(constrained["CompleteChainAccess"]),
            tolerance_s=CHAIN_INTERVAL_ABS_S,
        )
    except CrossValidationError:
        return
    raise CrossValidationError("MaxUses=0 did not change complete chain intervals")


@pytest.mark.calibration
@pytest.mark.xfail(
    reason="ChainCompute currently returns unchanged single-route intervals even for inconsistent MinUses/MaxUses values.",
    raises=CrossValidationError,
    strict=True,
)
def test_connection_min_uses_max_uses_inconsistent_expected_to_change_intervals() -> None:
    configure_astrox_from_env()
    chain_result, ground, relay, target = relay_chain()
    constrained = access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, relay, target],
        start_participant=ground,
        end_participant=target,
        connections=[
            access.connection(ground, relay, min_uses=2, max_uses=1),
            access.connection(relay, target, min_uses=2, max_uses=1),
        ],
        use_light_time_delay=True,
    )
    try:
        compare_intervals(
            intervals_from_chain(chain_result["CompleteChainAccess"]),
            intervals_from_chain(constrained["CompleteChainAccess"]),
            tolerance_s=CHAIN_INTERVAL_ABS_S,
        )
    except CrossValidationError:
        return
    raise CrossValidationError("inconsistent MinUses/MaxUses did not change complete chain intervals")
