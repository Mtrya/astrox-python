"""Access analysis functions and access-owned chain fragments."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from astrox import components
from astrox._http import raw

__all__ = [
    "Connection",
    "chain",
    "compute",
    "connection",
]


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _entity_to_wire(entity: components.Entity, *, parameter: str) -> dict[str, Any]:
    if not isinstance(entity, components.Entity):
        raise TypeError(f"{parameter} must be an astrox.components.Entity value")
    return entity.to_wire()


def _participant_name(
    value: components.Entity | components.EntityGroup | str,
    *,
    parameter: str,
) -> str:
    if isinstance(value, components.Entity):
        return value.name
    if isinstance(value, components.EntityGroup):
        return value.name
    if isinstance(value, str):
        return value
    raise TypeError(f"{parameter} must be an Entity, EntityGroup, or string name")


def _participant_to_wire(
    value: components.Entity | components.EntityGroup,
    *,
    parameter: str,
) -> dict[str, Any]:
    if isinstance(value, components.Entity):
        return {"$type": "EntityPath", **value.to_wire()}
    if isinstance(value, components.EntityGroup):
        return value.to_wire()
    raise TypeError(f"{parameter} items must be Entity or EntityGroup values")


def _participants_to_wire(
    values: Sequence[components.Entity | components.EntityGroup],
) -> list[dict[str, Any]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("participants must be a sequence of Entity or EntityGroup values")
    return [
        _participant_to_wire(value, parameter="participants")
        for value in values
    ]


def _connections_to_wire(values: Sequence[Connection]) -> list[dict[str, Any]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("connections must be a sequence of Connection values")
    items = list(values)
    if not all(isinstance(item, Connection) for item in items):
        raise TypeError("connections must be a sequence of Connection values")
    return [item.to_wire() for item in items]


@dataclass(frozen=True, kw_only=True)
class Connection:
    """Explicit access-chain connection between named participants."""

    from_participant: components.Entity | components.EntityGroup | str
    to_participant: components.Entity | components.EntityGroup | str
    min_uses: int | None = None
    max_uses: int | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX LinkConnection fragment."""
        payload: dict[str, Any] = {
            "FromObject": _participant_name(
                self.from_participant,
                parameter="from_participant",
            ),
            "ToObject": _participant_name(
                self.to_participant,
                parameter="to_participant",
            ),
        }
        _include_if_supplied(payload, "MinUses", self.min_uses)
        _include_if_supplied(payload, "MaxUses", self.max_uses)
        return payload


def connection(
    from_participant: components.Entity | components.EntityGroup | str,
    to_participant: components.Entity | components.EntityGroup | str,
    *,
    min_uses: int | None = None,
    max_uses: int | None = None,
) -> Connection:
    """Create an explicit access-chain connection fragment."""
    _participant_name(from_participant, parameter="from_participant")
    _participant_name(to_participant, parameter="to_participant")
    return Connection(
        from_participant=from_participant,
        to_participant=to_participant,
        min_uses=min_uses,
        max_uses=max_uses,
    )


def compute(
    *,
    start: str,
    stop: str,
    from_entity: components.Entity,
    to_entity: components.Entity,
    step_s: float | None = None,
    compute_aer: bool | None = None,
    use_light_time_delay: bool | None = None,
) -> dict[str, Any]:
    """Compute direct access between two entities."""
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "FromObjectPath": _entity_to_wire(from_entity, parameter="from_entity"),
        "ToObjectPath": _entity_to_wire(to_entity, parameter="to_entity"),
    }
    _include_if_supplied(payload, "OutStep", step_s)
    _include_if_supplied(payload, "ComputeAER", compute_aer)
    _include_if_supplied(payload, "UseLightTimeDelay", use_light_time_delay)

    return raw.post("/access/AccessComputeV2", json=payload)


def chain(
    *,
    start: str,
    stop: str,
    participants: Sequence[components.Entity | components.EntityGroup],
    start_participant: components.Entity | components.EntityGroup | str,
    end_participant: components.Entity | components.EntityGroup | str,
    connections: Sequence[Connection] | None = None,
    use_light_time_delay: bool | None = None,
) -> dict[str, Any]:
    """Compute access over a named direct or multi-hop participant chain."""
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "AllObjects": _participants_to_wire(participants),
        "StartObject": _participant_name(
            start_participant,
            parameter="start_participant",
        ),
        "EndObject": _participant_name(end_participant, parameter="end_participant"),
        "Connections": (
            _connections_to_wire(connections)
            if connections is not None
            else None
        ),
    }
    _include_if_supplied(payload, "UseLightTimeDelay", use_light_time_delay)

    return raw.post("/access/ChainCompute", json=payload)
