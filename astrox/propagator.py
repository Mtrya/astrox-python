"""Orbit propagation functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from astrox._http import raw
from astrox.orbits import KeplerianElements

__all__ = [
    "PropagatorPosition",
    "ballistic",
    "ballistic_apogee_altitude",
    "ballistic_delta_v",
    "ballistic_delta_v_min_ecc",
    "ballistic_time_of_flight",
    "j2",
    "sgp4",
    "simple_ascent",
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


def _success_path(result: dict[str, Any]) -> tuple[float, PropagatorPosition]:
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


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
    return _success_path(result)


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
    return _success_path(result)


def sgp4(
    *,
    start: str,
    stop: str,
    tle_lines: tuple[str, str],
    step_s: float | None = None,
    satellite_number: str | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a satellite from two-line element data using SGP4."""
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "TLEs": list(tle_lines),
    }
    if step_s is not None:
        payload["Step"] = step_s
    if satellite_number is not None:
        payload["SatelliteNumber"] = satellite_number

    result = raw.post("/Propagator/sgp4", json=payload)
    return _success_path(result)


def simple_ascent(
    *,
    start: str,
    stop: str,
    launch_latitude_deg: float,
    launch_longitude_deg: float,
    launch_altitude_m: float,
    burnout_velocity_m_s: float,
    burnout_latitude_deg: float,
    burnout_longitude_deg: float,
    burnout_altitude_m: float,
    step_s: float | None = None,
    central_body: str | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a simple ascent from launch point to burnout point."""
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "LaunchLatitude": launch_latitude_deg,
        "LaunchLongitude": launch_longitude_deg,
        "LaunchAltitude": launch_altitude_m,
        "BurnoutVelocity": burnout_velocity_m_s,
        "BurnoutLatitude": burnout_latitude_deg,
        "BurnoutLongitude": burnout_longitude_deg,
        "BurnoutAltitude": burnout_altitude_m,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body

    result = raw.post("/Propagator/SimpleAscent", json=payload)
    return _success_path(result)


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
    return _success_path(result)


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
    return _success_path(result)


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
    return _success_path(result)


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
    return _success_path(result)


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
    return _success_path(result)
