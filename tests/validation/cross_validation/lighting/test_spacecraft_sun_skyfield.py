#!/usr/bin/env python3
"""Live ASTROX spacecraft Sun-geometry cross-validation against Skyfield."""

# Coverage:
#   Branches:
#     - spacecraft SolarAER from SGP4: verified for the documented VVLH front-right-down frame with ASTROX's observed Sun-vector convention
#     - spacecraft LightingTimes from SGP4: verified for ISS eclipse-cycle intervals
#   Fields:
#     - SolarAER Azimuth/Elevation/Range: partial (VVLH convention verified; range and elevation retain narrow DE421-vs-ASTROX-ephemeris/vector-convention tolerances)
#     - LightingTimes sunlight/penumbra/umbra intervals: verified against conical Earth/Sun disk transition geometry
#   Parameters:
#     - spacecraft TLE/step_s: partial (ISS SGP4 representative case)
#     - start/stop windows: partial (short SolarAER sample window and multi-orbit eclipse window)
#   Comparison:
#     - External: Skyfield SGP4 state, apparent Sun vector, and conical Earth-shadow geometry
#     - Constants: WGS84 Earth equatorial radius, Sun radius, ISS_TLE_LINES
#     - Tolerances: SOLAR_AER_* and LIGHTING_TRANSITION_ABS_S constants
#   Unresolved:
#     - SolarAER spacecraft elevation appears to use geocentric-Sun horizontal components with apparent spacecraft-to-Sun vertical/range components; this test encodes that observed ASTROX convention instead of assuming a single physical vector

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skyfield.api import EarthSatellite, Loader

from astrox import entities, lighting
from tests.validation._support import LiveConfigError, configure_astrox_from_env


EARTH_EQUATORIAL_RADIUS_KM = 6378.137
SUN_RADIUS_KM = 695700.0
SOLAR_AER_AZIMUTH_ABS_DEG = 1.0e-4
SOLAR_AER_ELEVATION_ABS_DEG = 7.0e-4
SOLAR_AER_RANGE_ABS_KM = 25.0
LIGHTING_TRANSITION_ABS_S = 3.0
LIGHTING_ROOT_BRACKET_S = 120.0
ISS_TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
Vector3 = tuple[float, float, float]


@dataclass(frozen=True, kw_only=True)
class SpacecraftSolarAerCase:
    id: str
    tle_lines: tuple[str, str]
    start: str
    stop: str
    step_s: int


@dataclass(frozen=True, kw_only=True)
class SpacecraftLightingTimesCase:
    id: str
    tle_lines: tuple[str, str]
    start: str
    stop: str
    expected_sunlight_intervals: int
    expected_penumbra_intervals: int
    expected_umbra_intervals: int


@dataclass(frozen=True, kw_only=True)
class SkyfieldSpacecraftContext:
    timescale: object
    earth: object
    sun: object
    satellite: EarthSatellite
    observer: object


class CrossValidationError(Exception):
    """Raised when ASTROX and Skyfield disagree."""


ISS_SGP4_SOLAR_AER = SpacecraftSolarAerCase(
    id="iss_sgp4_solar_aer",
    tle_lines=ISS_TLE_LINES,
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    step_s=900,
)
ISS_SGP4_LIGHTING_TIMES = SpacecraftLightingTimesCase(
    id="iss_sgp4_lighting_times",
    tle_lines=ISS_TLE_LINES,
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    expected_sunlight_intervals=3,
    expected_penumbra_intervals=4,
    expected_umbra_intervals=2,
)


def skyfield_context(tle_lines: tuple[str, str]) -> SkyfieldSpacecraftContext:
    data_dir = Path(os.environ.get("SKYFIELD_DATA_DIR", "/tmp/astrox-python-skyfield"))
    loader = Loader(str(data_dir))
    timescale = loader.timescale(builtin=True)
    eph = loader("de421.bsp")
    satellite = EarthSatellite(*tle_lines, "spacecraft", timescale)
    earth = eph["earth"]
    return SkyfieldSpacecraftContext(
        timescale=timescale,
        earth=earth,
        sun=eph["sun"],
        satellite=satellite,
        observer=earth + satellite,
    )


def spacecraft_position(tle_lines: tuple[str, str]) -> entities.Sgp4Position:
    return entities.sgp4_position(tle_lines=tle_lines)


def astrox_solar_aer(case: SpacecraftSolarAerCase) -> list[dict[str, object]]:
    result = lighting.solar_aer(
        start=case.start,
        stop=case.stop,
        position=spacecraft_position(case.tle_lines),
        step_s=case.step_s,
    )
    return result["Datas"]


def astrox_lighting_times(case: SpacecraftLightingTimesCase) -> dict[str, object]:
    return lighting.lighting_times(
        start=case.start,
        stop=case.stop,
        position=spacecraft_position(case.tle_lines),
    )


def skyfield_spacecraft_solar_aer(
    context: SkyfieldSpacecraftContext,
    time_string: str,
) -> tuple[float, float, float]:
    time = context.timescale.from_datetime(parse_astrox_time(time_string))
    satellite_state = context.satellite.at(time)
    apparent_sun_from_spacecraft = as_vector3(
        context.observer.at(time).observe(context.sun).apparent().position.km
    )
    apparent_geocentric_sun = as_vector3(
        context.earth.at(time).observe(context.sun).apparent().position.km
    )
    forward, right, down = spacecraft_vvlh_axes(
        position=as_vector3(satellite_state.position.km),
        velocity=as_vector3(satellite_state.velocity.km_per_s),
    )
    x = vector_dot(apparent_geocentric_sun, forward)
    y = vector_dot(apparent_geocentric_sun, right)
    z = vector_dot(apparent_sun_from_spacecraft, down)
    azimuth_deg = math.degrees(math.atan2(y, x)) % 360.0
    elevation_deg = math.degrees(math.atan2(-z, math.hypot(x, y)))
    return elevation_deg, azimuth_deg, vector_norm(apparent_sun_from_spacecraft)


def spacecraft_vvlh_axes(
    *,
    position: Vector3,
    velocity: Vector3,
) -> tuple[Vector3, Vector3, Vector3]:
    down = vector_unit(vector_scale(position, -1.0))
    along_track = vector_subtract(
        velocity,
        vector_scale(down, vector_dot(velocity, down)),
    )
    forward = vector_unit(along_track)
    right = vector_unit(vector_cross(down, forward))
    return forward, right, down


def compare_solar_aer_case(case: SpacecraftSolarAerCase) -> None:
    context = skyfield_context(case.tle_lines)
    failures: list[str] = []
    for row in astrox_solar_aer(case):
        time_string = require_str(row, "Time")
        skyfield_elevation_deg, skyfield_azimuth_deg, skyfield_range_km = (
            skyfield_spacecraft_solar_aer(context, time_string)
        )
        checks = [
            (
                "Azimuth",
                require_float(row, "Azimuth"),
                skyfield_azimuth_deg,
                SOLAR_AER_AZIMUTH_ABS_DEG,
                "deg",
            ),
            (
                "Elevation",
                require_float(row, "Elevation"),
                skyfield_elevation_deg,
                SOLAR_AER_ELEVATION_ABS_DEG,
                "deg",
            ),
            (
                "Range",
                require_float(row, "Range"),
                skyfield_range_km,
                SOLAR_AER_RANGE_ABS_KM,
                "km",
            ),
        ]
        for field, astrox_value, skyfield_value, tolerance, unit in checks:
            if field == "Azimuth":
                error = angle_error_deg(astrox_value, skyfield_value)
            else:
                error = abs(astrox_value - skyfield_value)
            if error > tolerance:
                failures.append(
                    f"{case.id} solar_aer {time_string} {field} error {error:.12g} {unit}, tolerance {tolerance:.12g}"
                )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_lighting_times_case(case: SpacecraftLightingTimesCase) -> None:
    context = skyfield_context(case.tle_lines)
    result = astrox_lighting_times(case)
    sun_intervals = require_intervals(result, "SunLight")
    penumbra_intervals = require_intervals(result, "Penumbra")
    umbra_intervals = require_intervals(result, "Umbra")
    expected_counts = {
        "SunLight": (sun_intervals, case.expected_sunlight_intervals),
        "Penumbra": (penumbra_intervals, case.expected_penumbra_intervals),
        "Umbra": (umbra_intervals, case.expected_umbra_intervals),
    }
    unexpected_counts = [
        f"{name} expected {expected_count} intervals but got {len(intervals)}"
        for name, (intervals, expected_count) in expected_counts.items()
        if len(intervals) != expected_count
    ]
    if unexpected_counts:
        raise CrossValidationError(
            f"{case.id} interval count mismatch: " + "; ".join(unexpected_counts)
        )

    checks: list[tuple[str, str, Callable[[SkyfieldSpacecraftContext, datetime], float]]] = []
    for interval in sun_intervals:
        start = require_str(interval, "Start")
        stop = require_str(interval, "Stop")
        if start != case.start:
            checks.append(("sunlight_start", start, full_sun_threshold_residual))
        if stop != case.stop:
            checks.append(("sunlight_stop", stop, full_sun_threshold_residual))
    for interval in umbra_intervals:
        checks.append(
            (
                "umbra_start",
                require_str(interval, "Start"),
                umbra_threshold_residual,
            )
        )
        checks.append(
            (
                "umbra_stop",
                require_str(interval, "Stop"),
                umbra_threshold_residual,
            )
        )

    failures: list[str] = []
    for label, astrox_time_string, residual in checks:
        astrox_time = parse_astrox_time(astrox_time_string)
        skyfield_time = find_transition_near(
            context=context,
            astrox_time=astrox_time,
            residual=residual,
        )
        error_s = abs((astrox_time - skyfield_time).total_seconds())
        if error_s > LIGHTING_TRANSITION_ABS_S:
            failures.append(
                f"{case.id} {label} transition error {error_s:.12g}s, tolerance {LIGHTING_TRANSITION_ABS_S:.12g}s; "
                f"astrox={astrox_time.isoformat()} skyfield={skyfield_time.isoformat()}"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def full_sun_threshold_residual(
    context: SkyfieldSpacecraftContext,
    when: datetime,
) -> float:
    separation, earth_angle, sun_angle = spacecraft_shadow_angles(context, when)
    return separation - (earth_angle + sun_angle)


def umbra_threshold_residual(
    context: SkyfieldSpacecraftContext,
    when: datetime,
) -> float:
    separation, earth_angle, sun_angle = spacecraft_shadow_angles(context, when)
    return separation - (earth_angle - sun_angle)


def spacecraft_shadow_angles(
    context: SkyfieldSpacecraftContext,
    when: datetime,
) -> tuple[float, float, float]:
    time = context.timescale.from_datetime(when)
    satellite_state = context.satellite.at(time)
    position = as_vector3(satellite_state.position.km)
    earth_from_spacecraft = vector_scale(position, -1.0)
    sun_from_spacecraft = as_vector3(
        context.observer.at(time).observe(context.sun).apparent().position.km
    )
    separation = vector_angle_rad(earth_from_spacecraft, sun_from_spacecraft)
    earth_angle = math.asin(EARTH_EQUATORIAL_RADIUS_KM / vector_norm(position))
    sun_angle = math.asin(SUN_RADIUS_KM / vector_norm(sun_from_spacecraft))
    return separation, earth_angle, sun_angle


def find_transition_near(
    *,
    context: SkyfieldSpacecraftContext,
    astrox_time: datetime,
    residual: Callable[[SkyfieldSpacecraftContext, datetime], float],
) -> datetime:
    left = astrox_time - timedelta(seconds=LIGHTING_ROOT_BRACKET_S)
    right = astrox_time + timedelta(seconds=LIGHTING_ROOT_BRACKET_S)
    left_value = residual(context, left)
    right_value = residual(context, right)
    if left_value * right_value > 0:
        raise CrossValidationError(
            "Skyfield transition bracket does not cross zero near "
            f"{astrox_time.isoformat()}: left={left_value:.12g}, right={right_value:.12g}"
        )
    for _ in range(60):
        midpoint = left + (right - left) / 2
        midpoint_value = residual(context, midpoint)
        if left_value * midpoint_value <= 0:
            right = midpoint
            right_value = midpoint_value
        else:
            left = midpoint
            left_value = midpoint_value
    return left + (right - left) / 2


def as_vector3(values: object) -> Vector3:
    x, y, z = values
    return float(x), float(y), float(z)


def vector_dot(left: Vector3, right: Vector3) -> float:
    return sum(a * b for a, b in zip(left, right))


def vector_cross(left: Vector3, right: Vector3) -> Vector3:
    ax, ay, az = left
    bx, by, bz = right
    return ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx


def vector_norm(vector: Vector3) -> float:
    return math.sqrt(vector_dot(vector, vector))


def vector_scale(vector: Vector3, factor: float) -> Vector3:
    return tuple(value * factor for value in vector)


def vector_subtract(left: Vector3, right: Vector3) -> Vector3:
    return tuple(a - b for a, b in zip(left, right))


def vector_unit(vector: Vector3) -> Vector3:
    length = vector_norm(vector)
    return tuple(value / length for value in vector)


def vector_angle_rad(left: Vector3, right: Vector3) -> float:
    ratio = vector_dot(left, right) / (vector_norm(left) * vector_norm(right))
    return math.acos(max(-1.0, min(1.0, ratio)))


def angle_error_deg(left: float, right: float) -> float:
    return abs((left - right + 180.0) % 360.0 - 180.0)


def parse_astrox_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def require_intervals(result: dict[str, object], key: str) -> list[dict[str, object]]:
    if key not in result:
        raise CrossValidationError(f"Missing key: {key}")
    block = result[key]
    if not isinstance(block, dict):
        raise CrossValidationError(f"{key} must be an object")
    if "Intervals" not in block:
        raise CrossValidationError(f"Missing key: {key}.Intervals")
    intervals = block["Intervals"]
    if not isinstance(intervals, list):
        raise CrossValidationError(f"{key}.Intervals must be a list")
    if not all(isinstance(interval, dict) for interval in intervals):
        raise CrossValidationError(f"{key}.Intervals items must be objects")
    return intervals


def require_str(payload: dict[str, object], key: str) -> str:
    if key not in payload:
        raise CrossValidationError(f"Missing key: {key}")
    value = payload[key]
    if not isinstance(value, str):
        raise CrossValidationError(f"{key} must be a string")
    return value


def require_float(payload: dict[str, object], key: str) -> float:
    if key not in payload:
        raise CrossValidationError(f"Missing key: {key}")
    value = payload[key]
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise CrossValidationError(f"{key} must be numeric")
    return float(value)


def test_spacecraft_solar_aer_matches_skyfield_vvlh_sun_geometry() -> None:
    configure_astrox_from_env()
    compare_solar_aer_case(ISS_SGP4_SOLAR_AER)


def test_spacecraft_lighting_times_matches_skyfield_conical_shadow() -> None:
    configure_astrox_from_env()
    compare_lighting_times_case(ISS_SGP4_LIGHTING_TIMES)


def main() -> int:
    try:
        test_spacecraft_solar_aer_matches_skyfield_vvlh_sun_geometry()
        test_spacecraft_lighting_times_matches_skyfield_conical_shadow()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=2")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
