"""Focused tests for curated orbit wizard functions."""

from __future__ import annotations

from typing import get_type_hints

import pytest

from astrox import exceptions, orbits
from tests.sdk.orbits.helpers import (
    KEPLERIAN_WIRE,
    REPRESENTATIVE_WALKER_RESPONSE,
    REPRESENTATIVE_WALKER_SNAPSHOT,
    REPRESENTATIVE_WIZARD_RESPONSE,
    REPRESENTATIVE_WIZARD_SNAPSHOT,
    assert_canonical_equal,
    keplerian_snapshot,
    record_raw_post,
    sample_orbit,
    walker_snapshot,
)


def wizard_snapshot(
    pair: tuple[orbits.KeplerianElements, orbits.KeplerianElements],
) -> list[dict[str, object]]:
    return [keplerian_snapshot(pair[0]), keplerian_snapshot(pair[1])]


def test_geo_emits_payload_and_returns_tod_inertial_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_WIZARD_RESPONSE)

    pair = orbits.geo(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        inclination_deg=10.0,
        subsatellite_longitude_deg=120.0,
    )

    assert calls[0]["endpoint"] == "/OrbitWizard/GEO"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "OrbitEpoch": "2024-01-01T00:00:00.000Z",
            "Inclination": 10.0,
            "SubSatellitePoint": 120.0,
        },
    )
    assert isinstance(pair, tuple)
    assert all(isinstance(item, orbits.KeplerianElements) for item in pair)
    assert_canonical_equal(wizard_snapshot(pair), REPRESENTATIVE_WIZARD_SNAPSHOT)


def test_molniya_emits_payload_and_returns_tod_inertial_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_WIZARD_RESPONSE)

    pair = orbits.molniya(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        perigee_altitude_km=600.0,
        apogee_longitude_deg=100.0,
        argument_of_periapsis_deg=270.0,
    )

    assert calls[0]["endpoint"] == "/OrbitWizard/Molniya"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "OrbitEpoch": "2024-01-01T00:00:00.000Z",
            "PerigeeAltitude": 600.0,
            "ApogeeLongitude": 100.0,
            "ArgumentOfPeriapsis": 270.0,
        },
    )
    assert_canonical_equal(wizard_snapshot(pair), REPRESENTATIVE_WIZARD_SNAPSHOT)


def test_sso_emits_payload_and_returns_tod_inertial_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_WIZARD_RESPONSE)

    pair = orbits.sso(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        altitude_km=600.0,
        local_time_of_descending_node_hours=14.5,
    )

    assert calls[0]["endpoint"] == "/OrbitWizard/SSO"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "OrbitEpoch": "2024-01-01T00:00:00.000Z",
            "Altitude": 600.0,
            "LocalTimeOfDescendingNode": 14.5,
        },
    )
    assert_canonical_equal(wizard_snapshot(pair), REPRESENTATIVE_WIZARD_SNAPSHOT)


def test_walker_delta_emits_payload_and_returns_nested_keplerian_tuples(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_WALKER_RESPONSE)

    walker = orbits.walker_delta(
        seed_orbit=sample_orbit(),
        num_planes=3,
        num_sats_per_plane=2,
        inter_plane_phase_increment=1,
    )

    assert calls[0]["endpoint"] == "/OrbitWizard/Walker"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "SeedKepler": KEPLERIAN_WIRE,
            "WalkerType": "Delta",
            "NumPlanes": 3,
            "NumSatsPerPlane": 2,
            "InterPlanePhaseIncrement": 1,
        },
    )
    assert isinstance(walker, tuple)
    assert all(isinstance(plane, tuple) for plane in walker)
    assert all(
        isinstance(satellite, orbits.KeplerianElements)
        for plane in walker
        for satellite in plane
    )
    assert_canonical_equal(walker_snapshot(walker), REPRESENTATIVE_WALKER_SNAPSHOT)


def test_walker_star_omits_phase_increment_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_WALKER_RESPONSE)

    orbits.walker_star(
        seed_orbit=sample_orbit(),
        num_planes=3,
        num_sats_per_plane=2,
    )

    assert calls[0]["endpoint"] == "/OrbitWizard/Walker"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "SeedKepler": KEPLERIAN_WIRE,
            "WalkerType": "Star",
            "NumPlanes": 3,
            "NumSatsPerPlane": 2,
        },
    )


def test_walker_custom_emits_custom_branch_increments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, REPRESENTATIVE_WALKER_RESPONSE)

    orbits.walker_custom(
        seed_orbit=sample_orbit(),
        num_planes=3,
        num_sats_per_plane=2,
        inter_plane_true_anomaly_increment_deg=30.0,
        raan_increment_deg=60.0,
    )

    assert calls[0]["endpoint"] == "/OrbitWizard/Walker"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "SeedKepler": KEPLERIAN_WIRE,
            "WalkerType": "Custom",
            "NumPlanes": 3,
            "NumSatsPerPlane": 2,
            "InterPlaneTrueAnomalyIncrement": 30.0,
            "RAANIncrement": 60.0,
        },
    )


@pytest.mark.parametrize(
    "function_name",
    ["walker_delta", "walker_star", "walker_custom"],
)
def test_walker_functions_reject_raw_seed_orbit_fragments(function_name: str) -> None:
    function = getattr(orbits, function_name)

    with pytest.raises(TypeError):
        function(
            seed_orbit=[6778137.0, 0.001, 28.5, 0.0, 15.0, 45.0],
            num_planes=3,
            num_sats_per_plane=2,
        )


@pytest.mark.parametrize(
    ("function_name", "kwargs", "missing_field"),
    [
        (
            "geo",
            {
                "orbit_epoch": "2024-01-01T00:00:00.000Z",
                "inclination_deg": 10.0,
                "subsatellite_longitude_deg": 120.0,
            },
            "Elements_TOD",
        ),
        (
            "molniya",
            {
                "orbit_epoch": "2024-01-01T00:00:00.000Z",
                "perigee_altitude_km": 600.0,
                "apogee_longitude_deg": 100.0,
                "argument_of_periapsis_deg": 270.0,
            },
            "Elements_Inertial",
        ),
        (
            "sso",
            {
                "orbit_epoch": "2024-01-01T00:00:00.000Z",
                "altitude_km": 600.0,
                "local_time_of_descending_node_hours": 14.5,
            },
            "Elements_TOD",
        ),
    ],
)
def test_wizard_pair_parser_fails_loudly_for_missing_top_level_fields(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
    kwargs: dict[str, object],
    missing_field: str,
) -> None:
    response = dict(REPRESENTATIVE_WIZARD_RESPONSE)
    del response[missing_field]
    record_raw_post(monkeypatch, response)
    function = getattr(orbits, function_name)

    with pytest.raises(KeyError):
        function(**kwargs)


def test_wizard_pair_parser_fails_loudly_for_missing_nested_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = {
        **REPRESENTATIVE_WIZARD_RESPONSE,
        "Elements_TOD": dict(REPRESENTATIVE_WIZARD_RESPONSE["Elements_TOD"]),
    }
    del response["Elements_TOD"]["TrueAnomaly"]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        orbits.geo(
            orbit_epoch="2024-01-01T00:00:00.000Z",
            inclination_deg=10.0,
            subsatellite_longitude_deg=120.0,
        )


@pytest.mark.parametrize(
    "field_path",
    [
        ("WalkerSatellites",),
        ("WalkerSatellites", 0, 0, "SemimajorAxis"),
        ("WalkerSatellites", 0, 0, "Eccentricity"),
        ("WalkerSatellites", 0, 0, "Inclination"),
        ("WalkerSatellites", 0, 0, "ArgumentOfPeriapsis"),
        ("WalkerSatellites", 0, 0, "RightAscensionOfAscendingNode"),
        ("WalkerSatellites", 0, 0, "TrueAnomaly"),
    ],
)
def test_walker_parser_fails_loudly_for_missing_required_fields(
    monkeypatch: pytest.MonkeyPatch,
    field_path: tuple[str | int, ...],
) -> None:
    response = {
        **REPRESENTATIVE_WALKER_RESPONSE,
        "WalkerSatellites": [
            [dict(REPRESENTATIVE_WALKER_RESPONSE["WalkerSatellites"][0][0])]
        ],
    }
    current = response
    for field in field_path[:-1]:
        current = current[field]
    del current[field_path[-1]]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        orbits.walker_delta(
            seed_orbit=sample_orbit(),
            num_planes=3,
            num_sats_per_plane=2,
        )


def test_wizard_functions_propagate_api_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        raise exceptions.AstroxAPIError("bad wizard", endpoint, response=None)

    monkeypatch.setattr(orbits.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError, match="bad wizard"):
        orbits.geo(
            orbit_epoch="2024-01-01T00:00:00.000Z",
            inclination_deg=10.0,
            subsatellite_longitude_deg=120.0,
        )


def test_wizard_return_type_hints_are_curated_values() -> None:
    assert get_type_hints(orbits.geo)["return"] == tuple[
        orbits.KeplerianElements,
        orbits.KeplerianElements,
    ]
    assert get_type_hints(orbits.molniya)["return"] == tuple[
        orbits.KeplerianElements,
        orbits.KeplerianElements,
    ]
    assert get_type_hints(orbits.sso)["return"] == tuple[
        orbits.KeplerianElements,
        orbits.KeplerianElements,
    ]
    assert get_type_hints(orbits.walker_delta)["return"] == tuple[
        tuple[orbits.KeplerianElements, ...],
        ...,
    ]
    assert get_type_hints(orbits.walker_star)["return"] == tuple[
        tuple[orbits.KeplerianElements, ...],
        ...,
    ]
    assert get_type_hints(orbits.walker_custom)["return"] == tuple[
        tuple[orbits.KeplerianElements, ...],
        ...,
    ]
