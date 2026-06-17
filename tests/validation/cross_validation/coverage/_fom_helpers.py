"""Shared helpers for Coverage FOM cross-validation."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from astrox import coverage, entities

START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:30:00.000Z"
CONTINUOUS_START = "2024-01-01T00:02:00.000Z"
CONTINUOUS_STOP = "2024-01-01T00:08:00.000Z"
VALUE_ABS = 1.0e-6
POSITION_ABS_DEG = 1.0e-10
TLE_A = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
TLE_B_OFFSET_RAAN = (
    "1 25545U 98067B   24001.00000000  .00002182  00000-0  41420-4 0  9991",
    "2 25545  51.6461 159.8014 0001882  64.8995 295.2305 15.48919393123452",
)


class CrossValidationError(Exception):
    """Raised when live ASTROX FOM behavior disagrees with a documented invariant."""


def intermittent_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )


def no_coverage_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=80.0,
        max_latitude_deg=85.0,
        min_longitude_deg=0.0,
        max_longitude_deg=10.0,
        resolution_deg=5.0,
    )


def sgp4_asset(name: str, tle_lines: tuple[str, str] = TLE_A) -> entities.Entity:
    return entities.entity(
        name=name,
        position=entities.sgp4_position(tle_lines=tle_lines),
    )


def primary_asset() -> entities.Entity:
    return sgp4_asset("RelayA")


def duplicate_assets() -> list[entities.Entity]:
    return [sgp4_asset("RelayA"), sgp4_asset("RelayA2")]


def offset_assets() -> list[entities.Entity]:
    return [sgp4_asset("RelayA"), sgp4_asset("RelayB", TLE_B_OFFSET_RAAN)]


def compute_trace(
    *,
    start: str = START,
    stop: str = STOP,
    grid: coverage.CoverageGrid | None = None,
    assets: list[entities.Entity] | None = None,
    step_s: float = 60.0,
    minimum_assets: int | None = 1,
    exactly_assets: int | None = None,
    grid_point_sensor: entities.EntitySensor | None = None,
    grid_point_constraints: Sequence[entities.Constraint] | None = None,
) -> dict[str, Any]:
    return coverage.compute(
        start=start,
        stop=stop,
        grid=grid or intermittent_grid(),
        assets=assets or [primary_asset()],
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=True,
        include_coverage_points=True,
        step_s=step_s,
    )


def expected_points(grid: coverage.CoverageGrid) -> list[dict[str, Any]]:
    return coverage.grid_points(grid=grid)["Points"]["GridPoints"]


def duration_s(start: str = START, stop: str = STOP) -> float:
    return seconds_since_start(stop, start=start) - seconds_since_start(start, start=start)


def seconds_since_start(value: str, *, start: str = START) -> float:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    base = datetime.fromisoformat(start.replace("Z", "+00:00"))
    return (parsed.astimezone(UTC) - base.astimezone(UTC)).total_seconds()


def iso_at_offset(seconds: float, *, start: str = START) -> str:
    base = datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(UTC)
    value = base.timestamp() + seconds
    return datetime.fromtimestamp(value, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sample_offsets(stop: str, *, start: str = START, step_s: float) -> list[float]:
    total = duration_s(start=start, stop=stop)
    offsets: list[float] = []
    current = 0.0
    while current < total:
        offsets.append(current)
        current += step_s
    if not offsets or not math.isclose(offsets[-1], total, abs_tol=VALUE_ABS):
        offsets.append(total)
    return offsets


def total_positive_duration(intervals: list[dict[str, Any]]) -> float:
    return sum(interval["Duration"] for interval in intervals if interval["NumberOfAssets"] > 0)


def active_count_at(intervals: list[dict[str, Any]], seconds: float, *, start: str = START) -> int:
    for interval in intervals:
        if interval_start_s(interval, start=start) <= seconds <= interval_stop_s(interval, start=start):
            return int(interval["NumberOfAssets"])
    raise CrossValidationError(f"no interval contains t={seconds}")


def max_positive_count(intervals: list[dict[str, Any]]) -> int:
    return max(int(interval["NumberOfAssets"]) for interval in intervals)


def min_count(intervals: list[dict[str, Any]]) -> int:
    return min(int(interval["NumberOfAssets"]) for interval in intervals)


def gap_durations(intervals: list[dict[str, Any]]) -> list[float]:
    return [interval["Duration"] for interval in intervals if interval["NumberOfAssets"] == 0]


def containing_gap_duration(intervals: list[dict[str, Any]], seconds: float, *, start: str = START) -> float:
    for interval in intervals:
        if interval_start_s(interval, start=start) <= seconds <= interval_stop_s(interval, start=start):
            if interval["NumberOfAssets"] > 0:
                return 0.0
            return interval["Duration"]
    raise CrossValidationError(f"no interval contains t={seconds}")


def interval_start_s(interval: dict[str, Any], *, start: str = START) -> float:
    return seconds_since_start(interval["Start"], start=start)


def interval_stop_s(interval: dict[str, Any], *, start: str = START) -> float:
    return seconds_since_start(interval["Stop"], start=start)


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def assert_fom_values(
    label: str,
    actual_rows: list[dict[str, Any]],
    points: list[dict[str, Any]],
    expected_values: list[float],
) -> None:
    if len(actual_rows) != len(expected_values):
        raise CrossValidationError(f"{label}: expected {len(expected_values)} rows, got {len(actual_rows)}")
    for index, (actual, point, expected_value) in enumerate(zip(actual_rows, points, expected_values, strict=True)):
        latitude_rad, longitude_rad = point["Position"]
        assert_close(f"{label}[{index}].Latitude", math.degrees(latitude_rad), actual["Latitude"], POSITION_ABS_DEG)
        assert_close(f"{label}[{index}].Longitude", math.degrees(longitude_rad), actual["Longitude"], POSITION_ABS_DEG)
        assert_close(f"{label}[{index}].Altitude", 0.0, actual["Altitude"], VALUE_ABS)
        assert_close(f"{label}[{index}].FOM_Value", expected_value, actual["FOM_Value"], VALUE_ABS)


def assert_stats(label: str, actual: dict[str, Any], values: list[float]) -> None:
    assert_close(f"{label}.Minimum", min(values), actual["Minimum"], VALUE_ABS)
    assert_close(f"{label}.Maximum", max(values), actual["Maximum"], VALUE_ABS)
    assert_close(f"{label}.Average", mean(values), actual["Average"], VALUE_ABS)


def assert_epoch_series(label: str, actual_rows: list[dict[str, Any]], expected_offsets: list[float]) -> None:
    if len(actual_rows) != len(expected_offsets):
        raise CrossValidationError(f"{label}: expected {len(expected_offsets)} samples, got {len(actual_rows)}")
    for index, (actual, expected) in enumerate(zip(actual_rows, expected_offsets, strict=True)):
        assert_close(f"{label}[{index}].EpochSeconds", expected, actual["EpochSeconds"], VALUE_ABS)


def assert_close(label: str, expected: float, actual: float, abs_tol: float = VALUE_ABS) -> None:
    if not math.isclose(float(actual), float(expected), abs_tol=abs_tol):
        raise CrossValidationError(f"{label}: expected {expected}, got {actual}")
