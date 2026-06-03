"""Focused tests for SGP4 and simple-ascent propagator functions."""

from __future__ import annotations

from typing import get_type_hints

import pytest

from astrox import exceptions, propagator
from tests.sdk.propagator.helpers import (
    REPRESENTATIVE_PROPAGATOR_RESPONSE,
    REPRESENTATIVE_RETURN_SNAPSHOT,
    SGP4_REQUEST,
    SIMPLE_ASCENT_REQUEST,
    assert_canonical_equal,
    record_raw_post,
    return_snapshot,
)


def test_sgp4_emits_representative_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch)

    period_s, position = propagator.sgp4(
        start=SGP4_REQUEST["Start"],
        stop=SGP4_REQUEST["Stop"],
        step_s=SGP4_REQUEST["Step"],
        satellite_number=SGP4_REQUEST["SatelliteNumber"],
        tle_lines=tuple(SGP4_REQUEST["TLEs"]),
    )

    assert_canonical_equal(
        return_snapshot(period_s, position),
        REPRESENTATIVE_RETURN_SNAPSHOT,
    )
    assert calls[0]["endpoint"] == "/Propagator/sgp4"
    assert_canonical_equal(calls[0]["json"], SGP4_REQUEST)


def test_sgp4_omits_server_owned_optional_knobs_when_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch)

    propagator.sgp4(
        start=SGP4_REQUEST["Start"],
        stop=SGP4_REQUEST["Stop"],
        tle_lines=tuple(SGP4_REQUEST["TLEs"]),
    )

    assert calls[0]["endpoint"] == "/Propagator/sgp4"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": SGP4_REQUEST["Start"],
            "Stop": SGP4_REQUEST["Stop"],
            "TLEs": SGP4_REQUEST["TLEs"],
        },
    )


def test_sgp4_accepts_two_item_tle_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch)

    propagator.sgp4(
        start=SGP4_REQUEST["Start"],
        stop=SGP4_REQUEST["Stop"],
        tle_lines=SGP4_REQUEST["TLEs"],
    )

    assert calls[0]["endpoint"] == "/Propagator/sgp4"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": SGP4_REQUEST["Start"],
            "Stop": SGP4_REQUEST["Stop"],
            "TLEs": SGP4_REQUEST["TLEs"],
        },
    )


@pytest.mark.parametrize(
    "tle_lines",
    [
        (SGP4_REQUEST["TLEs"][0],),
        tuple(SGP4_REQUEST["TLEs"] + ["extra"]),
        "not-a-tle-pair",
        (SGP4_REQUEST["TLEs"][0], 123),
    ],
)
def test_sgp4_rejects_malformed_tle_lines(tle_lines: object) -> None:
    with pytest.raises(TypeError, match="tle_lines must be a two-item sequence"):
        propagator.sgp4(
            start=SGP4_REQUEST["Start"],
            stop=SGP4_REQUEST["Stop"],
            tle_lines=tle_lines,
        )


def test_simple_ascent_emits_representative_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch)

    period_s, position = propagator.simple_ascent(
        start=SIMPLE_ASCENT_REQUEST["Start"],
        stop=SIMPLE_ASCENT_REQUEST["Stop"],
        step_s=SIMPLE_ASCENT_REQUEST["Step"],
        central_body=SIMPLE_ASCENT_REQUEST["CentralBody"],
        launch_latitude_deg=SIMPLE_ASCENT_REQUEST["LaunchLatitude"],
        launch_longitude_deg=SIMPLE_ASCENT_REQUEST["LaunchLongitude"],
        launch_altitude_m=SIMPLE_ASCENT_REQUEST["LaunchAltitude"],
        burnout_velocity_m_s=SIMPLE_ASCENT_REQUEST["BurnoutVelocity"],
        burnout_latitude_deg=SIMPLE_ASCENT_REQUEST["BurnoutLatitude"],
        burnout_longitude_deg=SIMPLE_ASCENT_REQUEST["BurnoutLongitude"],
        burnout_altitude_m=SIMPLE_ASCENT_REQUEST["BurnoutAltitude"],
    )

    assert_canonical_equal(
        return_snapshot(period_s, position),
        REPRESENTATIVE_RETURN_SNAPSHOT,
    )
    assert calls[0]["endpoint"] == "/Propagator/SimpleAscent"
    assert_canonical_equal(calls[0]["json"], SIMPLE_ASCENT_REQUEST)


def test_simple_ascent_omits_server_owned_optional_knobs_when_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch)

    propagator.simple_ascent(
        start=SIMPLE_ASCENT_REQUEST["Start"],
        stop=SIMPLE_ASCENT_REQUEST["Stop"],
        launch_latitude_deg=SIMPLE_ASCENT_REQUEST["LaunchLatitude"],
        launch_longitude_deg=SIMPLE_ASCENT_REQUEST["LaunchLongitude"],
        launch_altitude_m=SIMPLE_ASCENT_REQUEST["LaunchAltitude"],
        burnout_velocity_m_s=SIMPLE_ASCENT_REQUEST["BurnoutVelocity"],
        burnout_latitude_deg=SIMPLE_ASCENT_REQUEST["BurnoutLatitude"],
        burnout_longitude_deg=SIMPLE_ASCENT_REQUEST["BurnoutLongitude"],
        burnout_altitude_m=SIMPLE_ASCENT_REQUEST["BurnoutAltitude"],
    )

    assert calls[0]["endpoint"] == "/Propagator/SimpleAscent"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": SIMPLE_ASCENT_REQUEST["Start"],
            "Stop": SIMPLE_ASCENT_REQUEST["Stop"],
            "LaunchLatitude": SIMPLE_ASCENT_REQUEST["LaunchLatitude"],
            "LaunchLongitude": SIMPLE_ASCENT_REQUEST["LaunchLongitude"],
            "LaunchAltitude": SIMPLE_ASCENT_REQUEST["LaunchAltitude"],
            "BurnoutVelocity": SIMPLE_ASCENT_REQUEST["BurnoutVelocity"],
            "BurnoutLatitude": SIMPLE_ASCENT_REQUEST["BurnoutLatitude"],
            "BurnoutLongitude": SIMPLE_ASCENT_REQUEST["BurnoutLongitude"],
            "BurnoutAltitude": SIMPLE_ASCENT_REQUEST["BurnoutAltitude"],
        },
    )


@pytest.mark.parametrize(
    ("function_name", "field_path"),
    [
        ("sgp4", ("Period",)),
        ("sgp4", ("Position",)),
        ("sgp4", ("Position", "CentralBody")),
        ("sgp4", ("Position", "cartesianVelocity")),
        ("sgp4", ("Position", "epoch")),
        ("sgp4", ("Position", "interpolationAlgorithm")),
        ("sgp4", ("Position", "interpolationDegree")),
        ("sgp4", ("Position", "referenceFrame")),
        ("simple_ascent", ("Period",)),
        ("simple_ascent", ("Position",)),
        ("simple_ascent", ("Position", "CentralBody")),
        ("simple_ascent", ("Position", "cartesianVelocity")),
        ("simple_ascent", ("Position", "epoch")),
        ("simple_ascent", ("Position", "interpolationAlgorithm")),
        ("simple_ascent", ("Position", "interpolationDegree")),
        ("simple_ascent", ("Position", "referenceFrame")),
    ],
)
def test_new_single_result_propagator_parsers_fail_loudly_for_missing_required_fields(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
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
        if function_name == "sgp4":
            propagator.sgp4(
                start=SGP4_REQUEST["Start"],
                stop=SGP4_REQUEST["Stop"],
                tle_lines=tuple(SGP4_REQUEST["TLEs"]),
            )
        else:
            propagator.simple_ascent(
                start=SIMPLE_ASCENT_REQUEST["Start"],
                stop=SIMPLE_ASCENT_REQUEST["Stop"],
                launch_latitude_deg=SIMPLE_ASCENT_REQUEST["LaunchLatitude"],
                launch_longitude_deg=SIMPLE_ASCENT_REQUEST["LaunchLongitude"],
                launch_altitude_m=SIMPLE_ASCENT_REQUEST["LaunchAltitude"],
                burnout_velocity_m_s=SIMPLE_ASCENT_REQUEST["BurnoutVelocity"],
                burnout_latitude_deg=SIMPLE_ASCENT_REQUEST["BurnoutLatitude"],
                burnout_longitude_deg=SIMPLE_ASCENT_REQUEST["BurnoutLongitude"],
                burnout_altitude_m=SIMPLE_ASCENT_REQUEST["BurnoutAltitude"],
            )


@pytest.mark.parametrize("function_name", ["sgp4", "simple_ascent"])
def test_new_single_result_propagators_propagate_api_errors(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        raise exceptions.AstroxAPIError("bad propagation", endpoint, response=None)

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError, match="bad propagation"):
        if function_name == "sgp4":
            propagator.sgp4(
                start=SGP4_REQUEST["Start"],
                stop=SGP4_REQUEST["Stop"],
                tle_lines=tuple(SGP4_REQUEST["TLEs"]),
            )
        else:
            propagator.simple_ascent(
                start=SIMPLE_ASCENT_REQUEST["Start"],
                stop=SIMPLE_ASCENT_REQUEST["Stop"],
                launch_latitude_deg=SIMPLE_ASCENT_REQUEST["LaunchLatitude"],
                launch_longitude_deg=SIMPLE_ASCENT_REQUEST["LaunchLongitude"],
                launch_altitude_m=SIMPLE_ASCENT_REQUEST["LaunchAltitude"],
                burnout_velocity_m_s=SIMPLE_ASCENT_REQUEST["BurnoutVelocity"],
                burnout_latitude_deg=SIMPLE_ASCENT_REQUEST["BurnoutLatitude"],
                burnout_longitude_deg=SIMPLE_ASCENT_REQUEST["BurnoutLongitude"],
                burnout_altitude_m=SIMPLE_ASCENT_REQUEST["BurnoutAltitude"],
            )


def test_new_single_result_propagator_return_type_hints_are_success_path_values() -> None:
    assert get_type_hints(propagator.sgp4)["return"] == tuple[
        float, propagator.PropagatorPosition
    ]
    assert get_type_hints(propagator.simple_ascent)["return"] == tuple[
        float, propagator.PropagatorPosition
    ]
