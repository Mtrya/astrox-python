"""Orbit propagation functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel

from astrox._http import Client, get_session, raw
from astrox._models import KeplerElementsWithEpoch, Propagator
from astrox.orbits import KeplerianElements

__all__ = [
    "PropagatorPosition",
    "ballistic",
    "ballistic_apogee_altitude",
    "ballistic_delta_v",
    "ballistic_delta_v_min_ecc",
    "ballistic_time_of_flight",
    "j2",
    "propagate_sgp4",
    "propagate_simple_ascent",
    "propagate_hpop",
    "propagate_j2_batch",
    "propagate_sgp4_batch",
    "propagate_two_body_batch",
    "two_body",
]


@dataclass(frozen=True, kw_only=True)
class PropagatorPosition:
    """Nested propagated position output."""

    central_body: str
    epoch: str
    reference_frame: str
    interpolation_algorithm: str
    interpolation_degree: int
    cartesian_velocity: tuple[float, ...]

    @classmethod
    def from_wire(cls, position_payload: dict[str, Any]) -> PropagatorPosition:
        """Build from the ASTROX nested Position payload."""
        return cls(
            central_body=position_payload["CentralBody"],
            epoch=position_payload["epoch"],
            reference_frame=position_payload["referenceFrame"],
            interpolation_algorithm=position_payload["interpolationAlgorithm"],
            interpolation_degree=position_payload["interpolationDegree"],
            cartesian_velocity=tuple(position_payload["cartesianVelocity"]),
        )


def two_body(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate Classical Keplerian elements using two-body dynamics."""
    if not isinstance(orbit, KeplerianElements):
        raise TypeError("orbit must be a KeplerianElements instance")

    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "OrbitEpoch": orbit_epoch,
        "CoordType": "Classical",
        "OrbitalElements": orbit.to_wire(),
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if coord_system is not None:
        payload["CoordSystem"] = coord_system

    result = raw.post("/Propagator/TwoBody", json=payload)
    if result["IsSuccess"] is not True:
        raise ValueError(result["Message"])
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


def j2(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
    j2_normalized_value: float | None = None,
    ref_distance_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate Classical Keplerian elements using the J2 model."""
    if not isinstance(orbit, KeplerianElements):
        raise TypeError("orbit must be a KeplerianElements instance")

    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "OrbitEpoch": orbit_epoch,
        "CoordType": "Classical",
        "OrbitalElements": orbit.to_wire(),
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if coord_system is not None:
        payload["CoordSystem"] = coord_system
    if j2_normalized_value is not None:
        payload["J2NormalizedValue"] = j2_normalized_value
    if ref_distance_m is not None:
        payload["RefDistance"] = ref_distance_m

    result = raw.post("/Propagator/J2", json=payload)
    if result["IsSuccess"] is not True:
        raise ValueError(result["Message"])
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


def ballistic(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate the verified nominal ballistic trajectory shape."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    if result["IsSuccess"] is not True:
        raise ValueError(result["Message"])
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


def ballistic_delta_v(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    delta_v_m_s: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a ballistic trajectory using the DeltaV branch."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
        "BallisticType": "DeltaV",
        "BallisticTypeValue": delta_v_m_s,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    if result["IsSuccess"] is not True:
        raise ValueError(result["Message"])
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


def ballistic_delta_v_min_ecc(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    delta_v_m_s: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a ballistic trajectory using the DeltaV_MinEcc branch."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
        "BallisticType": "DeltaV_MinEcc",
        "BallisticTypeValue": delta_v_m_s,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    if result["IsSuccess"] is not True:
        raise ValueError(result["Message"])
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


def ballistic_apogee_altitude(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    apogee_altitude_m: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a ballistic trajectory using the ApogeeAlt branch."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
        "BallisticType": "ApogeeAlt",
        "BallisticTypeValue": apogee_altitude_m,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    if result["IsSuccess"] is not True:
        raise ValueError(result["Message"])
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


def ballistic_time_of_flight(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    time_of_flight_s: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a ballistic trajectory using the TimeOfFlight branch."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
        "BallisticType": "TimeOfFlight",
        "BallisticTypeValue": time_of_flight_s,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    if result["IsSuccess"] is not True:
        raise ValueError(result["Message"])
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


def propagate_sgp4(
    start: str,
    stop: str,
    tles: list[str],
    *,
    step: Optional[float] = None,
    satellite_number: Optional[str] = None,
    session: Optional[Client] = None,
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
    session: Optional[Client] = None,
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
    session: Optional[Client] = None,
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
    session: Optional[Client] = None,
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
    session: Optional[Client] = None,
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
    session: Optional[Client] = None,
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
