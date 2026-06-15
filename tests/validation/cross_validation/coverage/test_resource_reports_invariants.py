#!/usr/bin/env python3
"""Coverage resource-count and report cross-validation against interval invariants."""

# Coverage:
#   Branches:
#     - ComputeCoverage one SGP4 asset with AtLeastN=1: verified against per-asset interval composition
#     - ComputeCoverage duplicate SGP4 assets with AtLeastN=2: verified against per-asset interval composition
#     - ComputeCoverage two SGP4 assets where only one reaches the grid with AtLeastN=2: verified as all-zero aggregate intervals while individual asset intervals remain present
#     - ComputeCoverage ExactlyN: verified for covered cases to behave as an at-least threshold, not strict equality; this is an observed ASTROX convention, not the SDK changing the wire name
#     - PercentCoverage report: verified against weighted grid-point membership sampled at Step seconds
#     - CoverageByAsset report: verified against summary statistics from the matching percent-coverage report for a one-asset case
#     - Fixed-site asset role: unresolved server behavior; smallest repro returns worker "Index was out of range" instead of coverage intervals
#   Fields:
#     - SatisfactionIntervalsWithNumberOfAssets: verified as thresholded count trace derived from AssetAccessResults in covered cases
#     - AssetAccessResults: verified to preserve per-grid-point, per-asset intervals and duplicate identical assets independently
#     - PercentCoverageDatas[].EpochSeconds: verified to follow Step samples from the report epoch
#     - PercentCoverageDatas[].PercentCovered: verified as area-weighted active grid-point coverage at the sample epoch
#     - PercentCoverageDatas[].PercentAccumulated: verified as area-weighted ever-covered grid-point coverage up to the sample epoch
#     - CoverageByAssetDatas[].Minimum/Maximum/Average/AccumulatedCoveragePercent: verified against PercentCoverageDatas summary for one asset
#   Parameters:
#     - minimum_assets: verified for N=1 and N=2
#     - exactly_assets: partial; covered cases show at-least behavior for N=1, but non-overlapping exact-only semantics remain unresolved
#     - include_asset_access_results: verified as required evidence for per-asset composition
#     - step_s: verified for report sampling; not claimed to affect interval boundary precision
#   Comparison:
#     - External: local interval composition over per-asset intervals, weighted grid-point percentage arithmetic, and cross-report summary invariants
#     - Constants: no physical constants; grid weights are ASTROX output fields whose area formula is calibrated separately
#     - Tolerances: TIME_ABS_S=0.002 because ASTROX interval strings are millisecond-formatted while Duration carries sub-millisecond internal values; PERCENT_ABS=1e-7 for floating-point weighted averages
#   Findings:
#     - ComputeCoverage keeps zero-asset intervals in SatisfactionIntervalsWithNumberOfAssets.
#     - Aggregate intervals include the actual number of simultaneously covering assets when that count meets the requested threshold; segments below the threshold are returned as zero.
#     - In the covered cases, ExactlyN is not strict equality. It behaves like the same NumberOfAssets threshold used by AtLeastN.
#     - PercentCoverage uses grid-point Weight values, not a simple point count, for representative LatLonBounds grids.

from __future__ import annotations

import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, entities, exceptions
from tests.validation._support import LiveConfigError, configure_astrox_from_env


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:30:00.000Z"
TIME_ABS_S = 0.002
PERCENT_ABS = 1.0e-7
TLE_A = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
TLE_B_OFFSET_RAAN = (
    "1 25545U 98067B   24001.00000000  .00002182  00000-0  41420-4 0  9991",
    "2 25545  51.6461 159.8014 0001882  64.8995 295.2305 15.48919393123452",
)


class CrossValidationError(Exception):
    """Raised when live ASTROX coverage behavior disagrees with an invariant."""


def sample_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )


def sgp4_asset(name: str, tle_lines: tuple[str, str] = TLE_A) -> entities.Entity:
    return entities.entity(
        name=name,
        position=entities.sgp4_position(tle_lines=tle_lines),
    )


def test_compute_resource_counts_match_asset_interval_composition() -> None:
    configure_astrox_from_env()
    cases = [
        {
            "label": "single_at_least_1",
            "assets": [sgp4_asset("RelayA")],
            "kwargs": {"minimum_assets": 1},
            "threshold": 1,
        },
        {
            "label": "duplicate_at_least_2",
            "assets": [sgp4_asset("RelayA"), sgp4_asset("RelayA2")],
            "kwargs": {"minimum_assets": 2},
            "threshold": 2,
        },
        {
            "label": "offset_at_least_2",
            "assets": [
                sgp4_asset("RelayA"),
                sgp4_asset("RelayB", TLE_B_OFFSET_RAAN),
            ],
            "kwargs": {"minimum_assets": 2},
            "threshold": 2,
        },
        {
            "label": "duplicate_exactly_1_observed_at_least",
            "assets": [sgp4_asset("RelayA"), sgp4_asset("RelayA2")],
            "kwargs": {"exactly_assets": 1},
            "threshold": 1,
        },
    ]
    for case in cases:
        result = coverage.compute(
            start=START,
            stop=STOP,
            grid=sample_grid(),
            assets=case["assets"],
            include_asset_access_results=True,
            step_s=60.0,
            **case["kwargs"],
        )
        assert_satisfaction_matches_asset_composition(
            label=case["label"],
            result=result,
            threshold=case["threshold"],
        )


def test_duplicate_assets_remain_distinct_asset_access_entries() -> None:
    configure_astrox_from_env()
    result = coverage.compute(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sgp4_asset("RelayA"), sgp4_asset("RelayA2")],
        minimum_assets=2,
        include_asset_access_results=True,
        step_s=60.0,
    )
    for point_index, point_assets in enumerate(result["AssetAccessResults"]):
        if len(point_assets) != 2:
            raise CrossValidationError(
                f"point {point_index}: expected two asset entries, got {len(point_assets)}"
            )
        if point_assets[0] != point_assets[1]:
            raise CrossValidationError(
                f"point {point_index}: duplicate assets produced different intervals"
            )


def test_percent_coverage_matches_weighted_sampled_satisfaction() -> None:
    configure_astrox_from_env()
    grid = sample_grid()
    asset = sgp4_asset("RelayA")
    points = coverage.grid_points(grid=grid)["Points"]["GridPoints"]
    compute_result = coverage.compute(
        start=START,
        stop=STOP,
        grid=grid,
        assets=[asset],
        minimum_assets=1,
        include_asset_access_results=True,
        step_s=300.0,
    )
    report = coverage.percent_coverage(
        start=START,
        stop=STOP,
        grid=grid,
        assets=[asset],
        minimum_assets=1,
        step_s=300.0,
    )
    weights = [point["Weight"] for point in points]
    for sample in report["PercentCoverageDatas"]:
        epoch_seconds = sample["EpochSeconds"]
        expected_current = weighted_current_percent(
            compute_result["SatisfactionIntervalsWithNumberOfAssets"],
            weights,
            epoch_seconds,
        )
        expected_accumulated = weighted_accumulated_percent(
            compute_result["SatisfactionIntervalsWithNumberOfAssets"],
            weights,
            epoch_seconds,
        )
        assert_close_percent(
            "PercentCovered",
            epoch_seconds,
            expected_current,
            sample["PercentCovered"],
        )
        assert_close_percent(
            "PercentAccumulated",
            epoch_seconds,
            expected_accumulated,
            sample["PercentAccumulated"],
        )


def test_coverage_by_asset_matches_percent_report_summary_for_one_asset() -> None:
    configure_astrox_from_env()
    grid = sample_grid()
    asset = sgp4_asset("RelayA")
    percent = coverage.percent_coverage(
        start=START,
        stop=STOP,
        grid=grid,
        assets=[asset],
        minimum_assets=1,
        step_s=60.0,
    )
    by_asset = coverage.coverage_by_asset(
        start=START,
        stop=STOP,
        grid=grid,
        assets=[asset],
        minimum_assets=1,
        step_s=60.0,
    )
    samples = percent["PercentCoverageDatas"]
    values = [sample["PercentCovered"] for sample in samples]
    summary = by_asset["CoverageByAssetDatas"][0]
    expected = {
        "MinimumCoveragePercent": min(values),
        "MaximumCoveragePercent": max(values),
        "AverageCoveragePercent": sum(values) / len(values),
        "AccumulatedCoveragePercent": samples[-1]["PercentAccumulated"],
    }
    for key, expected_value in expected.items():
        assert_close_percent(key, 0.0, expected_value, summary[key])


def test_fixed_site_asset_role_reduces_to_server_worker_error() -> None:
    configure_astrox_from_env()
    site_asset = entities.entity(
        name="GroundAsset",
        position=entities.site_position(
            latitude_deg=0.0,
            longitude_deg=0.0,
            height_m=0.0,
        ),
    )
    grid = coverage.lat_lon_grid(
        min_latitude_deg=-0.5,
        max_latitude_deg=0.5,
        min_longitude_deg=-0.5,
        max_longitude_deg=0.5,
        resolution_deg=10.0,
    )
    with pytest.raises(exceptions.AstroxAPIError, match="Index was out of range"):
        coverage.compute(
            start=START,
            stop="2024-01-01T00:10:00.000Z",
            grid=grid,
            assets=[site_asset],
            minimum_assets=1,
            include_asset_access_results=True,
            include_coverage_points=True,
            step_s=60.0,
        )


def assert_satisfaction_matches_asset_composition(
    *,
    label: str,
    result: dict[str, Any],
    threshold: int,
) -> None:
    expected_by_point = [
        expected_thresholded_intervals(point_assets, threshold=threshold)
        for point_assets in result["AssetAccessResults"]
    ]
    actual_by_point = result["SatisfactionIntervalsWithNumberOfAssets"]
    if len(actual_by_point) != len(expected_by_point):
        raise CrossValidationError(
            f"{label}: expected {len(expected_by_point)} point interval lists, got {len(actual_by_point)}"
        )
    for point_index, (expected, actual) in enumerate(
        zip(expected_by_point, actual_by_point, strict=True)
    ):
        compare_interval_trace(label, point_index, expected, actual)


def expected_thresholded_intervals(
    point_assets: list[list[dict[str, Any]]],
    *,
    threshold: int,
) -> list[dict[str, float | int]]:
    start_s = seconds_since_start(START)
    stop_s = seconds_since_start(STOP)
    boundaries = {start_s, stop_s}
    for asset_intervals in point_assets:
        for interval in asset_intervals:
            boundaries.add(seconds_since_start(interval["Start"]))
            boundaries.add(seconds_since_start(interval["Stop"]))
    ordered = sorted(boundaries)
    segments: list[dict[str, float | int]] = []
    for left, right in zip(ordered, ordered[1:], strict=False):
        if right <= left:
            continue
        midpoint = (left + right) / 2.0
        active_count = sum(
            any(
                seconds_since_start(interval["Start"])
                <= midpoint
                < seconds_since_start(interval["Stop"])
                for interval in asset_intervals
            )
            for asset_intervals in point_assets
        )
        count = active_count if active_count >= threshold else 0
        if segments and segments[-1]["NumberOfAssets"] == count:
            segments[-1]["StopSeconds"] = right
            segments[-1]["Duration"] = right - segments[-1]["StartSeconds"]
        else:
            segments.append(
                {
                    "NumberOfAssets": count,
                    "StartSeconds": left,
                    "StopSeconds": right,
                    "Duration": right - left,
                }
            )
    return segments


def compare_interval_trace(
    label: str,
    point_index: int,
    expected: list[dict[str, float | int]],
    actual: list[dict[str, Any]],
) -> None:
    if len(actual) != len(expected):
        raise CrossValidationError(
            f"{label}: point {point_index} expected {len(expected)} intervals, got {len(actual)}"
        )
    for interval_index, (expected_interval, actual_interval) in enumerate(
        zip(expected, actual, strict=True)
    ):
        if actual_interval["NumberOfAssets"] != expected_interval["NumberOfAssets"]:
            raise CrossValidationError(
                f"{label}: point {point_index} interval {interval_index} expected NumberOfAssets={expected_interval['NumberOfAssets']}, got {actual_interval['NumberOfAssets']}"
            )
        actual_start = seconds_since_start(actual_interval["Start"])
        actual_stop = seconds_since_start(actual_interval["Stop"])
        assert_close_time(
            label,
            point_index,
            interval_index,
            "Start",
            expected_interval["StartSeconds"],
            actual_start,
        )
        assert_close_time(
            label,
            point_index,
            interval_index,
            "Stop",
            expected_interval["StopSeconds"],
            actual_stop,
        )
        assert_close_time(
            label,
            point_index,
            interval_index,
            "Duration",
            expected_interval["Duration"],
            actual_interval["Duration"],
        )


def weighted_current_percent(
    point_intervals: list[list[dict[str, Any]]],
    weights: list[float],
    epoch_seconds: float,
) -> float:
    total_weight = sum(weights)
    covered_weight = sum(
        weight
        for weight, intervals in zip(weights, point_intervals, strict=True)
        if any(
            interval["NumberOfAssets"] > 0
            and seconds_since_start(interval["Start"])
            <= epoch_seconds
            < seconds_since_start(interval["Stop"])
            for interval in intervals
        )
    )
    return 100.0 * covered_weight / total_weight


def weighted_accumulated_percent(
    point_intervals: list[list[dict[str, Any]]],
    weights: list[float],
    epoch_seconds: float,
) -> float:
    total_weight = sum(weights)
    covered_weight = sum(
        weight
        for weight, intervals in zip(weights, point_intervals, strict=True)
        if any(
            interval["NumberOfAssets"] > 0
            and seconds_since_start(interval["Start"])
            <= epoch_seconds
            for interval in intervals
        )
    )
    return 100.0 * covered_weight / total_weight


def seconds_since_start(value: str) -> float:
    return (parse_utc(value) - parse_utc(START)).total_seconds()


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def assert_close_time(
    label: str,
    point_index: int,
    interval_index: int,
    field: str,
    expected: float | int,
    actual: float | int,
) -> None:
    if abs(float(expected) - float(actual)) > TIME_ABS_S:
        raise CrossValidationError(
            f"{label}: point {point_index} interval {interval_index} {field} expected {expected}, got {actual}"
        )


def assert_close_percent(
    field: str,
    epoch_seconds: float,
    expected: float,
    actual: float,
) -> None:
    if not math.isclose(expected, actual, abs_tol=PERCENT_ABS):
        raise CrossValidationError(
            f"{field} at t={epoch_seconds} expected {expected}, got {actual}"
        )


def run_all_checks() -> int:
    grid = sample_grid()
    asset = sgp4_asset("RelayA")
    result = coverage.compute(
        start=START,
        stop=STOP,
        grid=grid,
        assets=[asset],
        minimum_assets=1,
        include_asset_access_results=True,
        step_s=60.0,
    )
    assert_satisfaction_matches_asset_composition(
        label="single_at_least_1",
        result=result,
        threshold=1,
    )
    points = coverage.grid_points(grid=grid)["Points"]["GridPoints"]
    percent = coverage.percent_coverage(
        start=START,
        stop=STOP,
        grid=grid,
        assets=[asset],
        minimum_assets=1,
        step_s=300.0,
    )
    weights = [point["Weight"] for point in points]
    for sample in percent["PercentCoverageDatas"]:
        assert_close_percent(
            "PercentCovered",
            sample["EpochSeconds"],
            weighted_current_percent(
                result["SatisfactionIntervalsWithNumberOfAssets"],
                weights,
                sample["EpochSeconds"],
            ),
            sample["PercentCovered"],
        )
    return 2


def main() -> int:
    try:
        configure_astrox_from_env()
        checked = run_all_checks()
        print(f"CROSS_VALIDATION_CHECKED={checked}")
        print("CROSS_VALIDATION_FAILED=0")
        return 0
    except (CrossValidationError, LiveConfigError, exceptions.AstroxAPIError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
