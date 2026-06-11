"""Shared live access cases for access validation."""

from __future__ import annotations

from dataclasses import dataclass

from astrox import access, entities, orbits, propagator
from astrox.exceptions import AstroxAPIError

START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T02:00:00.000Z"
DAY_STOP = "2024-01-02T00:00:00.000Z"
EARTH_MU = 398600441500000.0
EARTH_RADIUS_M = 6378136.3
J2_NORMALIZED_VALUE = 0.000484165143790815
ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE = 0.000484166956667088
SPEED_OF_LIGHT_M_S = 299792458.0
TLE_A = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
TLE_B = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)
SITE_LONGITUDE_DEG = -155.468
SITE_LATITUDE_DEG = 19.821
SITE_HEIGHT_M = 4205.0
REMOTE_LONGITUDE_DEG = -4.2518
REMOTE_LATITUDE_DEG = 40.4903
REMOTE_HEIGHT_M = 700.0

INTERVAL_ABS_S = 0.25
CHAIN_INTERVAL_ABS_S = 5.0e-3
AER_CONVENTION_AZIMUTH_ABS_DEG = 5.0e-4
AER_CONVENTION_ELEVATION_ABS_DEG = 2.0e-4
AER_DENSE_AZIMUTH_ABS_DEG = 3.0e-3
AER_DENSE_ELEVATION_ABS_DEG = 1.5e-3
AER_CONVENTION_RANGE_ABS_M = 25.0
AER_STRICT_ABS_DEG = 1.0e-4
RANGE_SYMMETRY_ABS_M = 1.0e-6
SATELLITE_LOCAL_AER_ABS_DEG = 5.0e-3
LIGHT_TIME_SHIFT_ABS_S = 3.0e-3
LIGHT_TIME_AER_ABS_DEG = 1.0e-6
LIGHT_TIME_RANGE_ABS_M = 1.0e-3
SERVER_NO_PATH_MESSAGE = "未找到任何路径"
SERVER_INDEX_ERROR_MESSAGE = "Index was outside the bounds of the array"
SERVER_WORKER_THREAD_MESSAGE = "worker thread"


@dataclass(frozen=True, kw_only=True)
class BranchProbe:
    label: str
    success: bool
    message: str


class CrossValidationError(Exception):
    """Raised when ASTROX access behavior disagrees with a comparison path."""


def is_server_no_path_error(exc: AstroxAPIError) -> bool:
    return SERVER_NO_PATH_MESSAGE in str(exc)


def is_server_index_error(exc: AstroxAPIError) -> bool:
    return SERVER_INDEX_ERROR_MESSAGE in str(exc)


def is_server_worker_thread_message(message: str) -> bool:
    return SERVER_WORKER_THREAD_MESSAGE in message


def site(name: str = "Ground") -> entities.Entity:
    return entities.entity(
        name=name,
        position=entities.site_position(
            longitude_deg=SITE_LONGITUDE_DEG,
            latitude_deg=SITE_LATITUDE_DEG,
            height_m=SITE_HEIGHT_M,
        ),
    )


def remote_site() -> entities.Entity:
    return entities.entity(
        name="Madrid",
        position=entities.site_position(
            longitude_deg=REMOTE_LONGITUDE_DEG,
            latitude_deg=REMOTE_LATITUDE_DEG,
            height_m=REMOTE_HEIGHT_M,
        ),
    )


def sgp4_entity(name: str = "ISS", tle_lines: tuple[str, str] = TLE_A) -> entities.Entity:
    return entities.entity(name=name, position=entities.sgp4_position(tle_lines=tle_lines))


def access_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def distinct_access_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=7078137.0,
        eccentricity=0.002,
        inclination_deg=51.6,
        argument_of_periapsis_deg=10.0,
        raan_deg=120.0,
        true_anomaly_deg=5.0,
    )


def j2_entity() -> entities.Entity:
    return entities.entity(
        name="J2",
        position=entities.j2_position(
            orbit_epoch=START,
            orbit=access_orbit(),
            start=START,
            stop=STOP,
            step_s=300.0,
            coord_system="Inertial",
            gravitational_parameter_m3_s2=EARTH_MU,
            j2_normalized_value=J2_NORMALIZED_VALUE,
            ref_distance_m=EARTH_RADIUS_M,
        ),
    )


def two_body_entity(
    orbit: orbits.KeplerianElements | None = None,
    *,
    name: str = "TwoBody",
) -> entities.Entity:
    orbit = access_orbit() if orbit is None else orbit
    return entities.entity(
        name=name,
        position=entities.two_body_position(
            orbit_epoch=START,
            orbit=orbit,
            start=START,
            stop=STOP,
            step_s=300.0,
            coord_system="Inertial",
            gravitational_parameter_m3_s2=EARTH_MU,
        ),
    )


def hpop_entity(
    orbit: orbits.KeplerianElements | None = None,
    *,
    name: str = "HPOP",
) -> entities.Entity:
    orbit = access_orbit() if orbit is None else orbit
    return entities.entity(
        name=name,
        position=entities.hpop_position(
            start=START,
            stop=STOP,
            orbit_epoch=START,
            orbit=orbit,
            gravitational_parameter_m3_s2=EARTH_MU,
            config=propagator.hpop_config(
                integrator=propagator.hpop_rkf78(initial_step_s=30.0, max_step_s=120.0),
                gravity=propagator.hpop_two_body_gravity(),
            ),
        ),
    )


def compute_access(
    from_entity: entities.Entity,
    to_entity: entities.Entity,
    *,
    start: str = START,
    stop: str = STOP,
    step_s: float = 600.0,
    compute_aer: bool | None = None,
    use_light_time_delay: bool | None = None,
) -> dict[str, object]:
    return access.compute(
        start=start,
        stop=stop,
        from_entity=from_entity,
        to_entity=to_entity,
        step_s=step_s,
        compute_aer=compute_aer,
        use_light_time_delay=use_light_time_delay,
    )


def branch_probe(
    label: str,
    from_entity: entities.Entity,
    to_entity: entities.Entity,
) -> BranchProbe:
    try:
        result = compute_access(from_entity, to_entity)
    except AstroxAPIError as exc:
        return BranchProbe(label=label, success=False, message=str(exc))
    return BranchProbe(
        label=label,
        success=bool(result["IsSuccess"]),
        message=str(result["Message"]),
    )


def direct_chain_sgp4(*, use_light_time_delay: bool | None = None) -> dict[str, object]:
    ground = site()
    target = sgp4_entity()
    return access.chain(
        start=START,
        stop=STOP,
        participants=[ground, target],
        start_participant=ground,
        end_participant=target,
        use_light_time_delay=use_light_time_delay,
    )


def group_chain_anyof() -> dict[str, object]:
    ground = site()
    targets = entities.entity_group(
        name="Targets",
        members=[
            sgp4_entity("ISS", TLE_A),
            sgp4_entity("Hubble", TLE_B),
        ],
        to_restriction="AnyOf",
    )
    return access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, targets],
        start_participant=ground,
        end_participant=targets,
    )


def relay_chain() -> tuple[dict[str, object], entities.Entity, entities.Entity, entities.Entity]:
    ground_a = site("GroundA")
    relay = sgp4_entity("Relay")
    ground_b = entities.entity(
        name="GroundB",
        position=entities.site_position(
            longitude_deg=-150.0,
            latitude_deg=22.0,
            height_m=0.0,
        ),
    )
    result = access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground_a, relay, ground_b],
        start_participant=ground_a,
        end_participant=ground_b,
        connections=[
            access.connection(ground_a, relay),
            access.connection(relay, ground_b),
        ],
        use_light_time_delay=True,
    )
    return result, ground_a, relay, ground_b
