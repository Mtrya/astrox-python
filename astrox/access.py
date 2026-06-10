"""Access-owned value fragments for access workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from astrox import entities

__all__ = [
    "AccessParticipantRef",
    "Connection",
    "connection",
]


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


AccessParticipantRef: TypeAlias = entities.Entity | entities.EntityGroup | str


def _participant_name(value: AccessParticipantRef, *, parameter: str) -> str:
    if isinstance(value, entities.Entity):
        return value.name
    if isinstance(value, entities.EntityGroup):
        return value.name
    if isinstance(value, str):
        return value
    raise TypeError(f"{parameter} must be an Entity, EntityGroup, or string name")


@dataclass(frozen=True, kw_only=True)
class Connection:
    """Explicit access-chain connection between named participants."""

    from_participant: AccessParticipantRef
    to_participant: AccessParticipantRef
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
    from_participant: AccessParticipantRef,
    to_participant: AccessParticipantRef,
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
