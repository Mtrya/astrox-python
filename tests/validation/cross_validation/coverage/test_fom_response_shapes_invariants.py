#!/usr/bin/env python3
"""Coverage FOM response-shape cross-validation."""

# Coverage:
#   Branches:
#     - ValueByGridPoint response shape: verified for SimpleCoverage, CoverageTime, NumberOfAssets, ResponseTime, and RevisitTime
#     - ValueByGridPointAtTime response shape: verified for SimpleCoverage, NumberOfAssets, ResponseTime, and RevisitTime
#     - GridStats response shape: verified for SimpleCoverage, CoverageTime, NumberOfAssets, ResponseTime, and RevisitTime
#     - GridStatsOverTime response shape: verified for SimpleCoverage, NumberOfAssets, ResponseTime, and RevisitTime
#   Fields:
#     - IsSuccess/Message: verified as stable top-level server-status fields in successful FOM responses; no physical meaning is assigned here
#     - Datas[].Latitude/Longitude/Altitude/FOM_Value: verified as the stable by-grid-point row shape; value semantics are calibrated in metric-specific tests
#     - Minimum/Maximum/Average: verified as the stable grid-stat field shape; arithmetic semantics are calibrated in metric-specific tests
#     - Datas[].EpochSeconds/Minimum/Maximum/Average: verified as the stable over-time row shape; sampling semantics are calibrated in metric-specific tests
#   Parameters:
#     - metric route: verified across all 18 public FOM functions using successful representative inputs
#   Comparison:
#     - External: cross-route structural invariant plus metric-specific semantic tests in sibling files
#     - Constants: no physical constants; continuous-coverage inputs are used for response-time dynamic routes because intermittent no-next-access cases are calibrated as HTTP 500
#     - Tolerances: none; this file checks keys and row counts only
#   Findings:
#     - Successful FOM responses use three stable report shapes: point rows, grid statistics, and grid statistics over time.
#     - `IsSuccess` and `Message` are treated as server status fields; all physical interpretation is carried by the route-specific numeric fields.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

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
    intermittent_grid,
    primary_asset,
)


POINT_REPORT_KEYS = {"IsSuccess", "Message", "Datas"}
POINT_ROW_KEYS = {"Latitude", "Longitude", "Altitude", "FOM_Value"}
STATS_REPORT_KEYS = {"IsSuccess", "Message", "Minimum", "Maximum", "Average"}
OVER_TIME_ROW_KEYS = {"EpochSeconds", "Minimum", "Maximum", "Average"}


def test_fom_by_grid_point_shapes_are_stable() -> None:
    configure_astrox_from_env()
    cases = [
        ("simple", coverage.simple_coverage.by_grid_point, {}),
        ("coverage_time", coverage.coverage_time.by_grid_point, {"compute_type": "TotalTimeAbove"}),
        ("number", coverage.number_of_assets.by_grid_point, {"compute_type": "Average"}),
        ("response", coverage.response_time.by_grid_point, {"compute_type": "Maximum"}),
        ("revisit", coverage.revisit_time.by_grid_point, {"compute_type": "Average"}),
    ]
    for label, func, extra in cases:
        report = func(**intermittent_kwargs(), **extra)
        assert_point_report_shape(label, report)


def test_fom_at_time_shapes_are_stable() -> None:
    configure_astrox_from_env()
    cases = [
        ("simple", coverage.simple_coverage.by_grid_point_at_time, intermittent_kwargs(time="2024-01-01T00:05:00.000Z")),
        ("number", coverage.number_of_assets.by_grid_point_at_time, intermittent_kwargs(time="2024-01-01T00:05:00.000Z")),
        ("response", coverage.response_time.by_grid_point_at_time, continuous_kwargs(time="2024-01-01T00:05:00.000Z")),
        ("revisit", coverage.revisit_time.by_grid_point_at_time, intermittent_kwargs(time="2024-01-01T00:05:00.000Z")),
    ]
    for label, func, kwargs in cases:
        report = func(**kwargs)
        assert_point_report_shape(label, report)


def test_fom_grid_stats_shapes_are_stable() -> None:
    configure_astrox_from_env()
    cases = [
        ("simple", coverage.simple_coverage.grid_stats, {}),
        ("coverage_time", coverage.coverage_time.grid_stats, {"compute_type": "TotalTimeAbove"}),
        ("number", coverage.number_of_assets.grid_stats, {"compute_type": "Average"}),
        ("response", coverage.response_time.grid_stats, {"compute_type": "Maximum"}),
        ("revisit", coverage.revisit_time.grid_stats, {"compute_type": "Average"}),
    ]
    for label, func, extra in cases:
        report = func(**intermittent_kwargs(), **extra)
        assert_keys(f"{label}.grid_stats", report, STATS_REPORT_KEYS)
        assert report["IsSuccess"] is True


def test_fom_grid_stats_over_time_shapes_are_stable() -> None:
    configure_astrox_from_env()
    cases = [
        ("simple", coverage.simple_coverage.grid_stats_over_time, intermittent_kwargs()),
        ("number", coverage.number_of_assets.grid_stats_over_time, intermittent_kwargs()),
        ("response", coverage.response_time.grid_stats_over_time, continuous_kwargs()),
        ("revisit", coverage.revisit_time.grid_stats_over_time, intermittent_kwargs()),
    ]
    for label, func, kwargs in cases:
        report = func(**kwargs)
        assert_keys(f"{label}.grid_stats_over_time", report, POINT_REPORT_KEYS)
        assert report["IsSuccess"] is True
        if not report["Datas"]:
            raise CrossValidationError(f"{label}.grid_stats_over_time: expected at least one sample")
        for index, row in enumerate(report["Datas"]):
            assert_keys(f"{label}.grid_stats_over_time[{index}]", row, OVER_TIME_ROW_KEYS)


def intermittent_kwargs(**extra: Any) -> dict[str, Any]:
    return {
        "start": START,
        "stop": STOP,
        "grid": intermittent_grid(),
        "assets": [primary_asset()],
        "minimum_assets": 1,
        "step_s": 300.0,
        **extra,
    }


def continuous_kwargs(**extra: Any) -> dict[str, Any]:
    return {
        "start": CONTINUOUS_START,
        "stop": CONTINUOUS_STOP,
        "grid": intermittent_grid(),
        "assets": [primary_asset()],
        "minimum_assets": 1,
        "step_s": 120.0,
        **extra,
    }


def assert_point_report_shape(label: str, report: dict[str, Any]) -> None:
    assert_keys(label, report, POINT_REPORT_KEYS)
    assert report["IsSuccess"] is True
    if not report["Datas"]:
        raise CrossValidationError(f"{label}: expected at least one point row")
    for index, row in enumerate(report["Datas"]):
        assert_keys(f"{label}[{index}]", row, POINT_ROW_KEYS)


def assert_keys(label: str, value: dict[str, Any], expected: set[str]) -> None:
    actual = set(value)
    if actual != expected:
        raise CrossValidationError(f"{label}: expected keys {sorted(expected)}, got {sorted(actual)}")


def run_all_checks() -> int:
    test_fom_by_grid_point_shapes_are_stable()
    test_fom_at_time_shapes_are_stable()
    test_fom_grid_stats_shapes_are_stable()
    test_fom_grid_stats_over_time_shapes_are_stable()
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
