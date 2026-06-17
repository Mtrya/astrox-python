"""Constraint component value objects."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from ._common import _include_if_supplied, _number_sequence_to_list

@dataclass(frozen=True, kw_only=True)
class ElevationConstraint:
    """Elevation-angle constraint fragment shared by ASTROX entity and coverage inputs."""

    minimum_deg: float | None = None
    maximum_deg: float | None = None
    maximum_enabled: bool | None = None
    text: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX elevation-angle constraint fragment."""
        payload: dict[str, Any] = {"$type": "ElevationAngle"}
        _include_if_supplied(payload, "MinimumValue", self.minimum_deg)
        _include_if_supplied(payload, "MaximumValue", self.maximum_deg)
        _include_if_supplied(payload, "IsMaximumEnabled", self.maximum_enabled)
        _include_if_supplied(payload, "Text", self.text)
        return payload


@dataclass(frozen=True, kw_only=True)
class RangeConstraint:
    """Range constraint fragment shared by ASTROX entity and coverage inputs."""

    minimum_km: float | None = None
    maximum_km: float | None = None
    maximum_enabled: bool | None = None
    text: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX range constraint fragment."""
        payload: dict[str, Any] = {"$type": "Range"}
        _include_if_supplied(payload, "MinimumValue", self.minimum_km)
        _include_if_supplied(payload, "MaximumValue", self.maximum_km)
        _include_if_supplied(payload, "IsMaximumEnabled", self.maximum_enabled)
        _include_if_supplied(payload, "Text", self.text)
        return payload


@dataclass(frozen=True, kw_only=True)
class AzElMaskConstraint:
    """Azimuth/elevation mask constraint fragment shared by ASTROX entity and coverage inputs."""

    az_el_mask_rad: tuple[float, ...]
    max_range_km: float | None = None
    text: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX azimuth/elevation mask constraint fragment."""
        payload: dict[str, Any] = {
            "$type": "AzElMask",
            "AzElMaskData": list(self.az_el_mask_rad),
        }
        _include_if_supplied(payload, "MaxRange", self.max_range_km)
        _include_if_supplied(payload, "Text", self.text)
        return payload


Constraint: TypeAlias = ElevationConstraint | RangeConstraint | AzElMaskConstraint


_CONSTRAINT_TYPES = (ElevationConstraint, RangeConstraint, AzElMaskConstraint)


def elevation_constraint(
    *,
    minimum_deg: float | None = None,
    maximum_deg: float | None = None,
    maximum_enabled: bool | None = None,
    text: str | None = None,
) -> ElevationConstraint:
    """Create an elevation-angle constraint fragment."""
    return ElevationConstraint(
        minimum_deg=minimum_deg,
        maximum_deg=maximum_deg,
        maximum_enabled=maximum_enabled,
        text=text,
    )


def range_constraint(
    *,
    minimum_km: float | None = None,
    maximum_km: float | None = None,
    maximum_enabled: bool | None = None,
    text: str | None = None,
) -> RangeConstraint:
    """Create a range constraint fragment."""
    return RangeConstraint(
        minimum_km=minimum_km,
        maximum_km=maximum_km,
        maximum_enabled=maximum_enabled,
        text=text,
    )


def az_el_mask_constraint(
    *,
    az_el_mask_rad: Sequence[float],
    max_range_km: float | None = None,
    text: str | None = None,
) -> AzElMaskConstraint:
    """Create an azimuth/elevation mask constraint fragment.

    ``az_el_mask_rad`` is a flat sequence of alternating azimuth and elevation
    samples in radians. ASTROX interpolates the mask piecewise-linearly in
    azimuth and applies it at the constrained participant. Live validation shows
    this constraint is only meaningful for ``SitePosition`` participants; the
    server rejects it for moving position sources.

    ``max_range_km`` is forwarded but is not enforced by ASTROX. The live
    OpenAPI description and server behavior both treat it as documentation-only.
    """
    return AzElMaskConstraint(
        az_el_mask_rad=tuple(
            _number_sequence_to_list(
                az_el_mask_rad,
                parameter="az_el_mask_rad",
            )
        ),
        max_range_km=max_range_km,
        text=text,
    )


def _constraint_to_wire(constraint: Constraint) -> dict[str, Any]:
    if not isinstance(constraint, _CONSTRAINT_TYPES):
        raise TypeError("constraint must be an astrox.components constraint value")
    return constraint.to_wire()
