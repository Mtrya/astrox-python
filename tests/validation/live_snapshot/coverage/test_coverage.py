#!/usr/bin/env python3
"""Live snapshots for coverage core helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, entities, exceptions
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("coverage.snap.json")
# GitHub Actions has observed about 2 ms of live numeric drift from the same
# checked-in inputs while local runs match exactly. Keep this as a narrow live
# response-shape guard; cross-validation owns semantic precision.
COVERAGE_SNAPSHOT_ABS_TOL = 2.0e-3
START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:30:00.000Z"
TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def small_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )


def no_coverage_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=80.0,
        max_latitude_deg=85.0,
        min_longitude_deg=0.0,
        max_longitude_deg=10.0,
        resolution_deg=5.0,
    )


def cb_grid() -> coverage.CbLatLonGrid:
    return coverage.cb_lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )


def relay() -> entities.Entity:
    return entities.entity(
        name="Relay",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
    )


def ground_asset() -> entities.Entity:
    return entities.entity(
        name="GroundAsset",
        position=entities.site_position(
            latitude_deg=0.0,
            longitude_deg=0.0,
            height_m=0.0,
        ),
    )


def grid_points_lat_lon() -> dict[str, Any]:
    return coverage.grid_points(grid=small_grid())


def grid_points_cb_lat_lon() -> dict[str, Any]:
    return coverage.grid_points(grid=cb_grid())


def compute_basic() -> dict[str, Any]:
    return coverage.compute(
        start=START,
        stop=STOP,
        grid=small_grid(),
        assets=[relay()],
        minimum_assets=1,
        include_coverage_points=True,
        include_asset_access_results=True,
        step_s=300.0,
    )


def compute_with_grid_point_constraints() -> dict[str, Any]:
    return coverage.compute(
        start=START,
        stop=STOP,
        grid=small_grid(),
        assets=[relay()],
        minimum_assets=1,
        grid_point_constraints=[
            entities.elevation_constraint(minimum_deg=0.0),
            entities.range_constraint(maximum_km=5000.0, maximum_enabled=True),
        ],
        include_coverage_points=True,
        include_asset_access_results=True,
        step_s=300.0,
    )


def percent_coverage() -> dict[str, Any]:
    return coverage.percent_coverage(
        start=START,
        stop=STOP,
        grid=small_grid(),
        assets=[relay()],
        minimum_assets=1,
        step_s=300.0,
    )


def coverage_by_asset() -> dict[str, Any]:
    return coverage.coverage_by_asset(
        start=START,
        stop=STOP,
        grid=small_grid(),
        assets=[relay()],
        minimum_assets=1,
        step_s=300.0,
    )


def fom_route(
    func: Callable[..., dict[str, Any]],
    *,
    compute_type: str | None = None,
    time: str | None = None,
    expect_http_error: bool = False,
    grid: coverage.CoverageGrid | None = None,
    step_s: float = 300.0,
    http_error_marker: str | None = None,
) -> dict[str, Any]:
    """Call one FOM route, optionally freezing a current HTTP 500 response.

    The ``expect_http_error`` path is a live drift guard. If ASTROX starts
    returning a successful payload, this helper returns that payload and the
    snapshot comparison fails. If ASTROX changes to a non-HTTP API validation
    error, the exception bubbles and the live snapshot test fails immediately.
    """
    kwargs: dict[str, Any] = {
        "start": START,
        "stop": STOP,
        "grid": grid or small_grid(),
        "assets": [relay()],
        "minimum_assets": 1,
        "step_s": step_s,
    }
    if compute_type is not None:
        kwargs["compute_type"] = compute_type
    if time is not None:
        kwargs["time"] = time
    if not expect_http_error:
        return func(**kwargs)
    try:
        result = func(**kwargs)
    except exceptions.AstroxHTTPError as exc:
        return {
            "expected_current_behavior": http_error_marker or "live_http_500_drift_guard",
            "error": type(exc).__name__,
            "endpoint": exc.endpoint,
            "status_code": exc.status_code,
            "message": exc.message,
        }
    return result


FOM_TIME = "2024-01-01T00:10:00.000Z"
FOM_NO_NEXT_ACCESS_TIME = "2024-01-01T00:29:00.000Z"


CASES = [
    LiveSnapshotCase(
        id="grid_points_lat_lon",
        description="Grid-point generation for the LatLonBounds grid branch.",
        run=grid_points_lat_lon,
    ),
    LiveSnapshotCase(
        id="grid_points_cb_lat_lon",
        description="Grid-point generation for the CbLatLonBounds grid branch.",
        run=grid_points_cb_lat_lon,
    ),
    LiveSnapshotCase(
        id="compute_basic",
        description="Coverage compute with one SGP4 asset and output inclusion flags.",
        run=compute_basic,
    ),
    LiveSnapshotCase(
        id="compute_with_grid_point_constraints",
        description="Coverage compute with elevation and range grid-point constraints.",
        run=compute_with_grid_point_constraints,
    ),
    LiveSnapshotCase(
        id="percent_coverage",
        description="Percent-coverage report for one SGP4 asset.",
        run=percent_coverage,
    ),
    LiveSnapshotCase(
        id="coverage_by_asset",
        description="Coverage-by-asset report for one SGP4 asset.",
        run=coverage_by_asset,
    ),
    LiveSnapshotCase(
        id="fom_simple_coverage_by_grid_point",
        description="FOM simple coverage values by grid point.",
        run=lambda: fom_route(coverage.simple_coverage.by_grid_point),
    ),
    LiveSnapshotCase(
        id="fom_simple_coverage_by_grid_point_at_time",
        description="FOM simple coverage values by grid point at one time.",
        run=lambda: fom_route(
            coverage.simple_coverage.by_grid_point_at_time,
            time=FOM_TIME,
        ),
    ),
    LiveSnapshotCase(
        id="fom_simple_coverage_grid_stats",
        description="FOM simple coverage grid statistics.",
        run=lambda: fom_route(coverage.simple_coverage.grid_stats),
    ),
    LiveSnapshotCase(
        id="fom_simple_coverage_grid_stats_over_time",
        description="FOM simple coverage grid statistics over time.",
        run=lambda: fom_route(coverage.simple_coverage.grid_stats_over_time),
    ),
    LiveSnapshotCase(
        id="fom_coverage_time_by_grid_point",
        description="FOM coverage time values by grid point.",
        run=lambda: fom_route(
            coverage.coverage_time.by_grid_point,
            compute_type="TotalTimeAbove",
        ),
    ),
    LiveSnapshotCase(
        id="fom_coverage_time_grid_stats",
        description="FOM coverage time grid statistics.",
        run=lambda: fom_route(
            coverage.coverage_time.grid_stats,
            compute_type="TotalTimeAbove",
        ),
    ),
    LiveSnapshotCase(
        id="fom_number_of_assets_by_grid_point",
        description="FOM number of assets values by grid point.",
        run=lambda: fom_route(
            coverage.number_of_assets.by_grid_point,
            compute_type="Average",
        ),
    ),
    LiveSnapshotCase(
        id="fom_number_of_assets_by_grid_point_at_time",
        description="FOM number of assets values by grid point at one time.",
        run=lambda: fom_route(
            coverage.number_of_assets.by_grid_point_at_time,
            time=FOM_TIME,
        ),
    ),
    LiveSnapshotCase(
        id="fom_number_of_assets_grid_stats",
        description="FOM number of assets grid statistics.",
        run=lambda: fom_route(
            coverage.number_of_assets.grid_stats,
            compute_type="Average",
        ),
    ),
    LiveSnapshotCase(
        id="fom_number_of_assets_grid_stats_over_time",
        description="FOM number of assets grid statistics over time.",
        run=lambda: fom_route(coverage.number_of_assets.grid_stats_over_time),
    ),
    LiveSnapshotCase(
        id="fom_response_time_by_grid_point",
        description="FOM response time values by grid point.",
        run=lambda: fom_route(
            coverage.response_time.by_grid_point,
            compute_type="Maximum",
        ),
    ),
    LiveSnapshotCase(
        id="fom_response_time_by_grid_point_at_time",
        description=(
            "Drift guard: FOM response-time at-time currently returns ASTROX "
            "HTTP 500 when the representative intermittent case includes a "
            "grid point with no later access inside the analysis window."
        ),
        run=lambda: fom_route(
            coverage.response_time.by_grid_point_at_time,
            time=FOM_TIME,
            expect_http_error=True,
            http_error_marker="response_time_at_time_no_next_access_http_500",
        ),
    ),
    LiveSnapshotCase(
        id="fom_response_time_by_grid_point_at_time_all_no_next_access_http_500",
        description=(
            "Drift guard: FOM response-time at-time currently returns ASTROX "
            "HTTP 500 late in the representative window, when all points are "
            "uncovered and have no later access. If ASTROX returns a value or "
            "a clearer validation error, this snapshot must fail so we can "
            "recalibrate the SDK docs and cross-validation."
        ),
        run=lambda: fom_route(
            coverage.response_time.by_grid_point_at_time,
            time=FOM_NO_NEXT_ACCESS_TIME,
            expect_http_error=True,
            step_s=60.0,
            http_error_marker="response_time_at_time_all_no_next_access_http_500",
        ),
    ),
    LiveSnapshotCase(
        id="fom_response_time_by_grid_point_at_time_no_coverage_http_500",
        description=(
            "Drift guard: FOM response-time at-time currently returns ASTROX "
            "HTTP 500 for a never-covered grid. A future success or clearer "
            "server validation error should force this snapshot to change."
        ),
        run=lambda: fom_route(
            coverage.response_time.by_grid_point_at_time,
            time=FOM_TIME,
            expect_http_error=True,
            grid=no_coverage_grid(),
            step_s=60.0,
            http_error_marker="response_time_at_time_no_coverage_http_500",
        ),
    ),
    LiveSnapshotCase(
        id="fom_response_time_grid_stats",
        description="FOM response time grid statistics.",
        run=lambda: fom_route(
            coverage.response_time.grid_stats,
            compute_type="Maximum",
        ),
    ),
    LiveSnapshotCase(
        id="fom_response_time_grid_stats_over_time",
        description=(
            "Drift guard: FOM response-time over-time currently returns ASTROX "
            "HTTP 500 for the representative intermittent case because the "
            "sample series reaches a no-next-access condition."
        ),
        run=lambda: fom_route(
            coverage.response_time.grid_stats_over_time,
            expect_http_error=True,
            http_error_marker="response_time_over_time_no_next_access_http_500",
        ),
    ),
    LiveSnapshotCase(
        id="fom_response_time_grid_stats_over_time_no_coverage_http_500",
        description=(
            "Drift guard: FOM response-time over-time currently returns ASTROX "
            "HTTP 500 for a never-covered grid. If the server starts returning "
            "full-window durations, empty data, or a clearer validation error, "
            "this snapshot should fail and be recalibrated."
        ),
        run=lambda: fom_route(
            coverage.response_time.grid_stats_over_time,
            expect_http_error=True,
            grid=no_coverage_grid(),
            step_s=60.0,
            http_error_marker="response_time_over_time_no_coverage_http_500",
        ),
    ),
    LiveSnapshotCase(
        id="fom_revisit_time_by_grid_point",
        description="FOM revisit time values by grid point.",
        run=lambda: fom_route(
            coverage.revisit_time.by_grid_point,
            compute_type="Average",
        ),
    ),
    LiveSnapshotCase(
        id="fom_revisit_time_by_grid_point_at_time",
        description="FOM revisit time values by grid point at one time.",
        run=lambda: fom_route(
            coverage.revisit_time.by_grid_point_at_time,
            time=FOM_TIME,
        ),
    ),
    LiveSnapshotCase(
        id="fom_revisit_time_grid_stats",
        description="FOM revisit time grid statistics.",
        run=lambda: fom_route(
            coverage.revisit_time.grid_stats,
            compute_type="Average",
        ),
    ),
    LiveSnapshotCase(
        id="fom_revisit_time_grid_stats_over_time",
        description="FOM revisit time grid statistics over time.",
        run=lambda: fom_route(coverage.revisit_time.grid_stats_over_time),
    ),
]


def test_coverage_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(
        cases=CASES,
        snapshot_path=SNAPSHOT_PATH,
        abs_tol=COVERAGE_SNAPSHOT_ABS_TOL,
        datetime_abs_tol_s=COVERAGE_SNAPSHOT_ABS_TOL,
    )


def test_site_entity_as_coverage_asset_currently_returns_worker_error() -> None:
    configure_astrox_from_env()
    # This is a live drift guard, not semantic proof. Coverage assets appear to be
    # satellite-like resources in practice, but the schema accepts broad Entity
    # objects. If ASTROX adds a clear validation error for site assets, this test
    # should fail so the stale worker-error expectation can be removed.
    with pytest.raises(exceptions.AstroxAPIError, match="Index was out of range"):
        coverage.compute(
            start=START,
            stop="2024-01-01T00:10:00.000Z",
            grid=coverage.lat_lon_grid(
                min_latitude_deg=-0.5,
                max_latitude_deg=0.5,
                min_longitude_deg=-0.5,
                max_longitude_deg=0.5,
                resolution_deg=10.0,
            ),
            assets=[ground_asset()],
            minimum_assets=1,
            include_asset_access_results=True,
            include_coverage_points=True,
            step_s=60.0,
        )


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
