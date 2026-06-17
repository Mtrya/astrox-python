#!/usr/bin/env python3
"""Coverage FOM resource-count and ComputeType cross-validation."""

# Coverage:
#   Branches:
#     - duplicate two-asset FOM with AtLeastN=1 and AtLeastN=2: verified against ComputeCoverage interval traces
#     - duplicate two-asset FOM with ExactlyN=1 and ExactlyN=2: verified to follow the same threshold-like ASTROX convention as ComputeCoverage, not strict equality
#     - offset two-asset FOM with AtLeastN=1 and AtLeastN=2: verified against ComputeCoverage interval traces, including all-zero thresholded traces
#     - unsupported ComputeType strings: verified to fail loudly for CoverageTime, NumberOfAssets, ResponseTime, and RevisitTime ValueByGridPoint routes
#   Fields:
#     - Datas[].Latitude/Longitude/Altitude: verified against ComputeCoverage Points for resource-count cases
#     - Datas[].FOM_Value: verified for SimpleCoverage, CoverageTime, NumberOfAssets, ResponseTime, and RevisitTime from interval/gap derivations
#   Parameters:
#     - minimum_assets: verified for N=1 and N=2 across duplicate and offset asset cases
#     - exactly_assets: verified for N=1 and N=2 across duplicate assets; FOM inherits threshold-like server behavior
#     - compute_type: verified for supported values in the interval-invariant matrix and rejected unsupported strings here
#   Comparison:
#     - External: local interval/gap derivation from ComputeCoverage SatisfactionIntervalsWithNumberOfAssets plus unsupported-option error propagation checks
#     - Constants: no physical constants; duplicate and offset assets are chosen to distinguish one-cover, two-cover, and zero-cover resource-count regimes
#     - Tolerances: VALUE_ABS=1e-6 for endpoint-to-endpoint floating values; POSITION_ABS_DEG=1e-10 for grid coordinate echoes
#   Findings:
#     - FOM NumberOfAssets reports actual active asset count statistics, even when the requested resource-count threshold is lower.
#     - FOM ExactlyN follows ASTROX's observed threshold-like convention from ComputeCoverage for duplicate two-asset cases.
#     - Unsupported ComputeType values are rejected by ASTROX instead of being ignored, defaulted, or silently remapped.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

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
    compute_trace,
    containing_gap_duration,
    duplicate_assets,
    gap_durations,
    intermittent_grid,
    max_positive_count,
    mean,
    min_count,
    offset_assets,
    total_positive_duration,
)


@pytest.mark.parametrize(
    ("label", "assets_factory", "kwargs"),
    [
        ("duplicate_at_least_1", duplicate_assets, {"minimum_assets": 1}),
        ("duplicate_at_least_2", duplicate_assets, {"minimum_assets": 2}),
        ("duplicate_exactly_1", duplicate_assets, {"minimum_assets": None, "exactly_assets": 1}),
        ("duplicate_exactly_2", duplicate_assets, {"minimum_assets": None, "exactly_assets": 2}),
        ("offset_at_least_1", offset_assets, {"minimum_assets": 1}),
        ("offset_at_least_2", offset_assets, {"minimum_assets": 2}),
    ],
)
def test_fom_resource_count_options_match_compute_interval_derivation(
    label: str,
    assets_factory,
    kwargs: dict[str, int | None],
) -> None:
    configure_astrox_from_env()
    assets = assets_factory()
    trace = compute_trace(
        grid=intermittent_grid(),
        assets=assets,
        minimum_assets=kwargs.get("minimum_assets"),
        exactly_assets=kwargs.get("exactly_assets"),
    )
    point_traces = trace["SatisfactionIntervalsWithNumberOfAssets"]
    points = trace["Points"]["GridPoints"]
    duration = 1800.0
    coverage_time_values = [total_positive_duration(intervals) for intervals in point_traces]
    number_average_values = [sum(interval["Duration"] * interval["NumberOfAssets"] for interval in intervals) / duration for intervals in point_traces]
    number_maximum_values = [max_positive_count(intervals) for intervals in point_traces]
    number_minimum_values = [min_count(intervals) for intervals in point_traces]
    simple_values = [1.0 if value > 0.0 else 0.0 for value in coverage_time_values]
    response_max_values = [max(gap_durations(intervals)) if gap_durations(intervals) else 0.0 for intervals in point_traces]
    revisit_average_values = [mean(gap_durations(intervals)) if gap_durations(intervals) else 0.0 for intervals in point_traces]
    revisit_at_time_values = [containing_gap_duration(intervals, 300.0) for intervals in point_traces]
    number_at_time_values = [active_count_at(intervals, 300.0) for intervals in point_traces]

    cases = [
        ("simple", coverage.simple_coverage.by_grid_point, {}, simple_values),
        ("coverage_time", coverage.coverage_time.by_grid_point, {"compute_type": "TotalTimeAbove"}, coverage_time_values),
        ("number_average", coverage.number_of_assets.by_grid_point, {"compute_type": "Average"}, number_average_values),
        ("number_maximum", coverage.number_of_assets.by_grid_point, {"compute_type": "Maximum"}, number_maximum_values),
        ("number_minimum", coverage.number_of_assets.by_grid_point, {"compute_type": "Minimum"}, number_minimum_values),
        ("number_at_time", coverage.number_of_assets.by_grid_point_at_time, {"time": "2024-01-01T00:05:00.000Z"}, number_at_time_values),
        ("response_maximum", coverage.response_time.by_grid_point, {"compute_type": "Maximum"}, response_max_values),
        ("revisit_average", coverage.revisit_time.by_grid_point, {"compute_type": "Average"}, revisit_average_values),
        ("revisit_at_time", coverage.revisit_time.by_grid_point_at_time, {"time": "2024-01-01T00:05:00.000Z"}, revisit_at_time_values),
    ]
    for metric_label, func, extra, expected in cases:
        report = func(
            start=START,
            stop=STOP,
            grid=intermittent_grid(),
            assets=assets,
            step_s=60.0,
            **kwargs,
            **extra,
        )
        assert_fom_values(f"{label}_{metric_label}", report["Datas"], points, expected)


@pytest.mark.parametrize(
    ("label", "func", "compute_type"),
    [
        ("coverage_time", coverage.coverage_time.by_grid_point, "Bogus"),
        ("coverage_time_wrong_metric", coverage.coverage_time.by_grid_point, "Average"),
        ("number_of_assets", coverage.number_of_assets.by_grid_point, "Bogus"),
        ("number_of_assets_wrong_metric", coverage.number_of_assets.by_grid_point, "TotalTimeAbove"),
        ("response_time", coverage.response_time.by_grid_point, "Bogus"),
        ("response_time_wrong_metric", coverage.response_time.by_grid_point, "Average"),
        ("revisit_time", coverage.revisit_time.by_grid_point, "Bogus"),
        ("revisit_time_wrong_metric", coverage.revisit_time.by_grid_point, "TotalTimeAbove"),
    ],
)
def test_fom_unsupported_compute_type_is_rejected(label: str, func, compute_type: str) -> None:
    configure_astrox_from_env()
    with pytest.raises(exceptions.AstroxAPIError) as error:
        func(
            start=START,
            stop=STOP,
            grid=intermittent_grid(),
            assets=offset_assets()[:1],
            minimum_assets=1,
            compute_type=compute_type,
            step_s=300.0,
        )
    if compute_type.upper() not in str(error.value):
        raise CrossValidationError(f"{label}: unsupported ComputeType error did not mention {compute_type!r}")


def run_all_checks() -> int:
    count = 0
    for label, assets_factory, kwargs in [
        ("duplicate_at_least_1", duplicate_assets, {"minimum_assets": 1}),
        ("duplicate_at_least_2", duplicate_assets, {"minimum_assets": 2}),
        ("duplicate_exactly_1", duplicate_assets, {"minimum_assets": None, "exactly_assets": 1}),
        ("duplicate_exactly_2", duplicate_assets, {"minimum_assets": None, "exactly_assets": 2}),
        ("offset_at_least_1", offset_assets, {"minimum_assets": 1}),
        ("offset_at_least_2", offset_assets, {"minimum_assets": 2}),
    ]:
        test_fom_resource_count_options_match_compute_interval_derivation(label, assets_factory, kwargs)
        count += 1
    for label, func, compute_type in [
        ("coverage_time", coverage.coverage_time.by_grid_point, "Bogus"),
        ("coverage_time_wrong_metric", coverage.coverage_time.by_grid_point, "Average"),
        ("number_of_assets", coverage.number_of_assets.by_grid_point, "Bogus"),
        ("number_of_assets_wrong_metric", coverage.number_of_assets.by_grid_point, "TotalTimeAbove"),
        ("response_time", coverage.response_time.by_grid_point, "Bogus"),
        ("response_time_wrong_metric", coverage.response_time.by_grid_point, "Average"),
        ("revisit_time", coverage.revisit_time.by_grid_point, "Bogus"),
        ("revisit_time_wrong_metric", coverage.revisit_time.by_grid_point, "TotalTimeAbove"),
    ]:
        test_fom_unsupported_compute_type_is_rejected(label, func, compute_type)
        count += 1
    return count


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
