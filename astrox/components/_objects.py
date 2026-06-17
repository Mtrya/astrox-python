"""Named ASTROX analysis object components."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ._axes import EntityAxes, _AXES_TYPES, _axes_to_wire
from ._common import (
    _include_if_supplied,
    _typed_tuple,
    _validate_group_restriction,
)
from ._constraints import Constraint, _CONSTRAINT_TYPES, _constraint_to_wire
from ._positions import EntityPosition, _POSITION_TYPES, _position_to_wire
from ._sensors import (
    EntitySensor,
    SensorPointing,
    _SENSOR_POINTING_TYPES,
    _SENSOR_TYPES,
    _sensor_pointing_to_wire,
    _sensor_to_wire,
)
from ._vgt import VgtProvider, _vgt_to_wire

def _entities_to_tuple(
    values: Sequence[Entity],
    *,
    parameter: str,
) -> tuple[Entity, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{parameter} must be a sequence of Entity values")
    items = tuple(values)
    if not all(isinstance(item, Entity) for item in items):
        raise TypeError(f"{parameter} must be a sequence of Entity values")
    return items


@dataclass(frozen=True, kw_only=True)
class Entity:
    """Named ASTROX analysis object composed from a position source and metadata."""

    name: str
    position: EntityPosition
    description: str | None = None
    vgt: VgtProvider | None = None
    orientation: EntityAxes | None = None
    sensor: EntitySensor | None = None
    sensor_pointing: SensorPointing | None = None
    constraints: tuple[Constraint, ...] | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the common ASTROX entity body."""
        payload: dict[str, Any] = {
            "Name": self.name,
        }
        _include_if_supplied(payload, "Description", self.description)
        if self.vgt is not None:
            payload["Vgt"] = _vgt_to_wire(self.vgt)
        payload["Position"] = _position_to_wire(self.position)
        if self.orientation is not None:
            payload["Orientation"] = _axes_to_wire(self.orientation)
        if self.sensor is not None:
            payload["Sensor"] = _sensor_to_wire(self.sensor)
        if self.sensor_pointing is not None:
            payload["SensorPointing"] = _sensor_pointing_to_wire(self.sensor_pointing)
        if self.constraints is not None:
            payload["Constraints"] = [
                _constraint_to_wire(constraint) for constraint in self.constraints
            ]
        return payload


@dataclass(frozen=True, kw_only=True)
class EntityGroup:
    """Named entity group for workflows that accept grouped entities."""

    name: str
    members: tuple[Entity, ...]
    from_restriction: str | None = None
    from_number: int | None = None
    to_restriction: str | None = None
    to_number: int | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX EntityPathGroup fragment."""
        payload: dict[str, Any] = {
            "$type": "EntityPathGroup",
            "Name": self.name,
            "AssignedObjects": [member.to_wire() for member in self.members],
        }
        _include_if_supplied(payload, "FromAccess_Restriction", self.from_restriction)
        _include_if_supplied(payload, "FromAccess_Number", self.from_number)
        _include_if_supplied(payload, "ToAccess_Restriction", self.to_restriction)
        _include_if_supplied(payload, "ToAccess_Number", self.to_number)
        return payload


def entity(
    *,
    name: str,
    position: EntityPosition,
    description: str | None = None,
    vgt: VgtProvider | None = None,
    orientation: EntityAxes | None = None,
    sensor: EntitySensor | None = None,
    sensor_pointing: SensorPointing | None = None,
    constraints: Sequence[Constraint] | None = None,
) -> Entity:
    """Create a named ASTROX analysis object."""
    if not isinstance(position, _POSITION_TYPES):
        raise TypeError("position must be an astrox.components position value")
    if vgt is not None and not isinstance(vgt, VgtProvider):
        raise TypeError("vgt must be an astrox.components.VgtProvider value")
    if orientation is not None and not isinstance(orientation, _AXES_TYPES):
        raise TypeError("orientation must be an astrox.components axes value")
    if sensor is not None and not isinstance(sensor, _SENSOR_TYPES):
        raise TypeError("sensor must be an astrox.components sensor value")
    if sensor_pointing is not None and not isinstance(
        sensor_pointing,
        _SENSOR_POINTING_TYPES,
    ):
        raise TypeError(
            "sensor_pointing must be an astrox.components sensor-pointing value"
        )
    constraint_items = (
        _typed_tuple(constraints, _CONSTRAINT_TYPES, parameter="constraints")
        if constraints is not None
        else None
    )
    return Entity(
        name=name,
        position=position,
        description=description,
        vgt=vgt,
        orientation=orientation,
        sensor=sensor,
        sensor_pointing=sensor_pointing,
        constraints=constraint_items,
    )


def entity_group(
    *,
    name: str,
    members: Sequence[Entity],
    from_restriction: str | None = None,
    from_number: int | None = None,
    to_restriction: str | None = None,
    to_number: int | None = None,
) -> EntityGroup:
    """Create a named entity group."""
    return EntityGroup(
        name=name,
        members=_entities_to_tuple(members, parameter="members"),
        from_restriction=_validate_group_restriction(
            from_restriction,
            parameter="from_restriction",
        ),
        from_number=from_number,
        to_restriction=_validate_group_restriction(
            to_restriction,
            parameter="to_restriction",
        ),
        to_number=to_number,
    )
