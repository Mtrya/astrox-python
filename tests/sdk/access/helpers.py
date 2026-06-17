"""Shared test helpers for access SDK tests."""

from __future__ import annotations

from typing import Any

import pytest

from astrox import access, components


TLE_A = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
TLE_B = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, Any],
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, Any]:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(access.raw, "post", fake_post)
    return calls


def ground() -> components.Entity:
    return components.entity(
        name="Ground",
        position=components.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
    )


def iss() -> components.Entity:
    return components.entity(
        name="ISS",
        position=components.sgp4_position(tle_lines=TLE_A),
    )


def hubble() -> components.Entity:
    return components.entity(
        name="Hubble",
        position=components.sgp4_position(tle_lines=TLE_B),
    )
