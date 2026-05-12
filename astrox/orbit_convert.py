"""Orbit coordinate conversion functions."""

from __future__ import annotations

from typing import Optional

from astrox._http import HTTPClient, get_session
from astrox._models import KeplerElements

__all__ = [
    "kepler_to_rv",
    "rv_to_kepler",
    "kepler_to_lla_at_ascending_node",
    "geo_lambert_transfer_dv",
    "kozai_izsak_mean_elements",
]


def kepler_to_rv(
    semimajor_axis: float,
    eccentricity: float,
    inclination: float,
    argument_of_periapsis: float,
    right_ascension_of_ascending_node: float,
    true_anomaly: float,
    gravitational_parameter: float,
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Convert Kepler elements to position/velocity vectors.

    Endpoint: POST /OrbitConvert/Kepler2RV

    Args:
        semimajor_axis: Orbital semi-major axis (m)
        eccentricity: Orbital eccentricity
        inclination: Orbital inclination (deg)
        argument_of_periapsis: Argument of perigee (deg)
        right_ascension_of_ascending_node: RAAN (deg)
        true_anomaly: True anomaly (deg)
        gravitational_parameter: Gravitational constant (m³/s²)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Array of position and velocity components
    """
    sess = session or get_session()

    payload = {
        "SemimajorAxis": semimajor_axis,
        "Eccentricity": eccentricity,
        "Inclination": inclination,
        "ArgumentOfPeriapsis": argument_of_periapsis,
        "RightAscensionOfAscendingNode": right_ascension_of_ascending_node,
        "TrueAnomaly": true_anomaly,
        "GravitationalParameter": gravitational_parameter,
    }

    return sess.post(endpoint="/OrbitConvert/Kepler2RV", data=payload)


def rv_to_kepler(
    position_velocity: list[float],
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Convert position/velocity vectors to Kepler elements.

    Endpoint: POST /OrbitConvert/RV2Kepler

    Args:
        position_velocity: Position (m) and velocity (m/s) components
                          in Earth inertial frame (array of 6 floats: [x, y, z, vx, vy, vz])
        session: Optional HTTP session (uses default if not provided)

    Returns:
        KeplerElements schema
    """
    sess = session or get_session()

    # API expects raw array, not an object
    return sess.post(endpoint="/OrbitConvert/RV2Kepler", data=position_velocity)


def kepler_to_lla_at_ascending_node(
    semimajor_axis: float,
    eccentricity: float,
    inclination: float,
    argument_of_periapsis: float,
    right_ascension_of_ascending_node: float,
    true_anomaly: float,
    gravitational_parameter: float,
    *,
    orbit_epoch: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Convert Kepler elements to LLA at ascending node.

    Endpoint: POST /OrbitConvert/Kepler2LLAAtAscendNode

    Note: Earth only, two-body orbital propagation.

    Args:
        semimajor_axis: Orbital semi-major axis (m)
        eccentricity: Orbital eccentricity
        inclination: Orbital inclination (deg)
        argument_of_periapsis: Argument of perigee (deg)
        right_ascension_of_ascending_node: RAAN (deg)
        true_anomaly: True anomaly (deg)
        gravitational_parameter: Gravitational constant (m³/s²)
        orbit_epoch: Orbital epoch (UTCG) format: "yyyy-MM-ddTHH:mm:ss.fffZ"
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Array of latitude, longitude, altitude at ascending node
    """
    sess = session or get_session()

    payload: dict = {
        "SemimajorAxis": semimajor_axis,
        "Eccentricity": eccentricity,
        "Inclination": inclination,
        "ArgumentOfPeriapsis": argument_of_periapsis,
        "RightAscensionOfAscendingNode": right_ascension_of_ascending_node,
        "TrueAnomaly": true_anomaly,
        "GravitationalParameter": gravitational_parameter,
    }

    if orbit_epoch is not None:
        payload["OrbitEpoch"] = orbit_epoch

    return sess.post(endpoint="/OrbitConvert/Kepler2LLAAtAscendNode", data=payload)


def geo_lambert_transfer_dv(
    kepler_platform: KeplerElements,
    kepler_target: KeplerElements,
    time_of_flight: float,
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate Lambert transfer delta-V from GEO platform to target orbit.

    Endpoint: POST /OrbitConvert/CalGEOYMLambertDv

    Args:
        kepler_platform: GEO platform orbital Kepler elements
        kepler_target: Target orbital Kepler elements
        time_of_flight: Flight time (s)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Lambert transfer delta-V components (array of floats)
    """
    sess = session or get_session()

    payload = {
        "keplerPt": kepler_platform.model_dump(
            by_alias=True, exclude_none=True
        ),
        "keplerMb": kepler_target.model_dump(by_alias=True, exclude_none=True),
        "tof": time_of_flight,
    }

    return sess.post(endpoint="/OrbitConvert/CalGEOYMLambertDv", data=payload)


def kozai_izsak_mean_elements(
    semimajor_axis: float,
    eccentricity: float,
    inclination: float,
    argument_of_periapsis: float,
    right_ascension_of_ascending_node: float,
    true_anomaly: float,
    gravitational_parameter: float,
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Get mean Kepler elements via Kozai-Izsak method.

    Endpoint: POST /OrbitConvert/GetKozaiIzsakMeanElements

    Note: Circular orbits only, J2 short-period terms.

    Args:
        semimajor_axis: Orbital semi-major axis (m)
        eccentricity: Orbital eccentricity
        inclination: Orbital inclination (deg)
        argument_of_periapsis: Argument of perigee (deg)
        right_ascension_of_ascending_node: RAAN (deg)
        true_anomaly: True anomaly (deg)
        gravitational_parameter: Gravitational constant (m³/s²)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Mean Kepler elements accounting for J2 perturbation
    """
    sess = session or get_session()

    payload = {
        "SemimajorAxis": semimajor_axis,
        "Eccentricity": eccentricity,
        "Inclination": inclination,
        "ArgumentOfPeriapsis": argument_of_periapsis,
        "RightAscensionOfAscendingNode": right_ascension_of_ascending_node,
        "TrueAnomaly": true_anomaly,
        "GravitationalParameter": gravitational_parameter,
    }

    return sess.post(
        endpoint="/OrbitConvert/GetKozaiIzsakMeanElements", data=payload
    )
