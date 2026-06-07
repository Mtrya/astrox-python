"""Public entity, position-source, and sensor value objects."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from astrox.orbits import KeplerianElements

__all__ = [
    "ConicSensor",
    "CzmlPosition",
    "Entity",
    "EntityPosition",
    "EntitySensor",
    "J2Position",
    "RectangularSensor",
    "Sgp4Position",
    "SitePosition",
    "TwoBodyPosition",
    "conic_sensor",
    "czml_position",
    "entity",
    "j2_position",
    "rectangular_sensor",
    "sgp4_position",
    "site_position",
    "two_body_position",
]


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _number_sequence_to_list(value: Sequence[float], *, parameter: str) -> list[float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    return list(value)


def _tle_lines_to_list(value: tuple[str, str] | list[str]) -> list[str]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or not all(isinstance(line, str) for line in value)
    ):
        raise TypeError("tle_lines must be a two-item sequence of TLE strings")
    return list(value)


def _orbit_elements_to_wire(orbit: KeplerianElements, *, parameter: str) -> list[float]:
    if not isinstance(orbit, KeplerianElements):
        raise TypeError(f"{parameter} must be a KeplerianElements instance")
    return orbit.to_wire()


@dataclass(frozen=True, kw_only=True)
class SitePosition:
    """Fixed geodetic site position."""

    longitude_deg: float
    latitude_deg: float
    height_m: float
    central_body: str | None = None
    clamp_to_ground: bool | None = None
    height_above_ground_m: float | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        return {"$type": "SitePosition", **self.to_site_wire()}

    def to_site_wire(self) -> dict[str, Any]:
        """Lower to ASTROX site-only position shape."""
        payload: dict[str, Any] = {
            "cartographicDegrees": [
                self.longitude_deg,
                self.latitude_deg,
                self.height_m,
            ],
        }
        _include_if_supplied(payload, "CentralBody", self.central_body)
        _include_if_supplied(payload, "clampToGround", self.clamp_to_ground)
        _include_if_supplied(payload, "HeightAboveGround", self.height_above_ground_m)
        return payload


@dataclass(frozen=True, kw_only=True)
class CzmlPosition:
    """CZML-like sampled position source."""

    epoch: str
    central_body: str | None = None
    interpolation_algorithm: str | None = None
    interpolation_degree: int | None = None
    reference_frame: str | None = None
    interval: str | None = None
    cartesian: tuple[float, ...] | None = None
    cartesian_velocity: tuple[float, ...] | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {"$type": "CzmlPosition", "epoch": self.epoch}
        _include_if_supplied(payload, "CentralBody", self.central_body)
        _include_if_supplied(
            payload,
            "interpolationAlgorithm",
            self.interpolation_algorithm,
        )
        _include_if_supplied(payload, "interpolationDegree", self.interpolation_degree)
        _include_if_supplied(payload, "referenceFrame", self.reference_frame)
        _include_if_supplied(payload, "interval", self.interval)
        if self.cartesian is not None:
            payload["cartesian"] = list(self.cartesian)
        if self.cartesian_velocity is not None:
            payload["cartesianVelocity"] = list(self.cartesian_velocity)
        return payload


@dataclass(frozen=True, kw_only=True)
class J2Position:
    """J2-propagated Keplerian position source."""

    orbit_epoch: str
    orbit: KeplerianElements
    start: str | None = None
    stop: str | None = None
    step_s: float | None = None
    central_body: str | None = None
    gravitational_parameter_m3_s2: float | None = None
    coord_system: str | None = None
    j2_normalized_value: float | None = None
    ref_distance_m: float | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {
            "$type": "J2",
            "OrbitEpoch": self.orbit_epoch,
            "CoordType": "Classical",
            "OrbitalElements": _orbit_elements_to_wire(self.orbit, parameter="orbit"),
        }
        _include_if_supplied(payload, "Start", self.start)
        _include_if_supplied(payload, "Stop", self.stop)
        _include_if_supplied(payload, "Step", self.step_s)
        _include_if_supplied(payload, "CentralBody", self.central_body)
        _include_if_supplied(
            payload,
            "GravitationalParameter",
            self.gravitational_parameter_m3_s2,
        )
        _include_if_supplied(payload, "CoordSystem", self.coord_system)
        _include_if_supplied(payload, "J2NormalizedValue", self.j2_normalized_value)
        _include_if_supplied(payload, "RefDistance", self.ref_distance_m)
        return payload


@dataclass(frozen=True, kw_only=True)
class TwoBodyPosition:
    """Two-body propagated Keplerian position source."""

    orbit_epoch: str
    orbit: KeplerianElements
    start: str | None = None
    stop: str | None = None
    step_s: float | None = None
    central_body: str | None = None
    gravitational_parameter_m3_s2: float | None = None
    coord_system: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {
            "$type": "TwoBody",
            "OrbitEpoch": self.orbit_epoch,
            "CoordType": "Classical",
            "OrbitalElements": _orbit_elements_to_wire(self.orbit, parameter="orbit"),
        }
        _include_if_supplied(payload, "Start", self.start)
        _include_if_supplied(payload, "Stop", self.stop)
        _include_if_supplied(payload, "Step", self.step_s)
        _include_if_supplied(payload, "CentralBody", self.central_body)
        _include_if_supplied(
            payload,
            "GravitationalParameter",
            self.gravitational_parameter_m3_s2,
        )
        _include_if_supplied(payload, "CoordSystem", self.coord_system)
        return payload


@dataclass(frozen=True, kw_only=True)
class Sgp4Position:
    """SGP4 TLE position source."""

    tle_lines: tuple[str, str]
    start: str | None = None
    stop: str | None = None
    step_s: float | None = None
    satellite_number: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {
            "$type": "SGP4",
            "TLEs": list(self.tle_lines),
        }
        _include_if_supplied(payload, "Start", self.start)
        _include_if_supplied(payload, "Stop", self.stop)
        _include_if_supplied(payload, "Step", self.step_s)
        _include_if_supplied(payload, "SatelliteNumber", self.satellite_number)
        return payload


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


EntityPosition: TypeAlias = (
    SitePosition | CzmlPosition | J2Position | TwoBodyPosition | Sgp4Position
)
EntitySensor: TypeAlias = ConicSensor | RectangularSensor

_POSITION_TYPES = (SitePosition, CzmlPosition, J2Position, TwoBodyPosition, Sgp4Position)
_SENSOR_TYPES = (ConicSensor, RectangularSensor)


@dataclass(frozen=True, kw_only=True)
class Entity:
    """Named ASTROX analysis object composed from a position source and metadata."""

    name: str
    position: EntityPosition
    description: str | None = None
    sensor: EntitySensor | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the common ASTROX entity body."""
        payload: dict[str, Any] = {
            "Name": self.name,
            "Position": _position_to_wire(self.position),
        }
        _include_if_supplied(payload, "Description", self.description)
        if self.sensor is not None:
            payload["Sensor"] = _sensor_to_wire(self.sensor)
        return payload


def site_position(
    *,
    longitude_deg: float,
    latitude_deg: float,
    height_m: float,
    central_body: str | None = None,
    clamp_to_ground: bool | None = None,
    height_above_ground_m: float | None = None,
) -> SitePosition:
    """Create a fixed geodetic site position."""
    return SitePosition(
        longitude_deg=longitude_deg,
        latitude_deg=latitude_deg,
        height_m=height_m,
        central_body=central_body,
        clamp_to_ground=clamp_to_ground,
        height_above_ground_m=height_above_ground_m,
    )


def czml_position(
    *,
    epoch: str,
    central_body: str | None = None,
    interpolation_algorithm: str | None = None,
    interpolation_degree: int | None = None,
    reference_frame: str | None = None,
    interval: str | None = None,
    cartesian: Sequence[float] | None = None,
    cartesian_velocity: Sequence[float] | None = None,
) -> CzmlPosition:
    """Create a CZML-like sampled position source."""
    return CzmlPosition(
        epoch=epoch,
        central_body=central_body,
        interpolation_algorithm=interpolation_algorithm,
        interpolation_degree=interpolation_degree,
        reference_frame=reference_frame,
        interval=interval,
        cartesian=tuple(_number_sequence_to_list(cartesian, parameter="cartesian"))
        if cartesian is not None
        else None,
        cartesian_velocity=tuple(
            _number_sequence_to_list(cartesian_velocity, parameter="cartesian_velocity")
        )
        if cartesian_velocity is not None
        else None,
    )


def j2_position(
    *,
    orbit_epoch: str,
    orbit: KeplerianElements,
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
    j2_normalized_value: float | None = None,
    ref_distance_m: float | None = None,
) -> J2Position:
    """Create a J2-propagated Keplerian position source."""
    _orbit_elements_to_wire(orbit, parameter="orbit")
    return J2Position(
        orbit_epoch=orbit_epoch,
        orbit=orbit,
        start=start,
        stop=stop,
        step_s=step_s,
        central_body=central_body,
        gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        coord_system=coord_system,
        j2_normalized_value=j2_normalized_value,
        ref_distance_m=ref_distance_m,
    )


def two_body_position(
    *,
    orbit_epoch: str,
    orbit: KeplerianElements,
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
) -> TwoBodyPosition:
    """Create a two-body propagated Keplerian position source."""
    _orbit_elements_to_wire(orbit, parameter="orbit")
    return TwoBodyPosition(
        orbit_epoch=orbit_epoch,
        orbit=orbit,
        start=start,
        stop=stop,
        step_s=step_s,
        central_body=central_body,
        gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        coord_system=coord_system,
    )


def sgp4_position(
    *,
    tle_lines: tuple[str, str] | list[str],
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    satellite_number: str | None = None,
) -> Sgp4Position:
    """Create an SGP4 TLE position source."""
    return Sgp4Position(
        tle_lines=tuple(_tle_lines_to_list(tle_lines)),
        start=start,
        stop=stop,
        step_s=step_s,
        satellite_number=satellite_number,
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


def entity(
    *,
    name: str,
    position: EntityPosition,
    description: str | None = None,
    sensor: EntitySensor | None = None,
) -> Entity:
    """Create a named ASTROX analysis object."""
    if not isinstance(position, _POSITION_TYPES):
        raise TypeError("position must be an astrox.entities position value")
    if sensor is not None and not isinstance(sensor, _SENSOR_TYPES):
        raise TypeError("sensor must be an astrox.entities sensor value")
    return Entity(
        name=name,
        position=position,
        description=description,
        sensor=sensor,
    )


def _position_to_wire(position: EntityPosition) -> dict[str, Any]:
    if not isinstance(position, _POSITION_TYPES):
        raise TypeError("position must be an astrox.entities position value")
    return position.to_wire()


def _site_position_to_wire(position: SitePosition) -> dict[str, Any]:
    if not isinstance(position, SitePosition):
        raise TypeError("site_position must be an astrox.entities.SitePosition value")
    return position.to_site_wire()


def _sensor_to_wire(sensor: EntitySensor) -> dict[str, Any]:
    if not isinstance(sensor, _SENSOR_TYPES):
        raise TypeError("sensor must be an astrox.entities sensor value")
    return sensor.to_wire()
