"""Deterministic behavior tests for CRTBP and libration functions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction
from typing import Any, Callable

import pytest

from astrox import exceptions, libration
from tests.sdk.helpers import assert_canonical_equal


MU = 0.01215058560962404
STATE = libration.crtbp_state(
    x=1.189017399646985,
    y=0.0,
    z=0.06060558718057466,
    vx=0.0,
    vy=-0.17403902743307584,
    vz=0.0,
)
POINTS_RESPONSE = [
    0.15093428861801883,
    0.16783275105450815,
    0.9929120602006538,
    0.8369151257723572,
    1.1556821654448841,
    -1.0050626458102778,
    0.48784941439037594,
    0.48784941439037594,
    0.8660254037844386,
    -0.8660254037844386,
]
UNITS_RESPONSE = {
    "GravitationalParameter1": 398600441800000,
    "GravitationalParameter2": 4904869500000,
    "U": 0.012155650403206972,
    "UnitL": 384400000,
    "UnitT": 375189.2968837575,
    "UnitV": 1024.549482601835,
}
TRAJECTORY_RESPONSE = {
    "IsSuccess": True,
    "Message": "Success",
    "U": MU,
    "IsBarycentric": False,
    "Positions": [
        0.0,
        *STATE.to_wire(),
        0.1,
        1.1882162368206581,
        -0.01731736464079888,
        0.05995827744219876,
        -0.015957160742753745,
        -0.17144551071074926,
        -0.012928921761908418,
    ],
}
PERIODIC_RESPONSE = {
    "IsSuccess": True,
    "Message": "Success",
    "IsBarycentric": False,
    "Period": 2.7585313527865214,
    "X0": [0.835995246366249, 0, 0.05, 0, 0.15970397512870477, 0],
    "InitialX0": [0.8359, 0, 0.0501, 0, 0.1596, 0],
    "ListT": [0, 2.7585313527865214],
    "ListX": [
        [0.835995246366249, 0, 0.05, 0, 0.15970397512870477, 0],
        [0.8359952463654953, 2.5e-13, 0.05000000000004667, -1.9e-12, 0.1597039751295317, 3.5e-13],
    ],
}


def record_raw_get(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_get(endpoint: str, *, params: dict[str, Any]) -> object:
        calls.append({"endpoint": endpoint, "params": params})
        return response

    monkeypatch.setattr(libration.raw, "get", fake_get)
    return calls


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_post(endpoint: str, *, json: object) -> object:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(libration.raw, "post", fake_post)
    return calls


def test_libration_public_exports() -> None:
    import astrox

    assert astrox.libration is libration
    assert "libration" in astrox.__all__
    assert set(libration.__all__) == {
        "CrtbpSample",
        "CrtbpState",
        "CrtbpTrajectory",
        "LibrationPoint",
        "LibrationPoints",
        "LibrationUnitSystem",
        "PeriodicOrbit",
        "correct_periodic_orbit_fixed_x",
        "crtbp_state",
        "crtbp_trajectory",
        "earth_moon_dro",
        "earth_moon_l1_halo",
        "earth_moon_l2_halo",
        "positions",
        "units",
    }


def test_crtbp_state_is_frozen_and_lowers_exactly() -> None:
    state = libration.crtbp_state(
        x=Fraction(1, 2),
        y=0,
        z=Fraction(1, 4),
        vx=0,
        vy=Fraction(-1, 8),
        vz=0,
    )

    assert state.to_wire() == [0.5, 0.0, 0.25, 0.0, -0.125, 0.0]
    with pytest.raises(FrozenInstanceError):
        state.x = 1.0


def test_positions_lowers_mass_ratio_and_names_packed_points(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_get(monkeypatch, POINTS_RESPONSE)

    result = libration.positions(mass_ratio=Fraction(1, 10))

    assert_canonical_equal(
        calls[0],
        {"endpoint": "/libration/positions", "params": {"u": 0.1}},
    )
    assert result.l1 == libration.LibrationPoint(x=POINTS_RESPONSE[3], y=0.0)
    assert result.l2 == libration.LibrationPoint(x=POINTS_RESPONSE[4], y=0.0)
    assert result.l3 == libration.LibrationPoint(x=POINTS_RESPONSE[5], y=0.0)
    assert result.l4 == libration.LibrationPoint(x=POINTS_RESPONSE[6], y=POINTS_RESPONSE[8])
    assert result.l5 == libration.LibrationPoint(x=POINTS_RESPONSE[7], y=POINTS_RESPONSE[9])
    assert result.l1_distance_to_secondary == POINTS_RESPONSE[0]
    assert result.l2_distance_to_secondary == POINTS_RESPONSE[1]
    assert result.l3_distance_to_primary == POINTS_RESPONSE[2]
    with pytest.raises(FrozenInstanceError):
        result.l1 = result.l2


def test_units_lowers_dimensional_parameters_and_parses_named_scales(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_get(monkeypatch, UNITS_RESPONSE)

    result = libration.units(
        primary_gravitational_parameter_m3_s2=Fraction(398600441800000),
        secondary_gravitational_parameter_m3_s2=4904869500000,
        mean_separation_m=384400000,
    )

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/libration/unit",
            "params": {
                "gm1": 398600441800000.0,
                "gm2": 4904869500000.0,
                "meanRange": 384400000.0,
            },
        },
    )
    assert result == libration.LibrationUnitSystem(
        primary_gravitational_parameter_m3_s2=398600441800000.0,
        secondary_gravitational_parameter_m3_s2=4904869500000.0,
        mass_ratio=0.012155650403206972,
        length_unit_m=384400000.0,
        time_unit_s=375189.2968837575,
        velocity_unit_m_s=1024.549482601835,
    )


def test_units_omits_server_owned_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = record_raw_get(monkeypatch, UNITS_RESPONSE)

    libration.units()

    assert_canonical_equal(
        calls[0],
        {"endpoint": "/libration/unit", "params": {}},
    )


def test_crtbp_trajectory_lowers_complete_payload_and_parses_samples(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, TRAJECTORY_RESPONSE)

    result = libration.crtbp_trajectory(
        initial_state=STATE,
        mass_ratio=MU,
        start_time=0,
        end_time=0.1,
        barycentric=False,
        output_step=0.1,
    )

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/libration/crtbp-trajectory",
            "json": {
                "RV0": STATE.to_wire(),
                "U": MU,
                "T0": 0.0,
                "TEnd": 0.1,
                "IsBarycentric": False,
                "OutStep": 0.1,
            },
        },
    )
    assert result.mass_ratio == MU
    assert result.is_barycentric is False
    assert result.samples[0] == libration.CrtbpSample(time=0.0, state=STATE)
    assert len(result.samples) == 2


def test_crtbp_trajectory_omits_optional_time_origin_and_sampling_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, TRAJECTORY_RESPONSE)

    libration.crtbp_trajectory(initial_state=STATE, mass_ratio=MU)

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/libration/crtbp-trajectory",
            "json": {"RV0": STATE.to_wire(), "U": MU},
        },
    )


@pytest.mark.parametrize(
    ("function", "kwargs", "endpoint", "params"),
    [
        (
            libration.earth_moon_l1_halo,
            {"z_amplitude": 0.05, "southern": True},
            "/libration/em-l1-halo",
            {"az": 0.05, "isSouth": "true"},
        ),
        (
            libration.earth_moon_l2_halo,
            {"x_amplitude": 0.192, "southern": False},
            "/libration/em-l2-halo",
            {"ax": 0.192, "isSouth": "false"},
        ),
        (
            libration.earth_moon_dro,
            {"x_amplitude": 0.1801},
            "/libration/em-dro",
            {"ax": 0.1801},
        ),
    ],
)
def test_periodic_families_preserve_distinct_amplitude_and_branch_axes(
    monkeypatch: pytest.MonkeyPatch,
    function: Callable[..., libration.PeriodicOrbit],
    kwargs: dict[str, Any],
    endpoint: str,
    params: dict[str, Any],
) -> None:
    calls = record_raw_get(monkeypatch, PERIODIC_RESPONSE)

    result = function(**kwargs)

    assert_canonical_equal(calls[0], {"endpoint": endpoint, "params": params})
    assert result.period == PERIODIC_RESPONSE["Period"]
    assert result.initial_state.to_wire() == PERIODIC_RESPONSE["InitialX0"]
    assert result.corrected_state.to_wire() == PERIODIC_RESPONSE["X0"]
    assert [sample.time for sample in result.samples] == PERIODIC_RESPONSE["ListT"]
    assert [sample.state.to_wire() for sample in result.samples] == PERIODIC_RESPONSE["ListX"]


@pytest.mark.parametrize(
    "function",
    [
        libration.earth_moon_l1_halo,
        libration.earth_moon_l2_halo,
        libration.earth_moon_dro,
    ],
)
def test_periodic_families_omit_server_owned_defaults(
    monkeypatch: pytest.MonkeyPatch,
    function: Callable[..., libration.PeriodicOrbit],
) -> None:
    calls = record_raw_get(monkeypatch, PERIODIC_RESPONSE)

    function()

    assert calls[0]["params"] == {}


def test_fixed_x_correction_lowers_period_guess_without_inventing_start_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, PERIODIC_RESPONSE)

    result = libration.correct_periodic_orbit_fixed_x(
        initial_state=STATE,
        period_guess=2.75,
        mass_ratio=MU,
        barycentric=True,
        output_step=0.05,
    )

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/libration/crtbp-period-orbit-fixed-x",
            "json": {
                "RV0": STATE.to_wire(),
                "TEnd": 2.75,
                "U": MU,
                "IsBarycentric": True,
                "OutStep": 0.05,
            },
        },
    )
    assert isinstance(result, libration.PeriodicOrbit)


def test_fixed_x_correction_omits_optional_origin_and_sampling_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, PERIODIC_RESPONSE)

    libration.correct_periodic_orbit_fixed_x(
        initial_state=STATE,
        period_guess=2.75,
        mass_ratio=MU,
    )

    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/libration/crtbp-period-orbit-fixed-x",
            "json": {"RV0": STATE.to_wire(), "TEnd": 2.75, "U": MU},
        },
    )


@pytest.mark.parametrize(
    ("function", "kwargs", "parameter"),
    [
        (libration.positions, {"mass_ratio": True}, "mass_ratio"),
        (
            libration.units,
            {"primary_gravitational_parameter_m3_s2": True},
            "primary_gravitational_parameter_m3_s2",
        ),
        (
            libration.crtbp_trajectory,
            {"initial_state": STATE.to_wire(), "mass_ratio": MU},
            "initial_state",
        ),
        (
            libration.crtbp_trajectory,
            {"initial_state": STATE, "mass_ratio": MU, "barycentric": "false"},
            "barycentric",
        ),
        (libration.earth_moon_l1_halo, {"southern": 0}, "southern"),
        (libration.earth_moon_l2_halo, {"x_amplitude": True}, "x_amplitude"),
        (libration.earth_moon_dro, {"x_amplitude": True}, "x_amplitude"),
        (
            libration.correct_periodic_orbit_fixed_x,
            {"initial_state": STATE, "period_guess": True, "mass_ratio": MU},
            "period_guess",
        ),
    ],
)
def test_libration_rejects_mistyped_arguments(
    function: Callable[..., Any],
    kwargs: dict[str, Any],
    parameter: str,
) -> None:
    with pytest.raises(TypeError, match=parameter):
        function(**kwargs)


@pytest.mark.parametrize(
    ("function", "response", "message"),
    [
        (lambda: libration.positions(mass_ratio=MU), POINTS_RESPONSE[:-1], "ten numbers"),
        (libration.units, {**UNITS_RESPONSE, "UnitT": "bad"}, "UnitT"),
        (
            lambda: libration.crtbp_trajectory(initial_state=STATE, mass_ratio=MU),
            {**TRAJECTORY_RESPONSE, "Positions": TRAJECTORY_RESPONSE["Positions"][:-1]},
            "seven-number samples",
        ),
        (
            libration.earth_moon_l1_halo,
            {**PERIODIC_RESPONSE, "ListX": PERIODIC_RESPONSE["ListX"][:-1]},
            "equal length",
        ),
        (
            libration.earth_moon_l2_halo,
            {**PERIODIC_RESPONSE, "X0": PERIODIC_RESPONSE["X0"][:-1]},
            "six numbers",
        ),
        (
            libration.earth_moon_dro,
            {**PERIODIC_RESPONSE, "IsBarycentric": "false"},
            "IsBarycentric",
        ),
        (
            lambda: libration.correct_periodic_orbit_fixed_x(
                initial_state=STATE,
                period_guess=2.75,
                mass_ratio=MU,
            ),
            {**PERIODIC_RESPONSE, "Period": None},
            "Period",
        ),
    ],
)
def test_response_parsers_fail_loudly_for_malformed_fields(
    monkeypatch: pytest.MonkeyPatch,
    function: Callable[[], Any],
    response: object,
    message: str,
) -> None:
    monkeypatch.setattr(libration.raw, "get", lambda endpoint, *, params: response)
    monkeypatch.setattr(libration.raw, "post", lambda endpoint, *, json: response)

    with pytest.raises(TypeError, match=message):
        function()


@pytest.mark.parametrize(
    ("function", "method", "endpoint"),
    [
        (lambda: libration.positions(mass_ratio=MU), "get", "/libration/positions"),
        (libration.units, "get", "/libration/unit"),
        (
            lambda: libration.crtbp_trajectory(initial_state=STATE, mass_ratio=MU),
            "post",
            "/libration/crtbp-trajectory",
        ),
        (libration.earth_moon_l1_halo, "get", "/libration/em-l1-halo"),
        (libration.earth_moon_l2_halo, "get", "/libration/em-l2-halo"),
        (libration.earth_moon_dro, "get", "/libration/em-dro"),
        (
            lambda: libration.correct_periodic_orbit_fixed_x(
                initial_state=STATE,
                period_guess=2.75,
                mass_ratio=MU,
            ),
            "post",
            "/libration/crtbp-period-orbit-fixed-x",
        ),
    ],
)
def test_libration_propagates_api_errors_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    function: Callable[[], Any],
    method: str,
    endpoint: str,
) -> None:
    error = exceptions.AstroxAPIError("libration failed", endpoint, response=None)

    def fake_get(actual_endpoint: str, *, params: object) -> object:
        assert actual_endpoint == endpoint
        raise error

    def fake_post(actual_endpoint: str, *, json: object) -> object:
        assert actual_endpoint == endpoint
        raise error

    monkeypatch.setattr(libration.raw, method, fake_get if method == "get" else fake_post)

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        function()

    assert exc_info.value is error
