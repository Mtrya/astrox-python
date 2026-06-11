"""Independent geometry and interval helpers for access validation."""

# Coverage:
#   Branches:
#     - WGS84 segment-obstruction interval oracle: partial
#     - SGP4 site visibility oracle: partial
#     - sampled satellite-pair visibility oracle: partial
#     - ASTROX-like J2 state helper for access comparison: partial
#   Fields:
#     - AccessStart/AccessStop and chain Start/Stop interval parsing helpers: partial
#   Parameters:
#     - start/stop sampling, bracket tolerance, WGS84 ellipsoid constants, and ASTROX J2 constants: partial
#   Comparison path:
#     - External: Skyfield SGP4/site states, WGS84 ellipsoid obstruction, Brahe Kepler/J2 transforms where used

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

import brahe as bh
import numpy as np
from skyfield.api import EarthSatellite, load, wgs84
from skyfield.framelib import itrs

from astrox import orbits

from tests.validation.cross_validation.access._cases import (
    ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE,
    CHAIN_INTERVAL_ABS_S,
    EARTH_MU,
    EARTH_RADIUS_M,
    START,
    TLE_A,
)

WGS84_A_M = 6378137.0
WGS84_B_M = 6356752.314245179
SAMPLE_STEP_S = 60.0
BRACKET_ABS_S = 0.01


@dataclass(frozen=True, kw_only=True)
class Interval:
    start_s: float
    stop_s: float


def intervals_from_access_passes(values: list[dict[str, object]]) -> list[Interval]:
    return [
        Interval(
            start_s=seconds_since(str(item["AccessStart"]), START),
            stop_s=seconds_since(str(item["AccessStop"]), START),
        )
        for item in values
    ]


def intervals_from_chain(values: list[dict[str, object]]) -> list[Interval]:
    return [
        Interval(
            start_s=seconds_since(str(item["Start"]), START),
            stop_s=seconds_since(str(item["Stop"]), START),
        )
        for item in values
    ]


def compare_intervals(
    expected: list[Interval],
    actual: list[Interval],
    *,
    tolerance_s: float,
) -> None:
    from tests.validation.cross_validation.access._cases import CrossValidationError

    failures: list[str] = []
    if len(expected) != len(actual):
        raise CrossValidationError(
            f"interval count mismatch: expected={len(expected)} actual={len(actual)}"
        )
    for index, (expected_interval, actual_interval) in enumerate(zip(expected, actual, strict=True)):
        start_error_s = abs(expected_interval.start_s - actual_interval.start_s)
        stop_error_s = abs(expected_interval.stop_s - actual_interval.stop_s)
        if start_error_s > tolerance_s:
            failures.append(
                f"interval {index} start error {start_error_s:.12g} s exceeds {tolerance_s:.12g} s"
            )
        if stop_error_s > tolerance_s:
            failures.append(
                f"interval {index} stop error {stop_error_s:.12g} s exceeds {tolerance_s:.12g} s"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def intersect_intervals(left: list[Interval], right: list[Interval]) -> list[Interval]:
    intersections: list[Interval] = []
    for left_interval in left:
        for right_interval in right:
            start_s = max(left_interval.start_s, right_interval.start_s)
            stop_s = min(left_interval.stop_s, right_interval.stop_s)
            if start_s <= stop_s:
                intersections.append(Interval(start_s=start_s, stop_s=stop_s))
    return merge_intervals(intersections)


def merge_intervals(values: list[Interval]) -> list[Interval]:
    if not values:
        return []
    intervals = sorted(values, key=lambda interval: interval.start_s)
    merged = [intervals[0]]
    for interval in intervals[1:]:
        last = merged[-1]
        if interval.start_s <= last.stop_s + CHAIN_INTERVAL_ABS_S:
            merged[-1] = Interval(
                start_s=last.start_s,
                stop_s=max(last.stop_s, interval.stop_s),
            )
        else:
            merged.append(interval)
    return merged


def sgp4_site_visibility_intervals(
    *,
    start: str,
    stop: str,
    satellite: EarthSatellite,
    site_position: object,
) -> list[Interval]:
    def visible(offset_s: float) -> bool:
        instant = time_at_offset(start, offset_s)
        observer_ecef = np.array(site_position.at(instant).frame_xyz(itrs).m)
        satellite_ecef = np.array(satellite.at(instant).frame_xyz(itrs).m)
        return not segment_intersects_wgs84(observer_ecef, satellite_ecef)

    return visibility_intervals(start=start, stop=stop, visible=visible)


def sampled_satellite_visibility_intervals(
    *,
    start: str,
    stop: str,
    left_state: Callable[[float], np.ndarray],
    right_state: Callable[[float], np.ndarray],
) -> list[Interval]:
    def visible(offset_s: float) -> bool:
        return not segment_intersects_wgs84(left_state(offset_s), right_state(offset_s))

    return visibility_intervals(start=start, stop=stop, visible=visible)


def visibility_intervals(
    *,
    start: str,
    stop: str,
    visible: Callable[[float], bool],
) -> list[Interval]:
    total_s = (parse_time(stop) - parse_time(start)).total_seconds()
    samples = [0.0]
    current = 0.0
    while current < total_s:
        current = min(total_s, current + SAMPLE_STEP_S)
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
        intervals.append(Interval(start_s=current_start, stop_s=total_s))
    return intervals


def bisect_transition(
    low_s: float,
    high_s: float,
    visible: Callable[[float], bool],
) -> float:
    low_value = visible(low_s)
    while high_s - low_s > BRACKET_ABS_S:
        mid_s = (low_s + high_s) / 2.0
        if visible(mid_s) == low_value:
            low_s = mid_s
        else:
            high_s = mid_s
    return (low_s + high_s) / 2.0


def segment_intersects_wgs84(start_ecef_m: np.ndarray, stop_ecef_m: np.ndarray) -> bool:
    direction = stop_ecef_m - start_ecef_m
    scale = np.array([1.0 / WGS84_A_M, 1.0 / WGS84_A_M, 1.0 / WGS84_B_M])
    p = start_ecef_m * scale
    d = direction * scale
    a = float(np.dot(d, d))
    b = 2.0 * float(np.dot(p, d))
    c = float(np.dot(p, p) - 1.0)
    discriminant = b * b - 4.0 * a * c
    if discriminant <= 0.0:
        return False
    sqrt_discriminant = math.sqrt(discriminant)
    root_a = (-b - sqrt_discriminant) / (2.0 * a)
    root_b = (-b + sqrt_discriminant) / (2.0 * a)
    return (1.0e-12 < root_a < 1.0 - 1.0e-12) or (1.0e-12 < root_b < 1.0 - 1.0e-12)


def fixed_site_ecef(latitude_deg: float, longitude_deg: float, height_m: float) -> np.ndarray:
    return np.array(
        skyfield_site(latitude_deg, longitude_deg, height_m)
        .at(skyfield_time(START))
        .frame_xyz(itrs)
        .m
    )


def sgp4_state_ecef(offset_s: float) -> np.ndarray:
    return np.array(skyfield_satellite(TLE_A, "ISS").at(time_at_offset(START, offset_s)).frame_xyz(itrs).m)


def j2_state_ecef(orbit: orbits.KeplerianElements, offset_s: float) -> np.ndarray:
    state = elements_to_cartesian(astrox_like_j2_elements(orbit, offset_s))
    return inertial_to_ecef(state[:3], offset_s)


def inertial_to_ecef(position_m: np.ndarray, offset_s: float) -> np.ndarray:
    instant = time_at_offset(START, offset_s)
    return np.array(itrs.rotation_at(instant) @ position_m)


def astrox_like_j2_elements(
    orbit: orbits.KeplerianElements,
    offset_s: float,
) -> tuple[float, float, float, float, float, float]:
    semi_major_axis_m = orbit.semi_major_axis_m
    eccentricity = orbit.eccentricity
    inclination_rad = math.radians(orbit.inclination_deg)
    p = semi_major_axis_m * (1.0 - eccentricity * eccentricity)
    keplerian_mean_motion_rad_s = math.sqrt(EARTH_MU / semi_major_axis_m**3)
    j2 = math.sqrt(5.0) * ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE
    factor = j2 * (EARTH_RADIUS_M / p) ** 2
    cos_i = math.cos(inclination_rad)
    beta = math.sqrt(1.0 - eccentricity * eccentricity)
    corrected_mean_motion_rad_s = keplerian_mean_motion_rad_s * (
        1.0 + 0.75 * factor * beta * (3.0 * cos_i * cos_i - 1.0)
    )
    raan_rate = -1.5 * corrected_mean_motion_rad_s * factor * cos_i
    argument_rate = 0.75 * corrected_mean_motion_rad_s * factor * (5.0 * cos_i * cos_i - 1.0)
    mean_anomaly_rate = keplerian_mean_motion_rad_s + (
        0.75 * keplerian_mean_motion_rad_s * factor * beta * (3.0 * cos_i * cos_i - 1.0)
    )
    mean_anomaly_deg = true_to_mean_deg(orbit.true_anomaly_deg, eccentricity)
    propagated_mean_deg = (mean_anomaly_deg + math.degrees(mean_anomaly_rate * offset_s)) % 360.0
    return (
        semi_major_axis_m,
        eccentricity,
        orbit.inclination_deg,
        (orbit.raan_deg + math.degrees(raan_rate * offset_s)) % 360.0,
        (orbit.argument_of_periapsis_deg + math.degrees(argument_rate * offset_s)) % 360.0,
        propagated_mean_deg,
    )


def elements_to_cartesian(elements: tuple[float, float, float, float, float, float]) -> np.ndarray:
    return bh.state_koe_to_eci(np.array(elements), bh.AngleFormat.DEGREES)


def true_to_mean_deg(true_anomaly_deg: float, eccentricity: float) -> float:
    nu = math.radians(true_anomaly_deg)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 - eccentricity) * math.sin(nu / 2.0),
        math.sqrt(1.0 + eccentricity) * math.cos(nu / 2.0),
    )
    mean_anomaly = eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly)
    return math.degrees(mean_anomaly) % 360.0


def wrapped_angle_error_deg(actual: float, expected: float) -> float:
    return (actual - expected + 180.0) % 360.0 - 180.0


def seconds_since(value: str, start: str) -> float:
    return (parse_time(value) - parse_time(start)).total_seconds()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def skyfield_time(value: str):
    return ts().from_datetime(parse_time(value))


def time_at_offset(start: str, offset_s: float):
    return ts().from_datetime(parse_time(start) + timedelta(seconds=offset_s))


def skyfield_satellite(tle_lines: tuple[str, str], name: str) -> EarthSatellite:
    return EarthSatellite(tle_lines[0], tle_lines[1], name, ts())


def skyfield_site(latitude_deg: float, longitude_deg: float, height_m: float):
    return wgs84.latlon(
        latitude_degrees=latitude_deg,
        longitude_degrees=longitude_deg,
        elevation_m=height_m,
    )


def ts():
    return load.timescale(builtin=True)
