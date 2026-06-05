#!/usr/bin/env python3
"""Nonblocking Lambert calibration between ASTROX and lamberthub.

`lamberthub` is a dev-only validation dependency used here as an independent
zero-revolution Lambert solver. This comparison is intentionally marked as
calibration because the current ASTROX GEO-YM Lambert convention is not fully
explained yet.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
from lamberthub import izzo2015

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import orbits
from tests.validation._support import LiveConfigError, configure_astrox_from_env


EARTH_MU = 398600441500000.0
TIME_OF_FLIGHT_S = 3600.0
STRICT_RESIDUAL_M_S = 1.0e-3


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
    state = orbits.keplerian_to_cartesian(
        orbit,
        gravitational_parameter_m3_s2=EARTH_MU,
    )
    return (
        np.array([state.x_m, state.y_m, state.z_m]),
        np.array([state.vx_m_s, state.vy_m_s, state.vz_m_s]),
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


def best_target_lead_residual() -> tuple[float, LambertResidual]:
    current_target = target_orbit()
    best_lead_s = TIME_OF_FLIGHT_S
    best = LambertResidual(
        label="uninitialized",
        departure_m_s=float("inf"),
        arrival_m_s=float("inf"),
    )
    for lead_s in np.linspace(3590.0, 3610.0, 41):
        residual = lamberthub_residual(
            label=f"target_lead_s={float(lead_s):.1f}",
            target=advance_target(current_target, lead_s=float(lead_s)),
        )
        if residual.max_m_s < best.max_m_s:
            best_lead_s = float(lead_s)
            best = residual
    return best_lead_s, best


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
    best_lead_s, best = best_target_lead_residual()

    if target_at_arrival.max_m_s > STRICT_RESIDUAL_M_S:
        raise CrossValidationError(
            "\n".join(
                [
                    "ASTROX GEO-YM Lambert does not yet have a clean external match.",
                    target_at_input.format(),
                    target_at_arrival.format(),
                    f"best scanned target lead: {best_lead_s:.1f} s -> {best.format()}",
                    f"strict residual target: {STRICT_RESIDUAL_M_S:.12g} m/s",
                    "Do not widen tolerance; investigate target timing, endpoint convention, or ASTROX solver semantics.",
                ]
            )
        )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason="ASTROX GEO-YM Lambert has an unresolved target-timing or delta-v convention mismatch against lamberthub; run with --runxfail for residual diagnostics.",
    strict=False,
)
def test_geo_ym_lambert_calibration() -> None:
    configure_astrox_from_env()
    compare_current_lambert_case()


def main() -> int:
    try:
        configure_astrox_from_env()
        compare_current_lambert_case()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
