"""Focused tests for curated J2 and two-body propagator functions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from typing import get_type_hints

import pytest

from astrox import exceptions, orbits, propagator
from tests.sdk.propagator.helpers import (
    J2_REQUEST,
    REPRESENTATIVE_PROPAGATOR_RESPONSE,
    REPRESENTATIVE_RETURN_SNAPSHOT,
    TWO_BODY_REQUEST,
    assert_canonical_equal,
    return_snapshot,
)


@pytest.fixture
def orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )


def test_propagator_position_constructs_from_nested_position_wire_payload() -> None:
    position = propagator.PropagatorPosition.from_wire(
        REPRESENTATIVE_PROPAGATOR_RESPONSE["Position"],
    )

    assert is_dataclass(position)
    assert [field.name for field in fields(propagator.PropagatorPosition)] == [
        "central_body",
        "epoch",
        "reference_frame",
        "interpolation_algorithm",
        "interpolation_degree",
        "cartesian_velocity",
    ]
    assert_canonical_equal(
        return_snapshot(600.0, position)["position"],
        REPRESENTATIVE_RETURN_SNAPSHOT["position"],
    )

    with pytest.raises(FrozenInstanceError):
        position.central_body = "Mars"


def test_j2_calls_raw_route_with_fixture_backed_payload(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return REPRESENTATIVE_PROPAGATOR_RESPONSE

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    period_s, position = propagator.j2(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        step_s=300.0,
        coord_system="Inertial",
        gravitational_parameter_m3_s2=398600441500000.0,
        j2_normalized_value=0.000484165143790815,
        ref_distance_m=6378137.0,
    )

    assert_canonical_equal(
        return_snapshot(period_s, position),
        REPRESENTATIVE_RETURN_SNAPSHOT,
    )
    assert calls[0]["endpoint"] == "/Propagator/J2"
    assert_canonical_equal(calls[0]["json"], J2_REQUEST)


def test_two_body_calls_raw_route_with_fixture_backed_payload(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return REPRESENTATIVE_PROPAGATOR_RESPONSE

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    period_s, position = propagator.two_body(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        step_s=300.0,
        coord_system="Inertial",
        gravitational_parameter_m3_s2=398600441500000.0,
    )

    assert_canonical_equal(
        return_snapshot(period_s, position),
        REPRESENTATIVE_RETURN_SNAPSHOT,
    )
    assert calls[0]["endpoint"] == "/Propagator/TwoBody"
    assert_canonical_equal(calls[0]["json"], TWO_BODY_REQUEST)


@pytest.mark.parametrize(
    "field_path",
    [
        ("Period",),
        ("Position",),
        ("Position", "CentralBody"),
        ("Position", "cartesianVelocity"),
        ("Position", "epoch"),
        ("Position", "interpolationAlgorithm"),
        ("Position", "interpolationDegree"),
        ("Position", "referenceFrame"),
    ],
)
def test_propagator_response_parser_fails_loudly_for_missing_required_fields(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
    field_path: tuple[str, ...],
) -> None:
    response = {
        **REPRESENTATIVE_PROPAGATOR_RESPONSE,
        "Position": dict(REPRESENTATIVE_PROPAGATOR_RESPONSE["Position"]),
    }
    current = response
    for field in field_path[:-1]:
        current = current[field]
    del current[field_path[-1]]

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        return response

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(KeyError):
        propagator.j2(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T00:10:00.000Z",
            orbit_epoch="2024-01-01T00:00:00.000Z",
            orbit=orbit,
        )


@pytest.mark.parametrize("function_name", ["j2", "two_body"])
def test_propagator_functions_reject_raw_orbit_fragments(
    function_name: str,
) -> None:
    function = getattr(propagator, function_name)

    with pytest.raises(TypeError):
        function(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T00:10:00.000Z",
            orbit_epoch="2024-01-01T00:00:00.000Z",
            orbit=[6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0],
        )


def test_j2_propagates_api_error_for_unsuccessful_raw_response(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        raise exceptions.AstroxAPIError("bad orbit", endpoint, response=None)

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError, match="bad orbit"):
        propagator.j2(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T00:10:00.000Z",
            orbit_epoch="2024-01-01T00:00:00.000Z",
            orbit=orbit,
        )


def test_curated_propagator_return_type_hints_are_success_path_values() -> None:
    j2_hints = get_type_hints(propagator.j2)
    two_body_hints = get_type_hints(propagator.two_body)

    assert j2_hints["return"] == tuple[float, propagator.PropagatorPosition]
    assert two_body_hints["return"] == tuple[float, propagator.PropagatorPosition]
