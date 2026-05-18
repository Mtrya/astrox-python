"""Focused tests for PR 02 J2 and two-body propagator functions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from typing import get_type_hints

import pytest

from astrox import orbits, propagator


PROPAGATOR_RESPONSE = {
    "IsSuccess": True,
    "Message": "",
    "Period": 600.0,
    "Position": {
        "CentralBody": "Earth",
        "cartesianVelocity": [0.0, 1.0, 2.0, 3.0],
        "epoch": "2024-01-01T00:00:00.000Z",
        "interpolationAlgorithm": "Lagrange",
        "interpolationDegree": 5,
        "referenceFrame": "Inertial",
    },
}


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
    position = propagator.PropagatorPosition.from_wire(PROPAGATOR_RESPONSE["Position"])

    assert is_dataclass(position)
    assert [field.name for field in fields(propagator.PropagatorPosition)] == [
        "central_body",
        "epoch",
        "reference_frame",
        "interpolation_algorithm",
        "interpolation_degree",
        "cartesian_velocity",
    ]
    assert position.central_body == "Earth"
    assert position.epoch == "2024-01-01T00:00:00.000Z"
    assert position.reference_frame == "Inertial"
    assert position.interpolation_algorithm == "Lagrange"
    assert position.interpolation_degree == 5
    assert position.cartesian_velocity == (0.0, 1.0, 2.0, 3.0)

    with pytest.raises(FrozenInstanceError):
        position.central_body = "Mars"


def test_j2_calls_raw_route_with_fixture_backed_payload(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return PROPAGATOR_RESPONSE

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

    assert period_s == 600.0
    assert isinstance(position, propagator.PropagatorPosition)
    assert calls == [
        {
            "endpoint": "/Propagator/J2",
            "json": {
                "Start": "2024-01-01T00:00:00.000Z",
                "Stop": "2024-01-01T00:10:00.000Z",
                "Step": 300.0,
                "OrbitEpoch": "2024-01-01T00:00:00.000Z",
                "CoordSystem": "Inertial",
                "CoordType": "Classical",
                "J2NormalizedValue": 0.000484165143790815,
                "RefDistance": 6378137.0,
                "GravitationalParameter": 398600441500000.0,
                "OrbitalElements": orbit.to_wire(),
            },
        }
    ]


def test_two_body_calls_raw_route_and_includes_only_supplied_options(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return PROPAGATOR_RESPONSE

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    propagator.two_body(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        gravitational_parameter_m3_s2=398600441500000.0,
    )

    assert calls == [
        {
            "endpoint": "/Propagator/TwoBody",
            "json": {
                "Start": "2024-01-01T00:00:00.000Z",
                "Stop": "2024-01-01T00:10:00.000Z",
                "OrbitEpoch": "2024-01-01T00:00:00.000Z",
                "CoordType": "Classical",
                "GravitationalParameter": 398600441500000.0,
                "OrbitalElements": orbit.to_wire(),
            },
        }
    ]


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


def test_j2_raises_value_error_for_unsuccessful_raw_response(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        return {
            "IsSuccess": False,
            "Message": "bad orbit",
            "Period": 0.0,
            "Position": {},
        }

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(ValueError, match="bad orbit"):
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
