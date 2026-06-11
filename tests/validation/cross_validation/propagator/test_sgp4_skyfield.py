#!/usr/bin/env python3
"""Live SGP4 cross-validation between ASTROX and Skyfield."""

# Coverage:
#   Branches:
#     - single SGP4 propagation from TLE: verified
#   Fields:
#     - period_s: verified (Skyfield mean motion)
#     - Position.cartesian_velocity time/position/velocity samples: verified (GCRS state samples)
#   Parameters:
#     - satellite_number: verified for ISS sample
#     - tle_lines: verified for ISS TLE_A sample
#     - start/stop/step_s: partial (two samples over one 10-minute window)
#   Comparison:
#     - External: Skyfield EarthSatellite GCRS state
#     - Constants: TLE_LINES, SAMPLE_OFFSETS_S
#     - Tolerances: PERIOD_ABS_S, POSITION_ABS_M, VELOCITY_ABS_M_S

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skyfield.api import EarthSatellite, load

from astrox import propagator
from tests.validation._support import LiveConfigError, configure_astrox_from_env


PERIOD_ABS_S = 1.0e-9
POSITION_ABS_M = 0.02
VELOCITY_ABS_M_S = 2.0e-5
SAMPLE_OFFSETS_S = (0.0, 300.0)
START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
STEP_S = 300.0
SATELLITE_NUMBER = "25544"
TLE_LINES = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


@dataclass(frozen=True, kw_only=True)
class StateSample:
    offset_s: float
    position_m: tuple[float, float, float]
    velocity_m_s: tuple[float, float, float]


class CrossValidationError(Exception):
    """Raised when ASTROX and Skyfield disagree."""


def astrox_sgp4() -> tuple[float, dict[float, StateSample]]:
    period_s, position = propagator.sgp4(
        start=START,
        stop=STOP,
        step_s=STEP_S,
        satellite_number=SATELLITE_NUMBER,
        tle_lines=TLE_LINES,
    )
    return period_s, samples_from_astrox(position.cartesian_velocity)


def skyfield_sgp4() -> tuple[float, dict[float, StateSample]]:
    ts = load.timescale(builtin=True)
    satellite = EarthSatellite(
        TLE_LINES[0],
        TLE_LINES[1],
        SATELLITE_NUMBER,
        ts,
    )
    period_s = 2.0 * math.pi / satellite.model.no_kozai * 60.0

    samples: dict[float, StateSample] = {}
    for offset_s in SAMPLE_OFFSETS_S:
        minute = int(offset_s // 60.0)
        second = offset_s - minute * 60.0
        time = ts.utc(2024, 1, 1, 0, minute, second)
        # Skyfield applies the frame handling needed for this comparison. Raw
        # low-level SGP4 TEME coordinates are intentionally not the target here.
        state = satellite.at(time)
        samples[offset_s] = StateSample(
            offset_s=offset_s,
            position_m=tuple(float(value) for value in state.position.m),
            velocity_m_s=tuple(float(value) for value in state.velocity.m_per_s),
        )
    return period_s, samples


def samples_from_astrox(
    cartesian_velocity: tuple[float, ...],
) -> dict[float, StateSample]:
    if len(cartesian_velocity) % 7 != 0:
        raise CrossValidationError("ASTROX cartesian_velocity length is not divisible by 7")

    samples: dict[float, StateSample] = {}
    for index in range(0, len(cartesian_velocity), 7):
        offset_s = float(cartesian_velocity[index])
        samples[offset_s] = StateSample(
            offset_s=offset_s,
            position_m=tuple(float(value) for value in cartesian_velocity[index + 1 : index + 4]),
            velocity_m_s=tuple(float(value) for value in cartesian_velocity[index + 4 : index + 7]),
        )
    return samples


def compare(
    astrox_period_s: float,
    astrox_samples: dict[float, StateSample],
    skyfield_period_s: float,
    skyfield_samples: dict[float, StateSample],
) -> None:
    failures: list[str] = []

    period_error_s = abs(astrox_period_s - skyfield_period_s)
    if period_error_s > PERIOD_ABS_S:
        failures.append(
            f"period_s error {period_error_s:.12g} exceeds tolerance {PERIOD_ABS_S:.12g}"
        )

    for offset_s in SAMPLE_OFFSETS_S:
        astrox_sample = astrox_samples.get(offset_s)
        skyfield_sample = skyfield_samples.get(offset_s)
        if astrox_sample is None:
            failures.append(f"ASTROX missing sample at offset_s={offset_s:g}")
            continue
        if skyfield_sample is None:
            failures.append(f"Skyfield missing sample at offset_s={offset_s:g}")
            continue

        position_error_m = max(
            abs(astrox_value - skyfield_value)
            for astrox_value, skyfield_value in zip(
                astrox_sample.position_m,
                skyfield_sample.position_m,
            )
        )
        velocity_error_m_s = max(
            abs(astrox_value - skyfield_value)
            for astrox_value, skyfield_value in zip(
                astrox_sample.velocity_m_s,
                skyfield_sample.velocity_m_s,
            )
        )
        if position_error_m > POSITION_ABS_M:
            failures.append(
                f"position error at offset_s={offset_s:g} is {position_error_m:.12g}, tolerance {POSITION_ABS_M:.12g}"
            )
        if velocity_error_m_s > VELOCITY_ABS_M_S:
            failures.append(
                f"velocity error at offset_s={offset_s:g} is {velocity_error_m_s:.12g}, tolerance {VELOCITY_ABS_M_S:.12g}"
            )

    if failures:
        raise CrossValidationError("\n".join(failures))


def test_sgp4_matches_skyfield_gcrs_state() -> None:
    configure_astrox_from_env()
    compare(*astrox_sgp4(), *skyfield_sgp4())


def main() -> int:
    try:
        test_sgp4_matches_skyfield_gcrs_state()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
