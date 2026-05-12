"""Orbit design and wizard functions."""

from __future__ import annotations

from typing import Optional

from astrox._http import HTTPClient, get_session
from astrox._models import KeplerElements

__all__ = ["design_geo", "design_molniya", "design_sso", "design_walker"]


def design_geo(
    orbit_epoch: str,
    inclination: float,
    sub_satellite_point: float,
    *,
    description: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Generate geostationary orbit.

    Endpoint: POST /OrbitWizard/GEO

    Args:
        orbit_epoch: Orbital epoch (UTCG) format: "yyyy-MM-ddTHH:mm:ss.fffZ"
        inclination: Orbital inclination (deg)
        sub_satellite_point: Sub-satellite point geographic longitude (deg)
        description: Description
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Kepler elements in TOD and inertial frames
    """
    sess = session or get_session()

    payload: dict = {
        "OrbitEpoch": orbit_epoch,
        "Inclination": inclination,
        "SubSatellitePoint": sub_satellite_point,
    }

    if description is not None:
        payload["Description"] = description

    return sess.post(endpoint="/OrbitWizard/GEO", data=payload)


def design_molniya(
    orbit_epoch: str,
    perigee_altitude: float,
    apogee_longitude: float,
    argument_of_periapsis: float,
    *,
    description: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Generate Molniya orbit.

    Endpoint: POST /OrbitWizard/Molniya

    Args:
        orbit_epoch: Orbital epoch (UTCG)
        perigee_altitude: Perigee altitude (km), typically 600 km
        apogee_longitude: Apogee geographic longitude (deg)
        argument_of_periapsis: Argument of perigee (deg), typically 90° or 270°
        description: Description
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Kepler elements in TOD and inertial frames
    """
    sess = session or get_session()

    payload: dict = {
        "OrbitEpoch": orbit_epoch,
        "PerigeeAltitude": perigee_altitude,
        "ApogeeLongitude": apogee_longitude,
        "ArgumentOfPeriapsis": argument_of_periapsis,
    }

    if description is not None:
        payload["Description"] = description

    return sess.post(endpoint="/OrbitWizard/Molniya", data=payload)


def design_sso(
    orbit_epoch: str,
    altitude: float,
    local_time_of_descending_node: float,
    *,
    description: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Generate sun-synchronous orbit.

    Endpoint: POST /OrbitWizard/SSO

    Args:
        orbit_epoch: Orbital epoch (UTCG)
        altitude: Orbital altitude (km)
        local_time_of_descending_node: Local time of descending node
                                       (decimal hours, e.g., 14.5 = 14:30 PM)
        description: Description
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Kepler elements in TOD and inertial frames
    """
    sess = session or get_session()

    payload: dict = {
        "OrbitEpoch": orbit_epoch,
        "Altitude": altitude,
        "LocalTimeOfDescendingNode": local_time_of_descending_node,
    }

    if description is not None:
        payload["Description"] = description

    return sess.post(endpoint="/OrbitWizard/SSO", data=payload)


def design_walker(
    seed_kepler: KeplerElements,
    num_planes: int,
    num_sats_per_plane: int,
    *,
    walker_type: Optional[str] = None,
    inter_plane_phase_increment: Optional[int] = None,
    inter_plane_true_anomaly_increment: Optional[float] = None,
    raan_increment: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Generate Walker constellation.

    Endpoint: POST /OrbitWizard/Walker

    Args:
        seed_kepler: Seed Kepler elements for constellation
        num_planes: Number of orbital planes (1-999)
        num_sats_per_plane: Number of satellites per plane (1-999)
        walker_type: Constellation type ("Delta", "Star", or "Custom")
        inter_plane_phase_increment: Phase factor (Delta/Star types, < num_planes)
        inter_plane_true_anomaly_increment: True anomaly increment (deg, Custom type)
        raan_increment: RAAN increment between planes (deg, Custom type)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Generated Walker constellation Kepler elements (2D array by plane)
    """
    sess = session or get_session()

    payload: dict = {
        "SeedKepler": seed_kepler.model_dump(by_alias=True, exclude_none=True),
        "NumPlanes": num_planes,
        "NumSatsPerPlane": num_sats_per_plane,
    }

    if walker_type is not None:
        payload["WalkerType"] = walker_type
    if inter_plane_phase_increment is not None:
        payload["InterPlanePhaseIncrement"] = inter_plane_phase_increment
    if inter_plane_true_anomaly_increment is not None:
        payload["InterPlaneTrueAnomalyIncrement"] = inter_plane_true_anomaly_increment
    if raan_increment is not None:
        payload["RAANIncrement"] = raan_increment

    return sess.post(endpoint="/OrbitWizard/Walker", data=payload)
