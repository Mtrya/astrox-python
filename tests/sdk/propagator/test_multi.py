"""Focused tests for curated batch propagator functions."""

from __future__ import annotations

from dataclasses import asdict
from typing import get_type_hints

import pytest

from astrox import exceptions, orbits, propagator
from tests.sdk.propagator.helpers import assert_canonical_equal


TARGET_EPOCH = "2024-01-01T00:10:00.000Z"
ORBIT_EPOCH_A = "2024-01-01T00:00:00.000Z"
ORBIT_EPOCH_B = "2024-01-01T00:03:00.000Z"
EARTH_MU = 398600441500000.0
TLE_A = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
TLE_B = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)

REPRESENTATIVE_BATCH_RESPONSE = {
    "IsSuccess": True,
    "Message": "Success",
    "AllElementsAtEpoch": [
        {
            "SemimajorAxis": 6778137.0,
            "Eccentricity": 0.001,
            "Inclination": 28.5,
            "ArgumentOfPeriapsis": 0.1,
            "RightAscensionOfAscendingNode": 359.9,
            "TrueAnomaly": 39.0,
            "GravitationalParameter": 398600441800000.0,
        },
        {
            "SemimajorAxis": 7078137.0,
            "Eccentricity": 0.002,
            "Inclination": 51.6,
            "ArgumentOfPeriapsis": 1.2,
            "RightAscensionOfAscendingNode": 120.0,
            "TrueAnomaly": 42.0,
            "GravitationalParameter": 398600441800000.0,
        },
    ],
}


@pytest.fixture
def orbit_a() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )


@pytest.fixture
def orbit_b() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=7078137.0,
        eccentricity=0.002,
        inclination_deg=51.6,
        argument_of_periapsis_deg=10.0,
        raan_deg=120.0,
        true_anomaly_deg=5.0,
    )


def record_batch_post(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    if response is None:
        response = REPRESENTATIVE_BATCH_RESPONSE
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(propagator.raw, "post", fake_post)
    return calls


def batch_snapshot(elements: tuple[orbits.KeplerianElements, ...]) -> list[dict[str, object]]:
    return [asdict(element) for element in elements]


def test_multi_two_body_emits_representative_payload_and_returns_keplerian_tuple(
    monkeypatch: pytest.MonkeyPatch,
    orbit_a: orbits.KeplerianElements,
    orbit_b: orbits.KeplerianElements,
) -> None:
    calls = record_batch_post(monkeypatch)

    elements = propagator.multi_two_body(
        epoch=TARGET_EPOCH,
        gravitational_parameter_m3_s2=EARTH_MU,
        states=[
            (ORBIT_EPOCH_A, orbit_a),
            [ORBIT_EPOCH_B, orbit_b],
        ],
    )

    assert calls[0]["endpoint"] == "/Propagator/MultiTwoBody"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Epoch": TARGET_EPOCH,
            "AllSateElements": [
                {
                    "OrbitEpoch": ORBIT_EPOCH_A,
                    "SemimajorAxis": 6778137.0,
                    "Eccentricity": 0.001,
                    "Inclination": 28.5,
                    "ArgumentOfPeriapsis": 0.0,
                    "RightAscensionOfAscendingNode": 0.0,
                    "TrueAnomaly": 0.0,
                    "GravitationalParameter": EARTH_MU,
                },
                {
                    "OrbitEpoch": ORBIT_EPOCH_B,
                    "SemimajorAxis": 7078137.0,
                    "Eccentricity": 0.002,
                    "Inclination": 51.6,
                    "ArgumentOfPeriapsis": 10.0,
                    "RightAscensionOfAscendingNode": 120.0,
                    "TrueAnomaly": 5.0,
                    "GravitationalParameter": EARTH_MU,
                },
            ],
        },
    )
    assert isinstance(elements, tuple)
    assert all(isinstance(element, orbits.KeplerianElements) for element in elements)
    assert_canonical_equal(
        batch_snapshot(elements),
        [
            {
                "semi_major_axis_m": 6778137.0,
                "eccentricity": 0.001,
                "inclination_deg": 28.5,
                "argument_of_periapsis_deg": 0.1,
                "raan_deg": 359.9,
                "true_anomaly_deg": 39.0,
            },
            {
                "semi_major_axis_m": 7078137.0,
                "eccentricity": 0.002,
                "inclination_deg": 51.6,
                "argument_of_periapsis_deg": 1.2,
                "raan_deg": 120.0,
                "true_anomaly_deg": 42.0,
            },
        ],
    )
    assert "gravitational_parameter_m3_s2" not in asdict(elements[0])


def test_multi_j2_omits_j2_knobs_and_server_owned_mu_when_not_provided(
    monkeypatch: pytest.MonkeyPatch,
    orbit_a: orbits.KeplerianElements,
) -> None:
    calls = record_batch_post(monkeypatch)

    propagator.multi_j2(
        epoch=TARGET_EPOCH,
        states=[(ORBIT_EPOCH_A, orbit_a)],
    )

    assert calls[0]["endpoint"] == "/Propagator/MultiJ2"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Epoch": TARGET_EPOCH,
            "AllSateElements": [
                {
                    "OrbitEpoch": ORBIT_EPOCH_A,
                    "SemimajorAxis": 6778137.0,
                    "Eccentricity": 0.001,
                    "Inclination": 28.5,
                    "ArgumentOfPeriapsis": 0.0,
                    "RightAscensionOfAscendingNode": 0.0,
                    "TrueAnomaly": 0.0,
                }
            ],
        },
    )


def test_multi_sgp4_emits_newline_joined_tle_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_batch_post(monkeypatch)

    propagator.multi_sgp4(
        epoch=TARGET_EPOCH,
        tle_sets=[
            TLE_A,
            list(TLE_B),
        ],
    )

    assert calls[0]["endpoint"] == "/Propagator/MultiSgp4"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Epoch": TARGET_EPOCH,
            "TLEs": [
                "\n".join(TLE_A),
                "\n".join(TLE_B),
            ],
        },
    )


@pytest.mark.parametrize(
    ("function_name", "kwargs"),
    [
        ("multi_two_body", {"states": []}),
        ("multi_j2", {"states": []}),
        ("multi_sgp4", {"tle_sets": []}),
    ],
)
def test_multi_propagators_preserve_empty_batch_success_path(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
    kwargs: dict[str, object],
) -> None:
    calls = record_batch_post(
        monkeypatch,
        response={"IsSuccess": True, "Message": "Success", "AllElementsAtEpoch": []},
    )
    function = getattr(propagator, function_name)

    assert function(epoch=TARGET_EPOCH, **kwargs) == ()
    assert calls[0]["json"] in [
        {"Epoch": TARGET_EPOCH, "AllSateElements": []},
        {"Epoch": TARGET_EPOCH, "TLEs": []},
    ]


@pytest.mark.parametrize(
    "states",
    [
        [
            orbits.keplerian(
                semi_major_axis_m=1,
                eccentricity=0,
                inclination_deg=0,
                argument_of_periapsis_deg=0,
                raan_deg=0,
                true_anomaly_deg=0,
            )
        ],
        [(ORBIT_EPOCH_A, [6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0])],
        [
            (
                123,
                orbits.keplerian(
                    semi_major_axis_m=1,
                    eccentricity=0,
                    inclination_deg=0,
                    argument_of_periapsis_deg=0,
                    raan_deg=0,
                    true_anomaly_deg=0,
                ),
            )
        ],
        "not-states",
    ],
)
def test_multi_state_propagators_reject_malformed_state_items(states: object) -> None:
    with pytest.raises(TypeError):
        propagator.multi_two_body(epoch=TARGET_EPOCH, states=states)


@pytest.mark.parametrize(
    "tle_sets",
    [
        ["line1\nline2"],
        [(TLE_A[0],)],
        [(TLE_A[0], TLE_A[1], "extra")],
        [(TLE_A[0], 123)],
        "not-tle-sets",
    ],
)
def test_multi_sgp4_rejects_malformed_tle_set_items(tle_sets: object) -> None:
    with pytest.raises(TypeError):
        propagator.multi_sgp4(epoch=TARGET_EPOCH, tle_sets=tle_sets)


@pytest.mark.parametrize(
    "field_path",
    [
        ("AllElementsAtEpoch",),
        ("AllElementsAtEpoch", 0, "SemimajorAxis"),
        ("AllElementsAtEpoch", 0, "Eccentricity"),
        ("AllElementsAtEpoch", 0, "Inclination"),
        ("AllElementsAtEpoch", 0, "ArgumentOfPeriapsis"),
        ("AllElementsAtEpoch", 0, "RightAscensionOfAscendingNode"),
        ("AllElementsAtEpoch", 0, "TrueAnomaly"),
    ],
)
def test_multi_propagator_parser_fails_loudly_for_missing_required_fields(
    monkeypatch: pytest.MonkeyPatch,
    orbit_a: orbits.KeplerianElements,
    field_path: tuple[str | int, ...],
) -> None:
    response = {
        **REPRESENTATIVE_BATCH_RESPONSE,
        "AllElementsAtEpoch": [
            dict(REPRESENTATIVE_BATCH_RESPONSE["AllElementsAtEpoch"][0]),
        ],
    }
    current = response
    for field in field_path[:-1]:
        current = current[field]
    del current[field_path[-1]]

    record_batch_post(monkeypatch, response=response)

    with pytest.raises(KeyError):
        propagator.multi_two_body(
            epoch=TARGET_EPOCH,
            states=[(ORBIT_EPOCH_A, orbit_a)],
        )


def test_multi_propagators_propagate_api_errors(
    monkeypatch: pytest.MonkeyPatch,
    orbit_a: orbits.KeplerianElements,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        raise exceptions.AstroxAPIError("bad batch", endpoint, response=None)

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError, match="bad batch"):
        propagator.multi_two_body(
            epoch=TARGET_EPOCH,
            states=[(ORBIT_EPOCH_A, orbit_a)],
        )


def test_multi_propagator_return_type_hints_are_keplerian_tuples() -> None:
    assert get_type_hints(propagator.multi_two_body)["return"] == tuple[
        orbits.KeplerianElements, ...
    ]
    assert get_type_hints(propagator.multi_j2)["return"] == tuple[
        orbits.KeplerianElements, ...
    ]
    assert get_type_hints(propagator.multi_sgp4)["return"] == tuple[
        orbits.KeplerianElements, ...
    ]
