"""Public orbit value objects, constructors, and conversion helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from astrox._http import raw

__all__ = [
    "CartesianState",
    "KeplerianElements",
    "MeanKeplerianElements",
    "cartesian_state",
    "cartesian_to_keplerian",
    "transform_frame",
    "earth_moon_libration",
    "geo",
    "geo_ym_lambert_delta_v",
    "keplerian",
    "keplerian_to_cartesian",
    "kozai_izsak_mean_elements",
    "lambert_delta_v",
    "lla_at_ascending_node",
    "molniya",
    "sso",
    "walker_custom",
    "walker_delta",
    "walker_star",
]


@dataclass(frozen=True, kw_only=True)
class CartesianState:
    """Cartesian position and velocity state."""

    x_m: float
    y_m: float
    z_m: float
    vx_m_s: float
    vy_m_s: float
    vz_m_s: float

    def to_wire(self) -> list[float]:
        """Lower to ASTROX Cartesian OrbitalElements order."""
        return [
            self.x_m,
            self.y_m,
            self.z_m,
            self.vx_m_s,
            self.vy_m_s,
            self.vz_m_s,
        ]


@dataclass(frozen=True, kw_only=True)
class KeplerianElements:
    """Classical Keplerian orbital elements."""

    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    argument_of_periapsis_deg: float
    raan_deg: float
    true_anomaly_deg: float

    def to_wire(self) -> list[float]:
        """Lower to ASTROX Classical OrbitalElements order."""
        return [
            self.semi_major_axis_m,
            self.eccentricity,
            self.inclination_deg,
            self.argument_of_periapsis_deg,
            self.raan_deg,
            self.true_anomaly_deg,
        ]


@dataclass(frozen=True, kw_only=True)
class MeanKeplerianElements:
    """Kozai-Izsak mean Keplerian elements returned by ASTROX."""

    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    argument_of_perigee_deg: float
    raan_deg: float
    mean_anomaly_deg: float
    argument_of_latitude_deg: float
    longitude_of_perigee_deg: float
    mean_longitude_deg: float


def keplerian(
    *,
    semi_major_axis_m: float,
    eccentricity: float,
    inclination_deg: float,
    argument_of_periapsis_deg: float,
    raan_deg: float,
    true_anomaly_deg: float,
) -> KeplerianElements:
    """Create Classical Keplerian orbital elements."""
    return KeplerianElements(
        semi_major_axis_m=semi_major_axis_m,
        eccentricity=eccentricity,
        inclination_deg=inclination_deg,
        argument_of_periapsis_deg=argument_of_periapsis_deg,
        raan_deg=raan_deg,
        true_anomaly_deg=true_anomaly_deg,
    )


def cartesian_state(
    *,
    x_m: float,
    y_m: float,
    z_m: float,
    vx_m_s: float,
    vy_m_s: float,
    vz_m_s: float,
) -> CartesianState:
    """Create Cartesian position and velocity state."""
    return CartesianState(
        x_m=x_m,
        y_m=y_m,
        z_m=z_m,
        vx_m_s=vx_m_s,
        vy_m_s=vy_m_s,
        vz_m_s=vz_m_s,
    )


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _keplerian_to_wire_object(
    orbit: KeplerianElements,
    *,
    gravitational_parameter_m3_s2: float | None = None,
) -> dict[str, Any]:
    if not isinstance(orbit, KeplerianElements):
        raise TypeError("orbit must be a KeplerianElements instance")

    payload: dict[str, Any] = {
        "SemimajorAxis": orbit.semi_major_axis_m,
        "Eccentricity": orbit.eccentricity,
        "Inclination": orbit.inclination_deg,
        "ArgumentOfPeriapsis": orbit.argument_of_periapsis_deg,
        "RightAscensionOfAscendingNode": orbit.raan_deg,
        "TrueAnomaly": orbit.true_anomaly_deg,
    }
    _include_if_supplied(
        payload,
        "GravitationalParameter",
        gravitational_parameter_m3_s2,
    )
    return payload


def _keplerian_from_wire_object(payload: dict[str, Any]) -> KeplerianElements:
    return KeplerianElements(
        semi_major_axis_m=payload["SemimajorAxis"],
        eccentricity=payload["Eccentricity"],
        inclination_deg=payload["Inclination"],
        argument_of_periapsis_deg=payload["ArgumentOfPeriapsis"],
        raan_deg=payload["RightAscensionOfAscendingNode"],
        true_anomaly_deg=payload["TrueAnomaly"],
    )


def _mean_keplerian_from_wire_object(payload: dict[str, Any]) -> MeanKeplerianElements:
    return MeanKeplerianElements(
        semi_major_axis_m=payload["SemimajorAxis"],
        eccentricity=payload["Eccentricity"],
        inclination_deg=payload["Inclination"],
        argument_of_perigee_deg=payload["ArgOfPerigee"],
        raan_deg=payload["RAAN"],
        mean_anomaly_deg=payload["MeanAnomaly"],
        argument_of_latitude_deg=payload["ArgOfLatitude"],
        longitude_of_perigee_deg=payload["LongitudeOfPerigee"],
        mean_longitude_deg=payload["MeanLongitude"],
    )


def _cartesian_from_wire(values: Sequence[float]) -> CartesianState:
    return CartesianState(
        x_m=values[0],
        y_m=values[1],
        z_m=values[2],
        vx_m_s=values[3],
        vy_m_s=values[4],
        vz_m_s=values[5],
    )


def _wizard_pair_from_wire(
    result: dict[str, Any],
) -> tuple[KeplerianElements, KeplerianElements]:
    return (
        _keplerian_from_wire_object(result["Elements_TOD"]),
        _keplerian_from_wire_object(result["Elements_Inertial"]),
    )


def _walker_from_wire(
    result: dict[str, Any],
) -> tuple[tuple[KeplerianElements, ...], ...]:
    return tuple(
        tuple(_keplerian_from_wire_object(satellite) for satellite in plane)
        for plane in result["WalkerSatellites"]
    )


def keplerian_to_cartesian(
    orbit: KeplerianElements,
    *,
    gravitational_parameter_m3_s2: float | None = None,
) -> CartesianState:
    """Convert Keplerian elements to Cartesian state in meters and meters per second."""
    payload = _keplerian_to_wire_object(
        orbit,
        gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
    )

    result = raw.post("/OrbitConvert/Kepler2RV", json=payload)
    return _cartesian_from_wire(result)


def cartesian_to_keplerian(state: CartesianState) -> KeplerianElements:
    """Convert Cartesian state to Keplerian elements using ASTROX's default Earth gravity parameter."""
    if not isinstance(state, CartesianState):
        raise TypeError("state must be a CartesianState instance")

    result = raw.post("/OrbitConvert/RV2Kepler", json=state.to_wire())
    return _keplerian_from_wire_object(result)


def lla_at_ascending_node(
    orbit: KeplerianElements,
    *,
    orbit_epoch: str,
) -> tuple[float, float, float]:
    """Return ascending-node location as ``(longitude_deg, latitude_deg, height_m)``."""
    payload = {
        "OrbitEpoch": orbit_epoch,
        **_keplerian_to_wire_object(orbit),
    }

    result = raw.post("/OrbitConvert/Kepler2LLAAtAscendNode", json=payload)
    return result[0], result[1], result[2]


def kozai_izsak_mean_elements(orbit: KeplerianElements) -> MeanKeplerianElements:
    """Convert osculating Keplerian elements to Kozai-Izsak mean elements."""
    result = raw.post(
        "/OrbitConvert/GetKozaiIzsakMeanElements",
        json=_keplerian_to_wire_object(orbit),
    )
    return _mean_keplerian_from_wire_object(result)


def geo(
    *,
    orbit_epoch: str,
    inclination_deg: float,
    subsatellite_longitude_deg: float,
) -> tuple[KeplerianElements, KeplerianElements]:
    """Generate GEO elements as ``(elements_tod, elements_inertial)``."""
    result = raw.post(
        "/OrbitWizard/GEO",
        json={
            "OrbitEpoch": orbit_epoch,
            "Inclination": inclination_deg,
            "SubSatellitePoint": subsatellite_longitude_deg,
        },
    )
    return _wizard_pair_from_wire(result)


def molniya(
    *,
    orbit_epoch: str,
    perigee_altitude_km: float,
    apogee_longitude_deg: float,
    argument_of_periapsis_deg: float,
) -> tuple[KeplerianElements, KeplerianElements]:
    """Generate Molniya elements as ``(elements_tod, elements_inertial)``."""
    result = raw.post(
        "/OrbitWizard/Molniya",
        json={
            "OrbitEpoch": orbit_epoch,
            "PerigeeAltitude": perigee_altitude_km,
            "ApogeeLongitude": apogee_longitude_deg,
            "ArgumentOfPeriapsis": argument_of_periapsis_deg,
        },
    )
    return _wizard_pair_from_wire(result)


def sso(
    *,
    orbit_epoch: str,
    altitude_km: float,
    local_time_of_descending_node_hours: float,
) -> tuple[KeplerianElements, KeplerianElements]:
    """Generate SSO elements as ``(elements_tod, elements_inertial)``."""
    result = raw.post(
        "/OrbitWizard/SSO",
        json={
            "OrbitEpoch": orbit_epoch,
            "Altitude": altitude_km,
            "LocalTimeOfDescendingNode": local_time_of_descending_node_hours,
        },
    )
    return _wizard_pair_from_wire(result)


def _walker(
    *,
    seed_orbit: KeplerianElements,
    walker_type: str,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_phase_increment: int | None = None,
    inter_plane_true_anomaly_increment_deg: float | None = None,
    raan_increment_deg: float | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]:
    payload: dict[str, Any] = {
        "SeedKepler": _keplerian_to_wire_object(seed_orbit),
        "WalkerType": walker_type,
        "NumPlanes": num_planes,
        "NumSatsPerPlane": num_sats_per_plane,
    }
    _include_if_supplied(
        payload,
        "InterPlanePhaseIncrement",
        inter_plane_phase_increment,
    )
    _include_if_supplied(
        payload,
        "InterPlaneTrueAnomalyIncrement",
        inter_plane_true_anomaly_increment_deg,
    )
    _include_if_supplied(payload, "RAANIncrement", raan_increment_deg)

    result = raw.post("/OrbitWizard/Walker", json=payload)
    return _walker_from_wire(result)


def walker_delta(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_phase_increment: int | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]:
    """Generate a Walker Delta constellation as nested ``(plane, satellite)`` tuples."""
    return _walker(
        seed_orbit=seed_orbit,
        walker_type="Delta",
        num_planes=num_planes,
        num_sats_per_plane=num_sats_per_plane,
        inter_plane_phase_increment=inter_plane_phase_increment,
    )


def walker_star(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_phase_increment: int | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]:
    """Generate a Walker Star constellation as nested ``(plane, satellite)`` tuples."""
    return _walker(
        seed_orbit=seed_orbit,
        walker_type="Star",
        num_planes=num_planes,
        num_sats_per_plane=num_sats_per_plane,
        inter_plane_phase_increment=inter_plane_phase_increment,
    )


def walker_custom(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_true_anomaly_increment_deg: float | None = None,
    raan_increment_deg: float | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]:
    """Generate a custom Walker constellation as nested ``(plane, satellite)`` tuples."""
    return _walker(
        seed_orbit=seed_orbit,
        walker_type="Custom",
        num_planes=num_planes,
        num_sats_per_plane=num_sats_per_plane,
        inter_plane_true_anomaly_increment_deg=inter_plane_true_anomaly_increment_deg,
        raan_increment_deg=raan_increment_deg,
    )


def geo_ym_lambert_delta_v(
    *,
    platform_orbit: KeplerianElements,
    target_orbit: KeplerianElements,
    time_of_flight_s: float,
    platform_gravitational_parameter_m3_s2: float | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return Lambert delta-v as ``(departure_delta_v_m_s, arrival_delta_v_m_s)``."""
    payload = {
        "keplerPt": _keplerian_to_wire_object(
            platform_orbit,
            gravitational_parameter_m3_s2=platform_gravitational_parameter_m3_s2,
        ),
        "keplerMb": _keplerian_to_wire_object(target_orbit),
        "tof": time_of_flight_s,
    }

    result = raw.post("/OrbitConvert/CalGEOYMLambertDv", json=payload)
    return (
        (result[0], result[1], result[2]),
        (result[3], result[4], result[5]),
    )


def lambert_delta_v(
    *,
    departure_state: CartesianState,
    arrival_state: CartesianState,
    time_of_flight_s: float,
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return single-revolution Lambert delta-v between two Cartesian states."""
    if not isinstance(departure_state, CartesianState):
        raise TypeError("departure_state must be a CartesianState instance")
    if not isinstance(arrival_state, CartesianState):
        raise TypeError("arrival_state must be a CartesianState instance")

    payload: dict[str, Any] = {
        "RV1": departure_state.to_wire(),
        "RV2": arrival_state.to_wire(),
        "TOF": [time_of_flight_s],
    }
    _include_if_supplied(payload, "Gm", gravitational_parameter_m3_s2)

    result = raw.post("/orbit/lambert", json=payload)
    return (
        (result["DV1"][0], result["DV1"][1], result["DV1"][2]),
        (result["DV2"][0], result["DV2"][1], result["DV2"][2]),
    )


def transform_frame(
    position: entities.CzmlPosition,
    *,
    to_central_body: str,
    target_reference_frame: str | None = None,
) -> tuple[float, entities.CzmlPosition]:
    """Transform a sampled CZML position to another central-body frame.

    Returns ``(period_s, transformed_position)``.
    """
    if not isinstance(position, entities.CzmlPosition):
        raise TypeError("position must be a CzmlPosition instance")

    params: dict[str, Any] = {"toCb": to_central_body}
    _include_if_supplied(params, "referenceFrame", target_reference_frame)

    result = raw.post(
        "/OrbitSystem/CentralBodyFrame",
        json=position.to_czml_wire(),
        params=params,
    )
    return result["Period"], entities.CzmlPosition.from_czml_wire(result["Position"])


def earth_moon_libration(
    position: entities.CzmlPosition,
) -> entities.CzmlPositionSTM:
    """Transform a sampled CZML position to the Earth-Moon libration frame.

    Wires to ``/OrbitSystem/EarthMoonLibration2``.
    """
    if not isinstance(position, entities.CzmlPosition):
        raise TypeError("position must be a CzmlPosition instance")

    result = raw.post(
        "/OrbitSystem/EarthMoonLibration2",
        json=position.to_czml_wire(),
    )
    return entities.CzmlPositionSTM.from_czml_wire(result["position"])


import astrox.entities as entities  # noqa: E402
