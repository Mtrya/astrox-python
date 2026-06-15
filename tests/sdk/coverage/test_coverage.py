"""Focused tests for coverage request assembly."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass
from inspect import signature
from typing import Any, Callable

import pytest

import astrox
from astrox import coverage, entities, exceptions
from tests.sdk.helpers import assert_canonical_equal


TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

COVERAGE_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "SatisfactionIntervalsWithNumberOfAssets": [],
}

GRID_POINTS_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "Points": {"GridPoints": []},
}

PERCENT_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "PercentCoverageDatas": [],
}

BY_ASSET_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "CoverageByAssetDatas": [],
}


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, Any],
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, Any]:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(coverage.raw, "post", fake_post)
    return calls


def sample_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=35.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-100.0,
        resolution_deg=5.0,
    )


def sample_asset(name: str = "Relay") -> entities.Entity:
    return entities.entity(
        name=name,
        position=entities.sgp4_position(tle_lines=TLE_LINES),
    )


def test_package_exports_coverage_module() -> None:
    assert astrox.coverage is coverage
    assert "coverage" in astrox.__all__


def test_public_coverage_names_are_exported() -> None:
    assert "CbLatLonGrid" in coverage.__all__
    assert "CoverageGrid" in coverage.__all__
    assert "GlobalGrid" in coverage.__all__
    assert "LatitudeGrid" in coverage.__all__
    assert "LatLonGrid" in coverage.__all__
    assert "cb_lat_lon_grid" in coverage.__all__
    assert "compute" in coverage.__all__
    assert "coverage_by_asset" in coverage.__all__
    assert "global_grid" in coverage.__all__
    assert "grid_points" in coverage.__all__
    assert "lat_lon_grid" in coverage.__all__
    assert "latitude_grid" in coverage.__all__
    assert "percent_coverage" in coverage.__all__


def test_grid_constructors_lower_discriminated_fragments() -> None:
    global_grid = coverage.global_grid(
        central_body="Earth",
        resolution_deg=6.0,
        height_m=0.0,
        use_cell_surface_area_for_weight=True,
    )

    assert is_dataclass(global_grid)
    assert isinstance(global_grid, coverage.GlobalGrid)
    assert_canonical_equal(
        global_grid.to_wire(),
        {
            "$type": "Global",
            "CentralBodyName": "Earth",
            "Resolution": 6.0,
            "Height": 0.0,
            "UseCellSurfaceAreaForWeight": True,
        },
    )
    assert_canonical_equal(
        coverage.latitude_grid(
            min_latitude_deg=-30.0,
            max_latitude_deg=30.0,
            resolution_deg=10.0,
        ).to_wire(),
        {
            "$type": "LatitudeBounds",
            "MinLatitude": -30.0,
            "MaxLatitude": 30.0,
            "Resolution": 10.0,
        },
    )
    assert_canonical_equal(
        coverage.lat_lon_grid(
            min_latitude_deg=20.0,
            max_latitude_deg=35.0,
            min_longitude_deg=-120.0,
            max_longitude_deg=-100.0,
            height_m=100.0,
            use_cell_surface_area_for_weight=False,
        ).to_wire(),
        {
            "$type": "LatLonBounds",
            "MinLatitude": 20.0,
            "MaxLatitude": 35.0,
            "MinLongitude": -120.0,
            "MaxLongitude": -100.0,
            "Height": 100.0,
            "UseCellSurfaceAreaForWeight": False,
        },
    )
    assert_canonical_equal(
        coverage.cb_lat_lon_grid(
            min_latitude_deg=20.0,
            max_latitude_deg=35.0,
            min_longitude_deg=-120.0,
            max_longitude_deg=-100.0,
        ).to_wire(),
        {
            "$type": "CbLatLonBounds",
            "MinLatitude": 20.0,
            "MaxLatitude": 35.0,
            "MinLongitude": -120.0,
            "MaxLongitude": -100.0,
        },
    )

    with pytest.raises(FrozenInstanceError):
        global_grid.resolution_deg = 10.0


def test_global_grid_omits_server_owned_defaults() -> None:
    assert_canonical_equal(coverage.global_grid().to_wire(), {"$type": "Global"})


def test_grid_points_emits_grid_input_payload_and_returns_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, GRID_POINTS_RESPONSE)

    response = coverage.grid_points(grid=sample_grid(), text="Western US grid")

    assert response is GRID_POINTS_RESPONSE
    assert calls[0]["endpoint"] == "/Coverage/GetGridPoints"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Text": "Western US grid",
            "Grid": {
                "$type": "LatLonBounds",
                "MinLatitude": 20.0,
                "MaxLatitude": 35.0,
                "MinLongitude": -120.0,
                "MaxLongitude": -100.0,
                "Resolution": 5.0,
            },
        },
    )


def test_compute_signature_uses_public_coverage_shape() -> None:
    parameters = signature(coverage.compute).parameters

    assert "grid" in parameters
    assert "assets" in parameters
    assert "minimum_assets" in parameters
    assert "exactly_assets" in parameters
    assert "grid_point_sensor" in parameters
    assert "grid_point_constraints" in parameters
    assert "include_asset_access_results" in parameters
    assert "include_coverage_points" in parameters
    assert "step_s" in parameters
    assert "description" in parameters
    assert "filter_type" not in parameters
    assert "number_of_assets" not in parameters


def test_compute_emits_complete_coverage_payload_and_returns_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, COVERAGE_RESPONSE)
    asset = sample_asset()

    response = coverage.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        grid=sample_grid(),
        assets=[asset],
        minimum_assets=1,
        grid_point_sensor=entities.conic_sensor(outer_half_angle_deg=45.0),
        grid_point_constraints=[
            entities.elevation_constraint(minimum_deg=10.0),
            entities.range_constraint(maximum_km=2500.0, maximum_enabled=True),
        ],
        include_asset_access_results=True,
        include_coverage_points=True,
        step_s=60.0,
        description="Western US coverage",
    )

    assert response is COVERAGE_RESPONSE
    assert calls[0]["endpoint"] == "/Coverage/ComputeCoverage"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Description": "Western US coverage",
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T03:00:00.000Z",
            "Grid": {
                "$type": "LatLonBounds",
                "MinLatitude": 20.0,
                "MaxLatitude": 35.0,
                "MinLongitude": -120.0,
                "MaxLongitude": -100.0,
                "Resolution": 5.0,
            },
            "Assets": [asset.to_wire()],
            "GridPointSensor": {"$type": "Conic", "outerHalfAngle": 45.0},
            "GridPointConstraints": [
                {
                    "$type": "ElevationAngle",
                    "MinimumValue": 10.0,
                },
                {
                    "$type": "Range",
                    "MaximumValue": 2500.0,
                    "IsMaximumEnabled": True,
                },
            ],
            "FilterType": "AtLeastN",
            "NumberOfAssets": 1,
            "ContainAssetAccessResults": True,
            "ContainCoveragePoints": True,
            "Step": 60.0,
        },
    )


def test_compute_omits_optional_fields_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, COVERAGE_RESPONSE)

    coverage.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        grid=sample_grid(),
        assets=[],
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T03:00:00.000Z",
            "Grid": {
                "$type": "LatLonBounds",
                "MinLatitude": 20.0,
                "MaxLatitude": 35.0,
                "MinLongitude": -120.0,
                "MaxLongitude": -100.0,
                "Resolution": 5.0,
            },
            "Assets": [],
        },
    )


def test_reports_emit_shared_coverage_payload_to_report_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, PERCENT_RESPONSE)
    asset = sample_asset()

    percent = coverage.percent_coverage(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        grid=sample_grid(),
        assets=[asset],
        exactly_assets=1,
        include_coverage_points=False,
        step_s=120.0,
    )

    assert percent is PERCENT_RESPONSE
    assert calls[0]["endpoint"] == "/Coverage/Report/PercentCoverage"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T03:00:00.000Z",
            "Grid": {
                "$type": "LatLonBounds",
                "MinLatitude": 20.0,
                "MaxLatitude": 35.0,
                "MinLongitude": -120.0,
                "MaxLongitude": -100.0,
                "Resolution": 5.0,
            },
            "Assets": [asset.to_wire()],
            "FilterType": "ExactlyN",
            "NumberOfAssets": 1,
            "ContainCoveragePoints": False,
            "Step": 120.0,
        },
    )

    calls = record_raw_post(monkeypatch, BY_ASSET_RESPONSE)

    by_asset = coverage.coverage_by_asset(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        grid=sample_grid(),
        assets=[asset],
        minimum_assets=0,
        grid_point_sensor=entities.rectangular_sensor(
            x_half_angle_deg=30.0,
            y_half_angle_deg=20.0,
        ),
        grid_point_constraints=[
            entities.az_el_mask_constraint(az_el_mask_rad=[0.0, 0.1, 3.14, 0.2]),
        ],
        include_asset_access_results=True,
        description="by asset",
    )

    assert by_asset is BY_ASSET_RESPONSE
    assert calls[0]["endpoint"] == "/Coverage/Report/CoverageByAsset"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Description": "by asset",
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T03:00:00.000Z",
            "Grid": {
                "$type": "LatLonBounds",
                "MinLatitude": 20.0,
                "MaxLatitude": 35.0,
                "MinLongitude": -120.0,
                "MaxLongitude": -100.0,
                "Resolution": 5.0,
            },
            "Assets": [asset.to_wire()],
            "GridPointSensor": {
                "$type": "Rectangular",
                "xHalfAngle": 30.0,
                "yHalfAngle": 20.0,
            },
            "GridPointConstraints": [
                {
                    "$type": "AzElMask",
                    "AzElMaskData": [0.0, 0.1, 3.14, 0.2],
                }
            ],
            "FilterType": "AtLeastN",
            "NumberOfAssets": 0,
            "ContainAssetAccessResults": True,
        },
    )


def test_coverage_functions_return_malformed_raw_response_without_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = {"unexpected": ["coverage", "shape"]}
    record_raw_post(monkeypatch, response)

    actual = coverage.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        grid=sample_grid(),
        assets=[sample_asset()],
    )

    assert actual is response


@pytest.mark.parametrize(
    ("func", "endpoint"),
    (
        (coverage.compute, "/Coverage/ComputeCoverage"),
        (coverage.percent_coverage, "/Coverage/Report/PercentCoverage"),
        (coverage.coverage_by_asset, "/Coverage/Report/CoverageByAsset"),
    ),
)
def test_coverage_functions_propagate_api_errors_unchanged(
    func: Callable[..., dict[str, Any]],
    endpoint: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = exceptions.AstroxAPIError(
        "bad coverage",
        endpoint,
        response=None,
    )

    def fake_post(actual_endpoint: str, *, json: object) -> dict[str, Any]:
        assert actual_endpoint == endpoint
        raise error

    monkeypatch.setattr(coverage.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        func(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T03:00:00.000Z",
            grid=sample_grid(),
            assets=[sample_asset()],
        )

    assert exc_info.value is error


@pytest.mark.parametrize(
    ("factory", "kwargs", "match"),
    [
        (
            coverage.global_grid,
            {"resolution_deg": True},
            "resolution_deg must be a number",
        ),
        (
            coverage.global_grid,
            {"use_cell_surface_area_for_weight": 1},
            "use_cell_surface_area_for_weight must be a bool",
        ),
        (
            coverage.latitude_grid,
            {"min_latitude_deg": "0", "max_latitude_deg": 10.0},
            "min_latitude_deg must be a number",
        ),
        (
            coverage.grid_points,
            {"grid": {"$type": "Global"}},
            "grid must be an astrox.coverage grid value",
        ),
        (
            coverage.compute,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T03:00:00.000Z",
                "grid": sample_grid(),
                "assets": ["Relay"],
            },
            "assets must be a sequence of astrox.entities.Entity values",
        ),
        (
            coverage.compute,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T03:00:00.000Z",
                "grid": sample_grid(),
                "assets": [sample_asset()],
                "grid_point_sensor": {"$type": "Conic"},
            },
            "grid_point_sensor must be an astrox.entities sensor value",
        ),
        (
            coverage.compute,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T03:00:00.000Z",
                "grid": sample_grid(),
                "assets": [sample_asset()],
                "grid_point_constraints": [{"$type": "ElevationAngle"}],
            },
            "grid_point_constraints must be a sequence of astrox.entities constraint values",
        ),
        (
            coverage.compute,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T03:00:00.000Z",
                "grid": sample_grid(),
                "assets": [sample_asset()],
                "minimum_assets": True,
            },
            "minimum_assets must be an integer",
        ),
        (
            coverage.compute,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T03:00:00.000Z",
                "grid": sample_grid(),
                "assets": [sample_asset()],
                "include_coverage_points": "yes",
            },
            "include_coverage_points must be a bool",
        ),
    ],
)
def test_constructors_and_functions_reject_unsupported_shapes(
    factory: object,
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(TypeError, match=match):
        factory(**kwargs)


def test_resource_count_rule_rejects_ambiguous_mode() -> None:
    with pytest.raises(
        ValueError,
        match="minimum_assets and exactly_assets cannot both be supplied",
    ):
        coverage.compute(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T03:00:00.000Z",
            grid=sample_grid(),
            assets=[sample_asset()],
            minimum_assets=1,
            exactly_assets=1,
        )
