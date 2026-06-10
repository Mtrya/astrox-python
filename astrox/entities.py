"""Public entity, position-source, and sensor value objects."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any, TypeAlias

from astrox.orbits import CartesianState, KeplerianElements
from astrox.propagator import HpopConfig

__all__ = [
    "BallisticPosition",
    "CentralBodyPosition",
    "ConicSensor",
    "CzmlPosition",
    "CzmlPositions",
    "Entity",
    "EntityGroup",
    "EntityPosition",
    "EntitySensor",
    "HpopPosition",
    "J2Position",
    "RectangularSensor",
    "Sgp4Position",
    "SitePosition",
    "SimpleAscentPosition",
    "TwoBodyPosition",
    "ballistic_position",
    "central_body_position",
    "conic_sensor",
    "czml_position",
    "czml_positions",
    "entity",
    "entity_group",
    "hpop_position",
    "j2_position",
    "rectangular_sensor",
    "sgp4_position",
    "site_position",
    "simple_ascent_position",
    "two_body_position",
]

_GROUP_RESTRICTIONS = {"AnyOf", "AtLeastN"}


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _number_sequence_to_list(value: Sequence[float], *, parameter: str) -> list[float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    items = list(value)
    if not all(isinstance(item, Real) and not isinstance(item, bool) for item in items):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    return items


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


def _cartesian_state_to_wire(state: CartesianState, *, parameter: str) -> list[float]:
    if not isinstance(state, CartesianState):
        raise TypeError(f"{parameter} must be a CartesianState instance")
    return state.to_wire()


def _hpop_config_to_wire(
    config: HpopConfig | Mapping[str, Any],
    *,
    parameter: str,
) -> dict[str, Any]:
    if isinstance(config, HpopConfig):
        return config.to_wire()
    if isinstance(config, Mapping):
        return dict(config)
    raise TypeError(f"{parameter} must be an HpopConfig value or mapping fragment")


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


def _validate_group_restriction(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    if value not in _GROUP_RESTRICTIONS:
        accepted = ", ".join(sorted(_GROUP_RESTRICTIONS))
        raise ValueError(f"{parameter} must be one of: {accepted}")
    return value


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
        return {"$type": "CzmlPosition", **self.to_czml_wire()}

    def to_czml_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX CZML position-data fragment."""
        payload: dict[str, Any] = {"epoch": self.epoch}
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
class CzmlPositions:
    """Composite CZML-like sampled position source."""

    positions: tuple[CzmlPosition, ...]
    central_body: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {
            "$type": "CzmlPositions",
            "CzmlPositions": [
                position.to_czml_wire()
                for position in self.positions
            ],
        }
        _include_if_supplied(payload, "CentralBody", self.central_body)
        return payload


@dataclass(frozen=True, kw_only=True)
class CentralBodyPosition:
    """Central-body position source."""

    name: str

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        return {"$type": "CentralBody", "Name": self.name}


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
class HpopPosition:
    """HPOP-propagated position source."""

    start: str
    stop: str
    orbit_epoch: str
    orbital_elements: tuple[float, ...]
    coord_type: str
    config: HpopConfig | Mapping[str, Any] | None = None
    coord_epoch: str | None = None
    coord_system: str | None = None
    gravitational_parameter_m3_s2: float | None = None
    coefficient_of_drag: float | None = None
    area_mass_ratio_drag_m2_kg: float | None = None
    coefficient_of_srp: float | None = None
    area_mass_ratio_srp_m2_kg: float | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {
            "$type": "HPOP",
            "Start": self.start,
            "Stop": self.stop,
            "OrbitEpoch": self.orbit_epoch,
            "CoordType": self.coord_type,
            "OrbitalElements": list(self.orbital_elements),
        }
        _include_if_supplied(payload, "CoordEpoch", self.coord_epoch)
        _include_if_supplied(payload, "CoordSystem", self.coord_system)
        _include_if_supplied(
            payload,
            "GravitationalParameter",
            self.gravitational_parameter_m3_s2,
        )
        _include_if_supplied(payload, "CoefficientOfDrag", self.coefficient_of_drag)
        _include_if_supplied(
            payload,
            "AreaMassRatioDrag",
            self.area_mass_ratio_drag_m2_kg,
        )
        _include_if_supplied(payload, "CoefficientOfSRP", self.coefficient_of_srp)
        _include_if_supplied(
            payload,
            "AreaMassRatioSRP",
            self.area_mass_ratio_srp_m2_kg,
        )
        if self.config is not None:
            payload["HpopPropagator"] = _hpop_config_to_wire(
                self.config,
                parameter="config",
            )
        return payload


@dataclass(frozen=True, kw_only=True)
class SimpleAscentPosition:
    """Simple ascent position source."""

    start: str
    stop: str
    launch_latitude_deg: float
    launch_longitude_deg: float
    launch_altitude_m: float
    burnout_velocity_m_s: float
    burnout_latitude_deg: float
    burnout_longitude_deg: float
    burnout_altitude_m: float
    step_s: float | None = None
    central_body: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {
            "$type": "SimpleAscent",
            "Start": self.start,
            "Stop": self.stop,
            "LaunchLatitude": self.launch_latitude_deg,
            "LaunchLongitude": self.launch_longitude_deg,
            "LaunchAltitude": self.launch_altitude_m,
            "BurnoutVelocity": self.burnout_velocity_m_s,
            "BurnoutLatitude": self.burnout_latitude_deg,
            "BurnoutLongitude": self.burnout_longitude_deg,
            "BurnoutAltitude": self.burnout_altitude_m,
        }
        _include_if_supplied(payload, "Step", self.step_s)
        _include_if_supplied(payload, "CentralBody", self.central_body)
        return payload


@dataclass(frozen=True, kw_only=True)
class BallisticPosition:
    """Ballistic flight position source."""

    start: str
    ballistic_type: str
    ballistic_type_value: float
    step_s: float | None = None
    central_body: str | None = None
    gravitational_parameter_m3_s2: float | None = None
    launch_latitude_deg: float | None = None
    launch_longitude_deg: float | None = None
    launch_altitude_m: float | None = None
    impact_latitude_deg: float | None = None
    impact_longitude_deg: float | None = None
    impact_altitude_m: float | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {
            "$type": "Ballistic",
            "Start": self.start,
            "BallisticType": self.ballistic_type,
            "BallisticTypeValue": self.ballistic_type_value,
        }
        _include_if_supplied(payload, "Step", self.step_s)
        _include_if_supplied(payload, "CentralBody", self.central_body)
        _include_if_supplied(
            payload,
            "GravitationalParameter",
            self.gravitational_parameter_m3_s2,
        )
        _include_if_supplied(payload, "LaunchLatitude", self.launch_latitude_deg)
        _include_if_supplied(payload, "LaunchLongitude", self.launch_longitude_deg)
        _include_if_supplied(payload, "LaunchAltitude", self.launch_altitude_m)
        _include_if_supplied(payload, "ImpactLatitude", self.impact_latitude_deg)
        _include_if_supplied(payload, "ImpactLongitude", self.impact_longitude_deg)
        _include_if_supplied(payload, "ImpactAltitude", self.impact_altitude_m)
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
    SitePosition
    | CzmlPosition
    | CzmlPositions
    | CentralBodyPosition
    | J2Position
    | TwoBodyPosition
    | Sgp4Position
    | HpopPosition
    | SimpleAscentPosition
    | BallisticPosition
)
EntitySensor: TypeAlias = ConicSensor | RectangularSensor

_POSITION_TYPES = (
    SitePosition,
    CzmlPosition,
    CzmlPositions,
    CentralBodyPosition,
    J2Position,
    TwoBodyPosition,
    Sgp4Position,
    HpopPosition,
    SimpleAscentPosition,
    BallisticPosition,
)
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
            "AssignedObjects": [
                member.to_wire()
                for member in self.members
            ],
        }
        _include_if_supplied(payload, "FromAccess_Restriction", self.from_restriction)
        _include_if_supplied(payload, "FromAccess_Number", self.from_number)
        _include_if_supplied(payload, "ToAccess_Restriction", self.to_restriction)
        _include_if_supplied(payload, "ToAccess_Number", self.to_number)
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


def czml_positions(
    positions: Sequence[CzmlPosition],
    *,
    central_body: str | None = None,
) -> CzmlPositions:
    """Create a composite CZML-like sampled position source."""
    if isinstance(positions, (str, bytes)) or not isinstance(positions, Sequence):
        raise TypeError("positions must be a sequence of CzmlPosition values")
    items = tuple(positions)
    if not all(isinstance(position, CzmlPosition) for position in items):
        raise TypeError("positions must be a sequence of CzmlPosition values")
    return CzmlPositions(positions=items, central_body=central_body)


def central_body_position(name: str) -> CentralBodyPosition:
    """Create a central-body position source."""
    return CentralBodyPosition(name=name)


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


def hpop_position(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements | None = None,
    state: CartesianState | None = None,
    config: HpopConfig | Mapping[str, Any] | None = None,
    coord_epoch: str | None = None,
    coord_system: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coefficient_of_drag: float | None = None,
    area_mass_ratio_drag_m2_kg: float | None = None,
    coefficient_of_srp: float | None = None,
    area_mass_ratio_srp_m2_kg: float | None = None,
) -> HpopPosition:
    """Create an HPOP-propagated position source."""
    if (orbit is None) == (state is None):
        raise ValueError("exactly one of orbit or state must be provided")
    if orbit is not None:
        coord_type = "Classical"
        orbital_elements = tuple(_orbit_elements_to_wire(orbit, parameter="orbit"))
    else:
        coord_type = "Cartesian"
        orbital_elements = tuple(_cartesian_state_to_wire(state, parameter="state"))
    if config is not None:
        _hpop_config_to_wire(config, parameter="config")
    return HpopPosition(
        start=start,
        stop=stop,
        orbit_epoch=orbit_epoch,
        orbital_elements=orbital_elements,
        coord_type=coord_type,
        config=config,
        coord_epoch=coord_epoch,
        coord_system=coord_system,
        gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        coefficient_of_drag=coefficient_of_drag,
        area_mass_ratio_drag_m2_kg=area_mass_ratio_drag_m2_kg,
        coefficient_of_srp=coefficient_of_srp,
        area_mass_ratio_srp_m2_kg=area_mass_ratio_srp_m2_kg,
    )


def simple_ascent_position(
    *,
    start: str,
    stop: str,
    launch_latitude_deg: float,
    launch_longitude_deg: float,
    launch_altitude_m: float,
    burnout_velocity_m_s: float,
    burnout_latitude_deg: float,
    burnout_longitude_deg: float,
    burnout_altitude_m: float,
    step_s: float | None = None,
    central_body: str | None = None,
) -> SimpleAscentPosition:
    """Create a simple ascent position source."""
    return SimpleAscentPosition(
        start=start,
        stop=stop,
        launch_latitude_deg=launch_latitude_deg,
        launch_longitude_deg=launch_longitude_deg,
        launch_altitude_m=launch_altitude_m,
        burnout_velocity_m_s=burnout_velocity_m_s,
        burnout_latitude_deg=burnout_latitude_deg,
        burnout_longitude_deg=burnout_longitude_deg,
        burnout_altitude_m=burnout_altitude_m,
        step_s=step_s,
        central_body=central_body,
    )


def ballistic_position(
    *,
    start: str,
    ballistic_type: str,
    ballistic_type_value: float,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_latitude_deg: float | None = None,
    impact_longitude_deg: float | None = None,
    impact_altitude_m: float | None = None,
) -> BallisticPosition:
    """Create a ballistic flight position source."""
    return BallisticPosition(
        start=start,
        ballistic_type=ballistic_type,
        ballistic_type_value=ballistic_type_value,
        step_s=step_s,
        central_body=central_body,
        gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        launch_latitude_deg=launch_latitude_deg,
        launch_longitude_deg=launch_longitude_deg,
        launch_altitude_m=launch_altitude_m,
        impact_latitude_deg=impact_latitude_deg,
        impact_longitude_deg=impact_longitude_deg,
        impact_altitude_m=impact_altitude_m,
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
