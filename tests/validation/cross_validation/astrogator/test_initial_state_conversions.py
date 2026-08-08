#!/usr/bin/env python3
"""Cross-validate RunMCS initial-state representation conversions."""

# Coverage:
#   Branches:
#     - Cartesian initial state: verified
#     - Keplerian initial state: verified
#     - Spherical initial state: verified
#     - TargetVecOut hyperbolic initial state: verified
#   Fields:
#     - Cartesian identity and spherical-to-Cartesian conversion: verified
#     - Keplerian element echo/conversion: verified
#     - Hyperbolic periapsis radius, eccentricity, and semi-major axis: verified
#   Comparison:
#     - Local Cartesian/spherical basis equations and hyperbolic conic equations
#     - Constants: explicit Earth Mu=398600441500000 m^3/s^2
#     - Tolerances: state 1e-6 m or m/s; conic scalars 1e-9 relative

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import astrogator, exceptions
from tests.validation._support import LiveConfigError, configure_astrox_from_env


MU = 398600441500000.0
START = "2026-01-01T00:00:00Z"
STATE_EPS = 1.0e-6
SCALAR_EPS = 1.0e-9


class CrossValidationError(Exception):
    """Raised when a state representation conversion disagrees with its oracle."""


def initial_result(value: astrogator.InitialStateElement) -> astrogator.InitialStateResult:
    result = astrogator.run_mcs(
        [astrogator.initial_state("Init", value, epoch=START)]
    )
    segment = result.main_sequence_results[0]
    if not isinstance(segment, astrogator.InitialStateResult):
        raise CrossValidationError(f"expected InitialStateResult, got {type(segment).__name__}")
    return segment


def compare_cartesian() -> None:
    input_state = astrogator.cartesian_state(
        x_m=1_000_000.0,
        y_m=2_000_000.0,
        z_m=3_000_000.0,
        vx_m_s=4_000.0,
        vy_m_s=5_000.0,
        vz_m_s=6_000.0,
    )
    observed = np.asarray(initial_result(input_state).final_state.cartesian.to_wire())
    expected = np.asarray(
        [input_state.x_m, input_state.y_m, input_state.z_m,
         input_state.vx_m_s, input_state.vy_m_s, input_state.vz_m_s]
    )
    if np.max(np.abs(observed - expected)) > STATE_EPS:
        raise CrossValidationError("Cartesian initial-state identity mismatch")


def compare_keplerian() -> None:
    value = astrogator.keplerian_state(
        semi_major_axis_m=7_000_000.0,
        eccentricity=0.3,
        inclination_deg=45.0,
        raan_deg=30.0,
        argument_of_periapsis_deg=60.0,
        gravitational_parameter_m3_s2=MU,
        true_anomaly_deg=30.0,
    )
    observed = initial_result(value).final_state.keplerian
    checks = (
        (observed.semi_major_axis_m, value.semi_major_axis_m),
        (observed.eccentricity, value.eccentricity),
        (observed.inclination_deg, value.inclination_deg),
        (observed.raan_deg, value.raan_deg),
        (observed.argument_of_periapsis_deg, value.argument_of_periapsis_deg),
        (observed.true_anomaly_deg, value.true_anomaly_deg),
        (observed.gravitational_parameter_m3_s2, value.gravitational_parameter_m3_s2),
    )
    if any(abs(actual - expected) > STATE_EPS for actual, expected in checks):
        raise CrossValidationError("Keplerian initial-state conversion mismatch")


def compare_spherical() -> None:
    right_ascension_deg = 120.0
    declination_deg = 45.0
    radius_m = 5_056_327.563933446
    horizontal_fpa_deg = 6.79000160599057
    velocity_azimuth_deg = 90.0
    velocity_magnitude_m_s = 10_035.989759734246
    value = astrogator.spherical_state(
        right_ascension_deg=right_ascension_deg,
        declination_deg=declination_deg,
        radius_m=radius_m,
        horizontal_fpa_deg=horizontal_fpa_deg,
        velocity_azimuth_deg=velocity_azimuth_deg,
        velocity_magnitude_m_s=velocity_magnitude_m_s,
    )
    observed = np.asarray(initial_result(value).final_state.cartesian.to_wire())
    ra = math.radians(right_ascension_deg)
    dec = math.radians(declination_deg)
    fpa = math.radians(horizontal_fpa_deg)
    azimuth = math.radians(velocity_azimuth_deg)
    radial = np.array(
        [math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)]
    )
    east = np.array([-math.sin(ra), math.cos(ra), 0.0])
    north = np.array(
        [-math.sin(dec) * math.cos(ra), -math.sin(dec) * math.sin(ra), math.cos(dec)]
    )
    position = radius_m * radial
    velocity = velocity_magnitude_m_s * (
        math.sin(fpa) * radial
        + math.cos(fpa) * (math.cos(azimuth) * north + math.sin(azimuth) * east)
    )
    expected = np.concatenate((position, velocity))
    if np.max(np.abs(observed - expected)) > STATE_EPS:
        raise CrossValidationError(f"Spherical conversion mismatch: {observed} vs {expected}")


def compare_target_vector_out() -> None:
    radius_of_periapsis_m = 7_000_000.0
    c3_m2_s2 = 2.0e6
    value = astrogator.target_vector_out_state(
        radius_of_periapsis_km=7_000.0,
        c3_km2_s2=2.0,
        asymptote_ra_deg=30.0,
        asymptote_dec_deg=10.0,
        gravitational_parameter_m3_s2=MU,
    )
    observed = initial_result(value)
    keplerian = observed.final_state.keplerian
    spherical = observed.final_state.spherical
    expected_eccentricity = 1.0 + radius_of_periapsis_m * c3_m2_s2 / MU
    expected_semi_major_axis = -MU / c3_m2_s2
    expected_speed = math.sqrt(c3_m2_s2 + 2.0 * MU / radius_of_periapsis_m)
    checks = (
        (keplerian.eccentricity, expected_eccentricity),
        (keplerian.semi_major_axis_m, expected_semi_major_axis),
        (spherical.radius_m, radius_of_periapsis_m),
        (spherical.velocity_magnitude_m_s, expected_speed),
    )
    for actual, expected in checks:
        if abs((actual - expected) / expected) > SCALAR_EPS:
            raise CrossValidationError(f"TargetVecOut conic mismatch: {actual} vs {expected}")


def test_initial_state_representations_match_local_derivations() -> None:
    configure_astrox_from_env()
    compare_cartesian()
    compare_keplerian()
    compare_spherical()
    compare_target_vector_out()


def main() -> int:
    try:
        test_initial_state_representations_match_local_derivations()
    except (CrossValidationError, exceptions.AstroxError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=4")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
