"""Lighting and solar calculation functions."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import IEntityPosition, EntityPositionSite

__all__ = ["lighting_times", "solar_intensity", "solar_aer"]


def lighting_times(
    start: str,
    stop: str,
    position: IEntityPosition,
    *,
    description: Optional[str] = None,
    az_el_mask_data: Optional[list[float]] = None,
    occultation_bodies: Optional[list[str]] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate lighting time intervals (sunlight, penumbra, umbra).

    Endpoint: POST /Lighting/LightingTimes

    Args:
        start: Analysis start time (UTCG) format: "yyyy-MM-ddTHH:mm:ssZ"
        stop: Analysis end time (UTCG)
        position: Entity position (spacecraft or ground station)
        description: Description/comment
        az_el_mask_data: Terrain mask data (ground stations only);
                        format: (Az1, El1, Az2, El2, ...) in radians
        occultation_bodies: Occulting body list (1st element is central body)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        SunLight, Penumbra, and Umbra time parameters
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Position": position.model_dump(by_alias=True, exclude_none=True)
        if isinstance(position, BaseModel)
        else position,
    }

    if description is not None:
        payload["Description"] = description
    if az_el_mask_data is not None:
        payload["AzElMaskData"] = az_el_mask_data
    if occultation_bodies is not None:
        payload["OccultationBodies"] = occultation_bodies

    return sess.post(endpoint="/Lighting/LightingTimes", data=payload)


def solar_intensity(
    start: str,
    stop: str,
    position: IEntityPosition,
    *,
    description: Optional[str] = None,
    az_el_mask_data: Optional[list[float]] = None,
    time_step_sec: Optional[float] = None,
    occultation_bodies: Optional[list[str]] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate solar intensity at entity position.

    Endpoint: POST /Lighting/SolarIntensity

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        position: Entity position
        description: Description
        az_el_mask_data: Terrain mask data (ground stations only)
        time_step_sec: Calculation time step (s)
        occultation_bodies: Occulting body list
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Solar intensity data at uniformly sampled time points
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Position": position.model_dump(by_alias=True, exclude_none=True)
        if isinstance(position, BaseModel)
        else position,
    }

    if description is not None:
        payload["Description"] = description
    if az_el_mask_data is not None:
        payload["AzElMaskData"] = az_el_mask_data
    if time_step_sec is not None:
        payload["TimeStepSec"] = time_step_sec
    if occultation_bodies is not None:
        payload["OccultationBodies"] = occultation_bodies

    return sess.post(endpoint="/Lighting/SolarIntensity", data=payload)


def solar_aer(
    start: str,
    stop: str,
    site_position: EntityPositionSite,
    *,
    text: Optional[str] = None,
    time_step_sec: Optional[int] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate solar azimuth, elevation, and range from ground station.

    Endpoint: POST /Lighting/SolarAER

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        site_position: Ground station position
        text: Description
        time_step_sec: Calculation time step (s)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Solar AER data points
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "SitePosition": site_position.model_dump(by_alias=True, exclude_none=True)
        if isinstance(site_position, BaseModel)
        else site_position,
    }

    if text is not None:
        payload["Text"] = text
    if time_step_sec is not None:
        payload["TimeStepSec"] = time_step_sec

    return sess.post(endpoint="/Lighting/SolarAER", data=payload)
