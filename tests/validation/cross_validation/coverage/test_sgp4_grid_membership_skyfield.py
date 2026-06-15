#!/usr/bin/env python3
"""Coverage SGP4-to-grid membership cross-validation against Skyfield/WGS84."""

# Coverage:
#   Branches:
#     - ComputeCoverage one SGP4 asset over a LatLonBounds grid: verified against an independent Skyfield SGP4 plus WGS84 segment-obstruction oracle
#   Fields:
#     - AssetAccessResults[point][asset][]: verified as per-grid-point, per-asset line-of-sight intervals for the covered SGP4/LatLonBounds case
#     - Points.GridPoints[].Position: used as the live ASTROX grid-point coordinates; grid geometry generation itself is calibrated in test_grid_generation_local.py
#   Parameters:
#     - include_asset_access_results: verified to expose intervals that match independently derived per-point membership
#     - minimum_assets=1: used only to produce the coverage result; resource-count composition is calibrated in test_resource_reports_invariants.py
#     - step_s=60: verified not to limit interval boundaries to the output cadence in this case
#   Comparison:
#     - External: Skyfield EarthSatellite state from the same TLE, Skyfield WGS84 grid-point position, and WGS84 ellipsoid segment-obstruction visibility
#     - Constants: WGS84 ellipsoid constants from the shared access geometry oracle
#     - Tolerances: INTERVAL_ABS_S=0.25 s, inherited from calibrated access SGP4 interval comparisons; observed residuals are millisecond-scale in the covered case
#   Findings:
#     - For the representative SGP4/LatLonBounds case, coverage asset intervals match geometric satellite-to-grid line of sight, not a coarse step-sampled cadence.

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, entities
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import (
    CrossValidationError,
    INTERVAL_ABS_S,
)
from tests.validation.cross_validation.access._geometry import (
    Interval,
    compare_intervals,
    sgp4_site_visibility_intervals,
    skyfield_satellite,
    skyfield_site,
)


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:30:00.000Z"
TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def sample_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )


def sgp4_asset() -> entities.Entity:
    return entities.entity(
        name="RelayA",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
    )


def test_sgp4_asset_access_results_match_skyfield_wgs84_visibility() -> None:
    configure_astrox_from_env()
    assert_sgp4_asset_access_results_match_skyfield_wgs84_visibility()


def assert_sgp4_asset_access_results_match_skyfield_wgs84_visibility() -> None:
    grid = sample_grid()
    result = coverage.compute(
        start=START,
        stop=STOP,
        grid=grid,
        assets=[sgp4_asset()],
        minimum_assets=1,
        include_asset_access_results=True,
        step_s=60.0,
    )
    points = coverage.grid_points(grid=grid)["Points"]["GridPoints"]
    asset_results = result["AssetAccessResults"]
    if len(asset_results) != len(points):
        raise CrossValidationError(
            f"expected {len(points)} point access entries, got {len(asset_results)}"
        )
    satellite = skyfield_satellite(TLE_LINES, "RelayA")
    for point_index, (point, point_assets) in enumerate(
        zip(points, asset_results, strict=True)
    ):
        if len(point_assets) != 1:
            raise CrossValidationError(
                f"point {point_index}: expected one asset interval list, got {len(point_assets)}"
            )
        latitude_deg = math.degrees(point["Position"][0])
        longitude_deg = math.degrees(point["Position"][1])
        site = skyfield_site(latitude_deg, longitude_deg, 0.0)
        expected = sgp4_site_visibility_intervals(
            start=START,
            stop=STOP,
            satellite=satellite,
            site_position=site,
        )
        actual = intervals_from_asset_access(point_assets[0])
        compare_intervals(expected, actual, tolerance_s=INTERVAL_ABS_S)


def intervals_from_asset_access(values: list[dict[str, Any]]) -> list[Interval]:
    intervals: list[Interval] = []
    for interval in values:
        if interval["NumberOfAssets"] != 1:
            raise CrossValidationError(
                f"expected per-asset interval NumberOfAssets=1, got {interval['NumberOfAssets']}"
            )
        intervals.append(
            Interval(
                start_s=seconds_since_start(interval["Start"]),
                stop_s=seconds_since_start(interval["Stop"]),
            )
        )
    return intervals


def seconds_since_start(value: str) -> float:
    from tests.validation.cross_validation.access._geometry import seconds_since

    return seconds_since(value, START)


def run_all_checks() -> int:
    assert_sgp4_asset_access_results_match_skyfield_wgs84_visibility()
    return 1


def main() -> int:
    try:
        configure_astrox_from_env()
        checked = run_all_checks()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}")
        return 1
    print(f"CROSS_VALIDATION_CHECKED={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
