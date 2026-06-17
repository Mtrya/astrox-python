#!/usr/bin/env python3
"""Coverage grid-point modifier cross-validation against interval invariants."""

# Coverage:
#   Branches:
#     - GridPointConstraints Range: verified for permissive max/min equality and restrictive max/min pointwise subset behavior; over-restrictive branches reduce to worker error instead of empty intervals
#     - GridPointConstraints ElevationAngle: verified for permissive minimum equality and restrictive minimum/maximum pointwise subset behavior; over-restrictive branches reduce to worker error instead of empty intervals
#     - GridPointConstraints AzElMask: unresolved server role behavior; smallest repro returns a clear non-ground-station server error
#     - GridPointSensor Conic: verified for 90 deg full-hemisphere equality and 89 deg restrictive pointwise subset behavior; very narrow sensor reduces to worker error instead of empty intervals
#     - GridPointSensor Rectangular: verified for 90 deg full-hemisphere equality and 89 deg restrictive pointwise subset behavior; very narrow sensor reduces to worker error instead of empty intervals
#   Fields:
#     - SatisfactionIntervalsWithNumberOfAssets: verified for equality/subset relations against the unconstrained baseline in covered modifier branches
#     - AssetAccessResults: verified for equality/subset relations against the unconstrained baseline in covered modifier branches
#   Parameters:
#     - Range.MaximumValue/IsMaximumEnabled: verified at 5000 km as permissive and 2000 km as restrictive; 500 km captured as worker-error edge
#     - Range.MinimumValue: verified at 0 km as permissive and 1000 km as restrictive; 3000 km captured as worker-error edge
#     - ElevationAngle.MinimumValue: verified at 0 deg as permissive and 10 deg as restrictive; 45 deg captured as worker-error edge
#     - ElevationAngle.MaximumValue/IsMaximumEnabled: verified at 20 deg as restrictive and 90 deg as permissive; 0 deg captured as worker-error edge
#     - AzElMaskData: unresolved for coverage grid-point role because live ASTROX rejects the representative branch before intervals are produced
#     - Conic.outerHalfAngle: verified at 90 and 89 deg; 1 deg captured as worker-error edge
#     - Rectangular.xHalfAngle/yHalfAngle: verified at 90 and 89 deg; 1 deg captured as worker-error edge
#   Comparison:
#     - External: local interval set equality/subset arithmetic over unconstrained baseline intervals; physical monotonicity invariant for applying additional constraints or narrowing sensor field of view
#     - Constants: no physical constants; thresholds are selected only to produce permissive, restrictive, and over-restrictive branches on the representative live case
#     - Tolerances: TIME_ABS_S=0.002 because ASTROX interval strings are millisecond-formatted while Duration carries sub-millisecond internal values
#   Findings:
#     - Permissive range/elevation/sensor branches preserve baseline intervals exactly in the covered cases.
#     - Restrictive but still-accessible range/elevation/sensor branches return pointwise subsets of the baseline intervals.
#     - When a modifier eliminates all coverage in the covered cases, ASTROX returns a worker "Index was out of range" error instead of empty zero-asset intervals.
#     - AzElMask in the coverage grid-point modifier role currently fails with a server message that the current object is not a ground-station object.

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, components, exceptions
from tests.validation._support import LiveConfigError, configure_astrox_from_env


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:30:00.000Z"
TIME_ABS_S = 0.002
TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


class CrossValidationError(Exception):
    """Raised when live ASTROX coverage modifier behavior disagrees with invariants."""


def sample_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )


def sample_asset() -> components.Entity:
    return components.entity(
        name="RelayA",
        position=components.sgp4_position(tle_lines=TLE),
    )


def compute_with_modifiers(
    *,
    grid_point_sensor: components.EntitySensor | None = None,
    grid_point_constraints: list[components.Constraint] | None = None,
) -> dict[str, Any]:
    return coverage.compute(
        start=START,
        stop=STOP,
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=1,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=True,
        step_s=60.0,
    )


def test_permissive_grid_point_modifiers_match_unmodified_intervals() -> None:
    configure_astrox_from_env()
    baseline = compute_with_modifiers()
    cases = {
        "range_max_5000": compute_with_modifiers(
            grid_point_constraints=[
                components.range_constraint(maximum_km=5000.0, maximum_enabled=True)
            ]
        ),
        "range_min_0": compute_with_modifiers(
            grid_point_constraints=[components.range_constraint(minimum_km=0.0)]
        ),
        "elevation_min_0": compute_with_modifiers(
            grid_point_constraints=[components.elevation_constraint(minimum_deg=0.0)]
        ),
        "elevation_max_90": compute_with_modifiers(
            grid_point_constraints=[
                components.elevation_constraint(maximum_deg=90.0, maximum_enabled=True)
            ]
        ),
        "conic_90": compute_with_modifiers(
            grid_point_sensor=components.conic_sensor(outer_half_angle_deg=90.0)
        ),
        "rectangular_90": compute_with_modifiers(
            grid_point_sensor=components.rectangular_sensor(
                x_half_angle_deg=90.0,
                y_half_angle_deg=90.0,
            )
        ),
    }
    for label, result in cases.items():
        assert_same_coverage_traces(label, baseline, result)


def test_restrictive_grid_point_modifiers_are_baseline_subsets() -> None:
    configure_astrox_from_env()
    baseline = compute_with_modifiers()
    cases = {
        "range_max_2000": compute_with_modifiers(
            grid_point_constraints=[
                components.range_constraint(maximum_km=2000.0, maximum_enabled=True)
            ]
        ),
        "range_min_1000": compute_with_modifiers(
            grid_point_constraints=[components.range_constraint(minimum_km=1000.0)]
        ),
        "elevation_min_10": compute_with_modifiers(
            grid_point_constraints=[components.elevation_constraint(minimum_deg=10.0)]
        ),
        "elevation_max_20": compute_with_modifiers(
            grid_point_constraints=[
                components.elevation_constraint(maximum_deg=20.0, maximum_enabled=True)
            ]
        ),
        "conic_89": compute_with_modifiers(
            grid_point_sensor=components.conic_sensor(outer_half_angle_deg=89.0)
        ),
        "rectangular_89": compute_with_modifiers(
            grid_point_sensor=components.rectangular_sensor(
                x_half_angle_deg=89.0,
                y_half_angle_deg=89.0,
            )
        ),
    }
    for label, result in cases.items():
        assert_strict_subset_coverage_traces(label, baseline, result)


@pytest.mark.parametrize(
    ("label", "kwargs"),
    [
        (
            "range_max_500",
            {
                "grid_point_constraints": [
                    components.range_constraint(
                        maximum_km=500.0,
                        maximum_enabled=True,
                    )
                ]
            },
        ),
        (
            "range_min_3000",
            {
                "grid_point_constraints": [
                    components.range_constraint(minimum_km=3000.0)
                ]
            },
        ),
        (
            "elevation_min_45",
            {
                "grid_point_constraints": [
                    components.elevation_constraint(minimum_deg=45.0)
                ]
            },
        ),
        (
            "elevation_max_0",
            {
                "grid_point_constraints": [
                    components.elevation_constraint(
                        maximum_deg=0.0,
                        maximum_enabled=True,
                    )
                ]
            },
        ),
        (
            "conic_1",
            {
                "grid_point_sensor": components.conic_sensor(outer_half_angle_deg=1.0)
            },
        ),
        (
            "rectangular_1",
            {
                "grid_point_sensor": components.rectangular_sensor(
                    x_half_angle_deg=1.0,
                    y_half_angle_deg=1.0,
                )
            },
        ),
    ],
)
def test_over_restrictive_modifiers_reduce_to_worker_error(
    label: str,
    kwargs: dict[str, Any],
) -> None:
    configure_astrox_from_env()
    with pytest.raises(exceptions.AstroxAPIError, match="Index was out of range"):
        compute_with_modifiers(**kwargs)


def test_az_el_mask_grid_point_constraint_reduces_to_non_ground_station_error() -> None:
    configure_astrox_from_env()
    with pytest.raises(exceptions.AstroxAPIError, match="AzElMask"):
        compute_with_modifiers(
            grid_point_constraints=[
                components.az_el_mask_constraint(
                    az_el_mask_rad=[
                        0.0,
                        -1.57079632679,
                        6.28318530718,
                        -1.57079632679,
                    ]
                )
            ]
        )


def assert_same_coverage_traces(
    label: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> None:
    compare_point_traces(
        f"{label} SatisfactionIntervalsWithNumberOfAssets",
        expected["SatisfactionIntervalsWithNumberOfAssets"],
        actual["SatisfactionIntervalsWithNumberOfAssets"],
        relation="equal",
    )
    compare_point_traces(
        f"{label} AssetAccessResults",
        flatten_asset_access(expected["AssetAccessResults"]),
        flatten_asset_access(actual["AssetAccessResults"]),
        relation="equal",
    )


def assert_strict_subset_coverage_traces(
    label: str,
    baseline: dict[str, Any],
    constrained: dict[str, Any],
) -> None:
    baseline_duration = total_positive_duration(
        baseline["SatisfactionIntervalsWithNumberOfAssets"]
    )
    constrained_duration = total_positive_duration(
        constrained["SatisfactionIntervalsWithNumberOfAssets"]
    )
    if constrained_duration >= baseline_duration:
        raise CrossValidationError(
            f"{label}: expected restrictive modifier duration {constrained_duration} "
            f"to be less than baseline {baseline_duration}"
        )
    compare_point_traces(
        f"{label} SatisfactionIntervalsWithNumberOfAssets",
        baseline["SatisfactionIntervalsWithNumberOfAssets"],
        constrained["SatisfactionIntervalsWithNumberOfAssets"],
        relation="subset",
    )
    compare_point_traces(
        f"{label} AssetAccessResults",
        flatten_asset_access(baseline["AssetAccessResults"]),
        flatten_asset_access(constrained["AssetAccessResults"]),
        relation="subset",
    )


def flatten_asset_access(
    value: list[list[list[dict[str, Any]]]],
) -> list[list[dict[str, Any]]]:
    flattened: list[list[dict[str, Any]]] = []
    for point_assets in value:
        intervals: list[dict[str, Any]] = []
        for asset_intervals in point_assets:
            intervals.extend(asset_intervals)
        flattened.append(intervals)
    return flattened


def compare_point_traces(
    label: str,
    expected: list[list[dict[str, Any]]],
    actual: list[list[dict[str, Any]]],
    *,
    relation: str,
) -> None:
    if len(actual) != len(expected):
        raise CrossValidationError(
            f"{label}: expected {len(expected)} point traces, got {len(actual)}"
        )
    for point_index, (expected_trace, actual_trace) in enumerate(
        zip(expected, actual, strict=True)
    ):
        if relation == "equal":
            assert_trace_equal(label, point_index, expected_trace, actual_trace)
        elif relation == "subset":
            assert_trace_subset(label, point_index, expected_trace, actual_trace)
        else:
            raise AssertionError(f"unknown relation {relation!r}")


def assert_trace_equal(
    label: str,
    point_index: int,
    expected: list[dict[str, Any]],
    actual: list[dict[str, Any]],
) -> None:
    expected_positive = positive_segments(expected)
    actual_positive = positive_segments(actual)
    if len(actual_positive) != len(expected_positive):
        raise CrossValidationError(
            f"{label}: point {point_index} expected {len(expected_positive)} "
            f"positive intervals, got {len(actual_positive)}"
        )
    for interval_index, (expected_interval, actual_interval) in enumerate(
        zip(expected_positive, actual_positive, strict=True)
    ):
        if abs(expected_interval[0] - actual_interval[0]) > TIME_ABS_S:
            raise CrossValidationError(
                f"{label}: point {point_index} interval {interval_index} "
                f"start mismatch {expected_interval[0]} vs {actual_interval[0]}"
            )
        if abs(expected_interval[1] - actual_interval[1]) > TIME_ABS_S:
            raise CrossValidationError(
                f"{label}: point {point_index} interval {interval_index} "
                f"stop mismatch {expected_interval[1]} vs {actual_interval[1]}"
            )


def assert_trace_subset(
    label: str,
    point_index: int,
    baseline: list[dict[str, Any]],
    constrained: list[dict[str, Any]],
) -> None:
    baseline_positive = positive_segments(baseline)
    constrained_positive = positive_segments(constrained)
    for interval_index, (left, right) in enumerate(constrained_positive):
        if not any(
            base_left - TIME_ABS_S <= left and right <= base_right + TIME_ABS_S
            for base_left, base_right in baseline_positive
        ):
            raise CrossValidationError(
                f"{label}: point {point_index} interval {interval_index} "
                f"{(left, right)!r} is not a subset of baseline intervals "
                f"{baseline_positive!r}"
            )


def positive_segments(trace: list[dict[str, Any]]) -> list[tuple[float, float]]:
    return [
        (seconds_since_start(interval["Start"]), seconds_since_start(interval["Stop"]))
        for interval in trace
        if interval.get("NumberOfAssets", 1) > 0
    ]


def total_positive_duration(point_traces: list[list[dict[str, Any]]]) -> float:
    return sum(
        right - left
        for trace in point_traces
        for left, right in positive_segments(trace)
    )


def seconds_since_start(value: str) -> float:
    return (parse_utc(value) - parse_utc(START)).total_seconds()


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def run_all_checks() -> int:
    baseline = compute_with_modifiers()
    assert_same_coverage_traces(
        "range_max_5000",
        baseline,
        compute_with_modifiers(
            grid_point_constraints=[
                components.range_constraint(maximum_km=5000.0, maximum_enabled=True)
            ]
        ),
    )
    assert_strict_subset_coverage_traces(
        "elevation_min_10",
        baseline,
        compute_with_modifiers(
            grid_point_constraints=[components.elevation_constraint(minimum_deg=10.0)]
        ),
    )
    with pytest.raises(exceptions.AstroxAPIError, match="Index was out of range"):
        compute_with_modifiers(
            grid_point_sensor=components.conic_sensor(outer_half_angle_deg=1.0)
        )
    return 3


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
