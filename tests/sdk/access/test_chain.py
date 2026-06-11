"""Focused tests for chain access request assembly."""

from __future__ import annotations

from inspect import signature
from typing import Any

import pytest

from astrox import access, entities
from tests.sdk.access.helpers import ground, hubble, iss, record_raw_post
from tests.sdk.helpers import assert_canonical_equal


CHAIN_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "计算成功！",
    "ComputedStrands": [["Ground", "ISS"]],
    "CompleteChainAccess": [],
    "IndividualStrandAccess": {},
    "IndividualObjectAccess": {},
}


def targets() -> entities.EntityGroup:
    return entities.entity_group(
        name="Targets",
        members=[iss(), hubble()],
        to_restriction="AnyOf",
    )


def test_chain_signature_keeps_participant_topology_shape() -> None:
    parameters = signature(access.chain).parameters

    assert "participants" in parameters
    assert "start_participant" in parameters
    assert "end_participant" in parameters
    assert "connections" in parameters
    assert "use_light_time_delay" in parameters
    assert "description" not in parameters
    assert "step_s" not in parameters


def test_chain_emits_definition_table_name_references_and_direct_null_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, CHAIN_RESPONSE)
    target_group = targets()

    response = access.chain(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        participants=[ground(), target_group],
        start_participant=ground(),
        end_participant=target_group,
        use_light_time_delay=True,
    )

    assert response is CHAIN_RESPONSE
    assert calls[0]["endpoint"] == "/access/ChainCompute"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-02T00:00:00.000Z",
            "AllObjects": [
                {
                    "$type": "EntityPath",
                    "Name": "Ground",
                    "Position": {
                        "$type": "SitePosition",
                        "cartographicDegrees": [-155.468, 19.821, 4205.0],
                    },
                },
                {
                    "$type": "EntityPathGroup",
                    "Name": "Targets",
                    "AssignedObjects": [
                        {
                            "Name": "ISS",
                            "Position": {
                                "$type": "SGP4",
                                "TLEs": list(iss().position.tle_lines),
                            },
                        },
                        {
                            "Name": "Hubble",
                            "Position": {
                                "$type": "SGP4",
                                "TLEs": list(hubble().position.tle_lines),
                            },
                        },
                    ],
                    "ToAccess_Restriction": "AnyOf",
                },
            ],
            "StartObject": "Ground",
            "EndObject": "Targets",
            "Connections": None,
            "UseLightTimeDelay": True,
        },
    )


def test_chain_emits_explicit_multi_hop_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, CHAIN_RESPONSE)

    access.chain(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        participants=[ground(), iss(), hubble()],
        start_participant="Ground",
        end_participant="Hubble",
        connections=[
            access.connection("Ground", "ISS"),
            access.connection("ISS", "Hubble", min_uses=0, max_uses=2),
        ],
    )

    assert_canonical_equal(
        calls[0]["json"]["Connections"],
        [
            {
                "FromObject": "Ground",
                "ToObject": "ISS",
            },
            {
                "FromObject": "ISS",
                "ToObject": "Hubble",
                "MinUses": 0,
                "MaxUses": 2,
            },
        ],
    )


def test_chain_preserves_empty_connection_list_when_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, CHAIN_RESPONSE)

    access.chain(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        participants=[ground(), iss()],
        start_participant=ground(),
        end_participant=iss(),
        connections=[],
    )

    assert calls[0]["json"]["Connections"] == []


def test_chain_forwards_string_references_without_local_membership_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, CHAIN_RESPONSE)

    access.chain(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        participants=[ground()],
        start_participant="Ground",
        end_participant="NotInParticipants",
        connections=[
            access.connection("Ground", "AlsoNotInParticipants"),
        ],
    )

    assert calls[0]["json"]["EndObject"] == "NotInParticipants"
    assert_canonical_equal(
        calls[0]["json"]["Connections"],
        [
            {
                "FromObject": "Ground",
                "ToObject": "AlsoNotInParticipants",
            }
        ],
    )


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        (
            {
                "participants": [{"$type": "EntityPath", "Name": "Ground"}],
                "start_participant": "Ground",
                "end_participant": "Ground",
            },
            "participants items must be Entity or EntityGroup values",
        ),
        (
            {
                "participants": "Ground",
                "start_participant": "Ground",
                "end_participant": "Ground",
            },
            "participants must be a sequence of Entity or EntityGroup values",
        ),
        (
            {
                "participants": [ground(), iss()],
                "start_participant": {"Name": "Ground"},
                "end_participant": "ISS",
            },
            "start_participant must be an Entity, EntityGroup, or string name",
        ),
        (
            {
                "participants": [ground(), iss()],
                "start_participant": ground(),
                "end_participant": iss(),
                "connections": [{"FromObject": "Ground", "ToObject": "ISS"}],
            },
            "connections must be a sequence of Connection values",
        ),
    ],
)
def test_chain_rejects_values_that_cannot_lower_to_curated_topology(
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(TypeError, match=match):
        access.chain(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-02T00:00:00.000Z",
            **kwargs,
        )
