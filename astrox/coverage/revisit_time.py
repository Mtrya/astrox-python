"""Revisit-time FOM routes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from astrox import components

from ._core import CoverageGrid
from ._fom import (
    post_coverage_input,
    post_time_value_by_grid_point_input,
    post_value_by_grid_point_input,
)

__all__ = [
    "by_grid_point",
    "by_grid_point_at_time",
    "grid_stats",
    "grid_stats_over_time",
]


def by_grid_point(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[components.Entity],
    compute_type: str | None = None,
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: components.EntitySensor | None = None,
    grid_point_constraints: Sequence[components.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute revisit-time FOM values for each grid point."""
    return post_value_by_grid_point_input(
        "/Coverage/FOM/ValueByGridPoint/RevisitTime",
        start=start,
        stop=stop,
        grid=grid,
        assets=assets,
        compute_type=compute_type,
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=include_asset_access_results,
        include_coverage_points=include_coverage_points,
        step_s=step_s,
        description=description,
    )


def by_grid_point_at_time(
    *,
    time: str,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[components.Entity],
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: components.EntitySensor | None = None,
    grid_point_constraints: Sequence[components.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute revisit-time FOM values for each grid point at one time."""
    return post_time_value_by_grid_point_input(
        "/Coverage/FOM/ValueByGridPointAtTime/RevisitTime",
        time=time,
        start=start,
        stop=stop,
        grid=grid,
        assets=assets,
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=include_asset_access_results,
        include_coverage_points=include_coverage_points,
        step_s=step_s,
        description=description,
    )


def grid_stats(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[components.Entity],
    compute_type: str | None = None,
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: components.EntitySensor | None = None,
    grid_point_constraints: Sequence[components.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute revisit-time grid statistics."""
    return post_value_by_grid_point_input(
        "/Coverage/FOM/GridStats/RevisitTime",
        start=start,
        stop=stop,
        grid=grid,
        assets=assets,
        compute_type=compute_type,
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=include_asset_access_results,
        include_coverage_points=include_coverage_points,
        step_s=step_s,
        description=description,
    )


def grid_stats_over_time(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[components.Entity],
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: components.EntitySensor | None = None,
    grid_point_constraints: Sequence[components.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute revisit-time grid statistics over time."""
    return post_coverage_input(
        "/Coverage/FOM/GridStatsOverTime/RevisitTime",
        start=start,
        stop=stop,
        grid=grid,
        assets=assets,
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=include_asset_access_results,
        include_coverage_points=include_coverage_points,
        step_s=step_s,
        description=description,
    )
