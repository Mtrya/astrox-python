"""Axes component value objects."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING, TypeAlias

from ._common import (
    _axes_type,
    _include_axes_metadata,
    _include_if_supplied,
    _number_sequence_to_list,
    _optional_string,
    _string,
    _typed_tuple,
    _validate_axis_direction,
    _validate_relative_to,
)
from ._rotations import Rotation, _rotation_to_wire

if TYPE_CHECKING:
    from ._vgt import VgtVector


def _vector_reference_name(value: VgtVector | str, *, parameter: str) -> str:
    from ._vgt import _VGT_VECTOR_TYPES

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
            "Intervals": [interval.to_wire() for interval in self.intervals],
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


def _axes_to_wire(axes: EntityAxes) -> dict[str, Any]:
    if not isinstance(axes, _AXES_TYPES):
        raise TypeError("axes must be an astrox.components axes value")
    return axes.to_wire()


def _axes_reference_name(value: EntityAxes | str, *, parameter: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, _AXES_TYPES):
        if value.name is None:
            raise TypeError(
                f"{parameter} object must have a name before it can be referenced"
            )
        return value.name
    raise TypeError(f"{parameter} must be an astrox.components axes value or string name")


def _axes_tuple(
    values: Sequence[EntityAxes], *, parameter: str
) -> tuple[EntityAxes, ...]:
    return _typed_tuple(values, _AXES_TYPES, parameter=parameter)
