"""Sensor component value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from ._common import _include_if_supplied, _optional_string
from ._rotations import Rotation, _rotation_to_wire

@dataclass(frozen=True, kw_only=True)
class FixedSensorPointing:
    """Fixed sensor pointing using a rotation fragment."""

    rotation: Rotation
    text: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX fixed sensor-pointing fragment."""
        payload: dict[str, Any] = {
            "$type": "Fixed",
            "Orientation": _rotation_to_wire(self.rotation),
        }
        _include_if_supplied(payload, "Text", self.text)
        return payload


SensorPointing: TypeAlias = FixedSensorPointing


_SENSOR_POINTING_TYPES = (FixedSensorPointing,)


@dataclass(frozen=True, kw_only=True)
class ConicSensor:
    """Conic sensor shape metadata."""

    inner_half_angle_deg: float | None = None
    outer_half_angle_deg: float | None = None
    minimum_clock_angle_deg: float | None = None
    maximum_clock_angle_deg: float | None = None
    text: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX conic sensor fragment."""
        payload: dict[str, Any] = {"$type": "Conic"}
        _include_if_supplied(payload, "innerHalfAngle", self.inner_half_angle_deg)
        _include_if_supplied(payload, "outerHalfAngle", self.outer_half_angle_deg)
        _include_if_supplied(payload, "minimumClockAngle", self.minimum_clock_angle_deg)
        _include_if_supplied(payload, "maximumClockAngle", self.maximum_clock_angle_deg)
        _include_if_supplied(payload, "Text", self.text)
        return payload


@dataclass(frozen=True, kw_only=True)
class RectangularSensor:
    """Rectangular sensor shape metadata."""

    x_half_angle_deg: float | None = None
    y_half_angle_deg: float | None = None
    text: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX rectangular sensor fragment."""
        payload: dict[str, Any] = {"$type": "Rectangular"}
        _include_if_supplied(payload, "xHalfAngle", self.x_half_angle_deg)
        _include_if_supplied(payload, "yHalfAngle", self.y_half_angle_deg)
        _include_if_supplied(payload, "Text", self.text)
        return payload


EntitySensor: TypeAlias = ConicSensor | RectangularSensor


_SENSOR_TYPES = (ConicSensor, RectangularSensor)


def fixed_sensor_pointing(
    *,
    rotation: Rotation,
    text: str | None = None,
) -> FixedSensorPointing:
    """Create fixed sensor-pointing metadata."""
    _rotation_to_wire(rotation)
    return FixedSensorPointing(
        rotation=rotation,
        text=_optional_string(text, parameter="text"),
    )


def conic_sensor(
    *,
    inner_half_angle_deg: float | None = None,
    outer_half_angle_deg: float | None = None,
    minimum_clock_angle_deg: float | None = None,
    maximum_clock_angle_deg: float | None = None,
    text: str | None = None,
) -> ConicSensor:
    """Create conic sensor metadata."""
    return ConicSensor(
        inner_half_angle_deg=inner_half_angle_deg,
        outer_half_angle_deg=outer_half_angle_deg,
        minimum_clock_angle_deg=minimum_clock_angle_deg,
        maximum_clock_angle_deg=maximum_clock_angle_deg,
        text=text,
    )


def rectangular_sensor(
    *,
    x_half_angle_deg: float | None = None,
    y_half_angle_deg: float | None = None,
    text: str | None = None,
) -> RectangularSensor:
    """Create rectangular sensor metadata."""
    return RectangularSensor(
        x_half_angle_deg=x_half_angle_deg,
        y_half_angle_deg=y_half_angle_deg,
        text=text,
    )


def _sensor_to_wire(sensor: EntitySensor) -> dict[str, Any]:
    if not isinstance(sensor, _SENSOR_TYPES):
        raise TypeError("sensor must be an astrox.components sensor value")
    return sensor.to_wire()


def _sensor_pointing_to_wire(pointing: SensorPointing) -> dict[str, Any]:
    if not isinstance(pointing, _SENSOR_POINTING_TYPES):
        raise TypeError(
            "sensor_pointing must be an astrox.components sensor-pointing value"
        )
    return pointing.to_wire()
