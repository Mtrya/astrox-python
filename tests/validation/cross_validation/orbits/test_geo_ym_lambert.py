#!/usr/bin/env python3
"""Lambert cross-validation between ASTROX and lamberthub.

`lamberthub` is a dev-only validation dependency used here as an independent
zero-revolution Lambert solver.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from lamberthub import izzo2015

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits
from tests.validation._support import LiveConfigError, configure_astrox_from_env


EARTH_MU = 398600441500000.0
TIME_OF_FLIGHT_S = 3600.0
STRICT_RESIDUAL_M_S = 1.0e-3
CONVENTION_DIAGNOSTIC_RESIDUAL_M_S = 1.0e-2


@dataclass(frozen=True, kw_only=True)
class LambertResidual:
    label: str
    departure_m_s: float
    arrival_m_s: float

    @property
    def max_m_s(self) -> float:
        return max(self.departure_m_s, self.arrival_m_s)

    def format(self) -> str:
        return (
            f"{self.label}: departure={self.departure_m_s:.12g} m/s, "
            f"arrival={self.arrival_m_s:.12g} m/s, max={self.max_m_s:.12g} m/s"
        )


class CrossValidationError(Exception):
    """Raised when ASTROX and lamberthub disagree."""


def platform_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=42164000.0,
        eccentricity=0.0001,
        inclination_deg=0.2,
        argument_of_periapsis_deg=0.0,
        raan_deg=30.0,
        true_anomaly_deg=20.0,
    )


def target_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=42164000.0,
        eccentricity=0.001,
        inclination_deg=1.0,
        argument_of_periapsis_deg=10.0,
        raan_deg=80.0,
        true_anomaly_deg=95.0,
    )


def state_vector(orbit: orbits.KeplerianElements) -> tuple[np.ndarray, np.ndarray]:
    semi_latus_rectum_m = orbit.semi_major_axis_m * (1.0 - orbit.eccentricity**2)
    true_anomaly_rad = math.radians(orbit.true_anomaly_deg)
    perifocal_position_m = np.array(
        [
            semi_latus_rectum_m
            * math.cos(true_anomaly_rad)
            / (1.0 + orbit.eccentricity * math.cos(true_anomaly_rad)),
            semi_latus_rectum_m
            * math.sin(true_anomaly_rad)
            / (1.0 + orbit.eccentricity * math.cos(true_anomaly_rad)),
            0.0,
        ]
    )
    perifocal_velocity_m_s = np.array(
        [
            -math.sqrt(EARTH_MU / semi_latus_rectum_m)
            * math.sin(true_anomaly_rad),
            math.sqrt(EARTH_MU / semi_latus_rectum_m)
            * (orbit.eccentricity + math.cos(true_anomaly_rad)),
            0.0,
        ]
    )
    rotation = inertial_rotation_matrix(orbit)
    return rotation @ perifocal_position_m, rotation @ perifocal_velocity_m_s


def cartesian_state_from_orbit(orbit: orbits.KeplerianElements) -> orbits.CartesianState:
    position_m, velocity_m_s = state_vector(orbit)
    return orbits.cartesian_state(
        x_m=float(position_m[0]),
        y_m=float(position_m[1]),
        z_m=float(position_m[2]),
        vx_m_s=float(velocity_m_s[0]),
        vy_m_s=float(velocity_m_s[1]),
        vz_m_s=float(velocity_m_s[2]),
    )


def inertial_rotation_matrix(orbit: orbits.KeplerianElements) -> np.ndarray:
    raan_rad = math.radians(orbit.raan_deg)
    inclination_rad = math.radians(orbit.inclination_deg)
    argument_of_periapsis_rad = math.radians(orbit.argument_of_periapsis_deg)
    cos_raan = math.cos(raan_rad)
    sin_raan = math.sin(raan_rad)
    cos_inclination = math.cos(inclination_rad)
    sin_inclination = math.sin(inclination_rad)
    cos_argument = math.cos(argument_of_periapsis_rad)
    sin_argument = math.sin(argument_of_periapsis_rad)
    return np.array(
        [
            [
                cos_raan * cos_argument
                - sin_raan * sin_argument * cos_inclination,
                -cos_raan * sin_argument
                - sin_raan * cos_argument * cos_inclination,
                sin_raan * sin_inclination,
            ],
            [
                sin_raan * cos_argument
                + cos_raan * sin_argument * cos_inclination,
                -sin_raan * sin_argument
                + cos_raan * cos_argument * cos_inclination,
                -cos_raan * sin_inclination,
            ],
            [
                sin_argument * sin_inclination,
                cos_argument * sin_inclination,
                cos_inclination,
            ],
        ]
    )


def true_to_mean_rad(true_anomaly_deg: float, eccentricity: float) -> float:
    true_anomaly = math.radians(true_anomaly_deg)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 - eccentricity) * math.sin(true_anomaly / 2.0),
        math.sqrt(1.0 + eccentricity) * math.cos(true_anomaly / 2.0),
    )
    return (eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly)) % (
        2.0 * math.pi
    )


def mean_to_true_deg(mean_anomaly_rad: float, eccentricity: float) -> float:
    eccentric_anomaly = mean_anomaly_rad
    for _ in range(30):
        eccentric_anomaly -= (
            eccentric_anomaly
            - eccentricity * math.sin(eccentric_anomaly)
            - mean_anomaly_rad
        ) / (1.0 - eccentricity * math.cos(eccentric_anomaly))
    true_anomaly = 2.0 * math.atan2(
        math.sqrt(1.0 + eccentricity) * math.sin(eccentric_anomaly / 2.0),
        math.sqrt(1.0 - eccentricity) * math.cos(eccentric_anomaly / 2.0),
    )
    return math.degrees(true_anomaly) % 360.0


def advance_target(
    orbit: orbits.KeplerianElements,
    *,
    lead_s: float,
) -> orbits.KeplerianElements:
    mean_motion_rad_s = math.sqrt(EARTH_MU / orbit.semi_major_axis_m**3)
    true_anomaly_deg = mean_to_true_deg(
        true_to_mean_rad(orbit.true_anomaly_deg, orbit.eccentricity)
        + mean_motion_rad_s * lead_s,
        orbit.eccentricity,
    )
    return orbits.keplerian(
        semi_major_axis_m=orbit.semi_major_axis_m,
        eccentricity=orbit.eccentricity,
        inclination_deg=orbit.inclination_deg,
        argument_of_periapsis_deg=orbit.argument_of_periapsis_deg,
        raan_deg=orbit.raan_deg,
        true_anomaly_deg=true_anomaly_deg,
    )


def advance_target_true_anomaly_linearly(
    orbit: orbits.KeplerianElements,
    *,
    lead_s: float,
) -> orbits.KeplerianElements:
    """Match ASTROX GEO-YM's observed target convention.

    Focused live probes showed that the specialized GEO-YM route first advances
    the target's true anomaly by mean motion times TOF, then solves Lambert to
    that target state. That is different from physically propagating mean
    anomaly through Kepler's equation. This check intentionally validates the
    observed ASTROX convention rather than hiding it behind a loose tolerance.
    """
    mean_motion_rad_s = math.sqrt(EARTH_MU / orbit.semi_major_axis_m**3)
    return orbits.keplerian(
        semi_major_axis_m=orbit.semi_major_axis_m,
        eccentricity=orbit.eccentricity,
        inclination_deg=orbit.inclination_deg,
        argument_of_periapsis_deg=orbit.argument_of_periapsis_deg,
        raan_deg=orbit.raan_deg,
        true_anomaly_deg=(
            orbit.true_anomaly_deg + math.degrees(mean_motion_rad_s * lead_s)
        )
        % 360.0,
    )


def astrox_lambert_delta_v() -> tuple[np.ndarray, np.ndarray]:
    departure, arrival = orbits.geo_ym_lambert_delta_v(
        platform_orbit=platform_orbit(),
        target_orbit=target_orbit(),
        time_of_flight_s=TIME_OF_FLIGHT_S,
        platform_gravitational_parameter_m3_s2=EARTH_MU,
    )
    return np.array(departure), np.array(arrival)


def lamberthub_residual(
    *,
    label: str,
    target: orbits.KeplerianElements,
) -> LambertResidual:
    platform = platform_orbit()
    r1, platform_velocity = state_vector(platform)
    r2, target_velocity = state_vector(target)
    astrox_departure, astrox_arrival = astrox_lambert_delta_v()
    transfer_departure, transfer_arrival = izzo2015(
        EARTH_MU,
        r1,
        r2,
        TIME_OF_FLIGHT_S,
        M=0,
        prograde=True,
        low_path=True,
    )
    expected_departure_delta_v = np.array(transfer_departure) - platform_velocity
    expected_arrival_delta_v = np.array(transfer_arrival) - target_velocity
    return LambertResidual(
        label=label,
        departure_m_s=float(
            np.max(np.abs(astrox_departure - expected_departure_delta_v))
        ),
        arrival_m_s=float(np.max(np.abs(astrox_arrival - expected_arrival_delta_v))),
    )


def cartesian_lamberthub_residual() -> LambertResidual:
    departure_state = cartesian_state_from_orbit(platform_orbit())
    arrival_state = cartesian_state_from_orbit(
        advance_target(target_orbit(), lead_s=TIME_OF_FLIGHT_S)
    )
    r1 = np.array([departure_state.x_m, departure_state.y_m, departure_state.z_m])
    v1 = np.array(
        [
            departure_state.vx_m_s,
            departure_state.vy_m_s,
            departure_state.vz_m_s,
        ]
    )
    r2 = np.array([arrival_state.x_m, arrival_state.y_m, arrival_state.z_m])
    v2 = np.array([arrival_state.vx_m_s, arrival_state.vy_m_s, arrival_state.vz_m_s])
    astrox_departure, astrox_arrival = orbits.lambert_delta_v(
        departure_state=departure_state,
        arrival_state=arrival_state,
        time_of_flight_s=TIME_OF_FLIGHT_S,
        gravitational_parameter_m3_s2=EARTH_MU,
    )
    transfer_departure, transfer_arrival = izzo2015(
        EARTH_MU,
        r1,
        r2,
        TIME_OF_FLIGHT_S,
        M=0,
        prograde=True,
        low_path=True,
    )
    expected_departure_delta_v = np.array(transfer_departure) - v1
    expected_arrival_delta_v = np.array(transfer_arrival) - v2
    return LambertResidual(
        label="cartesian_lambert_delta_v",
        departure_m_s=float(
            np.max(np.abs(np.array(astrox_departure) - expected_departure_delta_v))
        ),
        arrival_m_s=float(
            np.max(np.abs(np.array(astrox_arrival) - expected_arrival_delta_v))
        ),
    )


def compare_cartesian_lambert_case() -> None:
    residual = cartesian_lamberthub_residual()
    if residual.max_m_s > STRICT_RESIDUAL_M_S:
        raise CrossValidationError(
            "\n".join(
                [
                    "ASTROX Cartesian Lambert no longer matches lamberthub.",
                    residual.format(),
                    f"strict residual target: {STRICT_RESIDUAL_M_S:.12g} m/s",
                    "Comparison: independent Keplerian-to-RV input, zero-revolution prograde Lambert, ASTROX delta-v versus lamberthub transfer velocity minus endpoint velocity.",
                    "Do not widen tolerance; investigate units, branch choice, or ASTROX solver semantics.",
                ]
            )
        )


def compare_current_lambert_case() -> None:
    current_target = target_orbit()
    target_at_input = lamberthub_residual(
        label="target_at_input_anomaly",
        target=current_target,
    )
    target_at_arrival = lamberthub_residual(
        label="target_advanced_by_time_of_flight",
        target=advance_target(current_target, lead_s=TIME_OF_FLIGHT_S),
    )
    linear_true_anomaly_target = lamberthub_residual(
        label="target_true_anomaly_advanced_linearly_by_time_of_flight",
        target=advance_target_true_anomaly_linearly(
            current_target,
            lead_s=TIME_OF_FLIGHT_S,
        ),
    )

    if linear_true_anomaly_target.max_m_s > STRICT_RESIDUAL_M_S:
        raise CrossValidationError(
            "\n".join(
                [
                    "ASTROX GEO-YM Lambert no longer matches the calibrated external comparison.",
                    linear_true_anomaly_target.format(),
                    target_at_input.format(),
                    target_at_arrival.format(),
                    f"strict residual target: {STRICT_RESIDUAL_M_S:.12g} m/s",
                    "Calibrated convention: advance target true anomaly linearly by mean motion * tof, then solve zero-revolution prograde Lambert.",
                    "Do not widen tolerance; investigate target timing, endpoint convention, or ASTROX solver semantics.",
                ]
            )
        )
    if target_at_arrival.max_m_s <= CONVENTION_DIAGNOSTIC_RESIDUAL_M_S:
        raise CrossValidationError(
            "\n".join(
                [
                    "ASTROX GEO-YM Lambert appears to have changed target timing convention.",
                    linear_true_anomaly_target.format(),
                    target_at_arrival.format(),
                    f"mean-anomaly propagation diagnostic threshold: {CONVENTION_DIAGNOSTIC_RESIDUAL_M_S:.12g} m/s",
                    "If this persists, update the comparison only after explaining the new convention.",
                ]
            )
        )


def test_geo_ym_lambert_matches_calibrated_lamberthub_comparison() -> None:
    configure_astrox_from_env()
    compare_current_lambert_case()


def test_cartesian_lambert_matches_lamberthub_comparison() -> None:
    configure_astrox_from_env()
    compare_cartesian_lambert_case()


def main() -> int:
    try:
        configure_astrox_from_env()
        compare_cartesian_lambert_case()
        compare_current_lambert_case()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
