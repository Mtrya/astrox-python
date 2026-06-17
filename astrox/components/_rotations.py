"""Rotation component value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from ._common import _real_number, _string

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


def _rotation_to_wire(rotation: Rotation) -> dict[str, Any]:
    if not isinstance(rotation, _ROTATION_TYPES):
        raise TypeError("rotation must be an astrox.components rotation value")
    return rotation.to_wire()
