"""Focused tests for lighting request assembly."""

from __future__ import annotations

from typing import Any

import pytest

from astrox import entities, exceptions, lighting, orbits
from tests.sdk.helpers import assert_canonical_equal


TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

LIGHTING_RESPONSE = {
    "IsSuccess": True,
    "Message": "",
    "SunLight": {"Intervals": [], "MeanDuration": 0.0, "TotalDuration": 0.0},
}

SOLAR_RESPONSE = {
    "IsSuccess": True,
    "Message": "",
    "Datas": [
        {
            "$type": "SolarIntensityScData",
            "Time": "2024-01-01T00:00:00.000Z",
            "Intensity": 1.0,
        }
    ],
}


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, Any],
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, Any]:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(lighting.raw, "post", fake_post)
    return calls


def sample_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def sample_site() -> entities.SitePosition:
    return entities.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    )


LIGHTING_RAW_CASES = [
    (
        lighting.lighting_times,
        {
            "start": "2024-01-01T00:00:00.000Z",
            "stop": "2024-01-01T01:00:00.000Z",
            "position": sample_site(),
        },
        "/Lighting/LightingTimes",
    ),
    (
        lighting.solar_intensity,
        {
            "start": "2024-01-01T00:00:00.000Z",
            "stop": "2024-01-01T01:00:00.000Z",
            "position": sample_site(),
        },
        "/Lighting/SolarIntensity",
    ),
    (
        lighting.solar_aer,
        {
            "start": "2024-01-01T00:00:00.000Z",
            "stop": "2024-01-01T01:00:00.000Z",
            "position": sample_site(),
        },
        "/Lighting/SolarAER",
    ),
]


@pytest.mark.parametrize(
    ("function", "kwargs", "endpoint"),
    LIGHTING_RAW_CASES,
)
def test_lighting_functions_return_malformed_raw_response_without_parsing(
    monkeypatch: pytest.MonkeyPatch,
    function: object,
    kwargs: dict[str, object],
    endpoint: str,
) -> None:
    response = {"unexpected": ["lighting", "shape"]}
    calls = record_raw_post(monkeypatch, response)

    actual = function(**kwargs)

    assert actual is response
    assert calls[0]["endpoint"] == endpoint


@pytest.mark.parametrize(
    ("function", "kwargs", "endpoint"),
    LIGHTING_RAW_CASES,
)
def test_lighting_functions_propagate_api_errors_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    function: object,
    kwargs: dict[str, object],
    endpoint: str,
) -> None:
    error = exceptions.AstroxAPIError("bad lighting", endpoint, response=None)

    def fake_post(post_endpoint: str, *, json: object) -> dict[str, Any]:
        assert post_endpoint == endpoint
        raise error

    monkeypatch.setattr(lighting.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        function(**kwargs)

    assert exc_info.value is error


def test_lighting_times_emits_typed_position_payload_and_returns_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, LIGHTING_RESPONSE)

    response = lighting.lighting_times(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T01:00:00.000Z",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
        description="ISS lighting",
        occultation_bodies=["Earth", "Moon"],
    )

    assert response is LIGHTING_RESPONSE
    assert calls[0]["endpoint"] == "/Lighting/LightingTimes"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T01:00:00.000Z",
            "Description": "ISS lighting",
            "Position": {
                "$type": "SGP4",
                "TLEs": list(TLE_LINES),
            },
            "OccultationBodies": ["Earth", "Moon"],
        },
    )


def test_solar_intensity_emits_position_payload_with_optional_site_mask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, SOLAR_RESPONSE)

    response = lighting.solar_intensity(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T01:00:00.000Z",
        position=sample_site(),
        az_el_mask_data=[0.0, 0.1, 3.14, 0.2],
        step_s=600.0,
    )

    assert response is SOLAR_RESPONSE
    assert calls[0]["endpoint"] == "/Lighting/SolarIntensity"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T01:00:00.000Z",
            "Position": {
                "$type": "SitePosition",
                "cartographicDegrees": [-155.468, 19.821, 4205.0],
            },
            "AzElMaskData": [0.0, 0.1, 3.14, 0.2],
            "TimeStepSec": 600.0,
        },
    )


def test_lighting_accepts_propagated_position_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, SOLAR_RESPONSE)

    lighting.solar_intensity(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T01:00:00.000Z",
        position=entities.j2_position(
            orbit_epoch="2024-01-01T00:00:00.000Z",
            orbit=sample_orbit(),
        ),
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T01:00:00.000Z",
            "Position": {
                "$type": "J2",
                "OrbitEpoch": "2024-01-01T00:00:00.000Z",
                "CoordType": "Classical",
                "OrbitalElements": [6778137.0, 0.001, 28.5, 0.0, 15.0, 45.0],
            },
        },
    )


def test_solar_aer_emits_typed_position_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(
        monkeypatch,
        {
            "IsSuccess": True,
            "Message": "",
            "Datas": [
                {
                    "Time": "2024-01-01T00:00:00.000Z",
                    "Azimuth": 100.0,
                    "Elevation": 30.0,
                    "Range": 147100000.0,
                }
            ],
        },
    )

    lighting.solar_aer(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T01:00:00.000Z",
        position=sample_site(),
        text="Mauna Kea sun",
        step_s=600,
    )

    assert calls[0]["endpoint"] == "/Lighting/SolarAER"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T01:00:00.000Z",
            "Text": "Mauna Kea sun",
            "Position": {
                "$type": "SitePosition",
                "cartographicDegrees": [-155.468, 19.821, 4205.0],
            },
            "TimeStepSec": 600,
        },
    )


def test_solar_aer_accepts_spacecraft_position_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(
        monkeypatch,
        {
            "IsSuccess": True,
            "Message": "",
            "Datas": [
                {
                    "Time": "2024-01-01T00:00:00.000Z",
                    "Azimuth": 205.0,
                    "Elevation": 28.0,
                    "Range": 147100000.0,
                }
            ],
        },
    )

    lighting.solar_aer(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T01:00:00.000Z",
        position=entities.sgp4_position(tle_lines=TLE_LINES),
        step_s=600,
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-01T01:00:00.000Z",
            "Position": {
                "$type": "SGP4",
                "TLEs": list(TLE_LINES),
            },
            "TimeStepSec": 600,
        },
    )


@pytest.mark.parametrize(
    ("function", "kwargs", "match"),
    [
        (
            lighting.lighting_times,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T01:00:00.000Z",
                "position": {"$type": "SGP4"},
            },
            "position must be an astrox.entities position value",
        ),
        (
            lighting.solar_intensity,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T01:00:00.000Z",
                "position": entities.entity(name="site", position=sample_site()),
            },
            "position must be an astrox.entities position value",
        ),
        (
            lighting.solar_aer,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T01:00:00.000Z",
                "position": {"$type": "SGP4"},
            },
            "position must be an astrox.entities position value",
        ),
        (
            lighting.solar_intensity,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T01:00:00.000Z",
                "position": sample_site(),
                "az_el_mask_data": [0.0, "0.1"],
            },
            "az_el_mask_data must be a sequence of numbers",
        ),
        (
            lighting.lighting_times,
            {
                "start": "2024-01-01T00:00:00.000Z",
                "stop": "2024-01-01T01:00:00.000Z",
                "position": sample_site(),
                "az_el_mask_data": [0.0, False],
            },
            "az_el_mask_data must be a sequence of numbers",
        ),
    ],
)
def test_lighting_functions_reject_unsupported_public_shapes(
    function: object,
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(TypeError, match=match):
        function(**kwargs)
