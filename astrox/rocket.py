"""Rocket analysis functions."""

from __future__ import annotations

from collections.abc import Sequence
from numbers import Real
from typing import Any

from astrox._http import raw

__all__ = [
    "landing_zone",
]


def _number_sequence_to_list(value: Sequence[float], *, parameter: str) -> list[float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    items = list(value)
    if not all(isinstance(item, Real) and not isinstance(item, bool) for item in items):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    return items


def landing_zone(
    *,
    launch_longitude_deg: float,
    launch_latitude_deg: float,
    launch_height_m: float,
    impact_longitude_deg: float,
    impact_latitude_deg: float,
    impact_height_m: float,
    zone_xys_km: Sequence[float],
) -> dict[str, Any]:
    """Compute rocket landing-zone boundary geodetic coordinates.

    Parameters match the ASTROX ``/LandingZone`` endpoint. ``zone_xys_km`` is a
    flat sequence of local downrange/crossrange offsets in kilometres, given in
    ``[+X1, +Y1, +X2, +Y2, ...]`` pairs.

    Cross-validation shows ASTROX builds a local right-handed frame at the
    impact point: ``+X`` is the southward-facing member of the launch-to-impact
    geodesic azimuth at the impact point and its supplement, and ``+Y`` is
    ``+X`` rotated 90 degrees clockwise. For cardinal tracks this coincides with
    the OpenAPI "forward/right" description; for diagonal tracks it does not.

    The function returns the raw ASTROX response dict, including ``IsSuccess``,
    ``Message``, and ``cartographicDegrees``.

    Example:
        >>> from astrox import rocket
        >>> result = rocket.landing_zone(
        ...     launch_longitude_deg=100.0,
        ...     launch_latitude_deg=30.0,
        ...     launch_height_m=0.0,
        ...     impact_longitude_deg=101.0,
        ...     impact_latitude_deg=30.5,
        ...     impact_height_m=100.0,
        ...     zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ... )
        >>> result["IsSuccess"]
        True
    """
    zone_xys = _number_sequence_to_list(zone_xys_km, parameter="zone_xys_km")
    if len(zone_xys) % 2 != 0:
        raise ValueError("zone_xys_km must contain an even number of values")

    payload: dict[str, Any] = {
        "FaSheDian": [
            launch_longitude_deg,
            launch_latitude_deg,
            launch_height_m,
        ],
        "LuoDian": [
            impact_longitude_deg,
            impact_latitude_deg,
            impact_height_m,
        ],
        "ZoneXYs": zone_xys,
    }

    return raw.post("/LandingZone", json=payload)
