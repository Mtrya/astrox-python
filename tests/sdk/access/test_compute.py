"""Focused tests for direct access request assembly."""

from __future__ import annotations

from inspect import signature
from typing import Any

import pytest

from astrox import access
from tests.sdk.access.helpers import ground, iss, record_raw_post
from tests.sdk.helpers import assert_canonical_equal


ACCESS_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "Passes": [],
}


def test_compute_signature_keeps_direct_entity_shape() -> None:
    parameters = signature(access.compute).parameters

    assert "from_entity" in parameters
    assert "to_entity" in parameters
    assert "step_s" in parameters
    assert "compute_aer" in parameters
    assert "use_light_time_delay" in parameters
    assert "description" not in parameters


def test_compute_emits_direct_access_payload_and_returns_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, ACCESS_RESPONSE)

    response = access.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        from_entity=ground(),
        to_entity=iss(),
        step_s=600.0,
        compute_aer=True,
        use_light_time_delay=False,
    )

    assert response is ACCESS_RESPONSE
    assert calls[0]["endpoint"] == "/access/AccessComputeV2"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-02T00:00:00.000Z",
            "FromObjectPath": {
                "Name": "Ground",
                "Position": {
                    "$type": "SitePosition",
                    "cartographicDegrees": [-155.468, 19.821, 4205.0],
                },
            },
            "ToObjectPath": {
                "Name": "ISS",
                "Position": {
                    "$type": "SGP4",
                    "TLEs": list(iss().position.tle_lines),
                },
            },
            "OutStep": 600.0,
            "ComputeAER": True,
            "UseLightTimeDelay": False,
        },
    )


def test_compute_omits_optional_fields_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, ACCESS_RESPONSE)

    access.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        from_entity=ground(),
        to_entity=iss(),
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": "2024-01-01T00:00:00.000Z",
            "Stop": "2024-01-02T00:00:00.000Z",
            "FromObjectPath": {
                "Name": "Ground",
                "Position": {
                    "$type": "SitePosition",
                    "cartographicDegrees": [-155.468, 19.821, 4205.0],
                },
            },
            "ToObjectPath": {
                "Name": "ISS",
                "Position": {
                    "$type": "SGP4",
                    "TLEs": list(iss().position.tle_lines),
                },
            },
        },
    )


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        (
            {
                "from_entity": {"Name": "Ground"},
                "to_entity": iss(),
            },
            "from_entity must be an astrox.entities.Entity value",
        ),
        (
            {
                "from_entity": ground(),
                "to_entity": "ISS",
            },
            "to_entity must be an astrox.entities.Entity value",
        ),
    ],
)
def test_compute_rejects_values_that_cannot_lower_to_entity_payloads(
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(TypeError, match=match):
        access.compute(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-02T00:00:00.000Z",
            **kwargs,
        )
