"""VGT component value objects."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from ._axes import EntityAxes, _axes_reference_name, _axes_tuple
from ._common import (
    _include_if_supplied,
    _optional_string,
    _real_number,
    _string,
    _typed_tuple,
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
            "Axes": [axes.to_wire() for axes in self.axes],
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


def _vgt_to_wire(provider: VgtProvider) -> dict[str, Any]:
    if not isinstance(provider, VgtProvider):
        raise TypeError("vgt must be an astrox.components.VgtProvider value")
    return provider.to_wire()


def _direction_to_wire(direction: VgtDirection) -> dict[str, Any]:
    if not isinstance(direction, _DIRECTION_TYPES):
        raise TypeError("direction must be an astrox.components VGT direction value")
    return direction.to_wire()


def _vector_reference_name(value: VgtVector | str, *, parameter: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, _VGT_VECTOR_TYPES):
        if value.name is None:
            raise TypeError(
                f"{parameter} object must have a name before it can be referenced"
            )
        return value.name
    raise TypeError(
        f"{parameter} must be an astrox.components VGT vector value or string name"
    )
