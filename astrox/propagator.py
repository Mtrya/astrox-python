"""Orbit propagation functions."""

from __future__ import annotations

from collections.abc import Sequence
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
    "multi_j2",
    "multi_sgp4",
    "multi_two_body",
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


def _keplerian_from_elements_object(payload: dict[str, Any]) -> KeplerianElements:
    return KeplerianElements(
        semi_major_axis_m=payload["SemimajorAxis"],
        eccentricity=payload["Eccentricity"],
        inclination_deg=payload["Inclination"],
        argument_of_periapsis_deg=payload["ArgumentOfPeriapsis"],
        raan_deg=payload["RightAscensionOfAscendingNode"],
        true_anomaly_deg=payload["TrueAnomaly"],
    )


def _batch_success_path(result: dict[str, Any]) -> tuple[KeplerianElements, ...]:
    return tuple(
        _keplerian_from_elements_object(item)
        for item in result["AllElementsAtEpoch"]
    )


def _state_item_to_wire(
    item: Sequence[object],
    *,
    gravitational_parameter_m3_s2: float | None,
) -> dict[str, Any]:
    if not isinstance(item, (list, tuple)) or len(item) != 2:
        raise TypeError("states items must be two-item sequences of orbit epoch and KeplerianElements")
    orbit_epoch, orbit = item
    if not isinstance(orbit_epoch, str):
        raise TypeError("states item orbit epoch must be a string")
    if not isinstance(orbit, KeplerianElements):
        raise TypeError("states item orbit must be a KeplerianElements instance")

    payload: dict[str, Any] = {
        "OrbitEpoch": orbit_epoch,
        "SemimajorAxis": orbit.semi_major_axis_m,
        "Eccentricity": orbit.eccentricity,
        "Inclination": orbit.inclination_deg,
        "ArgumentOfPeriapsis": orbit.argument_of_periapsis_deg,
        "RightAscensionOfAscendingNode": orbit.raan_deg,
        "TrueAnomaly": orbit.true_anomaly_deg,
    }
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    return payload


def _states_to_wire(
    states: Sequence[Sequence[object]],
    *,
    gravitational_parameter_m3_s2: float | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(states, Sequence) or isinstance(states, (str, bytes)):
        raise TypeError("states must be a sequence of two-item state sequences")
    return [
        _state_item_to_wire(
            item,
            gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        )
        for item in states
    ]


def _tle_set_to_wire(item: Sequence[object]) -> str:
    if not isinstance(item, (list, tuple)) or len(item) != 2:
        raise TypeError("tle_sets items must be two-item sequences of TLE strings")
    line1, line2 = item
    if not isinstance(line1, str) or not isinstance(line2, str):
        raise TypeError("tle_sets items must contain TLE strings")
    return f"{line1}\n{line2}"


def _tle_sets_to_wire(tle_sets: Sequence[Sequence[object]]) -> list[str]:
    if not isinstance(tle_sets, Sequence) or isinstance(tle_sets, (str, bytes)):
        raise TypeError("tle_sets must be a sequence of two-item TLE string sequences")
    return [_tle_set_to_wire(item) for item in tle_sets]


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


def multi_two_body(
    *,
    epoch: str,
    states: Sequence[tuple[str, KeplerianElements]],
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[KeplerianElements, ...]:
    """Propagate multiple Classical states to one target epoch using two-body dynamics.

    ASTROX raw batch responses include ``GravitationalParameter`` on each returned
    element. The curated return intentionally omits it because live behavior shows
    that field is not a reliable echo of the propagation parameter used for the
    result; use ``astrox.raw`` for the full raw envelope.
    """
    payload = {
        "Epoch": epoch,
        "AllSateElements": _states_to_wire(
            states,
            gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        ),
    }

    result = raw.post("/Propagator/MultiTwoBody", json=payload)
    return _batch_success_path(result)


def multi_j2(
    *,
    epoch: str,
    states: Sequence[tuple[str, KeplerianElements]],
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[KeplerianElements, ...]:
    """Propagate multiple Classical states to one target epoch using ASTROX J2.

    The batch ASTROX route owns its J2 constants; the curated SDK does not expose
    J2 constants for this function because live behavior does not show those
    inputs affecting the endpoint. ASTROX raw batch responses include
    ``GravitationalParameter`` on each returned element. The curated return
    intentionally omits it because live behavior shows that field is not a
    reliable echo of the propagation parameter used for the result; use
    ``astrox.raw`` for the full raw envelope.
    """
    payload = {
        "Epoch": epoch,
        "AllSateElements": _states_to_wire(
            states,
            gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        ),
    }

    result = raw.post("/Propagator/MultiJ2", json=payload)
    return _batch_success_path(result)


def multi_sgp4(
    *,
    epoch: str,
    tle_sets: Sequence[tuple[str, str]],
) -> tuple[KeplerianElements, ...]:
    """Propagate multiple TLEs to one target epoch using SGP4.

    Each public ``tle_sets`` item is a two-line TLE sequence. The SDK lowers it
    to the ASTROX batch route's newline-joined string format. ASTROX raw batch
    responses include ``GravitationalParameter`` on each returned element. The
    curated return intentionally omits it because live behavior shows that field
    is not a reliable echo of the propagation parameter used for the result; use
    ``astrox.raw`` for the full raw envelope.
    """
    payload = {
        "Epoch": epoch,
        "TLEs": _tle_sets_to_wire(tle_sets),
    }

    result = raw.post("/Propagator/MultiSgp4", json=payload)
    return _batch_success_path(result)


def sgp4(
    *,
    start: str,
    stop: str,
    tle_lines: tuple[str, str] | list[str],
    step_s: float | None = None,
    satellite_number: str | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a satellite from two-line element data using SGP4."""
    if (
        not isinstance(tle_lines, (list, tuple))
        or len(tle_lines) != 2
        or not all(isinstance(line, str) for line in tle_lines)
    ):
        raise TypeError("tle_lines must be a two-item sequence of TLE strings")

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
