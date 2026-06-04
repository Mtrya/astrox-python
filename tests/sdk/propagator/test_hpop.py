"""Focused tests for the curated HPOP propagator surface."""

from __future__ import annotations

from inspect import signature
from typing import get_type_hints

import pytest

from astrox import exceptions, orbits, propagator
from tests.sdk.propagator.helpers import (
    HPOP_CARTESIAN_REQUEST,
    HPOP_CLASSICAL_REQUEST,
    HPOP_CONFIG_REQUEST,
    REPRESENTATIVE_PROPAGATOR_RESPONSE,
    REPRESENTATIVE_RETURN_SNAPSHOT,
    assert_canonical_equal,
    record_raw_post,
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


@pytest.fixture
def state() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=7000000.0,
        y_m=1000.0,
        z_m=2000.0,
        vx_m_s=-1.0,
        vy_m_s=7500.0,
        vz_m_s=10.0,
    )


def hpop_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        name="Earth HPOP explicit",
        description="Representative HPOP configuration",
        user_comment="behavior test",
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="tight-rkf",
            description="tight integrator",
            user_comment="integrator comment",
            use_fixed_step=False,
            initial_step_s=30.0,
            max_step_s=120.0,
            min_step_s=0.001,
            max_abs_error=1e-10,
            max_rel_error=1e-12,
            max_iterations=50,
        ),
        gravity=propagator.hpop_gravity_field(
            name="egm",
            description="gravity field",
            user_comment="gravity comment",
            gravity_file_name="EGM2008.grv",
            degree=21,
            order=21,
            use_secular_variations=False,
            solid_tide_type="Permanent tide only",
            eop_file_path="EOP-v1.1.txt",
        ),
        atmosphere=propagator.hpop_jacchia_roberts(
            name="jr",
            description="atmosphere",
            user_comment="atmosphere comment",
            drag_model_type="Spherical",
            atmos_data_source="Constant Values",
            f10p7=150.0,
            f10p7_avg=150.0,
            kp=3.0,
        ),
        srp=propagator.hpop_srp_spherical(
            name="srp",
            description="srp model",
            user_comment="srp comment",
            shadow_model="DualCone",
            sun_position="Apparent",
            eclipsing_bodies=["Earth", "Moon"],
        ),
        third_bodies=[
            propagator.hpop_third_body(
                "Sun",
                name="sun",
                description="solar gravity",
                user_comment="third body comment",
                mode_type="PointMass",
                ephem_source="DeFile",
                grav_source="DeFile",
                mu_m3_s2=1.3271244004193938e20,
            ),
            propagator.hpop_third_body("Moon"),
        ],
    )


def test_hpop_branch_constructors_emit_exact_wire_fragments() -> None:
    assert_canonical_equal(hpop_config(), HPOP_CONFIG_REQUEST)


@pytest.mark.parametrize(
    ("fragment", "expected"),
    [
        (propagator.hpop_rkf78(), {"$type": "RKF7th8th"}),
        (propagator.hpop_two_body_gravity(), {"$type": "TwoBody"}),
        (
            propagator.hpop_gravity_field(
                gravity_file_name="EGM2008.grv",
                degree=2,
                order=2,
            ),
            {
                "$type": "GravityField",
                "GravityFileName": "EGM2008.grv",
                "Degree": 2,
                "Order": 2,
            },
        ),
        (propagator.hpop_jacchia_roberts(), {"$type": "JacchiaRoberts"}),
        (propagator.hpop_srp_spherical(), {"$type": "SRPSpherical"}),
        (propagator.hpop_third_body("Sun"), {"ThirdBodyName": "Sun"}),
        (propagator.hpop_config(), {}),
    ],
)
def test_hpop_constructors_omit_unsupplied_optional_values(
    fragment: dict[str, object],
    expected: dict[str, object],
) -> None:
    assert_canonical_equal(fragment, expected)


@pytest.mark.parametrize(
    ("kwargs", "parameter"),
    [
        ({"integrator": ["not", "mapping"]}, "integrator"),
        ({"gravity": ["not", "mapping"]}, "gravity"),
        ({"atmosphere": ["not", "mapping"]}, "atmosphere"),
        ({"srp": ["not", "mapping"]}, "srp"),
    ],
)
def test_hpop_config_rejects_non_mapping_subfragments(
    kwargs: dict[str, object],
    parameter: str,
) -> None:
    with pytest.raises(TypeError, match=f"{parameter} must be a mapping fragment"):
        propagator.hpop_config(**kwargs)


def test_hpop_sequence_fragments_reject_one_shot_iterators() -> None:
    with pytest.raises(TypeError, match="eclipsing_bodies must be a sequence"):
        propagator.hpop_srp_spherical(
            eclipsing_bodies=(body for body in ["Earth", "Moon"]),
        )

    with pytest.raises(TypeError, match="third_bodies must be a sequence"):
        propagator.hpop_config(
            third_bodies=(propagator.hpop_third_body("Sun") for _ in range(1)),
        )


def test_hpop_calls_raw_route_with_classical_payload(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    calls = record_raw_post(monkeypatch)

    period_s, position = propagator.hpop(
        start=HPOP_CLASSICAL_REQUEST["Start"],
        stop=HPOP_CLASSICAL_REQUEST["Stop"],
        orbit_epoch=HPOP_CLASSICAL_REQUEST["OrbitEpoch"],
        orbit=orbit,
        config=hpop_config(),
        coord_system=HPOP_CLASSICAL_REQUEST["CoordSystem"],
        coord_epoch=HPOP_CLASSICAL_REQUEST["CoordEpoch"],
        gravitational_parameter_m3_s2=HPOP_CLASSICAL_REQUEST["GravitationalParameter"],
        coefficient_of_drag=HPOP_CLASSICAL_REQUEST["CoefficientOfDrag"],
        area_mass_ratio_drag_m2_kg=HPOP_CLASSICAL_REQUEST["AreaMassRatioDrag"],
        coefficient_of_srp=HPOP_CLASSICAL_REQUEST["CoefficientOfSRP"],
        area_mass_ratio_srp_m2_kg=HPOP_CLASSICAL_REQUEST["AreaMassRatioSRP"],
    )

    assert_canonical_equal(
        return_snapshot(period_s, position),
        REPRESENTATIVE_RETURN_SNAPSHOT,
    )
    assert calls[0]["endpoint"] == "/Propagator/HPOP"
    assert_canonical_equal(calls[0]["json"], HPOP_CLASSICAL_REQUEST)


def test_hpop_calls_raw_route_with_cartesian_payload(
    monkeypatch: pytest.MonkeyPatch,
    state: orbits.CartesianState,
) -> None:
    calls = record_raw_post(monkeypatch)

    propagator.hpop(
        start=HPOP_CARTESIAN_REQUEST["Start"],
        stop=HPOP_CARTESIAN_REQUEST["Stop"],
        orbit_epoch=HPOP_CARTESIAN_REQUEST["OrbitEpoch"],
        state=state,
    )

    assert calls[0]["endpoint"] == "/Propagator/HPOP"
    assert_canonical_equal(calls[0]["json"], HPOP_CARTESIAN_REQUEST)


def test_hpop_forwards_mapping_config_without_deep_validation(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    calls = record_raw_post(monkeypatch)
    raw_config = {
        "Name": "raw-fragment",
        "GravityModel": {
            "$type": "Experimental",
            "UnverifiedServerField": {"nested": [1, 2, 3]},
        },
    }

    propagator.hpop(
        start=HPOP_CARTESIAN_REQUEST["Start"],
        stop=HPOP_CARTESIAN_REQUEST["Stop"],
        orbit_epoch=HPOP_CARTESIAN_REQUEST["OrbitEpoch"],
        orbit=orbit,
        config=raw_config,
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start": HPOP_CARTESIAN_REQUEST["Start"],
            "Stop": HPOP_CARTESIAN_REQUEST["Stop"],
            "OrbitEpoch": HPOP_CARTESIAN_REQUEST["OrbitEpoch"],
            "CoordType": "Classical",
            "OrbitalElements": orbit.to_wire(),
            "HpopPropagator": raw_config,
        },
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {
            "orbit": orbits.keplerian(
                semi_major_axis_m=6778137.0,
                eccentricity=0.001,
                inclination_deg=28.5,
                argument_of_periapsis_deg=0.0,
                raan_deg=0.0,
                true_anomaly_deg=0.0,
            ),
            "state": orbits.cartesian_state(
                x_m=7000000.0,
                y_m=1000.0,
                z_m=2000.0,
                vx_m_s=-1.0,
                vy_m_s=7500.0,
                vz_m_s=10.0,
            ),
        },
    ],
)
def test_hpop_requires_exactly_one_orbit_or_state(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="exactly one"):
        propagator.hpop(
            start=HPOP_CARTESIAN_REQUEST["Start"],
            stop=HPOP_CARTESIAN_REQUEST["Stop"],
            orbit_epoch=HPOP_CARTESIAN_REQUEST["OrbitEpoch"],
            **kwargs,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"orbit": [6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0]},
        {"state": [7000000.0, 1000.0, 2000.0, -1.0, 7500.0, 10.0]},
    ],
)
def test_hpop_rejects_raw_orbit_and_state_fragments(kwargs: dict[str, object]) -> None:
    with pytest.raises(TypeError):
        propagator.hpop(
            start=HPOP_CARTESIAN_REQUEST["Start"],
            stop=HPOP_CARTESIAN_REQUEST["Stop"],
            orbit_epoch=HPOP_CARTESIAN_REQUEST["OrbitEpoch"],
            **kwargs,
        )


def test_hpop_rejects_non_mapping_config(
    orbit: orbits.KeplerianElements,
) -> None:
    with pytest.raises(TypeError, match="config must be a mapping fragment"):
        propagator.hpop(
            start=HPOP_CARTESIAN_REQUEST["Start"],
            stop=HPOP_CARTESIAN_REQUEST["Stop"],
            orbit_epoch=HPOP_CARTESIAN_REQUEST["OrbitEpoch"],
            orbit=orbit,
            config=["not", "a", "mapping"],
        )


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
def test_hpop_response_parser_fails_loudly_for_missing_required_fields(
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
        propagator.hpop(
            start=HPOP_CARTESIAN_REQUEST["Start"],
            stop=HPOP_CARTESIAN_REQUEST["Stop"],
            orbit_epoch=HPOP_CARTESIAN_REQUEST["OrbitEpoch"],
            orbit=orbit,
        )


def test_hpop_propagates_api_error_for_unsuccessful_raw_response(
    monkeypatch: pytest.MonkeyPatch,
    orbit: orbits.KeplerianElements,
) -> None:
    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        raise exceptions.AstroxAPIError("bad hpop branch", endpoint, response=None)

    monkeypatch.setattr(propagator.raw, "post", fake_post)

    with pytest.raises(exceptions.AstroxAPIError, match="bad hpop branch"):
        propagator.hpop(
            start=HPOP_CARTESIAN_REQUEST["Start"],
            stop=HPOP_CARTESIAN_REQUEST["Stop"],
            orbit_epoch=HPOP_CARTESIAN_REQUEST["OrbitEpoch"],
            orbit=orbit,
        )


def test_hpop_does_not_expose_coord_type_argument() -> None:
    assert "coord_type" not in signature(propagator.hpop).parameters


def test_hpop_type_hints_are_success_path_values() -> None:
    assert get_type_hints(propagator.hpop)["return"] == tuple[
        float, propagator.PropagatorPosition
    ]
