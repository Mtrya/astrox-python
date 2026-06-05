"""Shared samples for orbit behavior tests."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pytest

from astrox import orbits
from tests.sdk.helpers import assert_canonical_equal


__all__ = [
    "EARTH_MU",
    "KEPLERIAN_WIRE",
    "MEAN_ELEMENTS_RESPONSE",
    "MEAN_ELEMENTS_SNAPSHOT",
    "REPRESENTATIVE_CARTESIAN_RESPONSE",
    "REPRESENTATIVE_CARTESIAN_SNAPSHOT",
    "REPRESENTATIVE_KEPLERIAN_RESPONSE",
    "REPRESENTATIVE_KEPLERIAN_SNAPSHOT",
    "REPRESENTATIVE_WALKER_RESPONSE",
    "REPRESENTATIVE_WALKER_SNAPSHOT",
    "REPRESENTATIVE_WIZARD_RESPONSE",
    "REPRESENTATIVE_WIZARD_SNAPSHOT",
    "TARGET_KEPLERIAN_WIRE",
    "assert_canonical_equal",
    "cartesian_snapshot",
    "keplerian_snapshot",
    "mean_keplerian_snapshot",
    "record_raw_post",
    "sample_cartesian_state",
    "sample_orbit",
    "target_orbit",
    "walker_snapshot",
]


EARTH_MU = 398600441500000.0

KEPLERIAN_WIRE: dict[str, Any] = {
    "SemimajorAxis": 6778137.0,
    "Eccentricity": 0.001,
    "Inclination": 28.5,
    "ArgumentOfPeriapsis": 0.0,
    "RightAscensionOfAscendingNode": 15.0,
    "TrueAnomaly": 45.0,
}

TARGET_KEPLERIAN_WIRE: dict[str, Any] = {
    "SemimajorAxis": 42164000.0,
    "Eccentricity": 0.0001,
    "Inclination": 0.5,
    "ArgumentOfPeriapsis": 10.0,
    "RightAscensionOfAscendingNode": 75.0,
    "TrueAnomaly": 180.0,
}

REPRESENTATIVE_CARTESIAN_RESPONSE = [
    6114454.0,
    2870352.0,
    3308542.0,
    -3548.0,
    6463.0,
    1830.0,
]

REPRESENTATIVE_CARTESIAN_SNAPSHOT = {
    "x_m": 6114454.0,
    "y_m": 2870352.0,
    "z_m": 3308542.0,
    "vx_m_s": -3548.0,
    "vy_m_s": 6463.0,
    "vz_m_s": 1830.0,
}

REPRESENTATIVE_KEPLERIAN_RESPONSE: dict[str, Any] = {
    "SemimajorAxis": 6778137.0,
    "Eccentricity": 0.001,
    "Inclination": 28.5,
    "ArgumentOfPeriapsis": 0.2,
    "RightAscensionOfAscendingNode": 15.5,
    "TrueAnomaly": 46.0,
    "GravitationalParameter": 398600441800000.0,
}

REPRESENTATIVE_KEPLERIAN_SNAPSHOT = {
    "semi_major_axis_m": 6778137.0,
    "eccentricity": 0.001,
    "inclination_deg": 28.5,
    "argument_of_periapsis_deg": 0.2,
    "raan_deg": 15.5,
    "true_anomaly_deg": 46.0,
}

MEAN_ELEMENTS_RESPONSE: dict[str, Any] = {
    "SemimajorAxis": 6778120.0,
    "Eccentricity": 0.0009,
    "Inclination": 28.499,
    "ArgOfPerigee": 0.1,
    "RAAN": 15.25,
    "MeanAnomaly": 44.75,
    "ArgOfLatitude": 44.85,
    "LongitudeOfPerigee": 15.35,
    "MeanLongitude": 60.1,
}

MEAN_ELEMENTS_SNAPSHOT = {
    "semi_major_axis_m": 6778120.0,
    "eccentricity": 0.0009,
    "inclination_deg": 28.499,
    "argument_of_perigee_deg": 0.1,
    "raan_deg": 15.25,
    "mean_anomaly_deg": 44.75,
    "argument_of_latitude_deg": 44.85,
    "longitude_of_perigee_deg": 15.35,
    "mean_longitude_deg": 60.1,
}

REPRESENTATIVE_WIZARD_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "Success",
    "Elements_TOD": {
        **REPRESENTATIVE_KEPLERIAN_RESPONSE,
        "RightAscensionOfAscendingNode": 101.0,
        "TrueAnomaly": 10.0,
    },
    "Elements_Inertial": {
        **REPRESENTATIVE_KEPLERIAN_RESPONSE,
        "RightAscensionOfAscendingNode": 100.5,
        "TrueAnomaly": 9.5,
    },
}

REPRESENTATIVE_WIZARD_SNAPSHOT = [
    {
        **REPRESENTATIVE_KEPLERIAN_SNAPSHOT,
        "raan_deg": 101.0,
        "true_anomaly_deg": 10.0,
    },
    {
        **REPRESENTATIVE_KEPLERIAN_SNAPSHOT,
        "raan_deg": 100.5,
        "true_anomaly_deg": 9.5,
    },
]

REPRESENTATIVE_WALKER_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "Success",
    "WalkerSatellites": [
        [
            {
                **REPRESENTATIVE_KEPLERIAN_RESPONSE,
                "RightAscensionOfAscendingNode": 0.0,
                "TrueAnomaly": 0.0,
            },
            {
                **REPRESENTATIVE_KEPLERIAN_RESPONSE,
                "RightAscensionOfAscendingNode": 0.0,
                "TrueAnomaly": 180.0,
            },
        ],
        [
            {
                **REPRESENTATIVE_KEPLERIAN_RESPONSE,
                "RightAscensionOfAscendingNode": 60.0,
                "TrueAnomaly": 45.0,
            }
        ],
    ],
}

REPRESENTATIVE_WALKER_SNAPSHOT = [
    [
        {
            **REPRESENTATIVE_KEPLERIAN_SNAPSHOT,
            "raan_deg": 0.0,
            "true_anomaly_deg": 0.0,
        },
        {
            **REPRESENTATIVE_KEPLERIAN_SNAPSHOT,
            "raan_deg": 0.0,
            "true_anomaly_deg": 180.0,
        },
    ],
    [
        {
            **REPRESENTATIVE_KEPLERIAN_SNAPSHOT,
            "raan_deg": 60.0,
            "true_anomaly_deg": 45.0,
        }
    ],
]


def sample_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def target_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=42164000.0,
        eccentricity=0.0001,
        inclination_deg=0.5,
        argument_of_periapsis_deg=10.0,
        raan_deg=75.0,
        true_anomaly_deg=180.0,
    )


def sample_cartesian_state() -> orbits.CartesianState:
    return orbits.cartesian_state(
        x_m=6114454.0,
        y_m=2870352.0,
        z_m=3308542.0,
        vx_m_s=-3548.0,
        vy_m_s=6463.0,
        vz_m_s=1830.0,
    )


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> object:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(orbits.raw, "post", fake_post)
    return calls


def keplerian_snapshot(elements: orbits.KeplerianElements) -> dict[str, Any]:
    return asdict(elements)


def mean_keplerian_snapshot(elements: orbits.MeanKeplerianElements) -> dict[str, Any]:
    return asdict(elements)


def cartesian_snapshot(state: orbits.CartesianState) -> dict[str, Any]:
    return asdict(state)


def walker_snapshot(
    walker: tuple[tuple[orbits.KeplerianElements, ...], ...],
) -> list[list[dict[str, Any]]]:
    return [
        [keplerian_snapshot(satellite) for satellite in plane]
        for plane in walker
    ]
