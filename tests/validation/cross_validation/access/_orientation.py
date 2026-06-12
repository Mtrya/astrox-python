"""Independent orientation geometry helpers for access cross-validation."""

# Coverage:
#   Branches:
#     - two-body inertial state sampling and WGS84 site target construction: partial
#     - VVLH, VNC, fixed, fixed-at-epoch, and composite axes local candidates: partial
#     - quaternion, Euler, and Az/El fixed-pointing local candidates: partial
#     - conic and rectangular sensor field-of-view predicates: partial
#     - VGT aligned-and-constrained TRIAD-style construction: partial
#   Fields:
#     - AccessStart/AccessStop local interval oracle for sensor-constrained access: partial
#   Parameters:
#     - rotation angles, quaternion components, sensor widths, composite interval cuts, and target choices: partial
#   Comparison path:
#     - External: independent two-body geometry with local frame/FOV derivations and WGS84 obstruction checks

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from skyfield.framelib import itrs

from astrox import access, entities, orbits
from tests.validation.cross_validation.access._cases import (
    EARTH_MU,
    START,
    STOP,
    CrossValidationError,
)
from tests.validation.cross_validation.access._geometry import (
    BRACKET_ABS_S,
    SAMPLE_STEP_S,
    Interval,
    compare_intervals,
    elements_to_cartesian,
    intervals_from_access_passes,
    parse_time,
    segment_intersects_wgs84,
    skyfield_site,
    time_at_offset,
    true_to_mean_deg,
    mean_to_true_deg,
)

ORIENTATION_INTERVAL_ABS_S = 0.5
SHORT_SAMPLE_STEP_S = 1.0
CONTROLLED_SEMI_MAJOR_AXIS_M = 6878137.0
CONTROLLED_ECCENTRICITY = 0.001
CONTROLLED_INCLINATION_DEG = 45.0
CONTROLLED_RAAN_DEG = 20.0
CONTROLLED_TRUE_ANOMALY_DEG = 10.0
SUBPOINT_HEIGHT_M = 0.0
BLOCKED_SITE_LONGITUDE_DEG = -105.0
BLOCKED_SITE_LATITUDE_DEG = 40.0
BLOCKED_SITE_HEIGHT_M = 1800.0
COMPOSITE_SWITCH_S = 20.0

Vector = np.ndarray
Frame = np.ndarray
StateFunction = Callable[[float], tuple[Vector, Vector]]


@dataclass(frozen=True, kw_only=True)
class SensorCase:
    id: str
    observer: entities.Entity
    target: entities.Entity
    expected: list[Interval]


def controlled_orbit(*, true_anomaly_offset_deg: float = 0.0) -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=CONTROLLED_SEMI_MAJOR_AXIS_M,
        eccentricity=CONTROLLED_ECCENTRICITY,
        inclination_deg=CONTROLLED_INCLINATION_DEG,
        argument_of_periapsis_deg=0.0,
        raan_deg=CONTROLLED_RAAN_DEG,
        true_anomaly_deg=CONTROLLED_TRUE_ANOMALY_DEG + true_anomaly_offset_deg,
    )


def two_body_entity(
    *,
    name: str,
    orbit: orbits.KeplerianElements | None = None,
    orientation: entities.EntityAxes | None = None,
    sensor: entities.EntitySensor | None = None,
    sensor_pointing: entities.SensorPointing | None = None,
    vgt: entities.VgtProvider | None = None,
) -> entities.Entity:
    orbit = controlled_orbit() if orbit is None else orbit
    return entities.entity(
        name=name,
        position=entities.two_body_position(
            orbit_epoch=START,
            orbit=orbit,
            start=START,
            stop=STOP,
            step_s=120.0,
            gravitational_parameter_m3_s2=EARTH_MU,
        ),
        vgt=vgt,
        orientation=orientation,
        sensor=sensor,
        sensor_pointing=sensor_pointing,
    )


def subpoint_site() -> entities.Entity:
    lon_deg, lat_deg = subpoint_geodetic_degrees(0.0)
    return entities.entity(
        name="Subpoint",
        position=entities.site_position(
            longitude_deg=lon_deg,
            latitude_deg=lat_deg,
            height_m=SUBPOINT_HEIGHT_M,
        ),
    )


def blocked_site() -> entities.Entity:
    return entities.entity(
        name="BlockedSite",
        position=entities.site_position(
            longitude_deg=BLOCKED_SITE_LONGITUDE_DEG,
            latitude_deg=BLOCKED_SITE_LATITUDE_DEG,
            height_m=BLOCKED_SITE_HEIGHT_M,
        ),
    )


def target_satellite(delta_true_anomaly_deg: float) -> entities.Entity:
    return two_body_entity(
        name=f"TargetSat{delta_true_anomaly_deg:g}",
        orbit=controlled_orbit(true_anomaly_offset_deg=delta_true_anomaly_deg),
    )


def compute_sensor_access(observer: entities.Entity, target: entities.Entity) -> list[Interval]:
    result = access.compute(
        start=START,
        stop=STOP,
        from_entity=observer,
        to_entity=target,
        step_s=120.0,
        compute_aer=True,
    )
    return intervals_from_access_passes(result["Passes"])


def compare_sensor_case(case: SensorCase) -> None:
    actual = compute_sensor_access(case.observer, case.target)
    compare_intervals(case.expected, actual, tolerance_s=ORIENTATION_INTERVAL_ABS_S)


def observer_with_sensor(
    *,
    name: str,
    orientation: entities.EntityAxes,
    sensor: entities.EntitySensor,
    rotation: entities.Rotation | None = None,
    vgt: entities.VgtProvider | None = None,
) -> entities.Entity:
    return two_body_entity(
        name=name,
        orientation=orientation,
        sensor=sensor,
        sensor_pointing=entities.fixed_sensor_pointing(rotation=rotation)
        if rotation is not None
        else None,
        vgt=vgt,
    )


def conic_sensor(half_angle_deg: float) -> entities.ConicSensor:
    return entities.conic_sensor(outer_half_angle_deg=half_angle_deg)


def rectangular_sensor(x_half_angle_deg: float, y_half_angle_deg: float) -> entities.RectangularSensor:
    return entities.rectangular_sensor(
        x_half_angle_deg=x_half_angle_deg,
        y_half_angle_deg=y_half_angle_deg,
    )


def expected_intervals(
    *,
    target_state: StateFunction,
    frame: Callable[[float], Frame],
    sensor_predicate: Callable[[Vector], bool],
    step_s: float = SHORT_SAMPLE_STEP_S,
    start_s: float = 0.0,
    stop_s: float = 7200.0,
) -> list[Interval]:
    observer_state = state_function(controlled_orbit())

    def visible(offset_s: float) -> bool:
        observer_position, _ = observer_state(offset_s)
        target_position, _ = target_state(offset_s)
        observer_ecef = inertial_to_ecef(observer_position, offset_s)
        target_ecef = inertial_to_ecef(target_position, offset_s)
        if segment_intersects_wgs84(observer_ecef, target_ecef):
            return False
        relative_inertial = target_position - observer_position
        relative_body = frame(offset_s).T @ unit(relative_inertial)
        return sensor_predicate(relative_body)

    return sampled_intervals(visible, start_s=start_s, stop_s=stop_s, step_s=step_s)


def expected_site_intervals(
    *,
    site: entities.Entity,
    frame: Callable[[float], Frame],
    sensor_predicate: Callable[[Vector], bool],
    step_s: float = SHORT_SAMPLE_STEP_S,
    stop_s: float = 7200.0,
) -> list[Interval]:
    site_position = site.position
    if not isinstance(site_position, entities.SitePosition):
        raise TypeError("site must use SitePosition")
    target_ecef = site_ecef(
        latitude_deg=site_position.latitude_deg,
        longitude_deg=site_position.longitude_deg,
        height_m=site_position.height_m,
    )

    def target_state(offset_s: float) -> tuple[Vector, Vector]:
        return ecef_to_inertial(target_ecef, offset_s), np.zeros(3)

    return expected_intervals(
        target_state=target_state,
        frame=frame,
        sensor_predicate=sensor_predicate,
        step_s=step_s,
        stop_s=stop_s,
    )


def sampled_intervals(
    visible: Callable[[float], bool],
    *,
    start_s: float,
    stop_s: float,
    step_s: float,
) -> list[Interval]:
    samples = [start_s]
    current = start_s
    while current < stop_s:
        current = min(stop_s, current + step_s)
        samples.append(current)
    intervals: list[Interval] = []
    previous_offset = samples[0]
    previous_value = visible(previous_offset)
    current_start = previous_offset if previous_value else None
    for offset in samples[1:]:
        value = visible(offset)
        if value != previous_value:
            transition = bisect_transition(previous_offset, offset, visible)
            if value:
                current_start = transition
            elif current_start is not None:
                intervals.append(Interval(start_s=current_start, stop_s=transition))
                current_start = None
        previous_offset = offset
        previous_value = value
    if current_start is not None:
        intervals.append(Interval(start_s=current_start, stop_s=stop_s))
    return intervals


def bisect_transition(low_s: float, high_s: float, visible: Callable[[float], bool]) -> float:
    low_value = visible(low_s)
    while high_s - low_s > BRACKET_ABS_S:
        mid_s = (low_s + high_s) / 2.0
        if visible(mid_s) == low_value:
            low_s = mid_s
        else:
            high_s = mid_s
    return (low_s + high_s) / 2.0


def state_function(orbit: orbits.KeplerianElements) -> StateFunction:
    mean_motion_rad_s = math.sqrt(EARTH_MU / orbit.semi_major_axis_m**3)
    mean_anomaly_deg = true_to_mean_deg(orbit.true_anomaly_deg, orbit.eccentricity)

    def state(offset_s: float) -> tuple[Vector, Vector]:
        mean_anomaly_rad = math.radians(mean_anomaly_deg) + mean_motion_rad_s * offset_s
        true_anomaly_deg = mean_to_true_deg(mean_anomaly_rad, orbit.eccentricity)
        state_vector = elements_to_cartesian(
            (
                orbit.semi_major_axis_m,
                orbit.eccentricity,
                orbit.inclination_deg,
                orbit.raan_deg,
                orbit.argument_of_periapsis_deg,
                true_anomaly_deg,
            )
        )
        return np.array(state_vector[:3]), np.array(state_vector[3:])

    return state


def subpoint_geodetic_degrees(offset_s: float) -> tuple[float, float]:
    position, _ = state_function(controlled_orbit())(offset_s)
    ecef = inertial_to_ecef(position, offset_s)
    radius = float(np.linalg.norm(ecef))
    longitude_deg = math.degrees(math.atan2(float(ecef[1]), float(ecef[0])))
    latitude_deg = math.degrees(math.asin(float(ecef[2]) / radius))
    return longitude_deg, latitude_deg


def site_ecef(*, latitude_deg: float, longitude_deg: float, height_m: float) -> Vector:
    return np.array(
        skyfield_site(latitude_deg, longitude_deg, height_m)
        .at(time_at_offset(START, 0.0))
        .frame_xyz(itrs)
        .m
    )


def inertial_to_ecef(position_m: Vector, offset_s: float) -> Vector:
    return np.array(itrs.rotation_at(time_at_offset(START, offset_s)) @ position_m)


def ecef_to_inertial(position_m: Vector, offset_s: float) -> Vector:
    return np.array(itrs.rotation_at(time_at_offset(START, offset_s)).T @ position_m)


def vvlh_frame(offset_s: float) -> Frame:
    position, velocity = state_function(controlled_orbit())(offset_s)
    down = unit(-position)
    forward = unit(velocity - down * float(np.dot(velocity, down)))
    right = unit(np.cross(down, forward))
    return np.column_stack((forward, right, down))


def vnc_frame(offset_s: float) -> Frame:
    position, velocity = state_function(controlled_orbit())(offset_s)
    x_axis = unit(velocity)
    y_axis = unit(np.cross(position, velocity))
    z_axis = unit(np.cross(x_axis, y_axis))
    return np.column_stack((x_axis, y_axis, z_axis))


def lvlh_frame(offset_s: float) -> Frame:
    position, velocity = state_function(controlled_orbit())(offset_s)
    z_axis = unit(np.cross(position, velocity))
    x_axis = unit(position)
    y_axis = unit(np.cross(z_axis, x_axis))
    return np.column_stack((x_axis, y_axis, z_axis))


def fixed_frame(reference: Callable[[float], Frame], rotation: Frame) -> Callable[[float], Frame]:
    return lambda offset_s: reference(offset_s) @ rotation


def frozen_at_epoch_frame(source: Callable[[float], Frame], reference: Callable[[float], Frame]) -> Callable[[float], Frame]:
    source_epoch = source(0.0)
    reference_epoch = reference(0.0)
    frozen_rotation = reference_epoch.T @ source_epoch
    return lambda offset_s: reference(offset_s) @ frozen_rotation


def composite_frame(
    *,
    first: Callable[[float], Frame],
    second: Callable[[float], Frame],
    switch_s: float = COMPOSITE_SWITCH_S,
) -> Callable[[float], Frame]:
    return lambda offset_s: first(offset_s) if offset_s < switch_s else second(offset_s)


def inertial_frame(_: float) -> Frame:
    return np.identity(3)


def conic_predicate(half_angle_deg: float, boresight: Vector) -> Callable[[Vector], bool]:
    limit = math.cos(math.radians(half_angle_deg))
    boresight = unit(boresight)
    return lambda relative_body: float(np.dot(unit(relative_body), boresight)) >= limit


def rectangular_predicate(
    *,
    x_half_angle_deg: float,
    y_half_angle_deg: float,
    boresight_rotation: Frame,
) -> Callable[[Vector], bool]:
    x_limit = math.radians(x_half_angle_deg)
    y_limit = math.radians(y_half_angle_deg)

    def contains(relative_body: Vector) -> bool:
        camera = boresight_rotation.T @ unit(relative_body)
        if camera[2] <= 0.0:
            return False
        x_angle = abs(math.atan2(float(camera[0]), float(camera[2])))
        y_angle = abs(math.atan2(float(camera[1]), float(camera[2])))
        return x_angle <= x_limit and y_angle <= y_limit

    return contains


def az_el_boresight(*, azimuth_deg: float, elevation_deg: float) -> Vector:
    azimuth_rad = math.radians(azimuth_deg)
    elevation_rad = math.radians(elevation_deg)
    return np.array(
        [
            math.cos(elevation_rad) * math.cos(azimuth_rad),
            math.cos(elevation_rad) * math.sin(azimuth_rad),
            math.sin(elevation_rad),
        ]
    )


def quaternion_rotation(*, scalar: float, x: float, y: float, z: float) -> Frame:
    norm = math.sqrt(scalar * scalar + x * x + y * y + z * z)
    w = scalar / norm
    qx = x / norm
    qy = y / norm
    qz = z / norm
    return np.array(
        [
            [1.0 - 2.0 * (qy * qy + qz * qz), 2.0 * (qx * qy - qz * w), 2.0 * (qx * qz + qy * w)],
            [2.0 * (qx * qy + qz * w), 1.0 - 2.0 * (qx * qx + qz * qz), 2.0 * (qy * qz - qx * w)],
            [2.0 * (qx * qz - qy * w), 2.0 * (qy * qz + qx * w), 1.0 - 2.0 * (qx * qx + qy * qy)],
        ]
    )


def euler_321_rotation(*, a_deg: float, b_deg: float, c_deg: float) -> Frame:
    return rotation_z(a_deg) @ rotation_y(b_deg) @ rotation_x(c_deg)


def rotation_x(angle_deg: float) -> Frame:
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rotation_y(angle_deg: float) -> Frame:
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rotation_z(angle_deg: float) -> Frame:
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def triad_aligned_frame(
    *,
    principal_vector: Vector,
    principal_axis: str,
    reference_vector: Vector,
    reference_axis: str,
) -> Frame:
    principal = unit(principal_vector)
    reference = unit(reference_vector - principal * float(np.dot(reference_vector, principal)))
    axes: dict[str, Vector] = {}
    axes[principal_axis] = principal
    axes[reference_axis] = reference
    signed_axes = {axis.lstrip("+-"): value if axis.startswith("+") else -value for axis, value in axes.items()}
    if "X" in signed_axes and "Z" in signed_axes:
        signed_axes["Y"] = unit(np.cross(signed_axes["Z"], signed_axes["X"]))
    elif "X" in signed_axes and "Y" in signed_axes:
        signed_axes["Z"] = unit(np.cross(signed_axes["X"], signed_axes["Y"]))
    elif "Y" in signed_axes and "Z" in signed_axes:
        signed_axes["X"] = unit(np.cross(signed_axes["Y"], signed_axes["Z"]))
    else:
        raise CrossValidationError("TRIAD helper requires two distinct axes")
    return np.column_stack((signed_axes["X"], signed_axes["Y"], signed_axes["Z"]))


def unit(vector: Vector) -> Vector:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise CrossValidationError("zero-length vector in orientation helper")
    return vector / norm


def access_failed_with(exc: Exception, expected: str) -> bool:
    return expected in str(exc)


def parse_offset_s(value: str) -> float:
    return (parse_time(value) - parse_time(START)).total_seconds()
