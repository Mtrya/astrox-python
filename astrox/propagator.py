"""Orbit propagation functions."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import KeplerElementsWithEpoch, Propagator

__all__ = [
    "propagate_two_body",
    "propagate_ballistic",
    "propagate_j2",
    "propagate_sgp4",
    "propagate_simple_ascent",
    "propagate_hpop",
    "propagate_j2_batch",
    "propagate_sgp4_batch",
    "propagate_two_body_batch",
]


def propagate_two_body(
    start: str,
    stop: str,
    orbit_epoch: str,
    orbital_elements: list[float],
    *,
    step: Optional[float] = None,
    central_body: Optional[str] = None,
    gravitational_parameter: Optional[float] = None,
    coord_system: Optional[str] = None,
    coord_type: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate orbit using two-body dynamics.

    Endpoint: POST /Propagator/TwoBody

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        orbit_epoch: Orbit epoch (UTCG)
        orbital_elements: Orbital elements (6 values)
            - Classical: SemiMajorAxis(m), Eccentricity, Inclination(deg),
                        ArgumentOfPeriapsis(deg), RAAN(deg), TrueAnomaly(deg)
            - Cartesian: X(m), Y(m), Z(m), Vx(m/s), Vy(m/s), Vz(m/s)
        step: Integration step size (s)
        central_body: Central body name (default: "Earth")
        gravitational_parameter: Gravitational constant (m³/s²)
        coord_system: Coordinate system (default: "Inertial")
        coord_type: Coordinate type ("Classical" or "Cartesian", default: "Classical")
        session: Optional HTTP session (uses default if not provided)

    Returns:
        CZML position output
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "OrbitEpoch": orbit_epoch,
        "OrbitalElements": orbital_elements,
    }

    if step is not None:
        payload["Step"] = step
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter is not None:
        payload["GravitationalParameter"] = gravitational_parameter
    if coord_system is not None:
        payload["CoordSystem"] = coord_system
    if coord_type is not None:
        payload["CoordType"] = coord_type

    return sess.post(endpoint="/Propagator/TwoBody", data=payload)


def propagate_ballistic(
    start: str,
    impact_latitude: float,
    impact_longitude: float,
    *,
    step: Optional[float] = None,
    central_body: Optional[str] = None,
    gravitational_parameter: Optional[float] = None,
    launch_latitude: Optional[float] = None,
    launch_longitude: Optional[float] = None,
    launch_altitude: Optional[float] = None,
    ballistic_type: Optional[str] = None,
    ballistic_type_value: Optional[float] = None,
    impact_altitude: Optional[float] = None,
    stop: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate ballistic trajectory.

    Endpoint: POST /Propagator/Ballistic

    Args:
        start: Launch time (UTCG)
        impact_latitude: Impact point latitude (deg)
        impact_longitude: Impact point longitude (deg)
        step: Integration step size (s)
        central_body: Central body name
        gravitational_parameter: Gravitational constant (m³/s²)
        launch_latitude: Launch site latitude (deg)
        launch_longitude: Launch site longitude (deg)
        launch_altitude: Launch site altitude (m)
        ballistic_type: Ballistic type ("DeltaV", "DeltaV_MinEcc", "ApogeeAlt", "TimeOfFlight")
        ballistic_type_value: Ballistic type value (m/s, m, or s)
        impact_altitude: Impact point altitude (m)
        stop: End time (computed after propagation if not provided)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        CZML position output
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "ImpactLatitude": impact_latitude,
        "ImpactLongitude": impact_longitude,
    }

    if step is not None:
        payload["Step"] = step
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter is not None:
        payload["GravitationalParameter"] = gravitational_parameter
    if launch_latitude is not None:
        payload["LaunchLatitude"] = launch_latitude
    if launch_longitude is not None:
        payload["LaunchLongitude"] = launch_longitude
    if launch_altitude is not None:
        payload["LaunchAltitude"] = launch_altitude
    if ballistic_type is not None:
        payload["BallisticType"] = ballistic_type
    if ballistic_type_value is not None:
        payload["BallisticTypeValue"] = ballistic_type_value
    if impact_altitude is not None:
        payload["ImpactAltitude"] = impact_altitude
    if stop is not None:
        payload["Stop"] = stop

    return sess.post(endpoint="/Propagator/Ballistic", data=payload)


def propagate_j2(
    start: str,
    stop: str,
    j2_normalized_value: float,
    ref_distance: float,
    orbit_epoch: str,
    orbital_elements: list[float],
    *,
    step: Optional[float] = None,
    central_body: Optional[str] = None,
    gravitational_parameter: Optional[float] = None,
    coord_system: Optional[str] = None,
    coord_type: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate orbit using J2 perturbation model.

    Endpoint: POST /Propagator/Propagate/J2

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        j2_normalized_value: J2 normalized value (Earth: 0.000484165143790815)
        ref_distance: Reference ellipsoid semi-major axis (m)
        orbit_epoch: Orbit epoch (UTCG)
        orbital_elements: Orbital elements (6 values for Classical)
        step: Integration step size (s)
        central_body: Central body name
        gravitational_parameter: Gravitational constant (m³/s²)
        coord_system: Coordinate system
        coord_type: Coordinate type
        session: Optional HTTP session (uses default if not provided)

    Returns:
        CZML position output
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "J2NormalizedValue": j2_normalized_value,
        "RefDistance": ref_distance,
        "OrbitEpoch": orbit_epoch,
        "OrbitalElements": orbital_elements,
    }

    if step is not None:
        payload["Step"] = step
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter is not None:
        payload["GravitationalParameter"] = gravitational_parameter
    if coord_system is not None:
        payload["CoordSystem"] = coord_system
    if coord_type is not None:
        payload["CoordType"] = coord_type

    return sess.post(endpoint="/Propagator/J2", data=payload)


def propagate_sgp4(
    start: str,
    stop: str,
    tles: list[str],
    *,
    step: Optional[float] = None,
    satellite_number: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate orbit using SGP4 model.

    Endpoint: POST /Propagator/SGP4

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        tles: TLE lines ["tle-line1", "tle-line2"]
        step: Output step size (s)
        satellite_number: Satellite SSC number
        session: Optional HTTP session (uses default if not provided)

    Returns:
        CZML position output
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "TLEs": tles,
    }

    if step is not None:
        payload["Step"] = step
    if satellite_number is not None:
        payload["SatelliteNumber"] = satellite_number

    return sess.post(endpoint="/Propagator/sgp4", data=payload)


def propagate_simple_ascent(
    start: str,
    stop: str,
    launch_latitude: float,
    launch_longitude: float,
    launch_altitude: float,
    burnout_velocity: float,
    burnout_latitude: float,
    burnout_longitude: float,
    burnout_altitude: float,
    *,
    central_body: Optional[str] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate simple ascent trajectory.

    Endpoint: POST /Propagator/SimpleAscent

    Args:
        start: Launch time (UTCG)
        stop: Burnout time (UTCG)
        launch_latitude: Launch latitude (deg)
        launch_longitude: Launch longitude (deg)
        launch_altitude: Launch altitude (m)
        burnout_velocity: Burnout velocity (m/s, Fixed frame)
        burnout_latitude: Burnout latitude (deg)
        burnout_longitude: Burnout longitude (deg)
        burnout_altitude: Burnout altitude (m)
        central_body: Central body name
        step: Integration step size (s)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        CZML position output
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "LaunchLatitude": launch_latitude,
        "LaunchLongitude": launch_longitude,
        "LaunchAltitude": launch_altitude,
        "BurnoutVelocity": burnout_velocity,
        "BurnoutLatitude": burnout_latitude,
        "BurnoutLongitude": burnout_longitude,
        "BurnoutAltitude": burnout_altitude,
    }

    if central_body is not None:
        payload["CentralBody"] = central_body
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint="/Propagator/SimpleAscent", data=payload)


def propagate_hpop(
    start: str,
    stop: str,
    orbit_epoch: str,
    orbital_elements: list[float],
    *,
    description: Optional[str] = None,
    coord_epoch: Optional[str] = None,
    coord_system: Optional[str] = None,
    coord_type: Optional[str] = None,
    gravitational_parameter: Optional[float] = None,
    coefficient_of_drag: Optional[float] = None,
    area_mass_ratio_drag: Optional[float] = None,
    coefficient_of_srp: Optional[float] = None,
    area_mass_ratio_srp: Optional[float] = None,
    hpop_propagator: Optional[Propagator] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate orbit using high-precision orbit propagator (HPOP).

    Endpoint: POST /Propagator/HPOP

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        orbit_epoch: Orbit epoch (UTCG)
        orbital_elements: Orbital elements (6 values)
        description: Description info
        coord_epoch: Coordinate system epoch
        coord_system: Orbit system ("Inertial", "J2000", "ICRF", ...)
        coord_type: Orbit type ("Classical" or "Cartesian")
        gravitational_parameter: Central body gravitational constant (m³/s²)
        coefficient_of_drag: Atmospheric drag coefficient
        area_mass_ratio_drag: Drag area-mass ratio (m²/kg)
        coefficient_of_srp: Solar radiation pressure coefficient
        area_mass_ratio_srp: SRP area-mass ratio (m²/kg)
        hpop_propagator: HPOP propagator configuration
        session: Optional HTTP session (uses default if not provided)

    Returns:
        CZML position output
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "OrbitEpoch": orbit_epoch,
        "OrbitalElements": orbital_elements,
    }

    if description is not None:
        payload["Description"] = description
    if coord_epoch is not None:
        payload["CoordEpoch"] = coord_epoch
    if coord_system is not None:
        payload["CoordSystem"] = coord_system
    if coord_type is not None:
        payload["CoordType"] = coord_type
    if gravitational_parameter is not None:
        payload["GravitationalParameter"] = gravitational_parameter
    if coefficient_of_drag is not None:
        payload["CoefficientOfDrag"] = coefficient_of_drag
    if area_mass_ratio_drag is not None:
        payload["AreaMassRatioDrag"] = area_mass_ratio_drag
    if coefficient_of_srp is not None:
        payload["CoefficientOfSRP"] = coefficient_of_srp
    if area_mass_ratio_srp is not None:
        payload["AreaMassRatioSRP"] = area_mass_ratio_srp
    if hpop_propagator is not None:
        payload["HpopPropagator"] = hpop_propagator.model_dump(
            by_alias=True, exclude_none=True
        )

    return sess.post(endpoint="/Propagator/HPOP", data=payload)


def propagate_j2_batch(
    epoch: str,
    all_satellite_elements: list[KeplerElementsWithEpoch],
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate multiple satellites using J2 perturbation to same epoch.

    Endpoint: POST /Propagator/J2Batch

    Args:
        epoch: Output epoch time (UTCG)
        all_satellite_elements: Collection of satellite orbital elements
        session: Optional HTTP session (uses default if not provided)

    Returns:
        All satellites' Kepler elements at output epoch (Earth inertial frame)
    """
    sess = session or get_session()

    payload = {
        "Epoch": epoch,
        "AllSateElements": [  # Note: API has typo - "Sate" not "Satellite"
            elem.model_dump(by_alias=True, exclude_none=True)
            if isinstance(elem, BaseModel)
            else elem
            for elem in all_satellite_elements
        ],
    }

    return sess.post(endpoint="/Propagator/MultiJ2", data=payload)


def propagate_sgp4_batch(
    epoch: str,
    tles: list[str],
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate multiple satellites using SGP4 to same epoch.

    Endpoint: POST /Propagator/SGP4Batch

    Args:
        epoch: Output epoch time (UTCG)
        tles: TLE lines for all satellites
        session: Optional HTTP session (uses default if not provided)

    Returns:
        All satellites' Kepler elements at epoch (Earth inertial frame)
    """
    sess = session or get_session()

    payload = {
        "Epoch": epoch,
        "TLEs": tles,
    }

    return sess.post(endpoint="/Propagator/MultiSgp4", data=payload)


def propagate_two_body_batch(
    epoch: str,
    all_satellite_elements: list[KeplerElementsWithEpoch],
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Propagate multiple satellites using two-body dynamics to same epoch.

    Endpoint: POST /Propagator/TwoBodyBatch

    Args:
        epoch: Output epoch time (UTCG)
        all_satellite_elements: Collection of satellite orbital elements
        session: Optional HTTP session (uses default if not provided)

    Returns:
        All satellites' Kepler elements at output epoch (Earth inertial frame)
    """
    sess = session or get_session()

    payload = {
        "Epoch": epoch,
        "AllSateElements": [  # Note: API has typo - "Sate" not "Satellite"
            elem.model_dump(by_alias=True, exclude_none=True)
            if isinstance(elem, BaseModel)
            else elem
            for elem in all_satellite_elements
        ],
    }

    return sess.post(endpoint="/Propagator/MultiTwoBody", data=payload)
