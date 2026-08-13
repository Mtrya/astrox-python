#!/usr/bin/env python3
"""Live snapshot validation for CRTBP and libration functions."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import libration  # noqa: E402
from tests.validation._support import (  # noqa: E402
    LiveSnapshotCase,
    SnapshotError,
    check_snapshot,
    configure_astrox_from_env,
    describe_json_shape,
    main as snapshot_main,
    to_json_compatible,
)


SNAPSHOT_PATH = Path(__file__).with_name("libration.snap.json")
EARTH_MOON_MASS_RATIO = 0.01215058560962404
PRIMARY_STATE = libration.crtbp_state(
    x=1.189017399646985,
    y=0.0,
    z=0.06060558718057466,
    vx=0.0,
    vy=-0.17403902743307584,
    vz=0.0,
)
BARYCENTRIC_STATE = libration.crtbp_state(
    x=PRIMARY_STATE.x - EARTH_MOON_MASS_RATIO,
    y=PRIMARY_STATE.y,
    z=PRIMARY_STATE.z,
    vx=PRIMARY_STATE.vx,
    vy=PRIMARY_STATE.vy,
    vz=PRIMARY_STATE.vz,
)
L1_STATE = libration.crtbp_state(
    x=0.835995246366249,
    y=0.0,
    z=0.05,
    vx=0.0,
    vy=0.15970397512870477,
    vz=0.0,
)
L1_PERIOD = 2.7585313527865214
L2_STATE = libration.crtbp_state(
    x=1.1,
    y=0.0,
    z=0.20193513798221166,
    vx=0.0,
    vy=-0.2058727734568767,
    vz=0.0,
)
L2_PERIOD = 2.4570041123164748
DRO_STATE = libration.crtbp_state(
    x=1.1801,
    y=0.0,
    z=0.0,
    vx=0.0,
    vy=-0.4881416417479895,
    vz=0.0,
)
DRO_PERIOD = 3.004683468879153


def _shape(value: Any, *, field: str) -> dict[str, Any]:
    return describe_json_shape(to_json_compatible(value), field=field)


def points_shape() -> dict[str, Any]:
    result = libration.positions(mass_ratio=EARTH_MOON_MASS_RATIO)
    if result.l4.y <= 0.0 or result.l5.y >= 0.0:
        raise SnapshotError("L4/L5 y signs do not match the maintained branch ordering")
    return {"shape": _shape(result, field="libration points")}


def units_shape() -> dict[str, Any]:
    result = libration.units(
        primary_gravitational_parameter_m3_s2=398600441800000.0,
        secondary_gravitational_parameter_m3_s2=4904869500000.0,
        mean_separation_m=384400000.0,
    )
    if min(result.length_unit_m, result.time_unit_s, result.velocity_unit_m_s) <= 0.0:
        raise SnapshotError("libration unit scales must be positive")
    return {"shape": _shape(result, field="libration units")}


def trajectory_shape(
    *,
    initial_state: libration.CrtbpState,
    start_time: float,
    end_time: float,
    barycentric: bool,
    output_step: float,
) -> dict[str, Any]:
    result = libration.crtbp_trajectory(
        initial_state=initial_state,
        mass_ratio=EARTH_MOON_MASS_RATIO,
        start_time=start_time,
        end_time=end_time,
        barycentric=barycentric,
        output_step=output_step,
    )
    if result.is_barycentric is not barycentric:
        raise SnapshotError("trajectory response did not echo the requested origin")
    if not result.samples:
        raise SnapshotError("trajectory response must contain samples")
    if not math.isclose(result.samples[0].time, start_time, abs_tol=1.0e-14):
        raise SnapshotError("trajectory response did not begin at start_time")
    if not math.isclose(result.samples[-1].time, end_time, abs_tol=1.0e-14):
        raise SnapshotError("trajectory response did not end at end_time")
    return {
        "shape": _shape(result, field="CRTBP trajectory"),
        "is_barycentric": result.is_barycentric,
        "sample_count": len(result.samples),
        "time_direction": "forward" if end_time > start_time else "reverse",
    }


def adaptive_trajectory_shape() -> dict[str, Any]:
    result = libration.crtbp_trajectory(
        initial_state=PRIMARY_STATE,
        mass_ratio=EARTH_MOON_MASS_RATIO,
        start_time=0.0,
        end_time=0.2,
        barycentric=False,
        output_step=0.0,
    )
    if len(result.samples) < 2:
        raise SnapshotError("adaptive trajectory response must contain at least two samples")
    return {
        "shape": _shape(result, field="adaptive CRTBP trajectory"),
        "is_barycentric": result.is_barycentric,
        "sample_count_is_positive": bool(result.samples),
    }


def periodic_shape(result: libration.PeriodicOrbit, *, expected_origin: bool) -> dict[str, Any]:
    if result.is_barycentric is not expected_origin:
        raise SnapshotError("periodic-orbit response did not echo the expected origin")
    if not result.samples:
        raise SnapshotError("periodic-orbit response must contain samples")
    if not math.isclose(result.samples[0].time, 0.0, abs_tol=1.0e-14):
        raise SnapshotError("periodic-orbit samples must begin at zero")
    if not math.isclose(result.samples[-1].time, result.period, abs_tol=1.0e-12):
        raise SnapshotError("periodic-orbit samples must end at Period")
    return {
        "shape": _shape(result, field="periodic orbit"),
        "is_barycentric": result.is_barycentric,
        "sample_count_is_positive": bool(result.samples),
    }


def l1_shape(*, southern: bool) -> dict[str, Any]:
    return periodic_shape(
        libration.earth_moon_l1_halo(z_amplitude=0.05, southern=southern),
        expected_origin=False,
    )


def l2_shape(*, southern: bool) -> dict[str, Any]:
    return periodic_shape(
        libration.earth_moon_l2_halo(x_amplitude=0.10, southern=southern),
        expected_origin=False,
    )


def dro_shape() -> dict[str, Any]:
    return periodic_shape(
        libration.earth_moon_dro(x_amplitude=0.1801),
        expected_origin=False,
    )


def corrected_shape(
    *,
    initial_state: libration.CrtbpState,
    period_guess: float,
    barycentric: bool,
) -> dict[str, Any]:
    if barycentric:
        initial_state = libration.crtbp_state(
            x=initial_state.x - EARTH_MOON_MASS_RATIO,
            y=initial_state.y,
            z=initial_state.z,
            vx=initial_state.vx,
            vy=initial_state.vy,
            vz=initial_state.vz,
        )
    return periodic_shape(
        libration.correct_periodic_orbit_fixed_x(
            initial_state=initial_state,
            period_guess=period_guess,
            mass_ratio=EARTH_MOON_MASS_RATIO,
            barycentric=barycentric,
            output_step=0.05,
        ),
        expected_origin=barycentric,
    )


CASES = [
    LiveSnapshotCase(
        id="positions_earth_moon_named_points",
        description="Named five-point shape decoded from the Earth-Moon packed response.",
        run=points_shape,
    ),
    LiveSnapshotCase(
        id="units_earth_moon_explicit_parameters",
        description="Named mass-ratio and dimensional scale fields for explicit Earth-Moon parameters.",
        run=units_shape,
    ),
    LiveSnapshotCase(
        id="trajectory_primary_centered_forward_fixed_step",
        description="Primary-centered forward trajectory using a fixed nondimensional output step.",
        run=lambda: trajectory_shape(
            initial_state=PRIMARY_STATE,
            start_time=0.0,
            end_time=0.2,
            barycentric=False,
            output_step=0.1,
        ),
    ),
    LiveSnapshotCase(
        id="trajectory_barycentric_forward_fixed_step",
        description="Barycentric forward trajectory using the independently shifted initial x coordinate.",
        run=lambda: trajectory_shape(
            initial_state=BARYCENTRIC_STATE,
            start_time=0.0,
            end_time=0.2,
            barycentric=True,
            output_step=0.1,
        ),
    ),
    LiveSnapshotCase(
        id="trajectory_primary_centered_reverse_fixed_step",
        description="Primary-centered reverse trajectory from the maintained forward endpoint.",
        run=lambda: trajectory_shape(
            initial_state=libration.crtbp_state(
                x=1.1858521851789159,
                y=-0.03411863250063764,
                z=0.05802670310302977,
                vx=-0.031129245925864593,
                vy=-0.1637429285613642,
                vz=-0.02565088873596596,
            ),
            start_time=0.2,
            end_time=0.0,
            barycentric=False,
            output_step=0.1,
        ),
    ),
    LiveSnapshotCase(
        id="trajectory_primary_centered_adaptive_nodes",
        description="Primary-centered trajectory preserving the OutStep=0 adaptive-node branch.",
        run=adaptive_trajectory_shape,
    ),
    LiveSnapshotCase(
        id="earth_moon_l1_halo_northern",
        description="Northern Earth-Moon L1 Halo periodic-result shape.",
        run=lambda: l1_shape(southern=False),
    ),
    LiveSnapshotCase(
        id="earth_moon_l1_halo_southern",
        description="Southern Earth-Moon L1 Halo periodic-result shape.",
        run=lambda: l1_shape(southern=True),
    ),
    LiveSnapshotCase(
        id="earth_moon_l2_halo_northern",
        description="Northern Earth-Moon L2 Halo periodic-result shape.",
        run=lambda: l2_shape(southern=False),
    ),
    LiveSnapshotCase(
        id="earth_moon_l2_halo_southern",
        description="Southern Earth-Moon L2 Halo periodic-result shape.",
        run=lambda: l2_shape(southern=True),
    ),
    LiveSnapshotCase(
        id="earth_moon_dro_planar",
        description="Planar Earth-Moon distant-retrograde periodic-result shape.",
        run=dro_shape,
    ),
    LiveSnapshotCase(
        id="fixed_x_l1_primary_centered",
        description="Successful fixed-x correction of an L1 Halo seed in the primary-centered origin.",
        run=lambda: corrected_shape(
            initial_state=L1_STATE,
            period_guess=L1_PERIOD,
            barycentric=False,
        ),
    ),
    LiveSnapshotCase(
        id="fixed_x_l1_barycentric",
        description="Successful fixed-x correction of the same L1 Halo seed in the barycentric origin.",
        run=lambda: corrected_shape(
            initial_state=L1_STATE,
            period_guess=L1_PERIOD,
            barycentric=True,
        ),
    ),
    LiveSnapshotCase(
        id="fixed_x_l2_primary_centered",
        description="Successful fixed-x correction of an L2 Halo seed in the primary-centered origin.",
        run=lambda: corrected_shape(
            initial_state=L2_STATE,
            period_guess=L2_PERIOD,
            barycentric=False,
        ),
    ),
    LiveSnapshotCase(
        id="fixed_x_dro_primary_centered",
        description="Successful fixed-x correction of a DRO seed in the primary-centered origin.",
        run=lambda: corrected_shape(
            initial_state=DRO_STATE,
            period_guess=DRO_PERIOD,
            barycentric=False,
        ),
    ),
]


def test_libration_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


def _main() -> int:
    try:
        return snapshot_main(cases=CASES, snapshot_path=SNAPSHOT_PATH)
    except Exception as exc:
        print(f"LIVE_SNAPSHOT_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
