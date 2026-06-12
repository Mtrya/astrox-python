"""Public entity, position-source, attitude, and sensor value objects.

ASTROX uses the word ``Orientation`` at two different levels. Entity
``Orientation`` fields are coordinate axes definitions from the ``CrdnAxes``
schema family: VVLH, LVLH, VNC, Fixed, FixedAtEpoch, Composite, and CZML-backed
axes. Sensor pointing and fixed axes then contain smaller Az/El, quaternion, or
Euler-angle orientation fragments. The SDK names those two levels separately:
public constructors and dataclasses use ``Axes`` for entity-level attitude
frames and ``Rotation`` for the inner Az/El, quaternion, or Euler fragments.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any, TypeAlias

from astrox.orbits import CartesianState, KeplerianElements
from astrox.propagator import HpopConfig

__all__ = [
    "AlignedAndConstrainedAxes",
    "AzElRotation",
    "BallisticPosition",
    "CentralBodyPosition",
    "ConicSensor",
    "CompositeAxes",
    "CzmlPosition",
    "CzmlPositionSTM",
    "CzmlPositions",
    "CzmlAxes",
    "Entity",
    "EntityAxes",
    "EntityGroup",
    "EntityPosition",
    "EntitySensor",
    "EulerRotation",
    "FixedAtEpochAxes",
    "FixedAxes",
    "FixedSensorPointing",
    "HpopPosition",
    "J2Position",
    "LvlhAxes",
    "QuaternionRotation",
    "RectangularSensor",
    "Rotation",
    "RaDecDirection",
    "SensorPointing",
    "Sgp4Position",
    "SitePosition",
    "SimpleAscentPosition",
    "TwoBodyPosition",
    "VgtAngle",
    "VgtDirection",
    "VgtFixedVector",
    "VgtPlane",
    "VgtPoint",
    "VgtProvider",
    "VgtSystem",
    "VgtVector",
    "VncAxes",
    "VvlhAxes",
    "XyzDirection",
    "aligned_and_constrained_axes",
    "az_el_rotation",
    "ballistic_position",
    "central_body_position",
    "conic_sensor",
    "composite_axes",
    "czml_position",
    "czml_positions",
    "czml_axes",
    "entity",
    "entity_group",
    "euler_rotation",
    "fixed_axes",
    "fixed_at_epoch_axes",
    "fixed_sensor_pointing",
    "hpop_position",
    "j2_position",
    "lvlh_axes",
    "quaternion_rotation",
    "ra_dec_direction",
    "rectangular_sensor",
    "vgt",
    "vgt_angle",
    "vgt_fixed_vector",
    "vgt_plane",
    "vgt_point",
    "vgt_system",
    "vnc_axes",
    "vvlh_axes",
    "xyz_direction",
    "sgp4_position",
    "site_position",
    "simple_ascent_position",
    "two_body_position",
]

_GROUP_RESTRICTIONS = {"AnyOf", "AtLeastN"}
_RELATIVE_TO_VALUES = {"Earth", "Moon", "Mars", "Sun", "CBF"}
_AXIS_DIRECTIONS = {"+X", "-X", "+Y", "-Y", "+Z", "-Z"}


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _real_number(value: float, *, parameter: str) -> float:
    if not isinstance(value, Real) or isinstance(value, bool):
        raise TypeError(f"{parameter} must be a number")
    return value


def _string(value: str, *, parameter: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{parameter} must be a string")
    return value


def _optional_string(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    return _string(value, parameter=parameter)


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


def _validate_relative_to(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    if value not in _RELATIVE_TO_VALUES:
        accepted = ", ".join(sorted(_RELATIVE_TO_VALUES))
        raise ValueError(f"{parameter} must be one of: {accepted}")
    return value


def _validate_axis_direction(value: str, *, parameter: str) -> str:
    if value not in _AXIS_DIRECTIONS:
        accepted = ", ".join(sorted(_AXIS_DIRECTIONS))
        raise ValueError(f"{parameter} must be one of: {accepted}")
    return value


def _axes_type(family: str, relative_to: str | None) -> str:
    return family if relative_to is None else f"{family}({relative_to})"


def _include_axes_metadata(
    payload: dict[str, Any],
    *,
    name: str | None,
    description: str | None,
    start: str | None,
    stop: str | None,
) -> None:
    _include_if_supplied(payload, "Name", name)
    _include_if_supplied(payload, "Description", description)
    _include_if_supplied(payload, "Start", start)
    _include_if_supplied(payload, "Stop", stop)


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

    @classmethod
    def from_czml_wire(cls, payload: dict[str, Any]) -> CzmlPosition:
        """Build from an ASTROX CZML position-data payload."""
        cartesian = payload.get("cartesian")
        cartesian_velocity = payload.get("cartesianVelocity")
        return cls(
            epoch=payload["epoch"],
            central_body=payload.get("CentralBody"),
            interpolation_algorithm=payload.get("interpolationAlgorithm"),
            interpolation_degree=payload.get("interpolationDegree"),
            reference_frame=payload.get("referenceFrame"),
            interval=payload.get("interval"),
            cartesian=None if cartesian is None else tuple(cartesian),
            cartesian_velocity=None
            if cartesian_velocity is None
            else tuple(cartesian_velocity),
        )


@dataclass(frozen=True, kw_only=True)
class CzmlPositionSTM(CzmlPosition):
    """CZML position sample augmented with STM-like orientation and translation."""

    unit_quaternion: tuple[float, ...]
    cartesian_translation: tuple[float, ...] | None = None

    @classmethod
    def from_czml_wire(cls, payload: dict[str, Any]) -> CzmlPositionSTM:
        """Build from the ASTROX CzmlPositionSTM payload."""
        cartesian_velocity = payload.get("cartesianVelocity")
        cartesian_translation = payload.get("cartesianTranslation")
        return cls(
            epoch=payload["epoch"],
            central_body=payload.get("CentralBody"),
            interpolation_algorithm=payload.get("interpolationAlgorithm"),
            interpolation_degree=payload.get("interpolationDegree"),
            reference_frame=payload["referenceFrame"],
            interval=payload.get("interval"),
            cartesian=tuple(payload["cartesian"]),
            cartesian_velocity=None
            if cartesian_velocity is None
            else tuple(cartesian_velocity),
            unit_quaternion=tuple(payload["unitQuaternion"]),
            cartesian_translation=None
            if cartesian_translation is None
            else tuple(cartesian_translation),
        )


@dataclass(frozen=True, kw_only=True)
class CzmlPositions:
    """Composite CZML-like sampled position source."""

    positions: tuple[CzmlPosition, ...]
    central_body: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to a typed ASTROX generic entity-position fragment."""
        payload: dict[str, Any] = {
            "$type": "CzmlPositions",
            "CzmlPositions": [position.to_czml_wire() for position in self.positions],
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
class AzElRotation:
    """Azimuth/elevation rotation fragment."""

    azimuth_deg: float
    elevation_deg: float

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX AzEl orientation fragment."""
        return {
            "$type": "AzEl",
            "Azimuth": self.azimuth_deg,
            "Elevation": self.elevation_deg,
        }


@dataclass(frozen=True, kw_only=True)
class QuaternionRotation:
    """Quaternion rotation fragment using scalar-first Python arguments."""

    scalar: float
    x: float
    y: float
    z: float

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX quaternion orientation fragment."""
        return {
            "$type": "Quaternion",
            "QS": self.scalar,
            "QX": self.x,
            "QY": self.y,
            "QZ": self.z,
        }


@dataclass(frozen=True, kw_only=True)
class EulerRotation:
    """Euler-angle rotation fragment."""

    sequence: str
    a_deg: float
    b_deg: float
    c_deg: float

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX EulerAngles orientation fragment."""
        return {
            "$type": "EulerAngles",
            "Sequence": self.sequence,
            "A": self.a_deg,
            "B": self.b_deg,
            "C": self.c_deg,
        }


Rotation: TypeAlias = AzElRotation | QuaternionRotation | EulerRotation
_ROTATION_TYPES = (AzElRotation, QuaternionRotation, EulerRotation)


@dataclass(frozen=True, kw_only=True)
class VvlhAxes:
    """Entity attitude axes using ASTROX VVLH variants."""

    relative_to: str | None = None
    name: str | None = None
    description: str | None = None
    start: str | None = None
    stop: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX VVLH CrdnAxes fragment."""
        payload: dict[str, Any] = {"$type": _axes_type("VVLH", self.relative_to)}
        _include_axes_metadata(
            payload,
            name=self.name,
            description=self.description,
            start=self.start,
            stop=self.stop,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class LvlhAxes:
    """Entity attitude axes using ASTROX LVLH variants."""

    relative_to: str | None = None
    name: str | None = None
    description: str | None = None
    start: str | None = None
    stop: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX LVLH CrdnAxes fragment."""
        payload: dict[str, Any] = {"$type": _axes_type("LVLH", self.relative_to)}
        _include_axes_metadata(
            payload,
            name=self.name,
            description=self.description,
            start=self.start,
            stop=self.stop,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class VncAxes:
    """Entity attitude axes using ASTROX VNC variants."""

    relative_to: str | None = None
    name: str | None = None
    description: str | None = None
    start: str | None = None
    stop: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX VNC CrdnAxes fragment."""
        payload: dict[str, Any] = {"$type": _axes_type("VNC", self.relative_to)}
        _include_axes_metadata(
            payload,
            name=self.name,
            description=self.description,
            start=self.start,
            stop=self.stop,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class FixedAxes:
    """Entity attitude axes fixed relative to named reference axes."""

    reference_axes: EntityAxes | str
    rotation: Rotation
    name: str | None = None
    description: str | None = None
    start: str | None = None
    stop: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX Fixed CrdnAxes fragment."""
        payload: dict[str, Any] = {
            "$type": "Fixed",
            "FixedOrientation": _rotation_to_wire(self.rotation),
            "ReferenceAxesName": _axes_reference_name(
                self.reference_axes,
                parameter="reference_axes",
            ),
        }
        _include_axes_metadata(
            payload,
            name=self.name,
            description=self.description,
            start=self.start,
            stop=self.stop,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class FixedAtEpochAxes:
    """Entity attitude axes frozen between source and reference axes at an epoch."""

    source_axes: EntityAxes | str
    reference_axes: EntityAxes | str
    epoch: str
    name: str | None = None
    description: str | None = None
    start: str | None = None
    stop: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX FixedAtEpoch CrdnAxes fragment."""
        payload: dict[str, Any] = {
            "$type": "FixedAtEpoch",
            "SourceAxesName": _axes_reference_name(
                self.source_axes,
                parameter="source_axes",
            ),
            "ReferenceAxesName": _axes_reference_name(
                self.reference_axes,
                parameter="reference_axes",
            ),
            "Epoch": self.epoch,
        }
        _include_axes_metadata(
            payload,
            name=self.name,
            description=self.description,
            start=self.start,
            stop=self.stop,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class AlignedAndConstrainedAxes:
    """Entity attitude axes aligned and constrained by named vectors."""

    principal: VgtVector | str
    principal_axis: str
    reference: VgtVector | str
    reference_axis: str
    name: str | None = None
    description: str | None = None
    start: str | None = None
    stop: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX AlignedAndConstrained CrdnAxes fragment."""
        payload: dict[str, Any] = {
            "$type": "AlignedAndConstrained",
            "Principal": _vector_reference_name(
                self.principal,
                parameter="principal",
            ),
            "PrincipalAxis": self.principal_axis,
            "Reference": _vector_reference_name(
                self.reference,
                parameter="reference",
            ),
            "ReferenceAxis": self.reference_axis,
        }
        _include_axes_metadata(
            payload,
            name=self.name,
            description=self.description,
            start=self.start,
            stop=self.stop,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class CompositeAxes:
    """Entity attitude axes made from multiple axes intervals."""

    intervals: tuple[EntityAxes, ...]
    name: str | None = None
    description: str | None = None
    start: str | None = None
    stop: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX Composite CrdnAxes fragment."""
        payload: dict[str, Any] = {
            "$type": "Composite",
            "Intervals": [
                interval.to_wire()
                for interval in self.intervals
            ],
        }
        _include_axes_metadata(
            payload,
            name=self.name,
            description=self.description,
            start=self.start,
            stop=self.stop,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class CzmlAxes:
    """Entity attitude axes from CZML unit-quaternion samples."""

    epoch: str
    unit_quaternion_xyzw: tuple[float, ...]
    central_body: str | None = None
    interpolation_algorithm: str | None = None
    interpolation_degree: int | None = None
    name: str | None = None
    description: str | None = None
    start: str | None = None
    stop: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX CzmlOrientation CrdnAxes fragment."""
        payload: dict[str, Any] = {
            "$type": "CzmlOrientation",
            "epoch": self.epoch,
            "unitQuaternion": list(self.unit_quaternion_xyzw),
        }
        _include_if_supplied(payload, "CentralBody", self.central_body)
        _include_if_supplied(
            payload,
            "interpolationAlgorithm",
            self.interpolation_algorithm,
        )
        _include_if_supplied(payload, "interpolationDegree", self.interpolation_degree)
        _include_axes_metadata(
            payload,
            name=self.name,
            description=self.description,
            start=self.start,
            stop=self.stop,
        )
        return payload


EntityAxes: TypeAlias = (
    VvlhAxes
    | LvlhAxes
    | VncAxes
    | FixedAxes
    | FixedAtEpochAxes
    | AlignedAndConstrainedAxes
    | CompositeAxes
    | CzmlAxes
)
_AXES_TYPES = (
    VvlhAxes,
    LvlhAxes,
    VncAxes,
    FixedAxes,
    FixedAtEpochAxes,
    AlignedAndConstrainedAxes,
    CompositeAxes,
    CzmlAxes,
)


@dataclass(frozen=True, kw_only=True)
class XyzDirection:
    """XYZ direction fragment for named VGT vectors."""

    x: float
    y: float
    z: float

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX XYZ direction fragment."""
        return {"$type": "XYZ", "X": self.x, "Y": self.y, "Z": self.z}


@dataclass(frozen=True, kw_only=True)
class RaDecDirection:
    """Right-ascension/declination direction fragment for named VGT vectors."""

    ra_deg: float
    dec_deg: float
    magnitude: float | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX RADec direction fragment."""
        payload: dict[str, Any] = {
            "$type": "RADec",
            "RA": self.ra_deg,
            "Dec": self.dec_deg,
        }
        _include_if_supplied(payload, "Magnitude", self.magnitude)
        return payload


VgtDirection: TypeAlias = XyzDirection | RaDecDirection
_DIRECTION_TYPES = (XyzDirection, RaDecDirection)


@dataclass(frozen=True, kw_only=True)
class VgtFixedVector:
    """Named VGT vector fixed in reference axes."""

    name: str
    reference_axes: EntityAxes | str
    direction: VgtDirection
    description: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX FixedInAxes vector fragment."""
        payload: dict[str, Any] = {
            "$type": "FixedInAxes",
            "Direction": _direction_to_wire(self.direction),
            "ReferenceAxesName": _axes_reference_name(
                self.reference_axes,
                parameter="reference_axes",
            ),
            "Name": self.name,
        }
        _include_if_supplied(payload, "Description", self.description)
        return payload


VgtVector: TypeAlias = VgtFixedVector
_VGT_VECTOR_TYPES = (VgtFixedVector,)


@dataclass(frozen=True, kw_only=True)
class VgtPoint:
    """Named VGT point definition."""

    name: str
    description: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX VGT point fragment."""
        payload: dict[str, Any] = {"Name": self.name}
        _include_if_supplied(payload, "Description", self.description)
        return payload


@dataclass(frozen=True, kw_only=True)
class VgtSystem:
    """Named VGT coordinate-system definition."""

    name: str
    description: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX VGT system fragment."""
        payload: dict[str, Any] = {"Name": self.name}
        _include_if_supplied(payload, "Description", self.description)
        return payload


@dataclass(frozen=True, kw_only=True)
class VgtAngle:
    """Named VGT angle between two named vectors."""

    name: str
    from_vector: VgtVector | str
    to_vector: VgtVector | str
    description: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX VGT angle fragment."""
        payload: dict[str, Any] = {
            "$type": "BetweenVectors",
            "Name": self.name,
            "FromVectorName": _vector_reference_name(
                self.from_vector,
                parameter="from_vector",
            ),
            "ToVectorName": _vector_reference_name(
                self.to_vector,
                parameter="to_vector",
            ),
        }
        _include_if_supplied(payload, "Description", self.description)
        return payload


@dataclass(frozen=True, kw_only=True)
class VgtPlane:
    """Named VGT plane definition."""

    name: str
    plane_type: str | None = None
    description: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX VGT plane fragment."""
        payload: dict[str, Any] = {"Name": self.name}
        _include_if_supplied(payload, "Description", self.description)
        _include_if_supplied(payload, "Type", self.plane_type)
        return payload


@dataclass(frozen=True, kw_only=True)
class VgtProvider:
    """Named geometry definitions attached to an entity.

    ASTROX exposes this field as ``Vgt``. The SDK keeps the same advanced name
    because VGT definitions are name-reference objects, not general geometry
    math values. ``axes`` are entity attitude frames; ``vectors`` and the other
    collections are named definitions that ASTROX can resolve by name from
    orientation branches such as ``Fixed`` or ``AlignedAndConstrained``.
    """

    axes: tuple[EntityAxes, ...]
    vectors: tuple[VgtVector, ...] | None = None
    points: tuple[VgtPoint, ...] | None = None
    systems: tuple[VgtSystem, ...] | None = None
    angles: tuple[VgtAngle, ...] | None = None
    planes: tuple[VgtPlane, ...] | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX CrdnProvider fragment."""
        payload: dict[str, Any] = {
            "Axes": [
                axes.to_wire()
                for axes in self.axes
            ],
        }
        if self.vectors is not None:
            payload["Vectors"] = [vector.to_wire() for vector in self.vectors]
        if self.points is not None:
            payload["Points"] = [point.to_wire() for point in self.points]
        if self.systems is not None:
            payload["Systems"] = [system.to_wire() for system in self.systems]
        if self.angles is not None:
            payload["Angles"] = [angle.to_wire() for angle in self.angles]
        if self.planes is not None:
            payload["Planes"] = [plane.to_wire() for plane in self.planes]
        return payload


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
    vgt: VgtProvider | None = None
    orientation: EntityAxes | None = None
    sensor: EntitySensor | None = None
    sensor_pointing: SensorPointing | None = None

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


def az_el_rotation(*, azimuth_deg: float, elevation_deg: float) -> AzElRotation:
    """Create an azimuth/elevation rotation fragment."""
    return AzElRotation(
        azimuth_deg=_real_number(azimuth_deg, parameter="azimuth_deg"),
        elevation_deg=_real_number(elevation_deg, parameter="elevation_deg"),
    )


def quaternion_rotation(
    *,
    scalar: float,
    x: float,
    y: float,
    z: float,
) -> QuaternionRotation:
    """Create a quaternion rotation fragment."""
    return QuaternionRotation(
        scalar=_real_number(scalar, parameter="scalar"),
        x=_real_number(x, parameter="x"),
        y=_real_number(y, parameter="y"),
        z=_real_number(z, parameter="z"),
    )


def euler_rotation(
    *,
    sequence: str,
    a_deg: float,
    b_deg: float,
    c_deg: float,
) -> EulerRotation:
    """Create an Euler-angle rotation fragment."""
    return EulerRotation(
        sequence=_string(sequence, parameter="sequence"),
        a_deg=_real_number(a_deg, parameter="a_deg"),
        b_deg=_real_number(b_deg, parameter="b_deg"),
        c_deg=_real_number(c_deg, parameter="c_deg"),
    )


def vvlh_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> VvlhAxes:
    """Create VVLH entity attitude axes."""
    return VvlhAxes(
        relative_to=_validate_relative_to(relative_to, parameter="relative_to"),
        name=_optional_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
        start=_optional_string(start, parameter="start"),
        stop=_optional_string(stop, parameter="stop"),
    )


def lvlh_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> LvlhAxes:
    """Create LVLH entity attitude axes."""
    return LvlhAxes(
        relative_to=_validate_relative_to(relative_to, parameter="relative_to"),
        name=_optional_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
        start=_optional_string(start, parameter="start"),
        stop=_optional_string(stop, parameter="stop"),
    )


def vnc_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> VncAxes:
    """Create VNC entity attitude axes."""
    return VncAxes(
        relative_to=_validate_relative_to(relative_to, parameter="relative_to"),
        name=_optional_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
        start=_optional_string(start, parameter="start"),
        stop=_optional_string(stop, parameter="stop"),
    )


def fixed_axes(
    *,
    reference_axes: EntityAxes | str,
    rotation: Rotation,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> FixedAxes:
    """Create entity attitude axes fixed relative to named reference axes."""
    _axes_reference_name(reference_axes, parameter="reference_axes")
    _rotation_to_wire(rotation)
    return FixedAxes(
        reference_axes=reference_axes,
        rotation=rotation,
        name=_optional_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
        start=_optional_string(start, parameter="start"),
        stop=_optional_string(stop, parameter="stop"),
    )


def fixed_at_epoch_axes(
    *,
    source_axes: EntityAxes | str,
    reference_axes: EntityAxes | str,
    epoch: str,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> FixedAtEpochAxes:
    """Create entity attitude axes fixed at an epoch."""
    _axes_reference_name(source_axes, parameter="source_axes")
    _axes_reference_name(reference_axes, parameter="reference_axes")
    return FixedAtEpochAxes(
        source_axes=source_axes,
        reference_axes=reference_axes,
        epoch=_string(epoch, parameter="epoch"),
        name=_optional_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
        start=_optional_string(start, parameter="start"),
        stop=_optional_string(stop, parameter="stop"),
    )


def aligned_and_constrained_axes(
    *,
    principal: VgtVector | str,
    principal_axis: str,
    reference: VgtVector | str,
    reference_axis: str,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> AlignedAndConstrainedAxes:
    """Create entity attitude axes aligned and constrained by named vectors."""
    _vector_reference_name(principal, parameter="principal")
    _vector_reference_name(reference, parameter="reference")
    return AlignedAndConstrainedAxes(
        principal=principal,
        principal_axis=_validate_axis_direction(
            principal_axis,
            parameter="principal_axis",
        ),
        reference=reference,
        reference_axis=_validate_axis_direction(
            reference_axis,
            parameter="reference_axis",
        ),
        name=_optional_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
        start=_optional_string(start, parameter="start"),
        stop=_optional_string(stop, parameter="stop"),
    )


def composite_axes(
    *,
    intervals: Sequence[EntityAxes],
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> CompositeAxes:
    """Create composite entity attitude axes."""
    return CompositeAxes(
        intervals=_axes_tuple(intervals, parameter="intervals"),
        name=_optional_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
        start=_optional_string(start, parameter="start"),
        stop=_optional_string(stop, parameter="stop"),
    )


def czml_axes(
    *,
    epoch: str,
    unit_quaternion_xyzw: Sequence[float],
    central_body: str | None = None,
    interpolation_algorithm: str | None = None,
    interpolation_degree: int | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> CzmlAxes:
    """Create CZML-sampled entity attitude axes."""
    return CzmlAxes(
        epoch=_string(epoch, parameter="epoch"),
        unit_quaternion_xyzw=tuple(
            _number_sequence_to_list(
                unit_quaternion_xyzw,
                parameter="unit_quaternion_xyzw",
            )
        ),
        central_body=_optional_string(central_body, parameter="central_body"),
        interpolation_algorithm=_optional_string(
            interpolation_algorithm,
            parameter="interpolation_algorithm",
        ),
        interpolation_degree=interpolation_degree,
        name=_optional_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
        start=_optional_string(start, parameter="start"),
        stop=_optional_string(stop, parameter="stop"),
    )


def xyz_direction(*, x: float, y: float, z: float) -> XyzDirection:
    """Create an XYZ direction fragment for a VGT vector."""
    return XyzDirection(
        x=_real_number(x, parameter="x"),
        y=_real_number(y, parameter="y"),
        z=_real_number(z, parameter="z"),
    )


def ra_dec_direction(
    *,
    ra_deg: float,
    dec_deg: float,
    magnitude: float | None = None,
) -> RaDecDirection:
    """Create a right-ascension/declination direction fragment."""
    return RaDecDirection(
        ra_deg=_real_number(ra_deg, parameter="ra_deg"),
        dec_deg=_real_number(dec_deg, parameter="dec_deg"),
        magnitude=_real_number(magnitude, parameter="magnitude")
        if magnitude is not None
        else None,
    )


def vgt_fixed_vector(
    *,
    name: str,
    reference_axes: EntityAxes | str,
    direction: VgtDirection,
    description: str | None = None,
) -> VgtFixedVector:
    """Create a named VGT vector fixed in reference axes."""
    _axes_reference_name(reference_axes, parameter="reference_axes")
    _direction_to_wire(direction)
    return VgtFixedVector(
        name=_string(name, parameter="name"),
        reference_axes=reference_axes,
        direction=direction,
        description=_optional_string(description, parameter="description"),
    )


def vgt_point(*, name: str, description: str | None = None) -> VgtPoint:
    """Create a named VGT point definition."""
    return VgtPoint(
        name=_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
    )


def vgt_system(*, name: str, description: str | None = None) -> VgtSystem:
    """Create a named VGT system definition."""
    return VgtSystem(
        name=_string(name, parameter="name"),
        description=_optional_string(description, parameter="description"),
    )


def vgt_angle(
    *,
    name: str,
    from_vector: VgtVector | str,
    to_vector: VgtVector | str,
    description: str | None = None,
) -> VgtAngle:
    """Create a named VGT angle between two named vectors."""
    _vector_reference_name(from_vector, parameter="from_vector")
    _vector_reference_name(to_vector, parameter="to_vector")
    return VgtAngle(
        name=_string(name, parameter="name"),
        from_vector=from_vector,
        to_vector=to_vector,
        description=_optional_string(description, parameter="description"),
    )


def vgt_plane(
    *,
    name: str,
    plane_type: str | None = None,
    description: str | None = None,
) -> VgtPlane:
    """Create a named VGT plane definition."""
    return VgtPlane(
        name=_string(name, parameter="name"),
        plane_type=_optional_string(plane_type, parameter="plane_type"),
        description=_optional_string(description, parameter="description"),
    )


def vgt(
    *,
    axes: Sequence[EntityAxes],
    vectors: Sequence[VgtVector] | None = None,
    points: Sequence[VgtPoint] | None = None,
    systems: Sequence[VgtSystem] | None = None,
    angles: Sequence[VgtAngle] | None = None,
    planes: Sequence[VgtPlane] | None = None,
) -> VgtProvider:
    """Create a VGT provider for named entity geometry definitions."""
    return VgtProvider(
        axes=_axes_tuple(axes, parameter="axes"),
        vectors=_typed_tuple(vectors, _VGT_VECTOR_TYPES, parameter="vectors")
        if vectors is not None
        else None,
        points=_typed_tuple(points, (VgtPoint,), parameter="points")
        if points is not None
        else None,
        systems=_typed_tuple(systems, (VgtSystem,), parameter="systems")
        if systems is not None
        else None,
        angles=_typed_tuple(angles, (VgtAngle,), parameter="angles")
        if angles is not None
        else None,
        planes=_typed_tuple(planes, (VgtPlane,), parameter="planes")
        if planes is not None
        else None,
    )


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


def entity(
    *,
    name: str,
    position: EntityPosition,
    description: str | None = None,
    vgt: VgtProvider | None = None,
    orientation: EntityAxes | None = None,
    sensor: EntitySensor | None = None,
    sensor_pointing: SensorPointing | None = None,
) -> Entity:
    """Create a named ASTROX analysis object."""
    if not isinstance(position, _POSITION_TYPES):
        raise TypeError("position must be an astrox.entities position value")
    if vgt is not None and not isinstance(vgt, VgtProvider):
        raise TypeError("vgt must be an astrox.entities.VgtProvider value")
    if orientation is not None and not isinstance(orientation, _AXES_TYPES):
        raise TypeError("orientation must be an astrox.entities axes value")
    if sensor is not None and not isinstance(sensor, _SENSOR_TYPES):
        raise TypeError("sensor must be an astrox.entities sensor value")
    if sensor_pointing is not None and not isinstance(
        sensor_pointing,
        _SENSOR_POINTING_TYPES,
    ):
        raise TypeError(
            "sensor_pointing must be an astrox.entities sensor-pointing value"
        )
    return Entity(
        name=name,
        position=position,
        description=description,
        vgt=vgt,
        orientation=orientation,
        sensor=sensor,
        sensor_pointing=sensor_pointing,
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


def _rotation_to_wire(rotation: Rotation) -> dict[str, Any]:
    if not isinstance(rotation, _ROTATION_TYPES):
        raise TypeError("rotation must be an astrox.entities rotation value")
    return rotation.to_wire()


def _axes_to_wire(axes: EntityAxes) -> dict[str, Any]:
    if not isinstance(axes, _AXES_TYPES):
        raise TypeError("axes must be an astrox.entities axes value")
    return axes.to_wire()


def _vgt_to_wire(provider: VgtProvider) -> dict[str, Any]:
    if not isinstance(provider, VgtProvider):
        raise TypeError("vgt must be an astrox.entities.VgtProvider value")
    return provider.to_wire()


def _sensor_pointing_to_wire(pointing: SensorPointing) -> dict[str, Any]:
    if not isinstance(pointing, _SENSOR_POINTING_TYPES):
        raise TypeError(
            "sensor_pointing must be an astrox.entities sensor-pointing value"
        )
    return pointing.to_wire()


def _direction_to_wire(direction: VgtDirection) -> dict[str, Any]:
    if not isinstance(direction, _DIRECTION_TYPES):
        raise TypeError("direction must be an astrox.entities VGT direction value")
    return direction.to_wire()


def _axes_reference_name(value: EntityAxes | str, *, parameter: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, _AXES_TYPES):
        if value.name is None:
            raise TypeError(f"{parameter} object must have a name before it can be referenced")
        return value.name
    raise TypeError(f"{parameter} must be an astrox.entities axes value or string name")


def _vector_reference_name(value: VgtVector | str, *, parameter: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, _VGT_VECTOR_TYPES):
        if value.name is None:
            raise TypeError(f"{parameter} object must have a name before it can be referenced")
        return value.name
    raise TypeError(f"{parameter} must be an astrox.entities VGT vector value or string name")


def _typed_tuple(
    values: Sequence[Any],
    accepted_types: tuple[type[Any], ...],
    *,
    parameter: str,
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{parameter} must be a sequence")
    items = tuple(values)
    if not all(isinstance(item, accepted_types) for item in items):
        raise TypeError(f"{parameter} contains unsupported item values")
    return items


def _axes_tuple(values: Sequence[EntityAxes], *, parameter: str) -> tuple[EntityAxes, ...]:
    return _typed_tuple(values, _AXES_TYPES, parameter=parameter)
