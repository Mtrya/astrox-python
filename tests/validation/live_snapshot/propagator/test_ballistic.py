#!/usr/bin/env python3
"""Live snapshots for promoted ballistic propagator functions."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import propagator
from tests.validation._support import (
    ContractCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("ballistic.snap.json")


def _base_inputs() -> dict[str, float | str]:
    return {
        "start": "2024-01-01T12:00:00.000Z",
        "step_s": 30.0,
        "launch_latitude_deg": 28.5721,
        "launch_longitude_deg": -80.648,
        "launch_altitude_m": 10.0,
        "impact_latitude_deg": 30.0,
        "impact_longitude_deg": -70.0,
        "impact_altitude_m": 0.0,
    }


def nominal() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.ballistic(**_base_inputs())


def delta_v() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.ballistic_delta_v(**_base_inputs(), delta_v_m_s=3000.0)


def delta_v_min_ecc() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.ballistic_delta_v_min_ecc(**_base_inputs(), delta_v_m_s=3000.0)


def apogee_altitude() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.ballistic_apogee_altitude(
        **_base_inputs(),
        apogee_altitude_m=200000.0,
    )


def time_of_flight() -> tuple[float, propagator.PropagatorPosition]:
    return propagator.ballistic_time_of_flight(
        **_base_inputs(),
        time_of_flight_s=600.0,
    )


CASES = [
    ContractCase(
        id="nominal",
        description="Nominal ballistic trajectory without an explicit branch discriminator.",
        run=nominal,
    ),
    ContractCase(
        id="delta_v",
        description="Ballistic trajectory branch constrained by launch delta-v.",
        run=delta_v,
    ),
    ContractCase(
        id="delta_v_min_ecc",
        description="Ballistic trajectory branch constrained by launch delta-v with minimum eccentricity.",
        run=delta_v_min_ecc,
    ),
    ContractCase(
        id="apogee_altitude",
        description="Ballistic trajectory branch constrained by apogee altitude.",
        run=apogee_altitude,
    ),
    ContractCase(
        id="time_of_flight",
        description="Ballistic trajectory branch constrained by time of flight.",
        run=time_of_flight,
    ),
]


def test_ballistic_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
