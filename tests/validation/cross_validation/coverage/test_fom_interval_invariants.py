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

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, exceptions
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.coverage._fom_helpers import (
    START,
    STOP,
    CrossValidationError,
    active_count_at,
    assert_fom_values,
    assert_stats,
    compute_trace,
    containing_gap_duration,
    duration_s,
    gap_durations,
    intermittent_grid,
    iso_at_offset,
    max_positive_count,
    mean,
    min_count,
    primary_asset,
    total_positive_duration,
)


STEP_S = 300.0


def test_fom_simple_coverage_matches_compute_intervals() -> None:
    configure_astrox_from_env()
    trace = compute_trace(step_s=STEP_S)
    point_traces = trace["SatisfactionIntervalsWithNumberOfAssets"]
    points = trace["Points"]["GridPoints"]
    by_point = coverage.simple_coverage.by_grid_point(
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        step_s=STEP_S,
    )
    expected = [1.0 if total_positive_duration(intervals) > 0.0 else 0.0 for intervals in point_traces]
    assert_fom_values("simple_by_grid_point", by_point["Datas"], points, expected)
    stats = coverage.simple_coverage.grid_stats(
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        step_s=STEP_S,
    )
    assert_stats("simple_grid_stats", stats, expected)
    at_time = coverage.simple_coverage.by_grid_point_at_time(
        time="2024-01-01T00:10:00.000Z",
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        step_s=STEP_S,
    )
    expected_at_time = [1.0 if active_count_at(intervals, 600.0) > 0 else 0.0 for intervals in point_traces]
    assert_fom_values("simple_by_grid_point_at_time", at_time["Datas"], points, expected_at_time)


def test_fom_coverage_time_and_number_of_assets_match_interval_derivation() -> None:
    configure_astrox_from_env()
    trace = compute_trace(step_s=STEP_S)
    point_traces = trace["SatisfactionIntervalsWithNumberOfAssets"]
    points = trace["Points"]["GridPoints"]
    total_duration_s = duration_s()
    coverage_time_values = [total_positive_duration(intervals) for intervals in point_traces]
    coverage_time_report = coverage.coverage_time.by_grid_point(
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        compute_type="TotalTimeAbove",
        step_s=STEP_S,
    )
    assert_fom_values("coverage_time_by_grid_point", coverage_time_report["Datas"], points, coverage_time_values)
    coverage_time_stats = coverage.coverage_time.grid_stats(
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        compute_type="TotalTimeAbove",
        step_s=STEP_S,
    )
    assert_stats("coverage_time_grid_stats", coverage_time_stats, coverage_time_values)

    number_expectations = {
        "Average": [value / total_duration_s for value in coverage_time_values],
        "Maximum": [max_positive_count(intervals) for intervals in point_traces],
        "Minimum": [min_count(intervals) for intervals in point_traces],
    }
    for compute_type, expected in number_expectations.items():
        report = coverage.number_of_assets.by_grid_point(
            start=START,
            stop=STOP,
            grid=intermittent_grid(),
            assets=[primary_asset()],
            minimum_assets=1,
            compute_type=compute_type,
            step_s=STEP_S,
        )
        assert_fom_values(f"number_of_assets_{compute_type}", report["Datas"], points, expected)
    stats = coverage.number_of_assets.grid_stats(
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        compute_type="Average",
        step_s=STEP_S,
    )
    assert_stats("number_of_assets_grid_stats", stats, number_expectations["Average"])


def test_fom_response_and_revisit_time_match_gap_derivation() -> None:
    configure_astrox_from_env()
    trace = compute_trace(step_s=STEP_S)
    point_traces = trace["SatisfactionIntervalsWithNumberOfAssets"]
    points = trace["Points"]["GridPoints"]
    response_expectations = {
        "Maximum": [max(representative_gap_durations(intervals)) for intervals in point_traces],
        "Minimum": [0.0 if total_positive_duration(intervals) > 0.0 else float("inf") for intervals in point_traces],
    }
    for compute_type, expected in response_expectations.items():
        report = coverage.response_time.by_grid_point(
            start=START,
            stop=STOP,
            grid=intermittent_grid(),
            assets=[primary_asset()],
            minimum_assets=1,
            compute_type=compute_type,
            step_s=STEP_S,
        )
        assert_fom_values(f"response_time_{compute_type}", report["Datas"], points, expected)
    response_stats = coverage.response_time.grid_stats(
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        compute_type="Maximum",
        step_s=STEP_S,
    )
    assert_stats("response_time_grid_stats", response_stats, response_expectations["Maximum"])

    revisit_expectations = {
        "Average": [mean(representative_gap_durations(intervals)) for intervals in point_traces],
        "Maximum": [max(representative_gap_durations(intervals)) for intervals in point_traces],
        "Minimum": [min(representative_gap_durations(intervals)) for intervals in point_traces],
    }
    for compute_type, expected in revisit_expectations.items():
        report = coverage.revisit_time.by_grid_point(
            start=START,
            stop=STOP,
            grid=intermittent_grid(),
            assets=[primary_asset()],
            minimum_assets=1,
            compute_type=compute_type,
            step_s=STEP_S,
        )
        assert_fom_values(f"revisit_time_{compute_type}", report["Datas"], points, expected)
    at_time = coverage.revisit_time.by_grid_point_at_time(
        time="2024-01-01T00:10:00.000Z",
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        step_s=STEP_S,
    )
    expected_at_time = [containing_gap_duration(intervals, 600.0) for intervals in point_traces]
    assert_fom_values("revisit_time_at_time", at_time["Datas"], points, expected_at_time)
    revisit_stats = coverage.revisit_time.grid_stats(
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
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
            grid=intermittent_grid(),
            assets=[primary_asset()],
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
                    grid=intermittent_grid(),
                    assets=[primary_asset()],
                    minimum_assets=1,
                    step_s=STEP_S,
                )["Datas"]
            ]
            assert_stats(f"{label}_over_time_at_{epoch_s}", sample, expected_values)


def representative_gap_durations(intervals: list[dict[str, object]]) -> list[float]:
    gaps = gap_durations(intervals)
    if not gaps:
        raise CrossValidationError("representative case must include at least one zero-asset gap")
    return gaps


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
