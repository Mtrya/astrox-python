"""Behavior tests for OrbitSystem frame and libration functions."""

from __future__ import annotations

from typing import Any, get_type_hints

import pytest

from astrox import entities, exceptions, orbits


EPOCH = "2024-01-01T00:00:00.000Z"


def sample_czml_position() -> entities.CzmlPosition:
    return entities.czml_position(
        epoch=EPOCH,
        central_body="Earth",
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=[0.0, 7000000.0, 0.0, 0.0],
    )


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def fake_post(
        endpoint: str,
        *,
        json: object,
        params: dict[str, Any] | None = None,
    ) -> object:
        calls.append({"endpoint": endpoint, "json": json, "params": params})
        return response

    monkeypatch.setattr(orbits.raw, "post", fake_post)
    return calls


def central_body_frame_response() -> dict[str, Any]:
    return {
        "IsSuccess": True,
        "Message": "",
        "Period": 6000.0,
        "Position": {
            "epoch": EPOCH,
            "CentralBody": "Earth",
            "referenceFrame": "FIXED",
            "interpolationAlgorithm": "LAGRANGE",
            "interpolationDegree": 7,
            "cartesian": [0.0, 7000000.0, 0.0, 0.0],
        },
    }


def libration_response() -> dict[str, Any]:
    return {
        "IsSuccess": True,
        "Message": "",
        "position": {
            "epoch": EPOCH,
            "CentralBody": "Moon",
            "referenceFrame": "Libration",
            "interpolationAlgorithm": "LAGRANGE",
            "interpolationDegree": 7,
            "cartesian": [0.0, 1.0, 2.0, 3.0],
            "unitQuaternion": [0.0, 0.0, 0.0, 1.0],
        },
    }


def test_central_body_frame_emits_payload_and_returns_position(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, central_body_frame_response())
    position = sample_czml_position()

    period_s, out_position = orbits.central_body_frame(
        position,
        to_central_body="Moon",
        target_reference_frame="J2000",
    )

    assert calls[0]["endpoint"] == "/OrbitSystem/CentralBodyFrame"
    assert calls[0]["json"] == position.to_czml_wire()
    assert calls[0]["params"] == {
        "toCb": "Moon",
        "referenceFrame": "J2000",
    }
    assert period_s == 6000.0
    assert isinstance(out_position, entities.CzmlPosition)
    assert out_position.epoch == EPOCH
    assert out_position.reference_frame == "FIXED"
    assert out_position.cartesian == (0.0, 7000000.0, 0.0, 0.0)


def test_central_body_frame_omits_reference_frame_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, central_body_frame_response())

    orbits.central_body_frame(sample_czml_position(), to_central_body="Moon")

    assert calls[0]["params"] == {"toCb": "Moon"}


def test_earth_moon_libration_emits_payload_and_returns_stm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, libration_response())
    position = sample_czml_position()

    state = orbits.earth_moon_libration(position)

    assert calls[0]["endpoint"] == "/OrbitSystem/EarthMoonLibration2"
    assert calls[0]["json"] == position.to_czml_wire()
    assert calls[0]["params"] is None
    assert isinstance(state, entities.CzmlPositionSTM)
    assert state.epoch == EPOCH
    assert state.reference_frame == "Libration"
    assert state.cartesian == (0.0, 1.0, 2.0, 3.0)
    assert state.unit_quaternion == (0.0, 0.0, 0.0, 1.0)
    assert state.cartesian_translation is None


@pytest.mark.parametrize(
    ("function_name", "kwargs"),
    [
        (
            "central_body_frame",
            {"position": [0.0, 7000000.0, 0.0, 0.0], "to_central_body": "Moon"},
        ),
        (
            "earth_moon_libration",
            {"position": [0.0, 7000000.0, 0.0, 0.0]},
        ),
    ],
)
def test_orbit_system_functions_reject_raw_fragments(
    function_name: str,
    kwargs: dict[str, object],
) -> None:
    function = getattr(orbits, function_name)

    with pytest.raises(TypeError):
        function(**kwargs)


@pytest.mark.parametrize(
    "missing_field",
    ["epoch", "cartesian"],
)
def test_central_body_frame_parser_fails_loudly_for_missing_position_fields(
    monkeypatch: pytest.MonkeyPatch,
    missing_field: str,
) -> None:
    response = central_body_frame_response()
    del response["Position"][missing_field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        orbits.central_body_frame(
            sample_czml_position(),
            to_central_body="Moon",
        )


@pytest.mark.parametrize(
    "missing_field",
    ["epoch", "referenceFrame", "cartesian", "unitQuaternion"],
)
def test_earth_moon_libration_parser_fails_loudly_for_missing_stm_fields(
    monkeypatch: pytest.MonkeyPatch,
    missing_field: str,
) -> None:
    response = libration_response()
    del response["position"][missing_field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        orbits.earth_moon_libration(sample_czml_position())


def test_orbit_system_functions_propagate_api_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(endpoint: str, *, json: object, params: object = None) -> object:
        raise exceptions.AstroxAPIError("bad frame", endpoint, response=None)

    monkeypatch.setattr(orbits.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError, match="bad frame"):
        orbits.central_body_frame(sample_czml_position(), to_central_body="Moon")

    with pytest.raises(exceptions.AstroxAPIError, match="bad frame"):
        orbits.earth_moon_libration(sample_czml_position())


def test_orbit_system_return_type_hints_are_curated_values() -> None:
    assert get_type_hints(orbits.central_body_frame)["return"] == tuple[
        float,
        entities.CzmlPosition,
    ]
    assert get_type_hints(orbits.earth_moon_libration)["return"] == entities.CzmlPositionSTM
