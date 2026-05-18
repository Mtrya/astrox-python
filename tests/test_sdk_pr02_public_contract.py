"""PR 02 public contract tests for the reference propagator slice."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

import astrox
from astrox import _http


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


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.status_code = 200
        self.payload = payload
        self.text = ""
        self.reason = "OK"

    def json(self) -> object:
        return self.payload


class RecordingSession:
    def __init__(self, payload: object = PROPAGATOR_RESPONSE) -> None:
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        json: object | None = None,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: object,
    ) -> FakeResponse:
        self.calls.append(
            {
                "method": method.upper(),
                "url": url,
                "json": json,
                "params": params,
                "headers": headers,
                "timeout": timeout,
                "kwargs": kwargs,
            }
        )
        return FakeResponse(self.payload)


@pytest.fixture(autouse=True)
def reset_default_session() -> None:
    _http._default_session.set(None)


def install_recording_client() -> RecordingSession:
    client = astrox.configure(
        base_url="https://astrox.example",
        timeout=7,
        max_retries=0,
        retry_delay=0,
    )
    session = RecordingSession()
    client._session = session
    return session


@pytest.mark.xfail(strict=True, reason="PR 02 later phases add astrox.orbits and curated propagator names")
def test_pr02_public_modules_and_names_are_available() -> None:
    from astrox import orbits, propagator

    assert "orbits" in astrox.__all__
    assert "propagator" in astrox.__all__

    assert hasattr(orbits, "KeplerianElements")
    assert hasattr(orbits, "keplerian")
    assert hasattr(propagator, "PropagatorPosition")
    assert hasattr(propagator, "j2")
    assert hasattr(propagator, "two_body")
    assert hasattr(propagator, "ballistic")
    assert hasattr(propagator, "ballistic_delta_v")
    assert hasattr(propagator, "ballistic_delta_v_min_ecc")
    assert hasattr(propagator, "ballistic_apogee_altitude")
    assert hasattr(propagator, "ballistic_time_of_flight")


@pytest.mark.xfail(strict=True, reason="PR 02 Phase 2 adds the KeplerianElements dataclass")
def test_keplerian_constructor_returns_frozen_dataclass_with_explicit_wire_lowering() -> None:
    from astrox import orbits

    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

    assert is_dataclass(orbit)
    assert isinstance(orbit, orbits.KeplerianElements)
    assert not hasattr(orbit, "orbit_epoch")
    assert orbit.to_wire() == [
        6778137.0,
        0.001,
        28.5,
        0.0,
        0.0,
        0.0,
    ]

    with pytest.raises(FrozenInstanceError):
        orbit.eccentricity = 0.0


@pytest.mark.xfail(strict=True, reason="PR 02 Phases 2 and 3 add curated J2 propagation")
def test_j2_assembles_fixture_backed_payload_and_returns_success_path_tuple() -> None:
    from astrox import orbits, propagator

    session = install_recording_client()
    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

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
    assert is_dataclass(position)
    assert position.central_body == "Earth"
    assert position.cartesian_velocity == (0.0, 1.0, 2.0, 3.0)
    assert session.calls == [
        {
            "method": "POST",
            "url": "https://astrox.example/Propagator/J2",
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
            "params": None,
            "headers": {"Accept": "application/json"},
            "timeout": 7,
            "kwargs": {},
        }
    ]


@pytest.mark.xfail(strict=True, reason="PR 02 Phases 2 and 3 add curated two-body propagation")
def test_two_body_omits_server_owned_optional_knobs_when_not_provided() -> None:
    from astrox import orbits, propagator

    session = install_recording_client()
    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

    propagator.two_body(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
    )

    assert session.calls[0]["url"] == "https://astrox.example/Propagator/TwoBody"
    assert session.calls[0]["json"] == {
        "Start": "2024-01-01T00:00:00.000Z",
        "Stop": "2024-01-01T00:10:00.000Z",
        "OrbitEpoch": "2024-01-01T00:00:00.000Z",
        "CoordType": "Classical",
        "OrbitalElements": orbit.to_wire(),
    }


@pytest.mark.xfail(strict=True, reason="PR 02 Phases 2 and 3 reject raw dict/list escape hatches")
def test_curated_propagator_functions_do_not_accept_raw_dict_orbit_fragments() -> None:
    from astrox import propagator

    install_recording_client()

    with pytest.raises(TypeError):
        propagator.two_body(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T00:10:00.000Z",
            orbit_epoch="2024-01-01T00:00:00.000Z",
            orbit={"OrbitalElements": [6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0]},
        )


@pytest.mark.xfail(strict=True, reason="PR 02 Phase 4 adds nominal ballistic propagation")
def test_ballistic_nominal_maps_to_verified_route_without_mode_payload() -> None:
    from astrox import propagator

    session = install_recording_client()

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

    assert period_s == 600.0
    assert isinstance(position, propagator.PropagatorPosition)
    assert session.calls[0]["url"] == "https://astrox.example/Propagator/Ballistic"
    assert session.calls[0]["json"] == {
        "Start": "2024-01-01T12:00:00.000Z",
        "Step": 30.0,
        "LaunchLatitude": 28.5721,
        "LaunchLongitude": -80.648,
        "LaunchAltitude": 10.0,
        "ImpactLatitude": 30.0,
        "ImpactLongitude": -70.0,
        "ImpactAltitude": 0.0,
    }


@pytest.mark.parametrize(
    ("function_name", "value_kwarg", "value", "wire_mode"),
    [
        ("ballistic_delta_v", "delta_v_m_s", 3000.0, "DeltaV"),
        ("ballistic_delta_v_min_ecc", "delta_v_m_s", 3000.0, "DeltaV_MinEcc"),
        ("ballistic_apogee_altitude", "apogee_altitude_m", 200000.0, "ApogeeAlt"),
        ("ballistic_time_of_flight", "time_of_flight_s", 600.0, "TimeOfFlight"),
    ],
)
@pytest.mark.xfail(strict=True, reason="PR 02 Phase 4 adds branch-specific ballistic functions")
def test_ballistic_branch_functions_make_mode_explicit_in_the_function_name(
    function_name: str,
    value_kwarg: str,
    value: float,
    wire_mode: str,
) -> None:
    from astrox import propagator

    session = install_recording_client()
    function = getattr(propagator, function_name)

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

    assert period_s == 600.0
    assert isinstance(position, propagator.PropagatorPosition)
    assert session.calls[0]["json"]["BallisticType"] == wire_mode
    assert session.calls[0]["json"]["BallisticTypeValue"] == value


def test_generated_model_alias_layer_is_not_part_of_the_package_public_exports() -> None:
    assert "models" not in astrox.__all__
