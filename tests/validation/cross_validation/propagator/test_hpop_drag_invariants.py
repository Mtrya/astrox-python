#!/usr/bin/env python3
"""Live ASTROX HPOP atmosphere/drag branch invariants."""

# Coverage:
#   Branches:
#     - HPOP Jacchia-Roberts atmosphere with spherical drag: partial
#   Fields:
#     - Position.cartesian_velocity time/position/velocity samples: partial
#   Parameters:
#     - AtmosphericModel JacchiaRoberts constant-values fields: partial
#     - CoefficientOfDrag and AreaMassRatioDrag: partial
#   Comparison:
#     - Strong invariant: zero drag area with atmosphere present matches no-atmosphere propagation
#     - Strong invariant: positive drag area changes the trajectory and lowers specific mechanical energy relative to the no-drag counterpart
#   Unresolved:
#     - Same-model comparison against GMAT/Orekit remains unavailable in this repo state: the GMAT driver still lacks atmosphere-model mapping, and Orekit 13.1.5 does not expose a Jacchia-Roberts atmosphere class through orekit-jpype

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
EARTH_MU = 398600441500000.0
ZERO_DRAG_STATE_ABS = 1.0e-9
POSITIVE_DRAG_FINAL_STATE_MIN_M = 1.0
POSITIVE_DRAG_ENERGY_MAX_J_KG = -1.0


@dataclass(frozen=True, kw_only=True)
class StateSample:
    offset_s: float
    cartesian_m_m_s: tuple[float, float, float, float, float, float]


class CrossValidationError(Exception):
    """Raised when ASTROX HPOP drag invariants fail."""


def low_leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6678137.0,
        eccentricity=0.001,
        inclination_deg=51.6,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )


def fixed_step_integrator() -> propagator.HpopIntegrator:
    return propagator.hpop_rkf78(
        use_fixed_step=True,
        initial_step_s=60.0,
        max_step_s=60.0,
        min_step_s=0.001,
        max_abs_error=1.0e-10,
        max_rel_error=1.0e-12,
        max_iterations=50,
    )


def atmosphere_config() -> propagator.HpopJacchiaRoberts:
    return propagator.hpop_jacchia_roberts(
        drag_model_type="Spherical",
        atmos_data_source="Constant Values",
        f10p7=150.0,
        f10p7_avg=150.0,
        kp=3.0,
    )


def hpop_config(
    atmosphere: propagator.HpopJacchiaRoberts | None,
) -> propagator.HpopConfig:
    return propagator.hpop_config(
        integrator=fixed_step_integrator(),
        gravity=propagator.hpop_two_body_gravity(),
        atmosphere=atmosphere,
    )


def astrox_hpop_samples(
    *,
    area_mass_ratio_drag_m2_kg: float,
    include_atmosphere: bool,
) -> dict[float, StateSample]:
    _, position = propagator.hpop(
        start=START,
        stop=STOP,
        orbit_epoch=START,
        orbit=low_leo_orbit(),
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU,
        coefficient_of_drag=2.2,
        area_mass_ratio_drag_m2_kg=area_mass_ratio_drag_m2_kg,
        coefficient_of_srp=1.0,
        area_mass_ratio_srp_m2_kg=0.0,
        config=hpop_config(atmosphere_config() if include_atmosphere else None),
    )
    return samples_from_astrox(position.cartesian_velocity)


def samples_from_astrox(cartesian_velocity: tuple[float, ...]) -> dict[float, StateSample]:
    if len(cartesian_velocity) % 7 != 0:
        raise CrossValidationError("ASTROX cartesian_velocity length is not divisible by 7")
    samples: dict[float, StateSample] = {}
    for index in range(0, len(cartesian_velocity), 7):
        offset_s = float(cartesian_velocity[index])
        samples[offset_s] = StateSample(
            offset_s=offset_s,
            cartesian_m_m_s=tuple(
                float(value) for value in cartesian_velocity[index + 1 : index + 7]
            ),
        )
    return samples


def compare_drag_invariants() -> None:
    no_atmosphere = astrox_hpop_samples(
        area_mass_ratio_drag_m2_kg=0.0,
        include_atmosphere=False,
    )
    zero_drag_area = astrox_hpop_samples(
        area_mass_ratio_drag_m2_kg=0.0,
        include_atmosphere=True,
    )
    positive_drag_area = astrox_hpop_samples(
        area_mass_ratio_drag_m2_kg=0.02,
        include_atmosphere=True,
    )

    failures: list[str] = []
    for offset_s, no_drag_sample in no_atmosphere.items():
        zero_drag_sample = require_sample(zero_drag_area, offset_s, label="zero_drag_area")
        zero_drag_error = max_abs_state_error(
            no_drag_sample.cartesian_m_m_s,
            zero_drag_sample.cartesian_m_m_s,
        )
        if zero_drag_error > ZERO_DRAG_STATE_ABS:
            failures.append(
                f"offset_s={offset_s:g} zero drag area differs from no-atmosphere by {zero_drag_error:.12g}, tolerance {ZERO_DRAG_STATE_ABS:.12g}"
            )

    final_offset_s = max(no_atmosphere)
    final_no_drag = no_atmosphere[final_offset_s]
    final_positive_drag = require_sample(
        positive_drag_area,
        final_offset_s,
        label="positive_drag_area",
    )
    final_state_delta = max_abs_state_error(
        final_no_drag.cartesian_m_m_s,
        final_positive_drag.cartesian_m_m_s,
    )
    if final_state_delta < POSITIVE_DRAG_FINAL_STATE_MIN_M:
        failures.append(
            f"positive drag final state delta {final_state_delta:.12g} is below expected minimum {POSITIVE_DRAG_FINAL_STATE_MIN_M:.12g}"
        )
    energy_delta = specific_mechanical_energy(final_positive_drag.cartesian_m_m_s) - specific_mechanical_energy(
        final_no_drag.cartesian_m_m_s
    )
    if energy_delta > POSITIVE_DRAG_ENERGY_MAX_J_KG:
        failures.append(
            f"positive drag final specific-energy delta {energy_delta:.12g} J/kg is not <= {POSITIVE_DRAG_ENERGY_MAX_J_KG:.12g} J/kg"
        )
    if failures:
        raise CrossValidationError("\n".join(failures))


def require_sample(
    samples: dict[float, StateSample],
    offset_s: float,
    *,
    label: str,
) -> StateSample:
    if offset_s not in samples:
        raise CrossValidationError(f"{label} missing sample at offset_s={offset_s:g}")
    return samples[offset_s]


def max_abs_state_error(
    left: tuple[float, float, float, float, float, float],
    right: tuple[float, float, float, float, float, float],
) -> float:
    return max(abs(a - b) for a, b in zip(left, right, strict=True))


def specific_mechanical_energy(
    state: tuple[float, float, float, float, float, float],
) -> float:
    x_m, y_m, z_m, vx_m_s, vy_m_s, vz_m_s = state
    radius_m = math.sqrt(x_m * x_m + y_m * y_m + z_m * z_m)
    speed_squared_m2_s2 = vx_m_s * vx_m_s + vy_m_s * vy_m_s + vz_m_s * vz_m_s
    return 0.5 * speed_squared_m2_s2 - EARTH_MU / radius_m


def test_hpop_jacchia_roberts_drag_branch_invariants() -> None:
    configure_astrox_from_env()
    compare_drag_invariants()


def main() -> int:
    try:
        test_hpop_jacchia_roberts_drag_branch_invariants()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
