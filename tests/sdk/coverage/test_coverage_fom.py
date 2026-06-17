"""Focused tests for coverage FOM request assembly."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

import astrox
from astrox import coverage, components, exceptions
from astrox.coverage import _fom
from tests.sdk.helpers import assert_canonical_equal


TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
FOM_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "Datas": [],
}


def sample_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )


def sample_asset(name: str = "Relay") -> components.Entity:
    return components.entity(
        name=name,
        position=components.sgp4_position(tle_lines=TLE_LINES),
    )


FOM_ROUTES: tuple[tuple[Callable[..., dict[str, Any]], str, str], ...] = (
    (
        coverage.simple_coverage.by_grid_point,
        "/Coverage/FOM/ValueByGridPoint/SimpleCoverage",
        "coverage",
    ),
    (
        coverage.simple_coverage.by_grid_point_at_time,
        "/Coverage/FOM/ValueByGridPointAtTime/SimpleCoverage",
        "time",
    ),
    (
        coverage.simple_coverage.grid_stats,
        "/Coverage/FOM/GridStats/SimpleCoverage",
        "coverage",
    ),
    (
        coverage.simple_coverage.grid_stats_over_time,
        "/Coverage/FOM/GridStatsOverTime/SimpleCoverage",
        "coverage",
    ),
    (
        coverage.coverage_time.by_grid_point,
        "/Coverage/FOM/ValueByGridPoint/CoverageTime",
        "compute",
    ),
    (
        coverage.coverage_time.grid_stats,
        "/Coverage/FOM/GridStats/CoverageTime",
        "compute",
    ),
    (
        coverage.number_of_assets.by_grid_point,
        "/Coverage/FOM/ValueByGridPoint/NumberOfAssets",
        "compute",
    ),
    (
        coverage.number_of_assets.by_grid_point_at_time,
        "/Coverage/FOM/ValueByGridPointAtTime/NumberOfAssets",
        "time",
    ),
    (
        coverage.number_of_assets.grid_stats,
        "/Coverage/FOM/GridStats/NumberOfAssets",
        "compute",
    ),
    (
        coverage.number_of_assets.grid_stats_over_time,
        "/Coverage/FOM/GridStatsOverTime/NumberOfAssets",
        "coverage",
    ),
    (
        coverage.response_time.by_grid_point,
        "/Coverage/FOM/ValueByGridPoint/ResponseTime",
        "compute",
    ),
    (
        coverage.response_time.by_grid_point_at_time,
        "/Coverage/FOM/ValueByGridPointAtTime/ResponseTime",
        "time",
    ),
    (
        coverage.response_time.grid_stats,
        "/Coverage/FOM/GridStats/ResponseTime",
        "compute",
    ),
    (
        coverage.response_time.grid_stats_over_time,
        "/Coverage/FOM/GridStatsOverTime/ResponseTime",
        "coverage",
    ),
    (
        coverage.revisit_time.by_grid_point,
        "/Coverage/FOM/ValueByGridPoint/RevisitTime",
        "compute",
    ),
    (
        coverage.revisit_time.by_grid_point_at_time,
        "/Coverage/FOM/ValueByGridPointAtTime/RevisitTime",
        "time",
    ),
    (
        coverage.revisit_time.grid_stats,
        "/Coverage/FOM/GridStats/RevisitTime",
        "compute",
    ),
    (
        coverage.revisit_time.grid_stats_over_time,
        "/Coverage/FOM/GridStatsOverTime/RevisitTime",
        "coverage",
    ),
)


def test_package_exports_coverage_fom_metric_modules() -> None:
    assert astrox.coverage.simple_coverage is coverage.simple_coverage
    assert astrox.coverage.coverage_time is coverage.coverage_time
    assert astrox.coverage.number_of_assets is coverage.number_of_assets
    assert astrox.coverage.response_time is coverage.response_time
    assert astrox.coverage.revisit_time is coverage.revisit_time


@pytest.mark.parametrize(("func", "endpoint", "kind"), FOM_ROUTES)
def test_fom_functions_emit_route_payloads_and_return_raw_response(
    func: Callable[..., dict[str, Any]],
    endpoint: str,
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(actual_endpoint: str, *, json: object) -> dict[str, Any]:
        calls.append({"endpoint": actual_endpoint, "json": json})
        return FOM_RESPONSE

    monkeypatch.setattr(_fom.raw, "post", fake_post)
    asset = sample_asset()
    kwargs: dict[str, object] = {
        "start": "2024-01-01T00:00:00.000Z",
        "stop": "2024-01-01T00:30:00.000Z",
        "grid": sample_grid(),
        "assets": [asset],
        "minimum_assets": 1,
        "grid_point_sensor": components.conic_sensor(outer_half_angle_deg=40.0),
        "grid_point_constraints": [
            components.elevation_constraint(minimum_deg=5.0),
        ],
        "include_asset_access_results": True,
        "include_coverage_points": False,
        "step_s": 120.0,
        "description": "FOM case",
    }
    expected: dict[str, object] = {
        "Description": "FOM case",
        "Start": "2024-01-01T00:00:00.000Z",
        "Stop": "2024-01-01T00:30:00.000Z",
        "Grid": {
            "$type": "LatLonBounds",
            "MinLatitude": 20.0,
            "MaxLatitude": 25.0,
            "MinLongitude": -120.0,
            "MaxLongitude": -110.0,
            "Resolution": 5.0,
        },
        "Assets": [asset.to_wire()],
        "GridPointSensor": {"$type": "Conic", "outerHalfAngle": 40.0},
        "GridPointConstraints": [
            {
                "$type": "ElevationAngle",
                "MinimumValue": 5.0,
            }
        ],
        "FilterType": "AtLeastN",
        "NumberOfAssets": 1,
        "ContainAssetAccessResults": True,
        "ContainCoveragePoints": False,
        "Step": 120.0,
    }
    if kind == "compute":
        kwargs["compute_type"] = "Average"
        expected["ComputeType"] = "Average"
    if kind == "time":
        kwargs["time"] = "2024-01-01T00:10:00.000Z"
        expected["Time"] = "2024-01-01T00:10:00.000Z"

    response = func(**kwargs)

    assert response is FOM_RESPONSE
    assert calls[0]["endpoint"] == endpoint
    assert_canonical_equal(calls[0]["json"], expected)


def test_fom_optional_compute_type_is_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, Any]:
        calls.append({"endpoint": endpoint, "json": json})
        return FOM_RESPONSE

    monkeypatch.setattr(_fom.raw, "post", fake_post)

    coverage.number_of_assets.by_grid_point(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:30:00.000Z",
        grid=sample_grid(),
        assets=[sample_asset()],
    )

    assert "ComputeType" not in calls[0]["json"]


def test_fom_exactly_assets_lowers_without_minimum_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, Any]:
        calls.append({"endpoint": endpoint, "json": json})
        return FOM_RESPONSE

    monkeypatch.setattr(_fom.raw, "post", fake_post)

    coverage.number_of_assets.by_grid_point(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:30:00.000Z",
        grid=sample_grid(),
        assets=[sample_asset()],
        minimum_assets=None,
        exactly_assets=2,
    )

    assert calls[0]["endpoint"] == "/Coverage/FOM/ValueByGridPoint/NumberOfAssets"
    assert calls[0]["json"]["FilterType"] == "ExactlyN"
    assert calls[0]["json"]["NumberOfAssets"] == 2


def test_fom_functions_return_malformed_raw_response_without_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = {"unexpected": ["fom", "shape"]}

    def fake_post(endpoint: str, *, json: object) -> dict[str, Any]:
        return response

    monkeypatch.setattr(_fom.raw, "post", fake_post)

    actual = coverage.simple_coverage.by_grid_point(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:30:00.000Z",
        grid=sample_grid(),
        assets=[sample_asset()],
    )

    assert actual is response


@pytest.mark.parametrize(
    ("func", "kwargs", "match"),
    [
        (
            coverage.coverage_time.by_grid_point,
            {"compute_type": 1},
            "compute_type must be a string",
        ),
        (
            coverage.simple_coverage.by_grid_point_at_time,
            {"time": None},
            "time must be a string",
        ),
    ],
)
def test_fom_functions_reject_unsupported_shapes(
    func: Callable[..., dict[str, Any]],
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(TypeError, match=match):
        func(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T00:30:00.000Z",
            grid=sample_grid(),
            assets=[sample_asset()],
            **kwargs,
        )


@pytest.mark.parametrize(("func", "endpoint", "kind"), FOM_ROUTES)
def test_fom_functions_propagate_api_errors_unchanged(
    func: Callable[..., dict[str, Any]],
    endpoint: str,
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = exceptions.AstroxAPIError("bad fom", endpoint, response=None)

    def fake_post(actual_endpoint: str, *, json: object) -> dict[str, Any]:
        assert actual_endpoint == endpoint
        raise error

    monkeypatch.setattr(_fom.raw, "post", fake_post)
    kwargs: dict[str, object] = {
        "start": "2024-01-01T00:00:00.000Z",
        "stop": "2024-01-01T00:30:00.000Z",
        "grid": sample_grid(),
        "assets": [sample_asset()],
    }
    if kind == "compute":
        kwargs["compute_type"] = "Average"
    if kind == "time":
        kwargs["time"] = "2024-01-01T00:10:00.000Z"

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        func(**kwargs)

    assert exc_info.value is error
