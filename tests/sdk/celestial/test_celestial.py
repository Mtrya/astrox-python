"""Deterministic behavior tests for read-like celestial functions."""

from __future__ import annotations

from typing import Any

import pytest

from astrox import celestial, exceptions
from tests.sdk.helpers import assert_canonical_equal


RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "Success",
    "Position": {"epoch": "2026-01-01T00:00:00.000Z"},
}
START = "2026-01-01T00:00:00.000Z"
STOP = "2026-01-02T00:00:00.000Z"


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_post(endpoint: str, *, json: object) -> object:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(celestial.raw, "post", fake_post)
    return calls


def test_celestial_public_exports() -> None:
    import astrox

    assert astrox.celestial is celestial
    assert "celestial" in astrox.__all__
    assert set(celestial.__all__) == {
        "cb_axes_rotation",
        "ephemeris",
        "mpc_ephemeris",
    }


def test_ephemeris_lowers_complete_payload_and_returns_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    response = celestial.ephemeris(
        target_name="Moon",
        start=START,
        stop=STOP,
        observer_name="Earth",
        observer_frame="J2000",
        step_s=3600.0,
    )

    assert response is RESPONSE
    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/ephemeris",
            "json": {
                "TargetName": "Moon",
                "Start": START,
                "Stop": STOP,
                "ObserverName": "Earth",
                "ObserverFrame": "J2000",
                "Step": 3600.0,
            },
        },
    )


def test_ephemeris_omits_server_owned_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    celestial.ephemeris(target_name="Moon", start=START, stop=STOP)

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/ephemeris",
            "json": {"TargetName": "Moon", "Start": START, "Stop": STOP},
        },
    )


def test_cb_axes_rotation_preserves_order_branch_and_frame_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    celestial.cb_axes_rotation(
        from_central_body="Earth",
        to_central_body="Moon",
        epoch=START,
        from_frame="INERTIAL",
        to_frame="FIXED",
        order=1,
    )

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/CbAxesRotation",
            "json": {
                "FromCbName": "Earth",
                "ToCbName": "Moon",
                "Epoch": START,
                "FromCbFrame": "INERTIAL",
                "ToCbFrame": "FIXED",
                "Order": 1,
            },
        },
    )


def test_cb_axes_rotation_omits_optional_server_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    celestial.cb_axes_rotation(
        from_central_body="Earth",
        to_central_body="Moon",
        epoch=START,
    )

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/CbAxesRotation",
            "json": {
                "FromCbName": "Earth",
                "ToCbName": "Moon",
                "Epoch": START,
            },
        },
    )


def test_mpc_ephemeris_preserves_external_route_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    celestial.mpc_ephemeris(target_name="Ceres")

    assert_canonical_equal(
        calls[0],
        {"endpoint": "/celestial/mpc", "json": {"TargetName": "Ceres"}},
    )


@pytest.mark.parametrize(
    ("function", "kwargs", "parameter"),
    [
        (celestial.ephemeris, {"target_name": 1, "start": START, "stop": STOP}, "target_name"),
        (celestial.ephemeris, {"target_name": "Moon", "start": 1, "stop": STOP}, "start"),
        (
            celestial.cb_axes_rotation,
            {
                "from_central_body": "Earth",
                "to_central_body": "Moon",
                "epoch": START,
                "order": True,
            },
            "order",
        ),
        (celestial.mpc_ephemeris, {"target_name": 1}, "target_name"),
    ],
)
def test_celestial_rejects_mistyped_arguments(
    function: Any,
    kwargs: dict[str, Any],
    parameter: str,
) -> None:
    with pytest.raises(TypeError, match=parameter):
        function(**kwargs)


def test_celestial_propagates_api_errors_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = exceptions.AstroxAPIError("celestial failed", "/celestial/ephemeris", response=None)

    def fake_post(endpoint: str, *, json: object) -> object:
        assert endpoint == "/celestial/ephemeris"
        raise error

    monkeypatch.setattr(celestial.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        celestial.ephemeris(target_name="Moon", start=START, stop=STOP)

    assert exc_info.value is error
