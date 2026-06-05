"""Focused tests for curated orbit conversion functions."""

from __future__ import annotations

from typing import get_type_hints

import pytest

from astrox import exceptions, orbits
from tests.sdk.orbits.helpers import (
    EARTH_MU,
    KEPLERIAN_WIRE,
    MEAN_ELEMENTS_RESPONSE,
    MEAN_ELEMENTS_SNAPSHOT,
    REPRESENTATIVE_CARTESIAN_RESPONSE,
    REPRESENTATIVE_CARTESIAN_SNAPSHOT,
    REPRESENTATIVE_KEPLERIAN_RESPONSE,
    REPRESENTATIVE_KEPLERIAN_SNAPSHOT,
    TARGET_KEPLERIAN_WIRE,
    assert_canonical_equal,
    cartesian_snapshot,
    keplerian_snapshot,
    mean_keplerian_snapshot,
    record_raw_post,
    sample_cartesian_state,
    sample_orbit,
    target_orbit,
)


def test_keplerian_to_cartesian_emits_payload_and_returns_cartesian_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_CARTESIAN_RESPONSE)

    state = orbits.keplerian_to_cartesian(
        sample_orbit(),
        gravitational_parameter_m3_s2=EARTH_MU,
    )

    assert calls[0]["endpoint"] == "/OrbitConvert/Kepler2RV"
    assert_canonical_equal(
        calls[0]["json"],
        {**KEPLERIAN_WIRE, "GravitationalParameter": EARTH_MU},
    )
    assert isinstance(state, orbits.CartesianState)
    assert_canonical_equal(cartesian_snapshot(state), REPRESENTATIVE_CARTESIAN_SNAPSHOT)


def test_keplerian_to_cartesian_omits_mu_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_CARTESIAN_RESPONSE)

    orbits.keplerian_to_cartesian(sample_orbit())

    assert calls[0]["endpoint"] == "/OrbitConvert/Kepler2RV"
    assert_canonical_equal(calls[0]["json"], KEPLERIAN_WIRE)


def test_cartesian_to_keplerian_emits_cartesian_wire_and_returns_keplerian(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_KEPLERIAN_RESPONSE)

    elements = orbits.cartesian_to_keplerian(sample_cartesian_state())

    assert calls[0]["endpoint"] == "/OrbitConvert/RV2Kepler"
    assert_canonical_equal(calls[0]["json"], REPRESENTATIVE_CARTESIAN_RESPONSE)
    assert isinstance(elements, orbits.KeplerianElements)
    assert_canonical_equal(
        keplerian_snapshot(elements),
        REPRESENTATIVE_KEPLERIAN_SNAPSHOT,
    )


def test_lla_at_ascending_node_emits_epoch_payload_and_returns_tuple(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, [-100.475, 0.126, 393221.966])

    location = orbits.lla_at_ascending_node(
        sample_orbit(),
        orbit_epoch="2024-01-01T00:00:00.000Z",
    )

    assert calls[0]["endpoint"] == "/OrbitConvert/Kepler2LLAAtAscendNode"
    assert_canonical_equal(
        calls[0]["json"],
        {"OrbitEpoch": "2024-01-01T00:00:00.000Z", **KEPLERIAN_WIRE},
    )
    assert location == (-100.475, 0.126, 393221.966)


def test_kozai_izsak_mean_elements_emits_payload_and_returns_mean_elements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, MEAN_ELEMENTS_RESPONSE)

    elements = orbits.kozai_izsak_mean_elements(sample_orbit())

    assert calls[0]["endpoint"] == "/OrbitConvert/GetKozaiIzsakMeanElements"
    assert_canonical_equal(calls[0]["json"], KEPLERIAN_WIRE)
    assert isinstance(elements, orbits.MeanKeplerianElements)
    assert_canonical_equal(
        mean_keplerian_snapshot(elements),
        MEAN_ELEMENTS_SNAPSHOT,
    )


def test_geo_ym_lambert_delta_v_emits_payload_and_returns_vector_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, [1.0, 2.0, 3.0, -1.0, -2.0, -3.0])

    delta_v = orbits.geo_ym_lambert_delta_v(
        platform_orbit=sample_orbit(),
        target_orbit=target_orbit(),
        time_of_flight_s=3600.0,
        platform_gravitational_parameter_m3_s2=EARTH_MU,
    )

    assert calls[0]["endpoint"] == "/OrbitConvert/CalGEOYMLambertDv"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "keplerPt": {**KEPLERIAN_WIRE, "GravitationalParameter": EARTH_MU},
            "keplerMb": TARGET_KEPLERIAN_WIRE,
            "tof": 3600.0,
        },
    )
    assert delta_v == ((1.0, 2.0, 3.0), (-1.0, -2.0, -3.0))


def test_geo_ym_lambert_delta_v_omits_platform_mu_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, [1.0, 2.0, 3.0, -1.0, -2.0, -3.0])

    orbits.geo_ym_lambert_delta_v(
        platform_orbit=sample_orbit(),
        target_orbit=target_orbit(),
        time_of_flight_s=3600.0,
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "keplerPt": KEPLERIAN_WIRE,
            "keplerMb": TARGET_KEPLERIAN_WIRE,
            "tof": 3600.0,
        },
    )


def test_lambert_delta_v_emits_single_case_payload_and_returns_vector_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(
        monkeypatch,
        {
            "IsSuccess": True,
            "Message": "",
            "DV1": [1.0, 2.0, 3.0],
            "DV2": [-1.0, -2.0, -3.0],
        },
    )
    arrival_state = orbits.cartesian_state(
        x_m=-4963330.5,
        y_m=4154175.2,
        z_m=1301603.0,
        vx_m_s=-5569.688,
        vy_m_s=-5716.8755,
        vz_m_s=323.9083,
    )

    delta_v = orbits.lambert_delta_v(
        departure_state=sample_cartesian_state(),
        arrival_state=arrival_state,
        time_of_flight_s=817.4257,
        gravitational_parameter_m3_s2=EARTH_MU,
    )

    assert calls[0]["endpoint"] == "/orbit/lambert"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "RV1": REPRESENTATIVE_CARTESIAN_RESPONSE,
            "RV2": [
                -4963330.5,
                4154175.2,
                1301603.0,
                -5569.688,
                -5716.8755,
                323.9083,
            ],
            "Gm": EARTH_MU,
            "TOF": [817.4257],
        },
    )
    assert delta_v == ((1.0, 2.0, 3.0), (-1.0, -2.0, -3.0))


def test_lambert_delta_v_omits_mu_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(
        monkeypatch,
        {
            "IsSuccess": True,
            "Message": "",
            "DV1": [1.0, 2.0, 3.0],
            "DV2": [-1.0, -2.0, -3.0],
        },
    )

    orbits.lambert_delta_v(
        departure_state=sample_cartesian_state(),
        arrival_state=sample_cartesian_state(),
        time_of_flight_s=817.4257,
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "RV1": REPRESENTATIVE_CARTESIAN_RESPONSE,
            "RV2": REPRESENTATIVE_CARTESIAN_RESPONSE,
            "TOF": [817.4257],
        },
    )


@pytest.mark.parametrize(
    ("function_name", "kwargs"),
    [
        ("keplerian_to_cartesian", {"orbit": [1, 0, 0, 0, 0, 0]}),
        ("cartesian_to_keplerian", {"state": [1, 2, 3, 4, 5, 6]}),
        (
            "lla_at_ascending_node",
            {"orbit": [1, 0, 0, 0, 0, 0], "orbit_epoch": "2024-01-01T00:00:00.000Z"},
        ),
        ("kozai_izsak_mean_elements", {"orbit": [1, 0, 0, 0, 0, 0]}),
        (
            "geo_ym_lambert_delta_v",
            {
                "platform_orbit": [1, 0, 0, 0, 0, 0],
                "target_orbit": target_orbit(),
                "time_of_flight_s": 3600.0,
            },
        ),
        (
            "geo_ym_lambert_delta_v",
            {
                "platform_orbit": sample_orbit(),
                "target_orbit": [1, 0, 0, 0, 0, 0],
                "time_of_flight_s": 3600.0,
            },
        ),
        (
            "lambert_delta_v",
            {
                "departure_state": [1, 2, 3, 4, 5, 6],
                "arrival_state": sample_cartesian_state(),
                "time_of_flight_s": 817.4257,
            },
        ),
        (
            "lambert_delta_v",
            {
                "departure_state": sample_cartesian_state(),
                "arrival_state": [1, 2, 3, 4, 5, 6],
                "time_of_flight_s": 817.4257,
            },
        ),
    ],
)
def test_conversion_functions_reject_raw_fragments(
    function_name: str,
    kwargs: dict[str, object],
) -> None:
    function = getattr(orbits, function_name)

    with pytest.raises(TypeError):
        function(**kwargs)


@pytest.mark.parametrize(
    "field",
    [
        "SemimajorAxis",
        "Eccentricity",
        "Inclination",
        "ArgumentOfPeriapsis",
        "RightAscensionOfAscendingNode",
        "TrueAnomaly",
    ],
)
def test_keplerian_response_parser_fails_loudly_for_missing_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    response = dict(REPRESENTATIVE_KEPLERIAN_RESPONSE)
    del response[field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        orbits.cartesian_to_keplerian(sample_cartesian_state())


@pytest.mark.parametrize("field", list(MEAN_ELEMENTS_RESPONSE))
def test_mean_elements_parser_fails_loudly_for_missing_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    response = dict(MEAN_ELEMENTS_RESPONSE)
    del response[field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        orbits.kozai_izsak_mean_elements(sample_orbit())


@pytest.mark.parametrize(
    ("function_name", "response", "kwargs"),
    [
        (
            "keplerian_to_cartesian",
            [1.0, 2.0, 3.0],
            {"orbit": sample_orbit()},
        ),
        (
            "lla_at_ascending_node",
            [1.0, 2.0],
            {"orbit": sample_orbit(), "orbit_epoch": "2024-01-01T00:00:00.000Z"},
        ),
        (
            "geo_ym_lambert_delta_v",
            [1.0, 2.0, 3.0],
            {
                "platform_orbit": sample_orbit(),
                "target_orbit": target_orbit(),
                "time_of_flight_s": 3600.0,
            },
        ),
        (
            "lambert_delta_v",
            {"DV1": [1.0, 2.0], "DV2": [-1.0, -2.0, -3.0]},
            {
                "departure_state": sample_cartesian_state(),
                "arrival_state": sample_cartesian_state(),
                "time_of_flight_s": 817.4257,
            },
        ),
    ],
)
def test_array_response_parsers_fail_loudly_for_short_arrays(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
    response: list[float],
    kwargs: dict[str, object],
) -> None:
    record_raw_post(monkeypatch, response)
    function = getattr(orbits, function_name)

    with pytest.raises(IndexError):
        function(**kwargs)


def test_conversion_functions_propagate_api_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        raise exceptions.AstroxAPIError("bad conversion", endpoint, response=None)

    monkeypatch.setattr(orbits.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError, match="bad conversion"):
        orbits.keplerian_to_cartesian(sample_orbit())


def test_lambert_delta_v_parser_fails_loudly_for_missing_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record_raw_post(
        monkeypatch,
        {"IsSuccess": True, "Message": "", "DV1": [1.0, 2.0, 3.0]},
    )

    with pytest.raises(KeyError):
        orbits.lambert_delta_v(
            departure_state=sample_cartesian_state(),
            arrival_state=sample_cartesian_state(),
            time_of_flight_s=817.4257,
        )


def test_conversion_return_type_hints_are_curated_values() -> None:
    assert get_type_hints(orbits.keplerian_to_cartesian)["return"] == orbits.CartesianState
    assert get_type_hints(orbits.cartesian_to_keplerian)["return"] == orbits.KeplerianElements
    assert get_type_hints(orbits.lla_at_ascending_node)["return"] == tuple[float, float, float]
    assert get_type_hints(orbits.kozai_izsak_mean_elements)["return"] == orbits.MeanKeplerianElements
    assert get_type_hints(orbits.geo_ym_lambert_delta_v)["return"] == tuple[
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    assert get_type_hints(orbits.lambert_delta_v)["return"] == tuple[
        tuple[float, float, float],
        tuple[float, float, float],
    ]
