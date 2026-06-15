#!/usr/bin/env python3
"""Coverage grid generation cross-validation against local grid-cell derivation."""

# Coverage:
#   Branches:
#     - LatLonBounds grid point centers and cell boundaries: verified for bounded 5x10 deg and 10x20 deg grids against local cell subdivision derivation
#     - CbLatLonBounds grid point centers and cell boundaries: unresolved (direct subdivision hypothesis fails; targeted probes show latitude-dependent clipped-grid behavior)
#     - ComputeCoverage ContainCoveragePoints grid echo: verified against GetGridPoints ordering and geometry for LatLonBounds representative grid
#     - Global and LatitudeBounds grids: partial (callable in runtime, not yet calibrated here)
#   Fields:
#     - Points.GridPoints[].Position: verified for LatLonBounds representative cases; unresolved for CbLatLonBounds
#     - Points.GridPoints[].GridCellBoundaryVertices: verified for LatLonBounds representative cases; unresolved for CbLatLonBounds
#     - Points.GridPoints[].Weight: partial (positive and present, exact area/weighting semantics not calibrated in this script)
#     - CoverageOutput.Points.GridPoints: verified to match GetGridPoints for the representative LatLonBounds grid when ContainCoveragePoints=True
#   Parameters:
#     - min/max latitude/longitude: verified for representative positive and negative longitude bounds
#     - resolution_deg: verified for LatLonBounds representative resolutions; unresolved for CbLatLonBounds
#     - use_cell_surface_area_for_weight: partial (not calibrated here)
#     - height_m and central_body: partial (not calibrated here)
#   Comparison:
#     - External: local derivation of equally spaced cell centers and boundary vertices in radians
#     - Constants: no tuned physical constants; positions derive directly from public degree inputs
#     - Tolerances: ANGLE_ABS_RAD=1e-12 for degree-to-radian conversion and JSON float roundoff
#   Findings:
#     - LatLonBounds subdivides each axis into ceil(span/resolution)+1 cells in the covered cases
#     - CbLatLonBounds does not follow direct box subdivision in all covered cases. For 0-5 deg latitude and 0-10 deg longitude at 5 deg resolution it returns one latitude row and two longitude columns; for 20-25 deg latitude with the same longitude/resolution it returns two latitude rows and two longitude columns.

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, entities
from tests.validation._support import LiveConfigError, configure_astrox_from_env


ANGLE_ABS_RAD = 1.0e-12
START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:30:00.000Z"
TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


class CrossValidationError(Exception):
    """Raised when live ASTROX coverage behavior disagrees with the oracle."""


@dataclass(frozen=True, kw_only=True)
class GridCase:
    label: str
    grid: coverage.LatLonGrid | coverage.CbLatLonGrid
    min_latitude_deg: float
    max_latitude_deg: float
    min_longitude_deg: float
    max_longitude_deg: float
    resolution_deg: float
    cell_count: Callable[[float, float], int]


def lat_lon_cell_count(span_deg: float, resolution_deg: float) -> int:
    return max(1, math.ceil(span_deg / resolution_deg) + 1)


def cb_lat_lon_cell_count(span_deg: float, resolution_deg: float) -> int:
    return max(1, math.ceil(span_deg / resolution_deg))


def lat_lon_cases() -> tuple[GridCase, ...]:
    return (
        GridCase(
            label="lat_lon_5x10",
            grid=coverage.lat_lon_grid(
                min_latitude_deg=20.0,
                max_latitude_deg=25.0,
                min_longitude_deg=-120.0,
                max_longitude_deg=-110.0,
                resolution_deg=5.0,
            ),
            min_latitude_deg=20.0,
            max_latitude_deg=25.0,
            min_longitude_deg=-120.0,
            max_longitude_deg=-110.0,
            resolution_deg=5.0,
            cell_count=lat_lon_cell_count,
        ),
        GridCase(
            label="lat_lon_10x20",
            grid=coverage.lat_lon_grid(
                min_latitude_deg=0.0,
                max_latitude_deg=10.0,
                min_longitude_deg=0.0,
                max_longitude_deg=20.0,
                resolution_deg=10.0,
            ),
            min_latitude_deg=0.0,
            max_latitude_deg=10.0,
            min_longitude_deg=0.0,
            max_longitude_deg=20.0,
            resolution_deg=10.0,
            cell_count=lat_lon_cell_count,
        ),
    )


def cb_lat_lon_cases() -> tuple[GridCase, ...]:
    return (
        GridCase(
            label="cb_lat_lon_5x10",
            grid=coverage.cb_lat_lon_grid(
                min_latitude_deg=20.0,
                max_latitude_deg=25.0,
                min_longitude_deg=-120.0,
                max_longitude_deg=-110.0,
                resolution_deg=5.0,
            ),
            min_latitude_deg=20.0,
            max_latitude_deg=25.0,
            min_longitude_deg=-120.0,
            max_longitude_deg=-110.0,
            resolution_deg=5.0,
            cell_count=cb_lat_lon_cell_count,
        ),
        GridCase(
            label="cb_lat_lon_10x20",
            grid=coverage.cb_lat_lon_grid(
                min_latitude_deg=0.0,
                max_latitude_deg=10.0,
                min_longitude_deg=0.0,
                max_longitude_deg=20.0,
                resolution_deg=10.0,
            ),
            min_latitude_deg=0.0,
            max_latitude_deg=10.0,
            min_longitude_deg=0.0,
            max_longitude_deg=20.0,
            resolution_deg=10.0,
            cell_count=cb_lat_lon_cell_count,
        ),
    )


def expected_points(case: GridCase) -> list[dict[str, object]]:
    lat_span = case.max_latitude_deg - case.min_latitude_deg
    lon_span = case.max_longitude_deg - case.min_longitude_deg
    lat_count = case.cell_count(lat_span, case.resolution_deg)
    lon_count = case.cell_count(lon_span, case.resolution_deg)
    lat_step = lat_span / lat_count
    lon_step = lon_span / lon_count
    points: list[dict[str, object]] = []
    for lat_index in range(lat_count):
        lat0 = case.min_latitude_deg + lat_index * lat_step
        lat1 = lat0 + lat_step
        center_lat = (lat0 + lat1) / 2.0
        for lon_index in range(lon_count):
            lon0 = case.min_longitude_deg + lon_index * lon_step
            lon1 = lon0 + lon_step
            center_lon = (lon0 + lon1) / 2.0
            points.append(
                {
                    "Position": [math.radians(center_lat), math.radians(center_lon)],
                    "GridCellBoundaryVertices": [
                        [math.radians(lat1), math.radians(lon0)],
                        [math.radians(lat1), math.radians(lon1)],
                        [math.radians(lat0), math.radians(lon1)],
                        [math.radians(lat0), math.radians(lon0)],
                    ],
                }
            )
    return points


def test_lat_lon_grid_points_match_local_cell_derivation() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in lat_lon_cases():
        actual = coverage.grid_points(grid=case.grid)["Points"]["GridPoints"]
        failures.extend(compare_grid_points(case.label, expected_points(case), actual))
    if failures:
        raise CrossValidationError("\n".join(failures))


@pytest.mark.xfail(
    strict=True,
    reason=(
        "CbLatLonBounds is not explained by direct box subdivision; targeted probes "
        "show latitude-dependent clipped-grid behavior that needs a separate oracle."
    ),
)
def test_cb_lat_lon_direct_subdivision_hypothesis_remains_unresolved() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in cb_lat_lon_cases():
        actual = coverage.grid_points(grid=case.grid)["Points"]["GridPoints"]
        failures.extend(compare_grid_points(case.label, expected_points(case), actual))
    if failures:
        raise CrossValidationError("\n".join(failures))


def test_compute_coverage_points_match_get_grid_points_ordering() -> None:
    configure_astrox_from_env()
    grid = coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )
    asset = entities.entity(
        name="Relay",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
    )
    expected = coverage.grid_points(grid=grid)["Points"]["GridPoints"]
    result = coverage.compute(
        start=START,
        stop=STOP,
        grid=grid,
        assets=[asset],
        minimum_assets=1,
        include_coverage_points=True,
        step_s=300.0,
    )
    actual = result["Points"]["GridPoints"]
    failures = compare_grid_points("compute_points_echo", expected, actual)
    if len(result["SatisfactionIntervalsWithNumberOfAssets"]) != len(expected):
        failures.append(
            "compute_points_echo: "
            "SatisfactionIntervalsWithNumberOfAssets length does not match grid point count"
        )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_grid_points(
    label: str,
    expected: list[dict[str, object]],
    actual: list[dict[str, object]],
) -> list[str]:
    failures: list[str] = []
    if len(actual) != len(expected):
        failures.append(f"{label}: expected {len(expected)} grid points, got {len(actual)}")
        return failures
    for index, (expected_point, actual_point) in enumerate(zip(expected, actual, strict=True)):
        failures.extend(
            compare_nested_float_sequence(
                label,
                index,
                "Position",
                expected_point["Position"],
                actual_point["Position"],
            )
        )
        failures.extend(
            compare_nested_float_sequence(
                label,
                index,
                "GridCellBoundaryVertices",
                expected_point["GridCellBoundaryVertices"],
                actual_point["GridCellBoundaryVertices"],
            )
        )
        weight = actual_point.get("Weight")
        if not isinstance(weight, int | float) or weight <= 0.0:
            failures.append(f"{label}: point {index} has non-positive Weight {weight!r}")
    return failures


def compare_nested_float_sequence(
    label: str,
    index: int,
    field: str,
    expected: object,
    actual: object,
) -> list[str]:
    expected_flat = flatten_numbers(expected)
    actual_flat = flatten_numbers(actual)
    failures: list[str] = []
    if len(actual_flat) != len(expected_flat):
        return [
            f"{label}: point {index} field {field} expected {len(expected_flat)} values, got {len(actual_flat)}"
        ]
    for value_index, (expected_value, actual_value) in enumerate(
        zip(expected_flat, actual_flat, strict=True)
    ):
        error = abs(expected_value - actual_value)
        if error > ANGLE_ABS_RAD:
            failures.append(
                f"{label}: point {index} field {field}[{value_index}] "
                f"expected {expected_value:.15g}, got {actual_value:.15g}, error {error:.3g}"
            )
    return failures


def flatten_numbers(value: object) -> list[float]:
    if isinstance(value, int | float):
        return [float(value)]
    if isinstance(value, list):
        flattened: list[float] = []
        for item in value:
            flattened.extend(flatten_numbers(item))
        return flattened
    raise CrossValidationError(f"expected numeric list, got {value!r}")


def main() -> int:
    try:
        configure_astrox_from_env()
        total = 0
        for case in lat_lon_cases():
            actual = coverage.grid_points(grid=case.grid)["Points"]["GridPoints"]
            failures = compare_grid_points(case.label, expected_points(case), actual)
            if failures:
                raise CrossValidationError("\n".join(failures))
            total += 1
        grid = coverage.lat_lon_grid(
            min_latitude_deg=20.0,
            max_latitude_deg=25.0,
            min_longitude_deg=-120.0,
            max_longitude_deg=-110.0,
            resolution_deg=5.0,
        )
        asset = entities.entity(
            name="Relay",
            position=entities.sgp4_position(tle_lines=TLE_LINES),
        )
        expected = coverage.grid_points(grid=grid)["Points"]["GridPoints"]
        result = coverage.compute(
            start=START,
            stop=STOP,
            grid=grid,
            assets=[asset],
            minimum_assets=1,
            include_coverage_points=True,
            step_s=300.0,
        )
        failures = compare_grid_points(
            "compute_points_echo",
            expected,
            result["Points"]["GridPoints"],
        )
        if failures:
            raise CrossValidationError("\n".join(failures))
        total += 1
        print(f"CROSS_VALIDATION_CHECKED={total}")
        print("CROSS_VALIDATION_FAILED=0")
        return 0
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
