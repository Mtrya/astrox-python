#!/usr/bin/env python3
"""Coverage FOM grid-branch and grid-point modifier cross-validation."""

# Coverage:
#   Branches:
#     - FOM with LatLonBounds grid: verified against ComputeCoverage interval/gap derivation
#     - FOM with LatitudeBounds grid: verified against ComputeCoverage interval/gap derivation for a no-coverage trace
#     - FOM with Global grid: verified against ComputeCoverage interval/gap derivation for a no-coverage trace
#     - FOM with CbLatLonBounds grid: verified against ComputeCoverage interval/gap derivation for a covered trace
#     - FOM GridStats weighting: verified as arithmetic rather than grid-weighted on a non-equal-weight LatLonBounds grid with differing values
#     - FOM with Range grid-point constraint: verified against modified ComputeCoverage interval/gap derivation
#     - FOM with ElevationAngle grid-point constraint: verified against modified ComputeCoverage interval/gap derivation
#     - FOM with AzElMask grid-point constraint: verified to reject consistently with coverage-role AzElMask server behavior
#     - FOM with Conic grid-point sensor: verified against modified ComputeCoverage interval/gap derivation
#     - FOM with Rectangular grid-point sensor: verified against modified ComputeCoverage interval/gap derivation
#   Fields:
#     - Datas[].Latitude/Longitude/Altitude: verified against ComputeCoverage Points for every branch in this file
#     - Datas[].FOM_Value: verified for SimpleCoverage, CoverageTime, NumberOfAssets, ResponseTime, and RevisitTime representative routes
#     - Minimum/Maximum/Average: verified as arithmetic statistics over derived per-point values for representative grid branches
#   Parameters:
#     - grid: verified for representative LatLonBounds, LatitudeBounds, Global, and CbLatLonBounds branches
#     - grid point Weight: verified not to affect FOM GridStats Average in the representative distinguishing case
#     - grid_point_sensor: verified for Conic and Rectangular restrictive branches that still return coverage
#     - grid_point_constraints: verified for Range and ElevationAngle restrictive branches that still return coverage; AzElMask rejection verified
#   Comparison:
#     - External: local interval/gap derivation from ComputeCoverage with the same grid, sensor, and constraint options
#     - Constants: no physical constants; sensor/constraint thresholds are selected from modifier cross-validation to be restrictive but not over-restrictive
#     - Tolerances: VALUE_ABS=1e-6 for endpoint-to-endpoint floating values; POSITION_ABS_DEG=1e-10 for grid coordinate echoes
#   Findings:
#     - Representative FOM routes consume range/elevation constraints and conic/rectangular sensors consistently with ComputeCoverage interval filtering.
#     - Representative FOM routes reject AzElMask in the coverage grid-point role, matching ComputeCoverage's current non-ground-station role behavior.
#     - FOM routes preserve ComputeCoverage point ordering and coordinates across representative LatLonBounds, LatitudeBounds, Global, and CbLatLonBounds grids.
#     - FOM GridStats Average is arithmetic over point values, not weighted by grid-point Weight.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, entities, exceptions
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.coverage._fom_helpers import (
    START,
    STOP,
    CrossValidationError,
    assert_fom_values,
    assert_stats,
    assert_close,
    compute_trace,
    duration_s,
    gap_durations,
    intermittent_grid,
    mean,
    primary_asset,
    total_positive_duration,
)


def test_fom_grid_point_modifiers_match_compute_interval_derivation() -> None:
    configure_astrox_from_env()
    cases = [
        {
            "label": "range_max_2000",
            "kwargs": {
                "grid_point_constraints": [
                    entities.range_constraint(maximum_km=2000.0, maximum_enabled=True)
                ]
            },
        },
        {
            "label": "elevation_min_10",
            "kwargs": {
                "grid_point_constraints": [
                    entities.elevation_constraint(minimum_deg=10.0)
                ]
            },
        },
        {
            "label": "conic_89",
            "kwargs": {
                "grid_point_sensor": entities.conic_sensor(outer_half_angle_deg=89.0)
            },
        },
        {
            "label": "rectangular_89",
            "kwargs": {
                "grid_point_sensor": entities.rectangular_sensor(
                    x_half_angle_deg=89.0,
                    y_half_angle_deg=89.0,
                )
            },
        },
    ]
    for case in cases:
        assert_representative_fom_routes_match_trace(
            label=case["label"],
            grid=intermittent_grid(),
            step_s=60.0,
            **case["kwargs"],
        )


def test_fom_grid_branches_match_compute_interval_derivation_and_arithmetic_stats() -> None:
    configure_astrox_from_env()
    cases = [
        {
            "label": "lat_lon_bounds",
            "grid": intermittent_grid(),
            "step_s": 300.0,
        },
        {
            "label": "latitude_bounds",
            "grid": coverage.latitude_grid(
                min_latitude_deg=20.0,
                max_latitude_deg=25.0,
                resolution_deg=20.0,
            ),
            "step_s": 300.0,
        },
        {
            "label": "global",
            "grid": coverage.global_grid(resolution_deg=60.0),
            "step_s": 300.0,
        },
        {
            "label": "cb_lat_lon_bounds",
            "grid": coverage.cb_lat_lon_grid(
                min_latitude_deg=20.0,
                max_latitude_deg=25.0,
                min_longitude_deg=-120.0,
                max_longitude_deg=-110.0,
                resolution_deg=5.0,
            ),
            "step_s": 300.0,
        },
    ]
    for case in cases:
        expected = assert_representative_fom_routes_match_trace(
            label=case["label"],
            grid=case["grid"],
            step_s=case["step_s"],
        )
        for metric_label, func, extra, values in [
            (
                "simple_grid_stats",
                coverage.simple_coverage.grid_stats,
                {},
                expected["simple"],
            ),
            (
                "coverage_time_grid_stats",
                coverage.coverage_time.grid_stats,
                {"compute_type": "TotalTimeAbove"},
                expected["coverage_time"],
            ),
            (
                "number_grid_stats",
                coverage.number_of_assets.grid_stats,
                {"compute_type": "Average"},
                expected["number_average"],
            ),
            (
                "response_grid_stats",
                coverage.response_time.grid_stats,
                {"compute_type": "Maximum"},
                expected["response_maximum"],
            ),
            (
                "revisit_grid_stats",
                coverage.revisit_time.grid_stats,
                {"compute_type": "Average"},
                expected["revisit_average"],
            ),
        ]:
            report = func(
                start=START,
                stop=STOP,
                grid=case["grid"],
                assets=[primary_asset()],
                minimum_assets=1,
                step_s=case["step_s"],
                **extra,
            )
            assert_stats(f"{case['label']}_{metric_label}", report, values)


def test_fom_grid_stats_average_is_arithmetic_not_grid_weighted() -> None:
    configure_astrox_from_env()
    trace = compute_trace(grid=intermittent_grid(), step_s=300.0)
    values = [
        total_positive_duration(intervals)
        for intervals in trace["SatisfactionIntervalsWithNumberOfAssets"]
    ]
    weights = [point["Weight"] for point in trace["Points"]["GridPoints"]]
    arithmetic_average = mean(values)
    weighted_average = sum(value * weight for value, weight in zip(values, weights, strict=True)) / sum(weights)
    if abs(arithmetic_average - weighted_average) <= 1.0e-3:
        raise CrossValidationError(
            "representative grid no longer distinguishes arithmetic from weighted FOM statistics"
        )
    report = coverage.coverage_time.grid_stats(
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        compute_type="TotalTimeAbove",
        step_s=300.0,
    )
    assert_close("coverage_time_grid_stats.Average", arithmetic_average, report["Average"])


def test_fom_az_el_mask_constraint_rejects_consistently_with_compute_coverage_role() -> None:
    configure_astrox_from_env()
    mask = entities.az_el_mask_constraint(
        az_el_mask_rad=[0.0, 0.0, 3.141592653589793, 0.0],
    )
    with pytest.raises(exceptions.AstroxAPIError) as compute_error:
        compute_trace(
            grid=intermittent_grid(),
            step_s=60.0,
            grid_point_constraints=[mask],
        )
    assert compute_error.value.endpoint == "/Coverage/ComputeCoverage"
    assert "AzElMask" in str(compute_error.value)

    route_cases = [
        (
            "simple",
            coverage.simple_coverage.by_grid_point,
            {},
            "/Coverage/FOM/ValueByGridPoint/SimpleCoverage",
        ),
        (
            "coverage_time",
            coverage.coverage_time.by_grid_point,
            {"compute_type": "TotalTimeAbove"},
            "/Coverage/FOM/ValueByGridPoint/CoverageTime",
        ),
        (
            "number",
            coverage.number_of_assets.by_grid_point,
            {"compute_type": "Average"},
            "/Coverage/FOM/ValueByGridPoint/NumberOfAssets",
        ),
        (
            "response",
            coverage.response_time.by_grid_point,
            {"compute_type": "Maximum"},
            "/Coverage/FOM/ValueByGridPoint/ResponseTime",
        ),
        (
            "revisit",
            coverage.revisit_time.by_grid_point,
            {"compute_type": "Average"},
            "/Coverage/FOM/ValueByGridPoint/RevisitTime",
        ),
    ]
    for label, func, extra, endpoint in route_cases:
        with pytest.raises(exceptions.AstroxAPIError) as error:
            func(
                start=START,
                stop=STOP,
                grid=intermittent_grid(),
                assets=[primary_asset()],
                minimum_assets=1,
                grid_point_constraints=[mask],
                step_s=60.0,
                **extra,
            )
        assert error.value.endpoint == endpoint
        if "AzElMask" not in str(error.value):
            raise CrossValidationError(f"{label}: AzElMask rejection did not mention the rejected branch")


def assert_representative_fom_routes_match_trace(
    *,
    label: str,
    grid: coverage.CoverageGrid,
    step_s: float,
    grid_point_sensor: entities.EntitySensor | None = None,
    grid_point_constraints: list[entities.Constraint] | None = None,
) -> dict[str, list[float]]:
    trace = compute_trace(
        grid=grid,
        step_s=step_s,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
    )
    intervals_by_point = trace["SatisfactionIntervalsWithNumberOfAssets"]
    points = trace["Points"]["GridPoints"]
    duration = duration_s()
    expected = {
        "simple": [
            1.0 if total_positive_duration(intervals) > 0.0 else 0.0
            for intervals in intervals_by_point
        ],
        "coverage_time": [
            total_positive_duration(intervals)
            for intervals in intervals_by_point
        ],
        "number_average": [
            sum(interval["Duration"] * interval["NumberOfAssets"] for interval in intervals) / duration
            for intervals in intervals_by_point
        ],
        "response_maximum": [
            max(gap_durations(intervals)) if gap_durations(intervals) else 0.0
            for intervals in intervals_by_point
        ],
        "revisit_average": [
            mean(gap_durations(intervals)) if gap_durations(intervals) else 0.0
            for intervals in intervals_by_point
        ],
    }
    route_cases = [
        ("simple", coverage.simple_coverage.by_grid_point, {}, expected["simple"]),
        (
            "coverage_time",
            coverage.coverage_time.by_grid_point,
            {"compute_type": "TotalTimeAbove"},
            expected["coverage_time"],
        ),
        (
            "number_average",
            coverage.number_of_assets.by_grid_point,
            {"compute_type": "Average"},
            expected["number_average"],
        ),
        (
            "response_maximum",
            coverage.response_time.by_grid_point,
            {"compute_type": "Maximum"},
            expected["response_maximum"],
        ),
        (
            "revisit_average",
            coverage.revisit_time.by_grid_point,
            {"compute_type": "Average"},
            expected["revisit_average"],
        ),
    ]
    for metric_label, func, extra, values in route_cases:
        report = func(
            start=START,
            stop=STOP,
            grid=grid,
            assets=[primary_asset()],
            minimum_assets=1,
            grid_point_sensor=grid_point_sensor,
            grid_point_constraints=grid_point_constraints,
            step_s=step_s,
            **extra,
        )
        assert_fom_values(f"{label}_{metric_label}", report["Datas"], points, values)
    return expected


def run_all_checks() -> int:
    test_fom_grid_point_modifiers_match_compute_interval_derivation()
    test_fom_grid_branches_match_compute_interval_derivation_and_arithmetic_stats()
    test_fom_grid_stats_average_is_arithmetic_not_grid_weighted()
    test_fom_az_el_mask_constraint_rejects_consistently_with_compute_coverage_role()
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
