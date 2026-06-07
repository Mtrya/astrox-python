#!/usr/bin/env python3
"""Live ASTROX lighting cross-validation against Skyfield topocentric Sun geometry."""

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

from skyfield.api import Loader, wgs84

from astrox import entities, lighting
from tests.validation._support import LiveConfigError, configure_astrox_from_env


LATITUDE_DEG = 19.821
LONGITUDE_DEG = -155.468
HEIGHT_M = 4205.0
START = "2024-01-01T00:00:00.000Z"
STOP_SHORT = "2024-01-01T00:30:00.000Z"
STOP_DAY = "2024-01-02T00:00:00.000Z"
STEP_S = 900
EARTH_EQUATORIAL_RADIUS_M = 6378137.0
SUN_RADIUS_KM = 695700.0
AER_AZIMUTH_ABS_DEG = 1.0e-4
AER_ELEVATION_ABS_DEG = 5.0e-5
# ASTROX states that lighting uses a DE430-like Sun position. Skyfield's small
# public ephemeris here is DE421, so range is checked with a narrow kilometer
# bound but not meter-level identity.
AER_RANGE_ABS_KM = 25.0
TRANSITION_ABS_S = 3.0
ROOT_BRACKET_S = 900.0


@dataclass(frozen=True, kw_only=True)
class SkyfieldContext:
    timescale: object
    observer: object
    sun: object


class CrossValidationError(Exception):
    """Raised when ASTROX and Skyfield disagree."""


def site_position() -> entities.SitePosition:
    return entities.site_position(
        longitude_deg=LONGITUDE_DEG,
        latitude_deg=LATITUDE_DEG,
        height_m=HEIGHT_M,
    )


def skyfield_context() -> SkyfieldContext:
    data_dir = Path(os.environ.get("SKYFIELD_DATA_DIR", "/tmp/astrox-python-skyfield"))
    loader = Loader(str(data_dir))
    timescale = loader.timescale(builtin=True)
    eph = loader("de421.bsp")
    observer = eph["earth"] + wgs84.latlon(
        latitude_degrees=LATITUDE_DEG,
        longitude_degrees=LONGITUDE_DEG,
        elevation_m=HEIGHT_M,
    )
    return SkyfieldContext(
        timescale=timescale,
        observer=observer,
        sun=eph["sun"],
    )


def astrox_solar_aer() -> list[dict[str, object]]:
    result = lighting.solar_aer(
        start=START,
        stop=STOP_SHORT,
        site_position=site_position(),
        step_s=STEP_S,
    )
    return result["Datas"]


def astrox_lighting_times() -> dict[str, object]:
    return lighting.lighting_times(
        start=START,
        stop=STOP_DAY,
        position=site_position(),
    )


def skyfield_alt_az_range(
    context: SkyfieldContext,
    time_string: str,
) -> tuple[float, float, float]:
    time = context.timescale.from_datetime(parse_astrox_time(time_string))
    apparent = context.observer.at(time).observe(context.sun).apparent()
    altitude, azimuth, distance = apparent.altaz()
    return altitude.degrees, azimuth.degrees, distance.km


def compare_solar_aer() -> None:
    context = skyfield_context()
    failures: list[str] = []
    for row in astrox_solar_aer():
        time_string = require_str(row, "Time")
        skyfield_elevation_deg, skyfield_azimuth_deg, skyfield_range_km = (
            skyfield_alt_az_range(context, time_string)
        )
        checks = [
            (
                "Azimuth",
                require_float(row, "Azimuth"),
                skyfield_azimuth_deg,
                AER_AZIMUTH_ABS_DEG,
                "deg",
            ),
            (
                "Elevation",
                require_float(row, "Elevation"),
                skyfield_elevation_deg,
                AER_ELEVATION_ABS_DEG,
                "deg",
            ),
            (
                "Range",
                require_float(row, "Range"),
                skyfield_range_km,
                AER_RANGE_ABS_KM,
                "km",
            ),
        ]
        for field, astrox_value, skyfield_value, tolerance, unit in checks:
            error = abs(astrox_value - skyfield_value)
            if error > tolerance:
                failures.append(
                    f"solar_aer {time_string} {field} error {error:.12g} {unit}, tolerance {tolerance:.12g}"
                )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_lighting_times() -> None:
    context = skyfield_context()
    result = astrox_lighting_times()
    sun_intervals = require_intervals(result, "SunLight")
    penumbra_intervals = require_intervals(result, "Penumbra")
    umbra_intervals = require_intervals(result, "Umbra")
    if len(sun_intervals) != 2 or len(penumbra_intervals) != 2 or len(umbra_intervals) != 1:
        raise CrossValidationError(
            "expected two SunLight intervals, two Penumbra intervals, and one Umbra interval"
        )

    checks = [
        (
            "evening_full_sun_stop",
            require_str(sun_intervals[0], "Stop"),
            full_sun_threshold_residual,
        ),
        (
            "evening_umbra_start",
            require_str(umbra_intervals[0], "Start"),
            umbra_threshold_residual,
        ),
        (
            "morning_umbra_stop",
            require_str(umbra_intervals[0], "Stop"),
            umbra_threshold_residual,
        ),
        (
            "morning_full_sun_start",
            require_str(sun_intervals[1], "Start"),
            full_sun_threshold_residual,
        ),
    ]
    failures: list[str] = []
    for label, astrox_time_string, residual in checks:
        astrox_time = parse_astrox_time(astrox_time_string)
        skyfield_time = find_transition_near(
            context=context,
            astrox_time=astrox_time,
            residual=residual,
        )
        error_s = abs((astrox_time - skyfield_time).total_seconds())
        if error_s > TRANSITION_ABS_S:
            failures.append(
                f"{label} transition error {error_s:.12g}s, tolerance {TRANSITION_ABS_S:.12g}s; "
                f"astrox={astrox_time.isoformat()} skyfield={skyfield_time.isoformat()}"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def full_sun_threshold_residual(context: SkyfieldContext, when: datetime) -> float:
    altitude_deg, _, distance_km = skyfield_alt_az_range(context, format_time(when))
    return altitude_deg - (geometric_horizon_deg() + solar_angular_radius_deg(distance_km))


def umbra_threshold_residual(context: SkyfieldContext, when: datetime) -> float:
    altitude_deg, _, distance_km = skyfield_alt_az_range(context, format_time(when))
    return altitude_deg - (geometric_horizon_deg() - solar_angular_radius_deg(distance_km))


def geometric_horizon_deg() -> float:
    return -math.degrees(
        math.acos(
            EARTH_EQUATORIAL_RADIUS_M / (EARTH_EQUATORIAL_RADIUS_M + HEIGHT_M)
        )
    )


def solar_angular_radius_deg(distance_km: float) -> float:
    return math.degrees(math.asin(SUN_RADIUS_KM / distance_km))


def find_transition_near(
    *,
    context: SkyfieldContext,
    astrox_time: datetime,
    residual: Callable[[SkyfieldContext, datetime], float],
) -> datetime:
    left = astrox_time - timedelta(seconds=ROOT_BRACKET_S)
    right = astrox_time + timedelta(seconds=ROOT_BRACKET_S)
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


def parse_astrox_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def format_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def require_intervals(result: dict[str, object], key: str) -> list[dict[str, object]]:
    block = result[key]
    if not isinstance(block, dict):
        raise CrossValidationError(f"{key} must be an object")
    intervals = block["Intervals"]
    if not isinstance(intervals, list):
        raise CrossValidationError(f"{key}.Intervals must be a list")
    if not all(isinstance(interval, dict) for interval in intervals):
        raise CrossValidationError(f"{key}.Intervals items must be objects")
    return intervals


def require_str(payload: dict[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise CrossValidationError(f"{key} must be a string")
    return value


def require_float(payload: dict[str, object], key: str) -> float:
    value = payload[key]
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise CrossValidationError(f"{key} must be numeric")
    return float(value)


def test_solar_aer_matches_skyfield_topocentric_sun() -> None:
    configure_astrox_from_env()
    compare_solar_aer()


def test_site_lighting_times_match_skyfield_solar_disk_geometry() -> None:
    configure_astrox_from_env()
    compare_lighting_times()


def main() -> int:
    try:
        test_solar_aer_matches_skyfield_topocentric_sun()
        test_site_lighting_times_match_skyfield_solar_disk_geometry()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=2")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
