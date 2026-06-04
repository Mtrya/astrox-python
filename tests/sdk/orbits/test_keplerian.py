"""Focused tests for public orbit value objects."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from astrox import orbits
from tests.sdk.helpers import assert_canonical_equal


def test_keplerian_constructor_returns_frozen_dataclass() -> None:
    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

    assert isinstance(orbit, orbits.KeplerianElements)
    assert is_dataclass(orbit)
    assert orbit.semi_major_axis_m == 6778137.0
    assert orbit.eccentricity == 0.001
    assert orbit.inclination_deg == 28.5
    assert orbit.argument_of_periapsis_deg == 0.0
    assert orbit.raan_deg == 0.0
    assert orbit.true_anomaly_deg == 0.0

    with pytest.raises(FrozenInstanceError):
        orbit.eccentricity = 0.0


def test_keplerian_has_only_classical_element_fields_without_epoch() -> None:
    assert [field.name for field in fields(orbits.KeplerianElements)] == [
        "semi_major_axis_m",
        "eccentricity",
        "inclination_deg",
        "argument_of_periapsis_deg",
        "raan_deg",
        "true_anomaly_deg",
    ]


def test_keplerian_to_wire_matches_fixture_classical_order() -> None:
    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

    assert_canonical_equal(
        orbit.to_wire(),
        [
            6778137.0,
            0.001,
            28.5,
            0.0,
            0.0,
            0.0,
        ],
    )


def test_keplerian_is_not_sequence_like() -> None:
    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

    with pytest.raises(TypeError):
        iter(orbit)

    with pytest.raises(TypeError):
        orbit[0]


def test_keplerian_requires_named_scalar_arguments() -> None:
    with pytest.raises(TypeError):
        orbits.keplerian([6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0])

    with pytest.raises(TypeError):
        orbits.KeplerianElements(6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0)


def test_cartesian_state_constructor_returns_frozen_dataclass() -> None:
    state = orbits.cartesian_state(
        x_m=7000000.0,
        y_m=1000.0,
        z_m=2000.0,
        vx_m_s=-1.0,
        vy_m_s=7500.0,
        vz_m_s=10.0,
    )

    assert isinstance(state, orbits.CartesianState)
    assert is_dataclass(state)
    assert state.x_m == 7000000.0
    assert state.y_m == 1000.0
    assert state.z_m == 2000.0
    assert state.vx_m_s == -1.0
    assert state.vy_m_s == 7500.0
    assert state.vz_m_s == 10.0

    with pytest.raises(FrozenInstanceError):
        state.x_m = 0.0


def test_cartesian_state_has_only_position_and_velocity_fields() -> None:
    assert [field.name for field in fields(orbits.CartesianState)] == [
        "x_m",
        "y_m",
        "z_m",
        "vx_m_s",
        "vy_m_s",
        "vz_m_s",
    ]


def test_cartesian_state_to_wire_matches_astrox_cartesian_order() -> None:
    state = orbits.cartesian_state(
        x_m=7000000.0,
        y_m=1000.0,
        z_m=2000.0,
        vx_m_s=-1.0,
        vy_m_s=7500.0,
        vz_m_s=10.0,
    )

    assert_canonical_equal(
        state.to_wire(),
        [7000000.0, 1000.0, 2000.0, -1.0, 7500.0, 10.0],
    )


def test_cartesian_state_requires_named_scalar_arguments() -> None:
    with pytest.raises(TypeError):
        orbits.cartesian_state([7000000.0, 1000.0, 2000.0, -1.0, 7500.0, 10.0])

    with pytest.raises(TypeError):
        orbits.CartesianState(7000000.0, 1000.0, 2000.0, -1.0, 7500.0, 10.0)
