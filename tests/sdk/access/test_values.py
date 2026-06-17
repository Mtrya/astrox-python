"""Focused tests for access-owned value fragments."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from astrox import access, components
from tests.sdk.helpers import assert_canonical_equal


TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def ground() -> components.Entity:
    return components.entity(
        name="Ground",
        position=components.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
    )


def iss() -> components.Entity:
    return components.entity(
        name="ISS",
        position=components.sgp4_position(tle_lines=TLE_LINES),
    )


def test_public_access_value_names_are_exported() -> None:
    assert "Connection" in access.__all__
    assert "chain" in access.__all__
    assert "compute" in access.__all__
    assert "connection" in access.__all__
    assert "AccessParticipant" not in access.__all__
    assert "AccessParticipantRef" not in access.__all__
    assert "EntityGroup" in components.__all__
    assert "entity_group" in components.__all__


def test_connection_lowers_participants_to_name_references() -> None:
    target_group = components.entity_group(name="Targets", members=[iss()])

    link = access.connection(
        ground(),
        target_group,
        min_uses=0,
        max_uses=2,
    )

    assert is_dataclass(link)
    assert isinstance(link, access.Connection)
    assert_canonical_equal(
        link.to_wire(),
        {
            "FromObject": "Ground",
            "ToObject": "Targets",
            "MinUses": 0,
            "MaxUses": 2,
        },
    )

    with pytest.raises(FrozenInstanceError):
        link.max_uses = 3


def test_connection_accepts_string_references_without_local_resolution() -> None:
    link = access.connection("Ground", "ISS")

    assert_canonical_equal(
        link.to_wire(),
        {
            "FromObject": "Ground",
            "ToObject": "ISS",
        },
    )


def test_connection_rejects_values_that_cannot_lower_to_names() -> None:
    with pytest.raises(TypeError, match="from_participant must be an Entity, EntityGroup, or string name"):
        access.connection({"Name": "Ground"}, iss())
