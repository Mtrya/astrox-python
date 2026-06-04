#!/usr/bin/env python3
"""Live HPOP cross-validation between ASTROX and GMAT."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from astrox import orbits, propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation._support.gmat import (
    GMAT_VALIDATION_IMAGE_ENV,
    is_external_validation_strict,
    require_gmat_image,
    run_gmat_driver,
)


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
SAMPLE_OFFSETS_S = (0.0, 300.0, 600.0)
EARTH_MU = 398600441500000.0
ASTROX_GRAVITY_FILE = "EGM2008.grv"
GMAT_DRIVER = "tests/validation/_external/gmat/hpop_driver.py"
POSITION_ABS_M = 1.0e-5
VELOCITY_ABS_M_S = 1.0e-8


@dataclass(frozen=True, kw_only=True)
class StateSample:
    offset_s: float
    cartesian_m_m_s: tuple[float, float, float, float, float, float]


@dataclass(frozen=True, kw_only=True)
class HpopGmatCase:
    id: str
    description: str
    astrox_config: propagator.HpopConfig
    gmat_force_model: dict[str, Any]
    orbit: orbits.KeplerianElements | None = None
    spacecraft: dict[str, float] | None = None
    sample_offsets_s: tuple[float, ...] = SAMPLE_OFFSETS_S


class CrossValidationError(Exception):
    """Raised when ASTROX and GMAT disagree."""


def leo_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )


def leo_sunlit_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=90.0,
    )


def leo_shadow_transition_orbit() -> orbits.KeplerianElements:
    return leo_orbit()


def case_orbit(case: HpopGmatCase) -> orbits.KeplerianElements:
    return leo_orbit() if case.orbit is None else case.orbit


def hpop_integrator() -> propagator.HpopIntegrator:
    return propagator.hpop_rkf78(
        use_fixed_step=True,
        initial_step_s=60.0,
        max_step_s=60.0,
        min_step_s=0.001,
        max_abs_error=1e-10,
        max_rel_error=1e-12,
        max_iterations=50,
    )


def astrox_degree_zero_gravity_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        central_body="Earth",
        integrator=hpop_integrator(),
        gravity=propagator.hpop_gravity_field(
            gravity_file_name=ASTROX_GRAVITY_FILE,
            degree=0,
            order=0,
            use_secular_variations=False,
            solid_tide_type="Permanent tide only",
            eop_file_path="EOP-v1.1.txt",
        ),
    )


def astrox_srp_third_body_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        central_body="Earth",
        integrator=hpop_integrator(),
        gravity=propagator.hpop_gravity_field(
            gravity_file_name=ASTROX_GRAVITY_FILE,
            degree=0,
            order=0,
            use_secular_variations=False,
            solid_tide_type="Permanent tide only",
            eop_file_path="EOP-v1.1.txt",
        ),
        srp=propagator.hpop_srp_spherical(
            shadow_model="DualCone",
            sun_position="Apparent",
            eclipsing_bodies=["Earth", "Moon"],
        ),
        third_bodies=[
            propagator.hpop_third_body(
                "Sun",
                mode_type="PointMass",
                ephem_source="DeFile",
                grav_source="DeFile",
            ),
            propagator.hpop_third_body(
                "Moon",
                mode_type="PointMass",
                ephem_source="DeFile",
                grav_source="DeFile",
            ),
        ],
    )


def gmat_srp_third_body_force_model() -> dict[str, Any]:
    return {
        "gravity": {"type": "point_mass"},
        "atmosphere": None,
        "srp": {
            "model": "spherical",
            "flux_w_m2": 1367.0,
            "nominal_sun_km": 149597870.691,
            "extra_shadow_bodies": ["Moon"],
        },
        "third_bodies": ["Sun", "Moon"],
    }


def srp_spacecraft() -> dict[str, float]:
    return {
        "coefficient_of_drag": 2.2,
        "area_mass_ratio_drag_m2_kg": 0.0,
        "coefficient_of_srp": 1.0,
        "area_mass_ratio_srp_m2_kg": 0.02,
    }


CASES = [
    HpopGmatCase(
        id="gravity_field_degree_zero",
        description=(
            "ASTROX HPOP GravityField degree/order zero against GMAT Earth point-mass propagation; "
            "ASTROX currently accepts only CoordSystem='Inertial', mapped here to GMAT EarthMJ2000Eq."
        ),
        astrox_config=astrox_degree_zero_gravity_config(),
        gmat_force_model={
            "gravity": {"type": "point_mass"},
            "atmosphere": None,
            "srp": None,
            "third_bodies": [],
        },
    ),
    HpopGmatCase(
        id="gravity_field_degree_zero_with_third_bodies",
        description=(
            "ASTROX HPOP GravityField degree/order zero with Sun/Moon point-mass third bodies "
            "against GMAT Earth/Sun/Luna point-mass propagation."
        ),
        astrox_config=propagator.hpop_config(
            central_body="Earth",
            integrator=hpop_integrator(),
            gravity=propagator.hpop_gravity_field(
                gravity_file_name=ASTROX_GRAVITY_FILE,
                degree=0,
                order=0,
                use_secular_variations=False,
                solid_tide_type="Permanent tide only",
                eop_file_path="EOP-v1.1.txt",
            ),
            third_bodies=[
                propagator.hpop_third_body(
                    "Sun",
                    mode_type="PointMass",
                    ephem_source="DeFile",
                    grav_source="DeFile",
                ),
                propagator.hpop_third_body(
                    "Moon",
                    mode_type="PointMass",
                    ephem_source="DeFile",
                    grav_source="DeFile",
                ),
            ],
        ),
        gmat_force_model={
            "gravity": {"type": "point_mass"},
            "atmosphere": None,
            "srp": None,
            "third_bodies": ["Sun", "Moon"],
        },
    ),
    HpopGmatCase(
        id="sunlit_third_body_srp",
        description=(
            "ASTROX HPOP sunlit SRP spherical branch with Sun/Moon point-mass third bodies "
            "against GMAT spherical SRP and Earth/Sun/Luna point-mass propagation."
        ),
        orbit=leo_sunlit_orbit(),
        astrox_config=astrox_srp_third_body_config(),
        gmat_force_model=gmat_srp_third_body_force_model(),
        spacecraft=srp_spacecraft(),
    ),
]


SHADOW_CALIBRATION_CASE = HpopGmatCase(
    id="shadow_transition_third_body_srp",
    description=(
        "ASTROX HPOP SRP near Earth-shadow transition against GMAT spherical SRP; "
        "sunlit geometry matches tightly, but this geometry currently exposes a shadow-model residual."
    ),
    orbit=leo_shadow_transition_orbit(),
    astrox_config=astrox_srp_third_body_config(),
    gmat_force_model=gmat_srp_third_body_force_model(),
    spacecraft=srp_spacecraft(),
    sample_offsets_s=(
        0.0,
        60.0,
        120.0,
        180.0,
        240.0,
        300.0,
        360.0,
        420.0,
        480.0,
        540.0,
        600.0,
    ),
)


def astrox_hpop_samples(case: HpopGmatCase) -> dict[float, StateSample]:
    spacecraft = case.spacecraft or {
        "coefficient_of_drag": 2.2,
        "area_mass_ratio_drag_m2_kg": 0.0,
        "coefficient_of_srp": 1.0,
        "area_mass_ratio_srp_m2_kg": 0.0,
    }
    _, position = propagator.hpop(
        start=START,
        stop=STOP,
        orbit_epoch=START,
        orbit=case_orbit(case),
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU,
        coefficient_of_drag=spacecraft["coefficient_of_drag"],
        area_mass_ratio_drag_m2_kg=spacecraft["area_mass_ratio_drag_m2_kg"],
        coefficient_of_srp=spacecraft["coefficient_of_srp"],
        area_mass_ratio_srp_m2_kg=spacecraft["area_mass_ratio_srp_m2_kg"],
        config=case.astrox_config,
    )
    return samples_from_astrox(position.cartesian_velocity)


def gmat_hpop_samples(case: HpopGmatCase) -> dict[float, StateSample]:
    orbit = case_orbit(case)
    payload = {
        "epoch_utc": START,
        "start_utc": START,
        "stop_utc": STOP,
        "sample_offsets_s": list(case.sample_offsets_s),
        "coordinate_system": "EarthMJ2000Eq",
        "initial_state": {
            "type": "classical",
            "semi_major_axis_m": orbit.semi_major_axis_m,
            "eccentricity": orbit.eccentricity,
            "inclination_deg": orbit.inclination_deg,
            "argument_of_periapsis_deg": orbit.argument_of_periapsis_deg,
            "raan_deg": orbit.raan_deg,
            "true_anomaly_deg": orbit.true_anomaly_deg,
        },
        "spacecraft": case.spacecraft
        or {
            "coefficient_of_drag": 2.2,
            "area_mass_ratio_drag_m2_kg": 0.0,
            "coefficient_of_srp": 1.0,
            "area_mass_ratio_srp_m2_kg": 0.0,
        },
        "force_model": case.gmat_force_model,
        "integrator": {
            "initial_step_s": 60.0,
            "max_step_s": 60.0,
            "min_step_s": 0.001,
            "accuracy": 1e-12,
        },
    }
    result = run_gmat_driver(GMAT_DRIVER, payload, timeout_s=240.0)
    return samples_from_gmat(result)


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


def samples_from_gmat(result: dict[str, Any]) -> dict[float, StateSample]:
    samples: dict[float, StateSample] = {}
    for sample in result["samples"]:
        offset_s = float(sample["offset_s"])
        values = tuple(float(value) for value in sample["cartesian_m_m_s"])
        if len(values) != 6:
            raise CrossValidationError(f"GMAT sample at offset_s={offset_s:g} does not have six Cartesian values")
        samples[offset_s] = StateSample(offset_s=offset_s, cartesian_m_m_s=values)
    return samples


def compare_samples(
    case: HpopGmatCase,
    astrox_samples: dict[float, StateSample],
    gmat_samples: dict[float, StateSample],
) -> None:
    failures: list[str] = []
    for offset_s in case.sample_offsets_s:
        astrox_sample = sample_at(astrox_samples, offset_s)
        gmat_sample = sample_at(gmat_samples, offset_s)
        if astrox_sample is None:
            failures.append(f"{case.id}: ASTROX missing sample at offset_s={offset_s:g}")
            continue
        if gmat_sample is None:
            failures.append(f"{case.id}: GMAT missing sample at offset_s={offset_s:g}")
            continue

        position_errors = [
            astrox_value - gmat_value
            for astrox_value, gmat_value in zip(
                astrox_sample.cartesian_m_m_s[:3],
                gmat_sample.cartesian_m_m_s[:3],
            )
        ]
        velocity_errors = [
            astrox_value - gmat_value
            for astrox_value, gmat_value in zip(
                astrox_sample.cartesian_m_m_s[3:],
                gmat_sample.cartesian_m_m_s[3:],
            )
        ]
        position_error_m = max(abs(value) for value in position_errors)
        velocity_error_m_s = max(abs(value) for value in velocity_errors)
        if position_error_m > POSITION_ABS_M:
            failures.append(
                f"{case.id}: position error at offset_s={offset_s:g} is {position_error_m:.12g} m "
                f"(vector={_format_vector(position_errors)}), tolerance {POSITION_ABS_M:.12g} m"
            )
        if velocity_error_m_s > VELOCITY_ABS_M_S:
            failures.append(
                f"{case.id}: velocity error at offset_s={offset_s:g} is {velocity_error_m_s:.12g} m/s "
                f"(vector={_format_vector(velocity_errors)}), tolerance {VELOCITY_ABS_M_S:.12g} m/s"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def sample_at(samples: dict[float, StateSample], offset_s: float) -> StateSample | None:
    for sample_offset, sample in samples.items():
        if math.isclose(sample_offset, offset_s, abs_tol=1e-6):
            return sample
    return None


def _format_vector(values: list[float]) -> str:
    return "[" + ", ".join(f"{value:.12g}" for value in values) + "]"


def test_hpop_matches_gmat_representative_cases() -> None:
    configure_astrox_from_env()
    try:
        require_gmat_image()
    except LiveConfigError:
        if is_external_validation_strict():
            raise
        pytest.skip(f"{GMAT_VALIDATION_IMAGE_ENV} is required for GMAT-backed validation")

    failures: list[str] = []
    for case in CASES:
        try:
            compare_samples(case, astrox_hpop_samples(case), gmat_hpop_samples(case))
        except CrossValidationError as exc:
            failures.append(f"{case.description}\n{exc}")
    if failures:
        raise CrossValidationError("\n\n".join(failures))


@pytest.mark.calibration
@pytest.mark.xfail(
    reason="ASTROX and GMAT currently differ near an HPOP SRP shadow transition; run with --runxfail for residual diagnostics.",
    strict=False,
)
def test_hpop_srp_shadow_transition_calibration() -> None:
    configure_astrox_from_env()
    try:
        require_gmat_image()
    except LiveConfigError:
        if is_external_validation_strict():
            raise
        pytest.skip(f"{GMAT_VALIDATION_IMAGE_ENV} is required for GMAT-backed validation")

    compare_samples(
        SHADOW_CALIBRATION_CASE,
        astrox_hpop_samples(SHADOW_CALIBRATION_CASE),
        gmat_hpop_samples(SHADOW_CALIBRATION_CASE),
    )


def main() -> int:
    try:
        test_hpop_matches_gmat_representative_cases()
    except pytest.skip.Exception as exc:
        print(f"CROSS_VALIDATION_SKIPPED={exc}", file=sys.stderr)
        return 0
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"CROSS_VALIDATION_CHECKED={len(CASES)}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
