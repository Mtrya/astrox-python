"""Shared samples and assertions for propagator behavior tests."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pytest

from astrox import propagator
from tests.sdk.helpers import assert_canonical_equal, canonical_bytes


__all__ = [
    "BALLISTIC_BRANCH_REQUESTS",
    "BALLISTIC_NOMINAL_REQUEST",
    "J2_REQUEST",
    "REPRESENTATIVE_FIXED_PROPAGATOR_RESPONSE",
    "REPRESENTATIVE_FIXED_RETURN_SNAPSHOT",
    "REPRESENTATIVE_PROPAGATOR_RESPONSE",
    "REPRESENTATIVE_RETURN_SNAPSHOT",
    "SGP4_REQUEST",
    "SIMPLE_ASCENT_REQUEST",
    "TWO_BODY_REQUEST",
    "assert_canonical_equal",
    "canonical_bytes",
    "record_raw_post",
    "return_snapshot",
]


REPRESENTATIVE_PROPAGATOR_RESPONSE: dict[str, Any] = {
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

REPRESENTATIVE_FIXED_PROPAGATOR_RESPONSE: dict[str, Any] = {
    **REPRESENTATIVE_PROPAGATOR_RESPONSE,
    "Position": {
        **REPRESENTATIVE_PROPAGATOR_RESPONSE["Position"],
        "epoch": "2024-01-01T12:00:00.000Z",
        "referenceFrame": "Fixed",
    },
}

REPRESENTATIVE_RETURN_SNAPSHOT: dict[str, Any] = {
    "period_s": 600.0,
    "position": {
        "central_body": "Earth",
        "epoch": "2024-01-01T00:00:00.000Z",
        "reference_frame": "Inertial",
        "interpolation_algorithm": "Lagrange",
        "interpolation_degree": 5,
        "cartesian_velocity": [0.0, 1.0, 2.0, 3.0],
    },
}

REPRESENTATIVE_FIXED_RETURN_SNAPSHOT: dict[str, Any] = {
    **REPRESENTATIVE_RETURN_SNAPSHOT,
    "position": {
        **REPRESENTATIVE_RETURN_SNAPSHOT["position"],
        "epoch": "2024-01-01T12:00:00.000Z",
        "reference_frame": "Fixed",
    },
}

J2_REQUEST: dict[str, Any] = {
    "Start": "2024-01-01T00:00:00.000Z",
    "Stop": "2024-01-01T00:10:00.000Z",
    "Step": 300.0,
    "OrbitEpoch": "2024-01-01T00:00:00.000Z",
    "CoordSystem": "Inertial",
    "CoordType": "Classical",
    "J2NormalizedValue": 0.000484165143790815,
    "RefDistance": 6378137.0,
    "GravitationalParameter": 398600441500000.0,
    "OrbitalElements": [6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0],
}

TWO_BODY_REQUEST: dict[str, Any] = {
    "Start": "2024-01-01T00:00:00.000Z",
    "Stop": "2024-01-01T00:10:00.000Z",
    "Step": 300.0,
    "OrbitEpoch": "2024-01-01T00:00:00.000Z",
    "CoordSystem": "Inertial",
    "CoordType": "Classical",
    "GravitationalParameter": 398600441500000.0,
    "OrbitalElements": [6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0],
}

BALLISTIC_NOMINAL_REQUEST: dict[str, Any] = {
    "Start": "2024-01-01T12:00:00.000Z",
    "Step": 30.0,
    "LaunchLatitude": 28.5721,
    "LaunchLongitude": -80.648,
    "LaunchAltitude": 10.0,
    "ImpactLatitude": 30.0,
    "ImpactLongitude": -70.0,
    "ImpactAltitude": 0.0,
}

BALLISTIC_BRANCH_REQUESTS: dict[str, dict[str, Any]] = {
    "DeltaV": {
        **BALLISTIC_NOMINAL_REQUEST,
        "BallisticType": "DeltaV",
        "BallisticTypeValue": 3000.0,
    },
    "DeltaV_MinEcc": {
        **BALLISTIC_NOMINAL_REQUEST,
        "BallisticType": "DeltaV_MinEcc",
        "BallisticTypeValue": 3000.0,
    },
    "ApogeeAlt": {
        **BALLISTIC_NOMINAL_REQUEST,
        "BallisticType": "ApogeeAlt",
        "BallisticTypeValue": 200000.0,
    },
    "TimeOfFlight": {
        **BALLISTIC_NOMINAL_REQUEST,
        "BallisticType": "TimeOfFlight",
        "BallisticTypeValue": 600.0,
    },
}

SGP4_REQUEST: dict[str, Any] = {
    "Start": "2024-01-01T00:00:00.000Z",
    "Stop": "2024-01-01T00:10:00.000Z",
    "Step": 300.0,
    "SatelliteNumber": "25544",
    "TLEs": [
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
        "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    ],
}

SIMPLE_ASCENT_REQUEST: dict[str, Any] = {
    "Start": "2024-01-01T03:00:00.000Z",
    "Stop": "2024-01-01T03:02:00.000Z",
    "Step": 30.0,
    "CentralBody": "Earth",
    "LaunchLatitude": 40.9575,
    "LaunchLongitude": 100.2912,
    "LaunchAltitude": 1000.0,
    "BurnoutVelocity": 7800.0,
    "BurnoutLatitude": 41.3,
    "BurnoutLongitude": 101.0,
    "BurnoutAltitude": 200000.0,
}


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, Any] = REPRESENTATIVE_PROPAGATOR_RESPONSE,
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, object]:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(propagator.raw, "post", fake_post)
    return calls


def return_snapshot(
    period_s: float,
    position: propagator.PropagatorPosition,
) -> dict[str, Any]:
    return {
        "period_s": period_s,
        "position": asdict(position),
    }
