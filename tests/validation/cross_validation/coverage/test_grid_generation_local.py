#!/usr/bin/env python3
"""Coverage grid generation cross-validation against local grid-cell derivation."""

# Coverage:
#   Branches:
#     - LatLonBounds grid point centers and cell boundaries: verified for divisible and non-divisible bounded grids against local cell subdivision derivation
#     - LatitudeBounds grid point centers and cell boundaries: verified for a symmetric latitude band against local full-longitude cell derivation
#     - Global grid point centers and cell boundaries: verified for divisible, non-divisible, and half-step resolutions against local variable-row derivation
#     - CbLatLonBounds grid tiling bounds: partial (returned cells tile the requested latitude/longitude box in representative cases; exact row/column count rule remains unresolved)
#     - CbLatLonBounds exact count rule: unresolved (direct subdivision, clipped parent-grid, span-only, and weight-option hypotheses fail)
#     - ComputeCoverage ContainCoveragePoints grid echo: verified against GetGridPoints ordering and geometry for LatLonBounds representative grid
#   Fields:
#     - Points.GridPoints[].Position: verified for LatLonBounds, LatitudeBounds, and Global representative cases; verified as cell midpoints for CbLatLonBounds representative cases
#     - Points.GridPoints[].GridCellBoundaryVertices: verified for LatLonBounds, LatitudeBounds, and Global representative cases; verified to tile the requested box for CbLatLonBounds representative cases
#     - Points.GridPoints[].Weight: partial (positive and present for area weighting; equal-weight branch verified to return 1 for all points)
#     - Points.Height: verified to echo supplied height_m for LatLonBounds representative grid
#     - CoverageOutput.Points.GridPoints: verified to match GetGridPoints for the representative LatLonBounds grid when ContainCoveragePoints=True
#   Parameters:
#     - min/max latitude/longitude: verified for representative positive, negative, and non-divisible longitude bounds
#     - resolution_deg: verified for LatLonBounds, LatitudeBounds, and Global representative resolutions; unresolved for CbLatLonBounds
#     - use_cell_surface_area_for_weight: partial (False branch verified as equal weights; area formula not calibrated)
#     - height_m: partial (response echo verified; access/coverage effect not calibrated)
#     - central_body: partial (Earth default observed; non-Earth values not calibrated)
#   Comparison:
#     - External: local derivation of equally spaced cell centers and boundary vertices in radians; cross-endpoint invariant for ComputeCoverage point echo
#     - Constants: no tuned physical constants; positions derive directly from public degree inputs
#     - Tolerances: ANGLE_ABS_RAD=1e-12 for degree-to-radian conversion and JSON float roundoff
#   Findings:
#     - LatLonBounds subdivides each axis into floor(span/resolution)+1 cells in the covered cases
#     - LatitudeBounds uses latitude cells spanning the requested latitude band and longitude cells around the full globe, with the first longitude cell centered at 180 deg across the seam
#     - Global uses round-half-up(180/resolution) latitude intervals, collapses pole rows to one point, and uses round-half-up(360*cos(latitude)/resolution) longitude cells on interior rows
#     - CbLatLonBounds tiles the requested latitude/longitude rectangle exactly in representative cases, but its count rule remains unresolved. Rejected hypotheses: direct LatLonBounds-style subdivision, clipped LatitudeBounds/Global parent grids, span-only ceil/floor rules, and UseCellSurfaceAreaForWeight-driven topology.

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

from astrox import coverage, components
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
    return max(1, math.floor(span_deg / resolution_deg) + 1)


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
        GridCase(
            label="lat_lon_nondivisible_10x25",
            grid=coverage.lat_lon_grid(
                min_latitude_deg=0.0,
                max_latitude_deg=10.0,
                min_longitude_deg=0.0,
                max_longitude_deg=25.0,
                resolution_deg=10.0,
            ),
            min_latitude_deg=0.0,
            max_latitude_deg=10.0,
            min_longitude_deg=0.0,
            max_longitude_deg=25.0,
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


def expected_latitude_points(
    *,
    min_latitude_deg: float,
    max_latitude_deg: float,
    resolution_deg: float,
) -> list[dict[str, object]]:
    lat_span = max_latitude_deg - min_latitude_deg
    lat_count = max(1, math.floor(lat_span / resolution_deg))
    lon_count = max(1, math.ceil(360.0 / resolution_deg))
    lat_step = lat_span / lat_count
    lon_step = 360.0 / lon_count
    points: list[dict[str, object]] = []
    for lat_index in range(lat_count):
        lat0 = min_latitude_deg + lat_index * lat_step
        lat1 = lat0 + lat_step
        center_lat = (lat0 + lat1) / 2.0
        for lon_index in range(lon_count):
            if lon_index == 0:
                center_lon = 180.0
                lon0 = 180.0 - lon_step / 2.0
                lon1 = normalize_longitude_deg(180.0 + lon_step / 2.0)
            else:
                center_lon = -180.0 + lon_index * lon_step
                lon0 = center_lon - lon_step / 2.0
                lon1 = center_lon + lon_step / 2.0
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


def expected_global_points(*, resolution_deg: float) -> list[dict[str, object]]:
    lat_divisions = max(1, round_half_up(180.0 / resolution_deg))
    lat_step = 180.0 / lat_divisions
    points: list[dict[str, object]] = []
    for lat_index in range(lat_divisions + 1):
        center_lat = -90.0 + lat_index * lat_step
        is_south_pole = lat_index == 0
        is_north_pole = lat_index == lat_divisions
        if is_south_pole or is_north_pole:
            if is_south_pole:
                boundary_lat = center_lat + lat_step / 2.0
            else:
                boundary_lat = center_lat - lat_step / 2.0
            points.append(
                {
                    "Position": [math.radians(center_lat), 0.0],
                    "GridCellBoundaryVertices": [
                        [math.radians(boundary_lat), math.radians(-180.0)],
                        [math.radians(boundary_lat), math.radians(-90.0)],
                        [math.radians(boundary_lat), math.radians(0.0)],
                        [math.radians(boundary_lat), math.radians(90.0)],
                    ],
                }
            )
            continue
        lat0 = center_lat - lat_step / 2.0
        lat1 = center_lat + lat_step / 2.0
        lon_count = max(
            1,
            round_half_up(360.0 * math.cos(math.radians(center_lat)) / resolution_deg),
        )
        lon_step = 360.0 / lon_count
        for lon_index in range(lon_count):
            center_lon = -180.0 + lon_index * lon_step
            lon0 = normalize_longitude_deg(center_lon - lon_step / 2.0)
            lon1 = normalize_longitude_deg(center_lon + lon_step / 2.0)
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


def round_half_up(value: float) -> int:
    return math.floor(value + 0.5)


def normalize_longitude_deg(value: float) -> float:
    return ((value + 180.0) % 360.0) - 180.0


def test_lat_lon_grid_points_match_local_cell_derivation() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in lat_lon_cases():
        actual = coverage.grid_points(grid=case.grid)["Points"]["GridPoints"]
        failures.extend(compare_grid_points(case.label, expected_points(case), actual))
    if failures:
        raise CrossValidationError("\n".join(failures))


def test_latitude_grid_points_match_local_full_longitude_derivation() -> None:
    configure_astrox_from_env()
    grid = coverage.latitude_grid(
        min_latitude_deg=-30.0,
        max_latitude_deg=30.0,
        resolution_deg=30.0,
    )
    actual = coverage.grid_points(grid=grid)["Points"]["GridPoints"]
    failures = compare_grid_points(
        "latitude_-30_30_30",
        expected_latitude_points(
            min_latitude_deg=-30.0,
            max_latitude_deg=30.0,
            resolution_deg=30.0,
        ),
        actual,
    )
    if failures:
        raise CrossValidationError("\n".join(failures))


def test_global_grid_points_match_local_variable_row_derivation() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for resolution_deg in (30.0, 40.0, 50.0):
        actual = coverage.grid_points(
            grid=coverage.global_grid(resolution_deg=resolution_deg)
        )["Points"]["GridPoints"]
        failures.extend(
            compare_grid_points(
                f"global_{resolution_deg:g}",
                expected_global_points(resolution_deg=resolution_deg),
                actual,
            )
        )
    if failures:
        raise CrossValidationError("\n".join(failures))


def test_equal_weight_and_height_echo_branches_are_explicit() -> None:
    configure_astrox_from_env()
    equal_weight_grid = coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
        use_cell_surface_area_for_weight=False,
    )
    equal_weight_points = coverage.grid_points(grid=equal_weight_grid)["Points"]
    weights = [point["Weight"] for point in equal_weight_points["GridPoints"]]
    if weights != [1] * len(weights):
        raise CrossValidationError(f"equal weight branch returned weights {weights!r}")

    height_grid = coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
        height_m=100.0,
    )
    height_points = coverage.grid_points(grid=height_grid)["Points"]
    if height_points["Height"] != 100:
        raise CrossValidationError(
            f"height_m echo expected 100, got {height_points['Height']!r}"
        )


def test_cb_lat_lon_cells_tile_requested_bounds() -> None:
    configure_astrox_from_env()
    cases = (
        ("cb_equator", 0.0, 10.0, 0.0, 20.0, 5.0),
        ("cb_mid_latitude", 20.0, 30.0, -120.0, -100.0, 5.0),
        ("cb_cross_equator", -10.0, 10.0, 0.0, 20.0, 5.0),
        ("cb_high_latitude", 40.0, 45.0, 0.0, 10.0, 5.0),
    )
    failures: list[str] = []
    for label, min_lat, max_lat, min_lon, max_lon, resolution in cases:
        grid = coverage.cb_lat_lon_grid(
            min_latitude_deg=min_lat,
            max_latitude_deg=max_lat,
            min_longitude_deg=min_lon,
            max_longitude_deg=max_lon,
            resolution_deg=resolution,
        )
        actual = coverage.grid_points(grid=grid)["Points"]["GridPoints"]
        failures.extend(
            assert_grid_tiles_requested_box(
                label,
                actual,
                min_latitude_deg=min_lat,
                max_latitude_deg=max_lat,
                min_longitude_deg=min_lon,
                max_longitude_deg=max_lon,
            )
        )
    if failures:
        raise CrossValidationError("\n".join(failures))


@pytest.mark.xfail(
    strict=True,
    reason=(
        "CbLatLonBounds exact count rule is unresolved after rejected direct "
        "subdivision, clipped parent-grid, span-only, and weight-option hypotheses."
    ),
)
def test_cb_lat_lon_direct_subdivision_hypothesis_remains_unresolved() -> None:
    # Investigation notes:
    # - Direct subdivision fails: 0..5 lat, 0..10 lon, res=5 returns one latitude
    #   row and two longitude columns, unlike LatLonBounds' two rows by three columns.
    # - Clipped parent grids fail: 0..10 lat, 0..20 lon, res=5 returns eight
    #   cells, while the matching LatitudeBounds slice has six and Global slice has
    #   three cells with different centers/boundaries.
    # - Span-only rules fail: 20..24.99 lat has one row, 20..25 lat has two rows,
    #   but 25..30 lat has one row for the same resolution and longitude span.
    # - UseCellSurfaceAreaForWeight changes weights only, not topology.
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
    asset = components.entity(
        name="Relay",
        position=components.sgp4_position(tle_lines=TLE_LINES),
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


def assert_grid_tiles_requested_box(
    label: str,
    actual: list[dict[str, object]],
    *,
    min_latitude_deg: float,
    max_latitude_deg: float,
    min_longitude_deg: float,
    max_longitude_deg: float,
) -> list[str]:
    failures: list[str] = []
    cells = [cell_bounds_degrees(point) for point in actual]
    lat_bands: dict[tuple[float, float], list[tuple[float, float]]] = {}
    for index, (lat0, lat1, lon0, lon1) in enumerate(cells):
        if lat0 < min_latitude_deg - 1.0e-10 or lat1 > max_latitude_deg + 1.0e-10:
            failures.append(
                f"{label}: point {index} latitude bounds {(lat0, lat1)!r} exceed requested bounds"
            )
        if lon0 < min_longitude_deg - 1.0e-10 or lon1 > max_longitude_deg + 1.0e-10:
            failures.append(
                f"{label}: point {index} longitude bounds {(lon0, lon1)!r} exceed requested bounds"
            )
        center_lat, center_lon = position_degrees(actual[index])
        midpoint_lat = (lat0 + lat1) / 2.0
        midpoint_lon = (lon0 + lon1) / 2.0
        if abs(center_lat - midpoint_lat) > 1.0e-10:
            failures.append(
                f"{label}: point {index} latitude center {center_lat} "
                f"is not cell midpoint {midpoint_lat}"
            )
        if abs(center_lon - midpoint_lon) > 1.0e-10:
            failures.append(
                f"{label}: point {index} longitude center {center_lon} "
                f"is not cell midpoint {midpoint_lon}"
            )
        lat_bands.setdefault((lat0, lat1), []).append((lon0, lon1))
    failures.extend(
        assert_contiguous_intervals(
            label,
            "latitude",
            sorted(lat_bands),
            min_latitude_deg,
            max_latitude_deg,
        )
    )
    for lat_band, lon_intervals in lat_bands.items():
        failures.extend(
            assert_contiguous_intervals(
                f"{label} lat_band={lat_band}",
                "longitude",
                sorted(lon_intervals),
                min_longitude_deg,
                max_longitude_deg,
            )
        )
    return failures


def cell_bounds_degrees(point: dict[str, object]) -> tuple[float, float, float, float]:
    vertices = point["GridCellBoundaryVertices"]
    if not isinstance(vertices, list):
        raise CrossValidationError(f"expected boundary vertex list, got {vertices!r}")
    flat = [[math.degrees(value) for value in vertex] for vertex in vertices]
    latitudes = [vertex[0] for vertex in flat]
    longitudes = [vertex[1] for vertex in flat]
    return min(latitudes), max(latitudes), min(longitudes), max(longitudes)


def position_degrees(point: dict[str, object]) -> tuple[float, float]:
    position = point["Position"]
    if not isinstance(position, list) or len(position) != 2:
        raise CrossValidationError(f"expected two-value position, got {position!r}")
    return math.degrees(position[0]), math.degrees(position[1])


def assert_contiguous_intervals(
    label: str,
    axis: str,
    intervals: list[tuple[float, float]],
    expected_start: float,
    expected_stop: float,
) -> list[str]:
    failures: list[str] = []
    if not intervals:
        return [f"{label}: no {axis} intervals"]
    cursor = expected_start
    for index, (left, right) in enumerate(intervals):
        if abs(left - cursor) > 1.0e-10:
            failures.append(
                f"{label}: {axis} interval {index} starts at {left}, expected {cursor}"
            )
        if right <= left:
            failures.append(
                f"{label}: {axis} interval {index} has non-positive span {(left, right)!r}"
            )
        cursor = right
    if abs(cursor - expected_stop) > 1.0e-10:
        failures.append(
            f"{label}: {axis} intervals end at {cursor}, expected {expected_stop}"
        )
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
        latitude_actual = coverage.grid_points(
            grid=coverage.latitude_grid(
                min_latitude_deg=-30.0,
                max_latitude_deg=30.0,
                resolution_deg=30.0,
            )
        )["Points"]["GridPoints"]
        latitude_failures = compare_grid_points(
            "latitude_-30_30_30",
            expected_latitude_points(
                min_latitude_deg=-30.0,
                max_latitude_deg=30.0,
                resolution_deg=30.0,
            ),
            latitude_actual,
        )
        if latitude_failures:
            raise CrossValidationError("\n".join(latitude_failures))
        total += 1
        equal_weight_points = coverage.grid_points(
            grid=coverage.lat_lon_grid(
                min_latitude_deg=20.0,
                max_latitude_deg=25.0,
                min_longitude_deg=-120.0,
                max_longitude_deg=-110.0,
                resolution_deg=5.0,
                use_cell_surface_area_for_weight=False,
            )
        )["Points"]["GridPoints"]
        weights = [point["Weight"] for point in equal_weight_points]
        if weights != [1] * len(weights):
            raise CrossValidationError(f"equal weight branch returned weights {weights!r}")
        total += 1
        grid = coverage.lat_lon_grid(
            min_latitude_deg=20.0,
            max_latitude_deg=25.0,
            min_longitude_deg=-120.0,
            max_longitude_deg=-110.0,
            resolution_deg=5.0,
        )
        asset = components.entity(
            name="Relay",
            position=components.sgp4_position(tle_lines=TLE_LINES),
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
