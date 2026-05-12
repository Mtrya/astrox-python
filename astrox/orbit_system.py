"""Orbit system calculation functions."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import EntityPositionCzml

__all__ = ["convert_central_body_frame", "compute_earth_moon_libration"]


def convert_central_body_frame(
    position: EntityPositionCzml,
    to_body: str,
    *,
    reference_frame: str,
    central_body: Optional[str] = None,
    interpolation_algorithm: Optional[str] = None,
    interpolation_degree: Optional[int] = None,
    epoch: Optional[str] = None,
    interval: Optional[str] = None,
    cartesian: Optional[list[float]] = None,
    cartesian_velocity: Optional[list[float]] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Convert position between central body reference frames.

    Endpoint: POST /OrbitSystem/CentralBodyFrame?toCb={to_body}&referenceFrame={reference_frame}

    Args:
        position: Entity position data (EntityPositionCzml)
        to_body: Target central body name (e.g., "Moon", "Mars") - query parameter
        reference_frame: Reference frame type (e.g., "INERTIAL", "FIXED") - query parameter, required
        central_body: Source central body (default: "Earth") - part of position data
        interpolation_algorithm: Interpolation method ("LINEAR", "LAGRANGE", "HERMITE")
        interpolation_degree: Interpolation degree
        epoch: Epoch time (UTCG)
        interval: Time interval for composite position
        cartesian: Position array [X, Y, Z] (m)
        cartesian_velocity: Position velocity array [X, Y, Z, dX, dY, dZ] (m, m/s)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Position data in target central body frame
    """
    sess = session or get_session()

    # Build query parameters
    params = {
        "toCb": to_body,
        "referenceFrame": reference_frame,
    }

    # Build request body (EntityPositionCzml with optional overrides)
    payload = position.model_dump(by_alias=True, exclude_none=True) if isinstance(position, BaseModel) else position

    # Apply optional overrides to payload
    if central_body is not None:
        payload["CentralBody"] = central_body
    if interpolation_algorithm is not None:
        payload["interpolationAlgorithm"] = interpolation_algorithm
    if interpolation_degree is not None:
        payload["interpolationDegree"] = interpolation_degree
    if epoch is not None:
        payload["epoch"] = epoch
    if interval is not None:
        payload["interval"] = interval
    if cartesian is not None:
        payload["cartesian"] = cartesian
    if cartesian_velocity is not None:
        payload["cartesianVelocity"] = cartesian_velocity

    return sess.post(endpoint="/OrbitSystem/CentralBodyFrame", data=payload, params=params)


def compute_earth_moon_libration(
    epoch: str,
    *,
    version: str = "v2",
    central_body: Optional[str] = None,
    interpolation_algorithm: Optional[str] = None,
    interpolation_degree: Optional[int] = None,
    reference_frame: Optional[str] = None,
    interval: Optional[str] = None,
    cartesian: Optional[list[float]] = None,
    cartesian_velocity: Optional[list[float]] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate Earth-Moon libration (Lagrange) points.

    Endpoints (merged):
    - POST /OrbitSystem/EarthMoonLibration (version="v1")
    - POST /OrbitSystem/EarthMoonLibration2 (version="v2", default)

    Args:
        epoch: Epoch time (UTCG) format: "yyyy-MM-ddTHH:mm:ssZ"
        version: API version ("v1" or "v2", default "v2")
        central_body: Central body (default: "Earth")
        interpolation_algorithm: Interpolation method (default: "LAGRANGE")
        interpolation_degree: Interpolation degree (default: 7)
        reference_frame: Reference frame (default: "FIXED")
        interval: Time interval for composite position
        cartesian: Position array [X, Y, Z] (m)
        cartesian_velocity: Position velocity array (m, m/s)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Libration point calculations
    """
    sess = session or get_session()

    # Map version to endpoint
    endpoints = {
        "v1": "/OrbitSystem/EarthMoonLibration",
        "v2": "/OrbitSystem/EarthMoonLibration2",
    }
    endpoint = endpoints.get(version, "/OrbitSystem/EarthMoonLibration2")

    payload: dict = {
        "Epoch": epoch,
    }

    if central_body is not None:
        payload["CentralBody"] = central_body
    if interpolation_algorithm is not None:
        payload["InterpolationAlgorithm"] = interpolation_algorithm
    if interpolation_degree is not None:
        payload["InterpolationDegree"] = interpolation_degree
    if reference_frame is not None:
        payload["ReferenceFrame"] = reference_frame
    if interval is not None:
        payload["Interval"] = interval
    if cartesian is not None:
        payload["Cartesian"] = cartesian
    if cartesian_velocity is not None:
        payload["CartesianVelocity"] = cartesian_velocity

    return sess.post(endpoint=endpoint, data=payload)
