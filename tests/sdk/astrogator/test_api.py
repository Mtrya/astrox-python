"""Behavior tests for the public Astrogator RunMCS endpoint."""

from __future__ import annotations

import pytest

from astrox import astrogator, exceptions, propagator
from astrox.astrogator import _api
from tests.sdk.helpers import assert_canonical_equal


MU = 3.986004415e14


def _initial() -> astrogator.InitialStateSegment:
    return astrogator.initial_state(
        "Init",
        astrogator.cartesian_state(
            x_m=1.0, y_m=2.0, z_m=3.0, vx_m_s=4.0, vy_m_s=5.0, vz_m_s=6.0
        ),
        epoch="2026-01-01T00:00:00Z",
    )


def test_run_mcs_lowers_top_level_and_returns_curated_parser_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    sentinel = object()

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return {"wire": "response"}

    monkeypatch.setattr(_api.raw, "post", fake_post)
    monkeypatch.setattr(_api, "run_mcs_result_from_wire", lambda value: sentinel)

    result = astrogator.run_mcs(
        [_initial()],
        central_body="Earth",
        out_czml_frame_name="FIXED",
        compute_czml_positions=True,
        text="mission text",
        engine_models=[
            astrogator.constant_engine(
                name="EngineA", thrust_n=500.0, isp_s=600.0
            )
        ],
    )

    assert result is sentinel
    assert calls[0]["endpoint"] == "/Astrogator/RunMCS"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "$type": "AstrogatorMCS",
            "CentralBody": "Earth",
            "OutCzmlFrameName": "FIXED",
            "MainSequence": [_initial().to_wire()],
            "ComputeCzmlPositions": True,
            "Text": "mission text",
            "EngineModels": [
                {
                    "$type": "EngineConstant",
                    "Name": "EngineA",
                    "Thrust": 500.0,
                    "Isp": 600.0,
                    "g": 9.80665,
                }
            ],
        },
    )


def test_run_mcs_lowers_entities_and_custom_propagators(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append(json)
        return {"wire": "response"}

    monkeypatch.setattr(_api.raw, "post", fake_post)
    monkeypatch.setattr(_api, "run_mcs_result_from_wire", lambda value: value)

    mission = astrogator.mission_position(main_sequence=[_initial()])
    entity = astrogator.entity_path("Leader", position=mission)
    config = propagator.hpop_config(
        name="Earth_TwoBody",
        central_body="Earth",
        integrator=propagator.hpop_rkf78(name="RKF7th8th"),
        gravity=propagator.hpop_two_body_gravity(
            gravitational_parameter_m3_s2=MU,
        ),
    )

    astrogator.run_mcs(
        [astrogator.follow("Follow", leader_name="Leader")],
        entities=[entity],
        propagators=[config],
    )

    payload = calls[0]
    assert payload["Entities"][0]["$type"] == "EntityPath"  # type: ignore[index]
    assert payload["Entities"][0]["Position"]["$type"] == "AstrogatorMCS"  # type: ignore[index]
    assert payload["Propagators"][0]["Name"] == "Earth_TwoBody"  # type: ignore[index]


def test_run_mcs_omits_unsupplied_optional_top_level_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        captured.append(json)
        return {"wire": "response"}

    monkeypatch.setattr(_api.raw, "post", fake_post)
    monkeypatch.setattr(_api, "run_mcs_result_from_wire", lambda value: value)

    astrogator.run_mcs([_initial()])
    payload = captured[0]
    assert "Text" not in payload
    assert "Entities" not in payload
    assert "Propagators" not in payload
    assert "EngineModels" not in payload
    assert "ComputeCzmlPositions" not in payload


def test_run_mcs_lowers_explicit_compute_czml_positions_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        captured.append(json)
        return {"wire": "response"}

    monkeypatch.setattr(_api.raw, "post", fake_post)
    monkeypatch.setattr(_api, "run_mcs_result_from_wire", lambda value: value)

    astrogator.run_mcs([_initial()], compute_czml_positions=False)
    assert captured[0]["ComputeCzmlPositions"] is False  # type: ignore[index]


def test_mission_position_omits_compute_czml_positions_when_unsupplied() -> None:
    omitted = astrogator.mission_position(main_sequence=[_initial()])
    assert "ComputeCzmlPositions" not in omitted.to_wire()
    explicit_false = astrogator.mission_position(
        main_sequence=[_initial()], compute_czml_positions=False
    )
    assert explicit_false.to_wire()["ComputeCzmlPositions"] is False
    explicit_true = astrogator.mission_position(
        main_sequence=[_initial()], compute_czml_positions=True
    )
    assert explicit_true.to_wire()["ComputeCzmlPositions"] is True


def test_run_mcs_rejects_raw_fragments_at_curated_boundary() -> None:
    with pytest.raises(TypeError):
        astrogator.run_mcs([{}])
    with pytest.raises(TypeError):
        astrogator.run_mcs([_initial()], entities=[{}])
    with pytest.raises(TypeError):
        astrogator.run_mcs([_initial()], propagators=[{}])
    with pytest.raises(TypeError):
        astrogator.run_mcs([_initial()], engine_models=[{}])


def test_run_mcs_propagates_api_error_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = exceptions.AstroxAPIError("server branch error", "/Astrogator/RunMCS", None)

    def fake_post(endpoint: str, *, json: object) -> object:
        raise error

    monkeypatch.setattr(_api.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError) as caught:
        astrogator.run_mcs([_initial()])
    assert caught.value is error
