#!/usr/bin/env python3
"""Coverage FOM at-time boundary cross-validation."""

# Coverage:
#   Branches:
#     - SimpleCoverage ValueByGridPointAtTime: verified at analysis-window start/stop and rounded interval transition strings
#     - NumberOfAssets ValueByGridPointAtTime: verified at analysis-window start/stop and rounded interval transition strings
#     - RevisitTime ValueByGridPointAtTime: verified at analysis-window start/stop and rounded interval transition strings
#     - SimpleCoverage/NumberOfAssets/RevisitTime outside analysis window: verified as current ASTROX zero-valued behavior for representative one-asset case
#   Fields:
#     - Datas[].Latitude/Longitude/Altitude: verified against ComputeCoverage Points for in-window boundary cases
#     - Datas[].FOM_Value: verified against local precise-duration interval derivation for in-window boundary cases
#   Parameters:
#     - time: verified at Start, Stop, a rounded positive-interval start string, a rounded positive-interval stop string, and one post-Stop time
#   Comparison:
#     - External: local interval membership derived from ComputeCoverage Duration values instead of rounded interval timestamp strings
#     - Constants: no physical constants; Duration is used because live ASTROX interval timestamps are millisecond strings while durations preserve sub-millisecond transition precision
#     - Tolerances: VALUE_ABS=1e-6 for endpoint-to-endpoint floating values; POSITION_ABS_DEG=1e-10 for grid coordinate echoes
#   Findings:
#     - At-time FOM routes use ASTROX's internal transition precision, not the rounded millisecond strings returned in ComputeCoverage intervals.
#     - A rounded access-start timestamp can still evaluate as uncovered when the precise transition occurs a fraction of a millisecond later.

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
    assert_fom_values,
    compute_trace,
    intermittent_grid,
    primary_asset,
    seconds_since_start,
)


def test_at_time_routes_match_precise_interval_derivation_at_boundaries() -> None:
    configure_astrox_from_env()
    trace = compute_trace(grid=intermittent_grid(), assets=[primary_asset()], step_s=60.0)
    transition_start = trace["SatisfactionIntervalsWithNumberOfAssets"][0][1]["Start"]
    transition_stop = trace["SatisfactionIntervalsWithNumberOfAssets"][0][1]["Stop"]
    for label, time in [
        ("window_start", START),
        ("rounded_access_start", transition_start),
        ("rounded_access_stop", transition_stop),
        ("window_stop", STOP),
    ]:
        seconds = seconds_since_start(time)
        simple_expected = [
            1.0 if precise_active_count_at(intervals, seconds) > 0 else 0.0
            for intervals in trace["SatisfactionIntervalsWithNumberOfAssets"]
        ]
        number_expected = [
            precise_active_count_at(intervals, seconds)
            for intervals in trace["SatisfactionIntervalsWithNumberOfAssets"]
        ]
        revisit_expected = [
            precise_containing_gap_duration(intervals, seconds)
            for intervals in trace["SatisfactionIntervalsWithNumberOfAssets"]
        ]
        route_cases = [
            ("simple", coverage.simple_coverage.by_grid_point_at_time, simple_expected),
            ("number", coverage.number_of_assets.by_grid_point_at_time, number_expected),
            ("revisit", coverage.revisit_time.by_grid_point_at_time, revisit_expected),
        ]
        for metric_label, func, expected in route_cases:
            report = func(
                time=time,
                start=START,
                stop=STOP,
                grid=intermittent_grid(),
                assets=[primary_asset()],
                minimum_assets=1,
                step_s=60.0,
            )
            assert_fom_values(
                f"{metric_label}_{label}",
                report["Datas"],
                trace["Points"]["GridPoints"],
                expected,
            )


def test_non_response_at_time_routes_outside_window_return_zero_values() -> None:
    configure_astrox_from_env()
    points = compute_trace(grid=intermittent_grid(), assets=[primary_asset()], step_s=60.0)["Points"]["GridPoints"]
    zeros = [0.0 for _ in points]
    route_cases = [
        ("simple", coverage.simple_coverage.by_grid_point_at_time),
        ("number", coverage.number_of_assets.by_grid_point_at_time),
        ("revisit", coverage.revisit_time.by_grid_point_at_time),
    ]
    for label, func in route_cases:
        report = func(
            time="2024-01-01T00:31:00.000Z",
            start=START,
            stop=STOP,
            grid=intermittent_grid(),
            assets=[primary_asset()],
            minimum_assets=1,
            step_s=60.0,
        )
        assert_fom_values(f"{label}_outside_window", report["Datas"], points, zeros)


def precise_active_count_at(intervals: list[dict], seconds: float) -> int:
    cursor = 0.0
    for interval in intervals:
        next_cursor = cursor + interval["Duration"]
        if cursor <= seconds <= next_cursor:
            return int(interval["NumberOfAssets"])
        cursor = next_cursor
    raise CrossValidationError(f"no precise interval contains t={seconds}")


def precise_containing_gap_duration(intervals: list[dict], seconds: float) -> float:
    cursor = 0.0
    for interval in intervals:
        next_cursor = cursor + interval["Duration"]
        if cursor <= seconds <= next_cursor:
            if interval["NumberOfAssets"] > 0:
                return 0.0
            return interval["Duration"]
        cursor = next_cursor
    raise CrossValidationError(f"no precise interval contains t={seconds}")


def run_all_checks() -> int:
    test_at_time_routes_match_precise_interval_derivation_at_boundaries()
    test_non_response_at_time_routes_outside_window_return_zero_values()
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
