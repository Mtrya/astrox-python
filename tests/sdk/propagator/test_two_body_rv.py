"""Focused tests for the curated two-body RV propagator function."""

from __future__ import annotations

from typing import get_type_hints

import pytest

from astrox import exceptions, orbits, propagator
from tests.sdk.helpers import assert_canonical_equal

REPRESENTATIVE_STATE = {
    "x_m": 7000000.0,
    "y_m": 0.0,
    "z_m": 0.0,
    "vx_m_s": 0.0,
    "vy_m_s": 7546.053290114564,
    "vz_m_s": 0.0,
}

REPRESENTATIVE_RESPONSE = {
    "IsSuccess": True,
    "Message": "",
    "Positions": [
        0.0,
        7000000.0,
        0.0,
        0.0,
        0.0,
        7546.053290114564,
        0.0,
        60.0,
        6999986.4,
        452695.8,
        0.0,
        -6.8,
        7546.0,
        0.0,
    ],
}


@pytest.fixture
def state() -> orbits.CartesianState:
    return orbits.cartesian_state(**REPRESENTATIVE_STATE)


def test_two_body_rv_calls_raw_route_with_representative_payload(
    monkeypatch: pytest.MonkeyPatch,
    state: orbits.CartesianState,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return REPRESENTATIVE_RESPONSE

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    positions = propagator.two_body_rv(
        state=state,
        time_of_flight_s=3600.0,
        gravitational_parameter_m3_s2=398600441500000.0,
        step_s=60.0,
    )

    assert calls[0]["endpoint"] == "/Propagator/TwoBodyRV"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "RV0": [7000000.0, 0.0, 0.0, 0.0, 7546.053290114564, 0.0],
            "Gm": 398600441500000.0,
            "TimeOfFlight": 3600.0,
            "Step": 60.0,
        },
    )
    assert positions == tuple(REPRESENTATIVE_RESPONSE["Positions"])


def test_two_body_rv_omits_server_owned_defaults_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
    state: orbits.CartesianState,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return REPRESENTATIVE_RESPONSE

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    propagator.two_body_rv(state=state, time_of_flight_s=3600.0)

    assert_canonical_equal(
        calls[0]["json"],
        {
            "RV0": [7000000.0, 0.0, 0.0, 0.0, 7546.053290114564, 0.0],
            "TimeOfFlight": 3600.0,
        },
    )


def test_two_body_rv_rejects_raw_state_fragments() -> None:
    with pytest.raises(TypeError):
        propagator.two_body_rv(
            state=[7000000.0, 0.0, 0.0, 0.0, 7546.053290114564, 0.0],
            time_of_flight_s=3600.0,
        )


def test_two_body_rv_parser_fails_loudly_for_missing_positions(
    monkeypatch: pytest.MonkeyPatch,
    state: orbits.CartesianState,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        return {"IsSuccess": True, "Message": ""}

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(KeyError):
        propagator.two_body_rv(state=state, time_of_flight_s=3600.0)


def test_two_body_rv_propagates_api_error_for_unsuccessful_raw_response(
    monkeypatch: pytest.MonkeyPatch,
    state: orbits.CartesianState,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        raise exceptions.AstroxAPIError("bad state", endpoint, response=None)

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError, match="bad state"):
        propagator.two_body_rv(state=state, time_of_flight_s=3600.0)


def test_two_body_rv_return_type_hint_is_flat_sample_sequence() -> None:
    assert get_type_hints(propagator.two_body_rv)["return"] == tuple[float, ...]
