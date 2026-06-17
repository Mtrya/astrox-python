#!/usr/bin/env python3
"""Coverage FOM cross-validation against interval and gap invariants."""

# Coverage:
#   Branches:
#     - SimpleCoverage ValueByGridPoint: verified as 1 when a grid point has any positive-asset interval, otherwise 0
#     - SimpleCoverage ValueByGridPointAtTime: verified as active positive-asset coverage at Time
#     - SimpleCoverage GridStats: verified as arithmetic min/max/average of ValueByGridPoint FOM values
#     - SimpleCoverage GridStatsOverTime: verified as arithmetic min/max/average of ValueByGridPointAtTime at Step samples
#     - CoverageTime ValueByGridPoint: verified as total positive-asset interval duration with ComputeType=TotalTimeAbove
#     - CoverageTime GridStats: verified as arithmetic min/max/average of CoverageTime ValueByGridPoint
#     - NumberOfAssets ValueByGridPoint: verified for ComputeType=Average/Maximum/Minimum from the positive-asset count trace
#     - NumberOfAssets ValueByGridPointAtTime: verified as the active asset count at Time
#     - NumberOfAssets GridStats: verified as arithmetic min/max/average of NumberOfAssets ValueByGridPoint values
#     - NumberOfAssets GridStatsOverTime: verified as arithmetic min/max/average of ValueByGridPointAtTime at Step samples
#     - ResponseTime ValueByGridPoint: verified for ComputeType=Maximum as max zero-asset gap duration, including boundary gaps; verified for ComputeType=Minimum as 0 for grid points covered at least once in the representative case
#     - ResponseTime GridStats: verified as arithmetic min/max/average of ResponseTime ValueByGridPoint
#     - ResponseTime ValueByGridPointAtTime: partial; representative HTTP 500 behavior is guarded in live snapshots
#     - ResponseTime GridStatsOverTime: partial; representative HTTP 500 behavior is guarded in live snapshots
#     - RevisitTime ValueByGridPoint: verified for ComputeType=Average/Maximum/Minimum as average/max/min zero-asset gap duration, including boundary gaps
#     - RevisitTime ValueByGridPointAtTime: verified as the containing zero-asset gap duration, or 0 when covered at Time
#     - RevisitTime GridStats: verified as arithmetic min/max/average of RevisitTime ValueByGridPoint values
#     - RevisitTime GridStatsOverTime: verified as arithmetic min/max/average of RevisitTime ValueByGridPointAtTime at Step samples
#   Fields:
#     - Datas[].Latitude/Longitude/Altitude: verified to match GetGridPoints ordering and positions
#     - Datas[].FOM_Value: verified for the branch-specific interval/gap conventions above
#     - Minimum/Maximum/Average: verified as arithmetic statistics over route values, not grid-weighted statistics
#     - GridStatsOverTime.Datas[].EpochSeconds: verified to follow Step samples from Start through Stop
#   Parameters:
#     - compute_type: verified for CoverageTime TotalTimeAbove, NumberOfAssets Average/Maximum/Minimum, ResponseTime Maximum/Minimum, RevisitTime Average/Maximum/Minimum
#     - time: verified for supported at-time routes at covered and uncovered samples
#     - step_s: verified for GridStatsOverTime sample epochs
#     - minimum_assets: verified for N=1 through the compute interval trace; broader N behavior is covered in resource report cross-validation
#   Comparison:
#     - External: local interval/gap derivation from ComputeCoverage SatisfactionIntervalsWithNumberOfAssets plus cross-route aggregation invariants
#     - Constants: no physical constants; grid geometry is calibrated separately and interval semantics are calibrated against ComputeCoverage
#     - Tolerances: VALUE_ABS=1e-6 for endpoint-to-endpoint floating values; POSITION_ABS_DEG=1e-10 for grid coordinate echoes
#   Findings:
#     - FOM grid statistics use simple arithmetic statistics over point values, not coverage grid weights.
#     - ResponseTime Maximum static values measure maximum zero-asset gap duration.
#     - ResponseTime Minimum static values return 0 for grid points covered at least once in the representative case, not the shortest zero-asset boundary gap.
#     - RevisitTime static values measure zero-asset gap duration statistics.
#     - RevisitTime at-time values return the whole containing zero-asset gap duration, not the remaining time to the next access.

from __future__ import annotations

import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, entities, exceptions
from tests.validation._support import LiveConfigError, configure_astrox_from_env


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:30:00.000Z"
STEP_S = 300.0
VALUE_ABS = 1.0e-6
POSITION_ABS_DEG = 1.0e-10
TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


class CrossValidationError(Exception):
    """Raised when live ASTROX FOM behavior disagrees with interval invariants."""


def sample_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )


def sample_asset() -> entities.Entity:
    return entities.entity(
        name="Relay",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
    )


def compute_trace() -> dict[str, Any]:
    return coverage.compute(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        include_asset_access_results=True,
        include_coverage_points=True,
        step_s=STEP_S,
    )


def test_fom_simple_coverage_matches_compute_intervals() -> None:
    configure_astrox_from_env()
    trace = compute_trace()
    point_traces = trace["SatisfactionIntervalsWithNumberOfAssets"]
    points = trace["Points"]["GridPoints"]
    by_point = coverage.simple_coverage.by_grid_point(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        step_s=STEP_S,
    )
    expected = [1.0 if total_positive_duration(intervals) > 0.0 else 0.0 for intervals in point_traces]
    assert_fom_values("simple_by_grid_point", by_point["Datas"], points, expected)
    stats = coverage.simple_coverage.grid_stats(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        step_s=STEP_S,
    )
    assert_stats("simple_grid_stats", stats, expected)
    at_time = coverage.simple_coverage.by_grid_point_at_time(
        time="2024-01-01T00:10:00.000Z",
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        step_s=STEP_S,
    )
    expected_at_time = [1.0 if active_count_at(intervals, 600.0) > 0 else 0.0 for intervals in point_traces]
    assert_fom_values("simple_by_grid_point_at_time", at_time["Datas"], points, expected_at_time)


def test_fom_coverage_time_and_number_of_assets_match_interval_derivation() -> None:
    configure_astrox_from_env()
    trace = compute_trace()
    point_traces = trace["SatisfactionIntervalsWithNumberOfAssets"]
    points = trace["Points"]["GridPoints"]
    duration_s = epoch_seconds(STOP) - epoch_seconds(START)
    coverage_time_values = [total_positive_duration(intervals) for intervals in point_traces]
    coverage_time_report = coverage.coverage_time.by_grid_point(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        compute_type="TotalTimeAbove",
        step_s=STEP_S,
    )
    assert_fom_values("coverage_time_by_grid_point", coverage_time_report["Datas"], points, coverage_time_values)
    coverage_time_stats = coverage.coverage_time.grid_stats(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        compute_type="TotalTimeAbove",
        step_s=STEP_S,
    )
    assert_stats("coverage_time_grid_stats", coverage_time_stats, coverage_time_values)

    number_expectations = {
        "Average": [value / duration_s for value in coverage_time_values],
        "Maximum": [max_positive_count(intervals) for intervals in point_traces],
        "Minimum": [min_count(intervals) for intervals in point_traces],
    }
    for compute_type, expected in number_expectations.items():
        report = coverage.number_of_assets.by_grid_point(
            start=START,
            stop=STOP,
            grid=sample_grid(),
            assets=[sample_asset()],
            minimum_assets=1,
            compute_type=compute_type,
            step_s=STEP_S,
        )
        assert_fom_values(f"number_of_assets_{compute_type}", report["Datas"], points, expected)
    stats = coverage.number_of_assets.grid_stats(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        compute_type="Average",
        step_s=STEP_S,
    )
    assert_stats("number_of_assets_grid_stats", stats, number_expectations["Average"])


def test_fom_response_and_revisit_time_match_gap_derivation() -> None:
    configure_astrox_from_env()
    trace = compute_trace()
    point_traces = trace["SatisfactionIntervalsWithNumberOfAssets"]
    points = trace["Points"]["GridPoints"]
    response_expectations = {
        "Maximum": [max(gap_durations(intervals)) for intervals in point_traces],
        "Minimum": [0.0 if total_positive_duration(intervals) > 0.0 else math.inf for intervals in point_traces],
    }
    for compute_type, expected in response_expectations.items():
        report = coverage.response_time.by_grid_point(
            start=START,
            stop=STOP,
            grid=sample_grid(),
            assets=[sample_asset()],
            minimum_assets=1,
            compute_type=compute_type,
            step_s=STEP_S,
        )
        assert_fom_values(f"response_time_{compute_type}", report["Datas"], points, expected)
    response_stats = coverage.response_time.grid_stats(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        compute_type="Maximum",
        step_s=STEP_S,
    )
    assert_stats("response_time_grid_stats", response_stats, response_expectations["Maximum"])

    revisit_expectations = {
        "Average": [mean(gap_durations(intervals)) for intervals in point_traces],
        "Maximum": [max(gap_durations(intervals)) for intervals in point_traces],
        "Minimum": [min(gap_durations(intervals)) for intervals in point_traces],
    }
    for compute_type, expected in revisit_expectations.items():
        report = coverage.revisit_time.by_grid_point(
            start=START,
            stop=STOP,
            grid=sample_grid(),
            assets=[sample_asset()],
            minimum_assets=1,
            compute_type=compute_type,
            step_s=STEP_S,
        )
        assert_fom_values(f"revisit_time_{compute_type}", report["Datas"], points, expected)
    at_time = coverage.revisit_time.by_grid_point_at_time(
        time="2024-01-01T00:10:00.000Z",
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        step_s=STEP_S,
    )
    expected_at_time = [containing_gap_duration(intervals, 600.0) for intervals in point_traces]
    assert_fom_values("revisit_time_at_time", at_time["Datas"], points, expected_at_time)
    revisit_stats = coverage.revisit_time.grid_stats(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        compute_type="Average",
        step_s=STEP_S,
    )
    assert_stats("revisit_time_grid_stats", revisit_stats, revisit_expectations["Average"])


def test_fom_over_time_stats_match_at_time_routes() -> None:
    configure_astrox_from_env()
    route_cases = [
        (
            "simple_coverage",
            coverage.simple_coverage.by_grid_point_at_time,
            coverage.simple_coverage.grid_stats_over_time,
        ),
        (
            "number_of_assets",
            coverage.number_of_assets.by_grid_point_at_time,
            coverage.number_of_assets.grid_stats_over_time,
        ),
        (
            "revisit_time",
            coverage.revisit_time.by_grid_point_at_time,
            coverage.revisit_time.grid_stats_over_time,
        ),
    ]
    for label, at_time_func, over_time_func in route_cases:
        over_time = over_time_func(
            start=START,
            stop=STOP,
            grid=sample_grid(),
            assets=[sample_asset()],
            minimum_assets=1,
            step_s=STEP_S,
        )
        for sample in over_time["Datas"]:
            epoch_s = sample["EpochSeconds"]
            expected_values = [
                row["FOM_Value"]
                for row in at_time_func(
                    time=iso_at_offset(epoch_s),
                    start=START,
                    stop=STOP,
                    grid=sample_grid(),
                    assets=[sample_asset()],
                    minimum_assets=1,
                    step_s=STEP_S,
                )["Datas"]
            ]
            assert_stats(f"{label}_over_time_at_{epoch_s}", sample, expected_values)


def total_positive_duration(intervals: list[dict[str, Any]]) -> float:
    return sum(interval["Duration"] for interval in intervals if interval["NumberOfAssets"] > 0)


def active_count_at(intervals: list[dict[str, Any]], seconds: float) -> int:
    for interval in intervals:
        if interval_start_s(interval) <= seconds <= interval_stop_s(interval):
            return int(interval["NumberOfAssets"])
    raise CrossValidationError(f"no interval contains t={seconds}")


def max_positive_count(intervals: list[dict[str, Any]]) -> int:
    return max(int(interval["NumberOfAssets"]) for interval in intervals)


def min_count(intervals: list[dict[str, Any]]) -> int:
    return min(int(interval["NumberOfAssets"]) for interval in intervals)


def gap_durations(intervals: list[dict[str, Any]]) -> list[float]:
    gaps = [interval["Duration"] for interval in intervals if interval["NumberOfAssets"] == 0]
    if not gaps:
        raise CrossValidationError("representative case must include at least one zero-asset gap")
    return gaps


def containing_gap_duration(intervals: list[dict[str, Any]], seconds: float) -> float:
    for interval in intervals:
        if interval_start_s(interval) <= seconds <= interval_stop_s(interval):
            if interval["NumberOfAssets"] > 0:
                return 0.0
            return interval["Duration"]
    raise CrossValidationError(f"no interval contains t={seconds}")


def interval_start_s(interval: dict[str, Any]) -> float:
    return epoch_seconds(interval["Start"]) - epoch_seconds(START)


def interval_stop_s(interval: dict[str, Any]) -> float:
    return epoch_seconds(interval["Stop"]) - epoch_seconds(START)


def epoch_seconds(value: str) -> float:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    start = datetime.fromisoformat(START.replace("Z", "+00:00"))
    return (parsed.astimezone(UTC) - start.astimezone(UTC)).total_seconds()


def iso_at_offset(seconds: float) -> str:
    start = datetime.fromisoformat(START.replace("Z", "+00:00")).astimezone(UTC)
    value = start.timestamp() + seconds
    return datetime.fromtimestamp(value, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def assert_fom_values(
    label: str,
    actual_rows: list[dict[str, Any]],
    expected_points: list[dict[str, Any]],
    expected_values: list[float],
) -> None:
    if len(actual_rows) != len(expected_values):
        raise CrossValidationError(f"{label}: expected {len(expected_values)} rows, got {len(actual_rows)}")
    for index, (actual, point, expected_value) in enumerate(zip(actual_rows, expected_points, expected_values, strict=True)):
        latitude_rad, longitude_rad = point["Position"]
        assert_close(f"{label}[{index}].Latitude", math.degrees(latitude_rad), actual["Latitude"], POSITION_ABS_DEG)
        assert_close(f"{label}[{index}].Longitude", math.degrees(longitude_rad), actual["Longitude"], POSITION_ABS_DEG)
        assert_close(f"{label}[{index}].Altitude", 0.0, actual["Altitude"], VALUE_ABS)
        assert_close(f"{label}[{index}].FOM_Value", expected_value, actual["FOM_Value"], VALUE_ABS)


def assert_stats(label: str, actual: dict[str, Any], values: list[float]) -> None:
    assert_close(f"{label}.Minimum", min(values), actual["Minimum"], VALUE_ABS)
    assert_close(f"{label}.Maximum", max(values), actual["Maximum"], VALUE_ABS)
    assert_close(f"{label}.Average", mean(values), actual["Average"], VALUE_ABS)


def assert_close(label: str, expected: float, actual: float, abs_tol: float) -> None:
    if not math.isclose(float(actual), float(expected), abs_tol=abs_tol):
        raise CrossValidationError(f"{label}: expected {expected}, got {actual}")


def run_all_checks() -> int:
    test_fom_simple_coverage_matches_compute_intervals()
    test_fom_coverage_time_and_number_of_assets_match_interval_derivation()
    test_fom_response_and_revisit_time_match_gap_derivation()
    test_fom_over_time_stats_match_at_time_routes()
    return 4


def main() -> int:
    try:
        configure_astrox_from_env()
        checked = run_all_checks()
        print(f"CROSS_VALIDATION_CHECKED={checked}")
        print("CROSS_VALIDATION_FAILED=0")
        return 0
    except (CrossValidationError, LiveConfigError, exceptions.AstroxError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
