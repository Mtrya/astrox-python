"""Focused tests for rocket request assembly."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from astrox import exceptions, rocket
from tests.sdk.helpers import assert_canonical_equal


LANDING_ZONE_RESPONSE = {
    "IsSuccess": True,
    "Message": "Success",
    "cartographicDegrees": [
        101.00644849946714,
        30.49160235039126,
        100.09828760419641,
        100.98837247272847,
        30.500570376621706,
        100.0979035792633,
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

    monkeypatch.setattr(rocket.raw, "post", fake_post)
    return calls


def test_landing_zone_emits_expected_payload_and_returns_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, LANDING_ZONE_RESPONSE)

    response = rocket.landing_zone(
        launch_longitude_deg=100.0,
        launch_latitude_deg=30.0,
        launch_height_m=0.0,
        impact_longitude_deg=101.0,
        impact_latitude_deg=30.5,
        impact_height_m=100.0,
        zone_xys_km=[1.0, 0.5, -1.0, 0.5],
    )

    assert response is LANDING_ZONE_RESPONSE
    assert calls[0]["endpoint"] == "/LandingZone"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "FaSheDian": [100.0, 30.0, 0.0],
            "LuoDian": [101.0, 30.5, 100.0],
            "ZoneXYs": [1.0, 0.5, -1.0, 0.5],
        },
    )


def test_landing_zone_returns_malformed_raw_response_without_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = {"unexpected": ["shape"]}
    calls = record_raw_post(monkeypatch, response)

    actual = rocket.landing_zone(
        launch_longitude_deg=100.0,
        launch_latitude_deg=30.0,
        launch_height_m=0.0,
        impact_longitude_deg=101.0,
        impact_latitude_deg=30.5,
        impact_height_m=100.0,
        zone_xys_km=[1.0, 0.5, -1.0, 0.5],
    )

    assert actual is response
    assert calls[0]["endpoint"] == "/LandingZone"


def test_landing_zone_propagates_api_errors_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = exceptions.AstroxAPIError("bad landing zone", "/LandingZone", response=None)

    def fake_post(endpoint: str, *, json: object) -> dict[str, Any]:
        assert endpoint == "/LandingZone"
        raise error

    monkeypatch.setattr(rocket.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        rocket.landing_zone(
            launch_longitude_deg=100.0,
            launch_latitude_deg=30.0,
            launch_height_m=0.0,
            impact_longitude_deg=101.0,
            impact_latitude_deg=30.5,
            impact_height_m=100.0,
            zone_xys_km=[1.0, 0.5, -1.0, 0.5],
        )

    assert exc_info.value is error


@pytest.mark.parametrize(
    "zone_xys_km",
    [
        [1.0, 0.5, -1.0],  # odd length
        (1.0, 0.5, -1.0),  # odd length tuple
    ],
)
def test_landing_zone_rejects_odd_length_zone_xys_km(
    zone_xys_km: Sequence[float],
) -> None:
    with pytest.raises(ValueError, match="zone_xys_km must contain an even number of values"):
        rocket.landing_zone(
            launch_longitude_deg=100.0,
            launch_latitude_deg=30.0,
            launch_height_m=0.0,
            impact_longitude_deg=101.0,
            impact_latitude_deg=30.5,
            impact_height_m=100.0,
            zone_xys_km=zone_xys_km,
        )


@pytest.mark.parametrize(
    "zone_xys_km",
    [
        "not a sequence",
        b"not a sequence",
        [1.0, "0.5"],
        [1.0, False],
        {1.0, 0.5},  # set is not ordered but is a sequence? Actually set is not Sequence
    ],
)
def test_landing_zone_rejects_non_numeric_zone_xys_km(
    zone_xys_km: Any,
) -> None:
    with pytest.raises(TypeError, match="zone_xys_km must be a sequence of numbers"):
        rocket.landing_zone(
            launch_longitude_deg=100.0,
            launch_latitude_deg=30.0,
            launch_height_m=0.0,
            impact_longitude_deg=101.0,
            impact_latitude_deg=30.5,
            impact_height_m=100.0,
            zone_xys_km=zone_xys_km,
        )
