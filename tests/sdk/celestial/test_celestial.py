"""Deterministic behavior tests for celestial endpoint functions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
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
        "MpcOrbitalElements",
        "cb_axes_rotation",
        "ephemeris",
        "lambert_transfer_window",
        "mpc_ephemeris",
        "mpc_orbital_elements",
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

    assert response == {"Position": {"epoch": "2026-01-01T00:00:00.000Z"}}
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


def test_ephemeris_omits_server_owned_window_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    celestial.ephemeris(target_name="Moon")

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/ephemeris",
            "json": {"TargetName": "Moon"},
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


def test_mpc_ephemeris_lowers_optional_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    celestial.mpc_ephemeris(
        target_name="Ceres",
        observer_frame="topocentric",
        start=START,
        stop=STOP,
    )

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/mpc",
            "json": {
                "TargetName": "Ceres",
                "ObserverFrame": "topocentric",
                "Start": START,
                "Stop": STOP,
            },
        },
    )


def test_mpc_ephemeris_omits_none_optional_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, RESPONSE)

    celestial.mpc_ephemeris(
        target_name="Ceres",
        observer_frame=None,
        start=START,
        stop=None,
    )

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/mpc",
            "json": {"TargetName": "Ceres", "Start": START},
        },
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


def test_mpc_orbital_elements_are_frozen_and_lower_complete_wire_shape() -> None:
    elements = celestial.mpc_orbital_elements(
        epoch_mjd_tdt=61000.0,
        periapsis_time_mjd_tdt=60900.0,
        periapsis_distance_au=0.6740515,
        semi_major_axis_au=0.9898367,
        eccentricity=0.3190276,
        inclination_deg=0.79379,
        raan_deg=209.81829,
        argument_of_periapsis_deg=100.88187,
        mean_anomaly_deg=120.0,
    )

    assert isinstance(elements, celestial.MpcOrbitalElements)
    assert_canonical_equal(
        elements.to_wire(),
        {
            "EpochMjdTdt": 61000.0,
            "PeriTimeMjdTdt": 60900.0,
            "Q": 0.6740515,
            "SemimajorAxis": 0.9898367,
            "Eccentricity": 0.3190276,
            "Inclination": 0.79379,
            "Raan": 209.81829,
            "ArgOfPeriapsis": 100.88187,
            "MeanAnomaly": 120.0,
        },
    )
    with pytest.raises(FrozenInstanceError):
        elements.mean_anomaly_deg = 121.0


def test_mpc_orbital_elements_omit_unsupplied_server_fields() -> None:
    elements = celestial.mpc_orbital_elements(
        epoch_mjd_tdt=61000.0,
        semi_major_axis_au=0.9898367,
    )

    assert_canonical_equal(
        elements.to_wire(),
        {"EpochMjdTdt": 61000.0, "SemimajorAxis": 0.9898367},
    )


def test_lambert_transfer_window_lowers_complete_payload_and_strips_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    elements = celestial.mpc_orbital_elements(
        epoch_mjd_tdt=61000.0,
        periapsis_time_mjd_tdt=60900.0,
        periapsis_distance_au=0.6740515,
        semi_major_axis_au=0.9898367,
        eccentricity=0.3190276,
        inclination_deg=0.79379,
        raan_deg=209.81829,
        argument_of_periapsis_deg=100.88187,
        mean_anomaly_deg=120.0,
    )
    transfer_response = {
        "IsSuccess": True,
        "Message": "Success",
        "TransferResults": [{"RV1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}],
        "FutureField": {"preserve": True},
    }
    calls = record_raw_post(monkeypatch, transfer_response)

    response = celestial.lambert_transfer_window(
        departure_body="Earth",
        arrival_body="2015 XF261",
        departure_start="2028-06-01T00:00:00Z",
        departure_stop="2028-06-03T00:00:00Z",
        arrival_start="2029-04-01T00:00:00Z",
        arrival_stop="2029-04-03T00:00:00Z",
        sun_frame="ICRF",
        min_time_of_flight_days=10,
        departure_step_days=2.0,
        arrival_step_days=1.0,
        departure_elements=elements,
        arrival_elements=elements,
    )

    assert response == {
        "TransferResults": [{"RV1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}],
        "FutureField": {"preserve": True},
    }
    assert response is not transfer_response
    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/transfer",
            "json": {
                "SunFrameName": "ICRF",
                "DepartureCbName": "Earth",
                "ArrivalCbName": "2015 XF261",
                "DepartureInterval": "2028-06-01T00:00:00Z/2028-06-03T00:00:00Z",
                "ArrivalInterval": "2029-04-01T00:00:00Z/2029-04-03T00:00:00Z",
                "MinTofDays": 10,
                "DepartureStepDay": 2.0,
                "ArrivalStepDay": 1.0,
                "DepartureElements": elements.to_wire(),
                "ArrivalElements": elements.to_wire(),
            },
        },
    )
    assert transfer_response["IsSuccess"] is True
    assert transfer_response["Message"] == "Success"


def test_lambert_transfer_window_omits_server_owned_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(
        monkeypatch,
        {"IsSuccess": True, "Message": "Success", "TransferResults": []},
    )

    response = celestial.lambert_transfer_window(
        departure_body="Earth",
        arrival_body="Mars",
        departure_start=START,
        departure_stop=STOP,
        arrival_start=START,
        arrival_stop=STOP,
    )

    assert response == {"TransferResults": []}
    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/celestial/transfer",
            "json": {
                "DepartureCbName": "Earth",
                "ArrivalCbName": "Mars",
                "DepartureInterval": f"{START}/{STOP}",
                "ArrivalInterval": f"{START}/{STOP}",
            },
        },
    )


def test_lambert_transfer_window_propagates_api_errors_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = exceptions.AstroxAPIError(
        "transfer failed",
        "/celestial/transfer",
        response=None,
    )

    def fake_post(endpoint: str, *, json: object) -> object:
        assert endpoint == "/celestial/transfer"
        raise error

    monkeypatch.setattr(celestial.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        celestial.lambert_transfer_window(
            departure_body="Earth",
            arrival_body="Mars",
            departure_start=START,
            departure_stop=STOP,
            arrival_start=START,
            arrival_stop=STOP,
        )

    assert exc_info.value is error


@pytest.mark.parametrize(
    ("kwargs", "parameter"),
    [
        (
            {
                "departure_body": "Earth",
                "arrival_body": "Mars",
                "departure_start": START,
                "departure_stop": STOP,
                "arrival_start": START,
                "arrival_stop": STOP,
                "departure_elements": {},
            },
            "departure_elements",
        ),
        (
            {
                "departure_body": "Earth",
                "arrival_body": "Mars",
                "departure_start": START,
                "departure_stop": STOP,
                "arrival_start": START,
                "arrival_stop": STOP,
                "min_time_of_flight_days": True,
            },
            "min_time_of_flight_days",
        ),
    ],
)
def test_lambert_transfer_window_rejects_mistyped_arguments(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, Any],
    parameter: str,
) -> None:
    record_raw_post(monkeypatch, {"TransferResults": []})
    with pytest.raises(TypeError, match=parameter):
        celestial.lambert_transfer_window(**kwargs)
