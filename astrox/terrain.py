"""Terrain mask and analysis functions."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import TerrainMaskConfig, EntityPositionSite

__all__ = ["get_terrain_mask"]


def get_terrain_mask(
    site_position: EntityPositionSite,
    *,
    method: str = "default",
    text: Optional[str] = None,
    terrain_mask_para: Optional[TerrainMaskConfig] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Get azimuth-elevation terrain mask for ground station.

    Endpoints (merged):
    - POST /Terrain/AzElMask (method="default")
    - POST /Terrain/AzElMaskSimple (method="simple")

    Args:
        site_position: Ground station position
        method: Calculation method ("default" or "simple")
        text: Description
        terrain_mask_para: Terrain mask configuration
        session: Optional HTTP session (uses default if not provided)

    Returns:
        360° azimuth-elevation mask data
    """
    sess = session or get_session()

    # Map method to endpoint
    endpoints = {
        "default": "/Terrain/AzElMask",
        "simple": "/Terrain/AzElMaskSimple",
    }
    endpoint = endpoints.get(method, "/Terrain/AzElMask")

    payload: dict = {
        "SitePosition": site_position.model_dump(by_alias=True, exclude_none=True)
        if isinstance(site_position, BaseModel)
        else site_position,
    }

    if text is not None:
        payload["Text"] = text
    if terrain_mask_para is not None:
        payload["TerrainMaskPara"] = terrain_mask_para.model_dump(
            by_alias=True, exclude_none=True
        )

    return sess.post(endpoint=endpoint, data=payload)
