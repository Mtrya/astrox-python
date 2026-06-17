"""Shared lowering helpers for Coverage FOM metric modules."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from astrox import components
from astrox._http import raw

from ._core import (
    CoverageGrid,
    _coverage_input_payload,
    _include_if_supplied,
    _optional_string,
)


def post_coverage_input(
    endpoint: str,
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
    payload = _coverage_input_payload(
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
    return raw.post(endpoint, json=payload)


def post_value_by_grid_point_input(
    endpoint: str,
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
    payload = _coverage_input_payload(
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
    _include_if_supplied(
        payload,
        "ComputeType",
        _optional_string(compute_type, parameter="compute_type"),
    )
    return raw.post(endpoint, json=payload)


def post_time_value_by_grid_point_input(
    endpoint: str,
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
    if not isinstance(time, str):
        raise TypeError("time must be a string")
    payload = _coverage_input_payload(
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
    payload["Time"] = time
    return raw.post(endpoint, json=payload)
