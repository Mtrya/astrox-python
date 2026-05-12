"""Landing zone computation functions."""

from __future__ import annotations

from typing import Optional

from astrox._http import HTTPClient, get_session

__all__ = ["compute_landing_zone"]


def compute_landing_zone(
    fa_she_dian: list[float],
    luo_dian: list[float],
    zone_xys: list[float],
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Compute landing zone parameters.

    Endpoint: POST /LandingZone

    Args:
        fa_she_dian: Launch point coordinates [lon(deg), lat(deg), alt(m)]
        luo_dian: Landing point coordinates [lon(deg), lat(deg), alt(m)]
        zone_xys: Boundary point parameters (front is +X axis, right is +Y axis, unit: km)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Landing zone computation results
    """
    sess = session or get_session()

    payload = {
        "FaSheDian": fa_she_dian,
        "LuoDian": luo_dian,
        "ZoneXYs": zone_xys,
    }

    return sess.post(endpoint="/LandingZone", data=payload)
