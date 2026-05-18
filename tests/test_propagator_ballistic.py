"""Focused tests for PR 02 ballistic propagator functions."""

from __future__ import annotations

from inspect import signature
from typing import Callable, get_type_hints

import pytest

from astrox import propagator


PROPAGATOR_RESPONSE = {
    "IsSuccess": True,
    "Message": "",
    "Period": 600.0,
    "Position": {
        "CentralBody": "Earth",
        "cartesianVelocity": [0.0, 1.0, 2.0, 3.0],
        "epoch": "2024-01-01T12:00:00.000Z",
        "interpolationAlgorithm": "Lagrange",
        "interpolationDegree": 5,
        "referenceFrame": "Fixed",
    },
}


NOMINAL_PAYLOAD = {
    "Start": "2024-01-01T12:00:00.000Z",
    "Step": 30.0,
    "LaunchLatitude": 28.5721,
    "LaunchLongitude": -80.648,
    "LaunchAltitude": 10.0,
    "ImpactLatitude": 30.0,
    "ImpactLongitude": -70.0,
    "ImpactAltitude": 0.0,
}


def record_raw_post(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return PROPAGATOR_RESPONSE

    monkeypatch.setattr(propagator.raw, "post", fake_post)
    return calls


def assert_success_path_return(
    period_s: float,
    position: propagator.PropagatorPosition,
) -> None:
    assert period_s == 600.0
    assert isinstance(position, propagator.PropagatorPosition)
    assert position.central_body == "Earth"
    assert position.reference_frame == "Fixed"
    assert position.cartesian_velocity == (0.0, 1.0, 2.0, 3.0)


def test_ballistic_nominal_matches_verified_fixture_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch)

    period_s, position = propagator.ballistic(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude_deg=30.0,
        impact_longitude_deg=-70.0,
        step_s=30.0,
        launch_latitude_deg=28.5721,
        launch_longitude_deg=-80.648,
        launch_altitude_m=10.0,
        impact_altitude_m=0.0,
    )

    assert_success_path_return(period_s, position)
    assert calls == [
        {
            "endpoint": "/Propagator/Ballistic",
            "json": NOMINAL_PAYLOAD,
        }
    ]


@pytest.mark.parametrize(
    ("function", "value_kwarg", "value", "wire_type"),
    [
        (propagator.ballistic_delta_v, "delta_v_m_s", 3000.0, "DeltaV"),
        (
            propagator.ballistic_delta_v_min_ecc,
            "delta_v_m_s",
            3000.0,
            "DeltaV_MinEcc",
        ),
        (
            propagator.ballistic_apogee_altitude,
            "apogee_altitude_m",
            200000.0,
            "ApogeeAlt",
        ),
        (
            propagator.ballistic_time_of_flight,
            "time_of_flight_s",
            600.0,
            "TimeOfFlight",
        ),
    ],
)
def test_ballistic_branch_functions_match_verified_fixture_payloads(
    monkeypatch: pytest.MonkeyPatch,
    function: Callable[..., tuple[float, propagator.PropagatorPosition]],
    value_kwarg: str,
    value: float,
    wire_type: str,
) -> None:
    calls = record_raw_post(monkeypatch)

    period_s, position = function(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude_deg=30.0,
        impact_longitude_deg=-70.0,
        step_s=30.0,
        launch_latitude_deg=28.5721,
        launch_longitude_deg=-80.648,
        launch_altitude_m=10.0,
        impact_altitude_m=0.0,
        **{value_kwarg: value},
    )

    assert_success_path_return(period_s, position)
    assert calls == [
        {
            "endpoint": "/Propagator/Ballistic",
            "json": {
                **NOMINAL_PAYLOAD,
                "BallisticType": wire_type,
                "BallisticTypeValue": value,
            },
        }
    ]


def test_ballistic_omits_server_owned_optional_knobs_when_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch)

    propagator.ballistic(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude_deg=30.0,
        impact_longitude_deg=-70.0,
    )

    assert calls == [
        {
            "endpoint": "/Propagator/Ballistic",
            "json": {
                "Start": "2024-01-01T12:00:00.000Z",
                "ImpactLatitude": 30.0,
                "ImpactLongitude": -70.0,
            },
        }
    ]


def test_ballistic_delta_v_includes_only_explicit_supplied_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch)

    propagator.ballistic_delta_v(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude_deg=30.0,
        impact_longitude_deg=-70.0,
        delta_v_m_s=3000.0,
        central_body="Earth",
        gravitational_parameter_m3_s2=398600441500000.0,
    )

    assert calls == [
        {
            "endpoint": "/Propagator/Ballistic",
            "json": {
                "Start": "2024-01-01T12:00:00.000Z",
                "ImpactLatitude": 30.0,
                "ImpactLongitude": -70.0,
                "BallisticType": "DeltaV",
                "BallisticTypeValue": 3000.0,
                "CentralBody": "Earth",
                "GravitationalParameter": 398600441500000.0,
            },
        }
    ]


def test_ballistic_functions_do_not_expose_mode_arguments() -> None:
    functions = [
        propagator.ballistic,
        propagator.ballistic_delta_v,
        propagator.ballistic_delta_v_min_ecc,
        propagator.ballistic_apogee_altitude,
        propagator.ballistic_time_of_flight,
    ]

    for function in functions:
        parameters = signature(function).parameters
        assert "mode" not in parameters
        assert "mode_value" not in parameters
        assert "ballistic_type" not in parameters
        assert "ballistic_type_value" not in parameters


def test_ballistic_raises_value_error_for_unsuccessful_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        return {
            "IsSuccess": False,
            "Message": "bad ballistic branch",
            "Period": 0.0,
            "Position": {},
        }

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(ValueError, match="bad ballistic branch"):
        propagator.ballistic(
            start="2024-01-01T12:00:00.000Z",
            impact_latitude_deg=30.0,
            impact_longitude_deg=-70.0,
        )


def test_ballistic_return_type_hints_are_success_path_values() -> None:
    functions = [
        propagator.ballistic,
        propagator.ballistic_delta_v,
        propagator.ballistic_delta_v_min_ecc,
        propagator.ballistic_apogee_altitude,
        propagator.ballistic_time_of_flight,
    ]

    for function in functions:
        assert get_type_hints(function)["return"] == tuple[
            float, propagator.PropagatorPosition
        ]
