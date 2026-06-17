#!/usr/bin/env python3
"""Coverage FOM edge-case cross-validation against interval and route invariants."""

# Coverage:
#   Branches:
#     - no-coverage grid with one SGP4 asset: verified for all static FOM routes and supported at-time/over-time routes; ComputeCoverage worker-error behavior is recorded separately
#     - continuous-coverage grid/window with one SGP4 asset: verified for all static, at-time, and over-time FOM routes, including response-time dynamic routes
#     - ResponseTime ValueByGridPointAtTime/GridStatsOverTime: partial; verified to succeed for continuous coverage; current no-coverage HTTP 500 behavior is guarded in live snapshots
#   Fields:
#     - Datas[].Latitude/Longitude/Altitude: verified against GetGridPoints for no-coverage and continuous-coverage cases
#     - Datas[].FOM_Value: verified against all-zero/all-window/all-covered local derivations where ComputeCoverage has worker-error edge behavior
#     - Minimum/Maximum/Average: verified as arithmetic statistics over point values for no-coverage and continuous-coverage cases
#     - GridStatsOverTime.Datas[].EpochSeconds: verified to include Start, interior Step samples, and Stop
#   Parameters:
#     - time: verified for supported at-time routes in never-covered and always-covered cases
#     - step_s: verified for over-time routes with exact-dividing and non-dividing steps
#     - minimum_assets: verified at N=1 for edge-case regimes
#   Comparison:
#     - External: local endpoint-independent all-zero/all-window/all-covered derivations, plus wider-window ComputeCoverage evidence that the continuous window lies inside positive-asset intervals
#     - Constants: no physical constants; the continuous window is chosen from a wider calibrated ComputeCoverage trace
#     - Tolerances: VALUE_ABS=1e-6 for endpoint-to-endpoint floating values; POSITION_ABS_DEG=1e-10 for grid coordinate echoes
#   Findings:
#     - ComputeCoverage currently returns a worker "Index was out of range" error for all-zero and all-covered edge cases, but most FOM routes return meaningful edge-case values.
#     - No-coverage FOM routes return 0 for SimpleCoverage, CoverageTime, and NumberOfAssets; full-window duration for ResponseTime and RevisitTime; response-time dynamic HTTP 500 cases are drift-guarded in live snapshots.
#     - Continuous-coverage FOM routes return 1 for SimpleCoverage and NumberOfAssets, full-window duration for CoverageTime, and 0 for ResponseTime and RevisitTime; response-time dynamic routes succeed in this regime.

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, exceptions
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.coverage._fom_helpers import (
    CONTINUOUS_START,
    CONTINUOUS_STOP,
    START,
    STOP,
    CrossValidationError,
    assert_epoch_series,
    assert_fom_values,
    assert_stats,
    compute_trace,
    duration_s,
    expected_points,
    intermittent_grid,
    no_coverage_grid,
    primary_asset,
    sample_offsets,
)


def test_no_coverage_fom_routes_match_edge_case_conventions() -> None:
    configure_astrox_from_env()
    grid = no_coverage_grid()
    points = expected_points(grid)
    assets = [primary_asset()]
    duration = duration_s()
    zeros = [0.0 for _ in points]
    full_window = [duration for _ in points]

    with pytest.raises(exceptions.AstroxAPIError) as compute_error:
        compute_trace(grid=grid)
    assert compute_error.value.endpoint == "/Coverage/ComputeCoverage"
    assert "Index was out of range" in str(compute_error.value)

    static_cases = [
        ("simple_by_grid_point", coverage.simple_coverage.by_grid_point, {}, zeros),
        ("simple_by_grid_point_at_time", coverage.simple_coverage.by_grid_point_at_time, {"time": "2024-01-01T00:10:00.000Z"}, zeros),
        ("coverage_time_by_grid_point", coverage.coverage_time.by_grid_point, {"compute_type": "TotalTimeAbove"}, zeros),
        ("number_average", coverage.number_of_assets.by_grid_point, {"compute_type": "Average"}, zeros),
        ("number_minimum", coverage.number_of_assets.by_grid_point, {"compute_type": "Minimum"}, zeros),
        ("number_maximum", coverage.number_of_assets.by_grid_point, {"compute_type": "Maximum"}, zeros),
        ("number_at_time", coverage.number_of_assets.by_grid_point_at_time, {"time": "2024-01-01T00:10:00.000Z"}, zeros),
        ("response_minimum", coverage.response_time.by_grid_point, {"compute_type": "Minimum"}, full_window),
        ("response_maximum", coverage.response_time.by_grid_point, {"compute_type": "Maximum"}, full_window),
        ("revisit_minimum", coverage.revisit_time.by_grid_point, {"compute_type": "Minimum"}, full_window),
        ("revisit_average", coverage.revisit_time.by_grid_point, {"compute_type": "Average"}, full_window),
        ("revisit_maximum", coverage.revisit_time.by_grid_point, {"compute_type": "Maximum"}, full_window),
        ("revisit_at_time", coverage.revisit_time.by_grid_point_at_time, {"time": "2024-01-01T00:10:00.000Z"}, full_window),
    ]
    for label, func, extra, expected in static_cases:
        report = func(start=START, stop=STOP, grid=grid, assets=assets, minimum_assets=1, step_s=60.0, **extra)
        assert_fom_values(label, report["Datas"], points, expected)

    stat_cases = [
        ("simple_grid_stats", coverage.simple_coverage.grid_stats, {}, zeros),
        ("coverage_time_grid_stats", coverage.coverage_time.grid_stats, {"compute_type": "TotalTimeAbove"}, zeros),
        ("number_grid_stats", coverage.number_of_assets.grid_stats, {"compute_type": "Average"}, zeros),
        ("response_grid_stats", coverage.response_time.grid_stats, {"compute_type": "Maximum"}, full_window),
        ("revisit_grid_stats", coverage.revisit_time.grid_stats, {"compute_type": "Average"}, full_window),
    ]
    for label, func, extra, expected in stat_cases:
        report = func(start=START, stop=STOP, grid=grid, assets=assets, minimum_assets=1, step_s=60.0, **extra)
        assert_stats(label, report, expected)

    over_time_cases = [
        ("simple_over_time", coverage.simple_coverage.grid_stats_over_time, zeros),
        ("number_over_time", coverage.number_of_assets.grid_stats_over_time, zeros),
        ("revisit_over_time", coverage.revisit_time.grid_stats_over_time, full_window),
    ]
    expected_offsets = sample_offsets(STOP, step_s=700.0)
    for label, func, expected in over_time_cases:
        report = func(start=START, stop=STOP, grid=grid, assets=assets, minimum_assets=1, step_s=700.0)
        assert_epoch_series(label, report["Datas"], expected_offsets)
        for row in report["Datas"]:
            assert_stats(f"{label}@{row['EpochSeconds']}", row, expected)


def test_continuous_coverage_fom_routes_match_edge_case_conventions() -> None:
    configure_astrox_from_env()
    grid = intermittent_grid()
    assets = [primary_asset()]
    points = expected_points(grid)
    duration = duration_s(start=CONTINUOUS_START, stop=CONTINUOUS_STOP)
    zeros = [0.0 for _ in points]
    ones = [1.0 for _ in points]
    full_window = [duration for _ in points]

    wider_trace = compute_trace(grid=grid, assets=assets)
    assert_continuous_window_is_inside_positive_intervals(wider_trace)
    with pytest.raises(exceptions.AstroxAPIError) as compute_error:
        compute_trace(start=CONTINUOUS_START, stop=CONTINUOUS_STOP, grid=grid, assets=assets, step_s=120.0)
    assert compute_error.value.endpoint == "/Coverage/ComputeCoverage"
    assert "Index was out of range" in str(compute_error.value)

    static_cases = [
        ("simple_by_grid_point", coverage.simple_coverage.by_grid_point, {}, ones),
        ("simple_at_time", coverage.simple_coverage.by_grid_point_at_time, {"time": "2024-01-01T00:05:00.000Z"}, ones),
        ("coverage_time_by_grid_point", coverage.coverage_time.by_grid_point, {"compute_type": "TotalTimeAbove"}, full_window),
        ("number_average", coverage.number_of_assets.by_grid_point, {"compute_type": "Average"}, ones),
        ("number_minimum", coverage.number_of_assets.by_grid_point, {"compute_type": "Minimum"}, ones),
        ("number_maximum", coverage.number_of_assets.by_grid_point, {"compute_type": "Maximum"}, ones),
        ("number_at_time", coverage.number_of_assets.by_grid_point_at_time, {"time": "2024-01-01T00:05:00.000Z"}, ones),
        ("response_minimum", coverage.response_time.by_grid_point, {"compute_type": "Minimum"}, zeros),
        ("response_maximum", coverage.response_time.by_grid_point, {"compute_type": "Maximum"}, zeros),
        ("response_at_time", coverage.response_time.by_grid_point_at_time, {"time": "2024-01-01T00:05:00.000Z"}, zeros),
        ("revisit_minimum", coverage.revisit_time.by_grid_point, {"compute_type": "Minimum"}, zeros),
        ("revisit_average", coverage.revisit_time.by_grid_point, {"compute_type": "Average"}, zeros),
        ("revisit_maximum", coverage.revisit_time.by_grid_point, {"compute_type": "Maximum"}, zeros),
        ("revisit_at_time", coverage.revisit_time.by_grid_point_at_time, {"time": "2024-01-01T00:05:00.000Z"}, zeros),
    ]
    for label, func, extra, expected in static_cases:
        report = func(
            start=CONTINUOUS_START,
            stop=CONTINUOUS_STOP,
            grid=grid,
            assets=assets,
            minimum_assets=1,
            step_s=120.0,
            **extra,
        )
        assert_fom_values(label, report["Datas"], points, expected)

    stat_cases = [
        ("simple_grid_stats", coverage.simple_coverage.grid_stats, {}, ones),
        ("coverage_time_grid_stats", coverage.coverage_time.grid_stats, {"compute_type": "TotalTimeAbove"}, full_window),
        ("number_grid_stats", coverage.number_of_assets.grid_stats, {"compute_type": "Average"}, ones),
        ("response_grid_stats", coverage.response_time.grid_stats, {"compute_type": "Maximum"}, zeros),
        ("revisit_grid_stats", coverage.revisit_time.grid_stats, {"compute_type": "Average"}, zeros),
    ]
    for label, func, extra, expected in stat_cases:
        report = func(
            start=CONTINUOUS_START,
            stop=CONTINUOUS_STOP,
            grid=grid,
            assets=assets,
            minimum_assets=1,
            step_s=120.0,
            **extra,
        )
        assert_stats(label, report, expected)

    over_time_cases = [
        ("simple_over_time", coverage.simple_coverage.grid_stats_over_time, ones),
        ("number_over_time", coverage.number_of_assets.grid_stats_over_time, ones),
        ("response_over_time", coverage.response_time.grid_stats_over_time, zeros),
        ("revisit_over_time", coverage.revisit_time.grid_stats_over_time, zeros),
    ]
    expected_offsets = sample_offsets(CONTINUOUS_STOP, start=CONTINUOUS_START, step_s=120.0)
    for label, func, expected in over_time_cases:
        report = func(
            start=CONTINUOUS_START,
            stop=CONTINUOUS_STOP,
            grid=grid,
            assets=assets,
            minimum_assets=1,
            step_s=120.0,
        )
        assert_epoch_series(label, report["Datas"], expected_offsets)
        for row in report["Datas"]:
            assert_stats(f"{label}@{row['EpochSeconds']}", row, expected)


def assert_continuous_window_is_inside_positive_intervals(trace: dict) -> None:
    window_start = duration_s(start=START, stop=CONTINUOUS_START)
    window_stop = duration_s(start=START, stop=CONTINUOUS_STOP)
    for point_index, intervals in enumerate(trace["SatisfactionIntervalsWithNumberOfAssets"]):
        if not any(
            interval["NumberOfAssets"] > 0
            and duration_s(start=START, stop=interval["Start"]) <= window_start
            and duration_s(start=START, stop=interval["Stop"]) >= window_stop
            for interval in intervals
        ):
            raise CrossValidationError(f"point {point_index}: continuous window is not inside a positive interval")


def run_all_checks() -> int:
    test_no_coverage_fom_routes_match_edge_case_conventions()
    test_continuous_coverage_fom_routes_match_edge_case_conventions()
    return 2


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
