"""Coverage-time FOM routes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from astrox import entities

from ._core import CoverageGrid
from ._fom import post_value_by_grid_point_input

__all__ = ["by_grid_point", "grid_stats"]


def by_grid_point(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[entities.Entity],
    compute_type: str | None = None,
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: entities.EntitySensor | None = None,
    grid_point_constraints: Sequence[entities.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute coverage-time FOM values for each grid point."""
    return post_value_by_grid_point_input(
        "/Coverage/FOM/ValueByGridPoint/CoverageTime",
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


def grid_stats(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[entities.Entity],
    compute_type: str | None = None,
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: entities.EntitySensor | None = None,
    grid_point_constraints: Sequence[entities.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute coverage-time grid statistics."""
    return post_value_by_grid_point_input(
        "/Coverage/FOM/GridStats/CoverageTime",
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
