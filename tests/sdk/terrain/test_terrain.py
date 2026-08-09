"""Deterministic behavior tests for terrain-mask functions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction
from typing import Any

import pytest

from astrox import components, exceptions, terrain
from tests.sdk.helpers import assert_canonical_equal


RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "Success",
    "AzElMaskData": [],
}
SITE = components.site_position(
    longitude_deg=0.0,
    latitude_deg=-89.0,
    height_m=0.0,
    central_body="Moon",
)
CONFIG = terrain.TerrainMaskConfig(
    text="probe",
    terrain_server_url="",
    flag_pole=1,
    polar_dem_file_name="Moon_LDEM_80s_20m",
    terrain_zoom_level=-1,
    step_size_m=Fraction(30),
    max_search_range_km=Fraction(15),
)


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_post(endpoint: str, *, json: object) -> object:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(terrain.raw, "post", fake_post)
    return calls


def test_terrain_public_exports() -> None:
    import astrox

    assert astrox.terrain is terrain
    assert "terrain" in astrox.__all__
    assert set(terrain.__all__) == {
        "TerrainMaskConfig",
        "azimuth_elevation_mask",
        "azimuth_elevation_mask_simple",
    }


def test_terrain_mask_config_is_frozen_and_lowers_exactly() -> None:
    assert_canonical_equal(
        CONFIG.to_wire(),
        {
            "Text": "probe",
            "TerrainServerUrl": "",
            "FlagPole": 1,
            "PolarDemFileName": "Moon_LDEM_80s_20m",
            "TerrainZoomLevel": -1,
            "StepSize": 30.0,
            "MaxSearchRange": 15.0,
        },
    )
    with pytest.raises(FrozenInstanceError):
        CONFIG.flag_pole = 0


def test_terrain_mask_config_omits_none_fields() -> None:
    config = terrain.TerrainMaskConfig(
        text="terrain example",
        polar_dem_file_name="Moon_LDEM_80s_20m",
    )

    assert_canonical_equal(
        config.to_wire(),
        {
            "Text": "terrain example",
            "PolarDemFileName": "Moon_LDEM_80s_20m",
        },
    )


def test_full_terrain_mask_lowers_complete_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    response = terrain.azimuth_elevation_mask(
        site_position=SITE,
        config=CONFIG,
        text="request text",
    )

    assert response == {"AzElMaskData": []}
    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/Terrain/AzElMask",
            "json": {
                "Text": "request text",
                "sitePosition": {
                    "cartographicDegrees": [0.0, -89.0, 0.0],
                    "CentralBody": "Moon",
                },
                "TerrainMaskPara": CONFIG.to_wire(),
            },
        },
    )


def test_simple_terrain_mask_omits_server_owned_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    response = terrain.azimuth_elevation_mask_simple(site_position=SITE)

    assert response == {"AzElMaskData": []}
    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/Terrain/AzElMaskSimple",
            "json": {
                "sitePosition": {
                    "cartographicDegrees": [0.0, -89.0, 0.0],
                    "CentralBody": "Moon",
                },
            },
        },
    )


@pytest.mark.parametrize(
    ("function", "kwargs", "parameter"),
    [
        (
            terrain.azimuth_elevation_mask,
            {"site_position": {}},
            "site_position",
        ),
        (
            terrain.azimuth_elevation_mask,
            {"site_position": SITE, "config": {}},
            "config",
        ),
        (
            terrain.TerrainMaskConfig,
            {"flag_pole": True},
            "flag_pole",
        ),
        (
            terrain.TerrainMaskConfig,
            {"step_size_m": True},
            "step_size_m",
        ),
    ],
)
def test_terrain_rejects_mistyped_arguments(
    function: Any,
    kwargs: dict[str, Any],
    parameter: str,
) -> None:
    with pytest.raises(TypeError, match=parameter):
        function(**kwargs)


def test_terrain_propagates_api_errors_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = exceptions.AstroxAPIError("terrain failed", "/Terrain/AzElMask", response=None)

    def fake_post(endpoint: str, *, json: object) -> object:
        assert endpoint == "/Terrain/AzElMask"
        raise error

    monkeypatch.setattr(terrain.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        terrain.azimuth_elevation_mask(site_position=SITE)

    assert exc_info.value is error
