#!/usr/bin/env python3
"""Live celestial ephemeris cross-validation against Skyfield DE421 geometry."""

# Coverage:
#   Branches:
#     - celestial.ephemeris for Moon and Mars in J2000 and MeanEclpJ2000:
#       partial; the wire-declared frame, epoch, units, and same-epoch geometric
#       state are checked, while ASTROX's internal planetary kernel is not known
#       to be identical to Skyfield's DE421 kernel
#   Fields:
#     - Position.CentralBody, referenceFrame, epoch, and cartesianVelocity sample
#       layout: verified for the maintained cases
#     - cartesianVelocity position/velocity values: partial; residuals remain
#       inside the calibrated cross-kernel envelope
#   Parameters:
#     - target_name: Moon and Mars
#     - observer_name: Earth
#     - observer_frame: J2000 and MeanEclpJ2000
#     - explicit Start/Stop window and 43200-second sample step
#   Comparison:
#     - External: Skyfield 1.54 DE421 geometric target-minus-Earth state at the
#       requested epoch; MeanEclpJ2000 uses the standard J2000 mean-obliquity
#       rotation of the same geometric state
#     - Units: ASTROX cartesianVelocity positions are m and velocities are m/s;
#       Skyfield values are converted to km and km/s before comparison
#     - Tolerances: Moon 0.1 km / 1e-6 km/s; Mars 40 km / 2e-5 km/s
#
# Calibration notes:
#   - The comparison intentionally does not use Skyfield observe(), which applies
#     light-time and would compare a retarded apparent state with ASTROX's sampled
#     same-epoch state.
#   - Moon residuals are approximately 0.04-0.06 km and 2.2-2.4e-7 km/s in the
#     maintained 2026 window. Mars residuals are approximately 32.7 km and
#     1.27e-5 km/s. These stable differences are treated as cross-kernel/model
#     residuals, not erased by claiming exact ephemeris equivalence.

from __future__ import annotations

import math
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import celestial  # noqa: E402
from tests.validation._support import (  # noqa: E402
    configure_astrox_from_env,
    load_skyfield_ephemeris,
    skyfield_loader_from_env,
)


START = "2026-01-01T00:00:00.000Z"
STOP = "2026-01-02T00:00:00.000Z"
SAMPLE_STEP_S = 43200.0
SAMPLE_OFFSETS_S = (0.0, 43200.0, 86400.0)
FRAMES = ("J2000", "MeanEclpJ2000")
J2000_MEAN_OBLIQUITY_DEG = 23.439291111

POSITION_ABS_KM = {"Moon": 0.1, "Mars": 40.0}
VELOCITY_ABS_KM_S = {"Moon": 1.0e-6, "Mars": 2.0e-5}


class CrossValidationError(Exception):
    """Raised when ASTROX and the independent ephemeris comparison disagree."""


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def require_numeric(value: Any, *, field: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise CrossValidationError(f"{field} must be numeric")
    return float(value)


def samples_from_response(response: dict[str, Any], *, frame: str) -> list[tuple[float, np.ndarray, np.ndarray]]:
    if response.get("IsSuccess") is not True:
        raise CrossValidationError(
            f"ephemeris returned IsSuccess={response.get('IsSuccess')!r}: {response.get('Message')!r}"
        )
    position = response.get("Position")
    if not isinstance(position, dict):
        raise CrossValidationError("ephemeris Position must be an object")
    if position.get("CentralBody") != "Earth":
        raise CrossValidationError(
            f"ephemeris Position.CentralBody={position.get('CentralBody')!r}, expected 'Earth'"
        )
    if position.get("referenceFrame") != frame:
        raise CrossValidationError(
            f"ephemeris referenceFrame={position.get('referenceFrame')!r}, expected {frame!r}"
        )
    if position.get("epoch") != START:
        raise CrossValidationError(
            f"ephemeris epoch={position.get('epoch')!r}, expected {START!r}"
        )
    values = position.get("cartesianVelocity")
    if not isinstance(values, list) or len(values) % 7 != 0:
        raise CrossValidationError(
            "ephemeris cartesianVelocity must be a non-empty 7-value-per-sample list"
        )
    samples: list[tuple[float, np.ndarray, np.ndarray]] = []
    for index in range(0, len(values), 7):
        offset_s = require_numeric(values[index], field="cartesianVelocity time offset")
        position_m = np.array(
            [
                require_numeric(values[index + component], field="cartesianVelocity position")
                for component in range(1, 4)
            ],
            dtype=float,
        )
        velocity_m_s = np.array(
            [
                require_numeric(values[index + component], field="cartesianVelocity velocity")
                for component in range(4, 7)
            ],
            dtype=float,
        )
        samples.append((offset_s, position_m, velocity_m_s))
    if len(samples) != len(SAMPLE_OFFSETS_S):
        raise CrossValidationError(
            f"ephemeris returned {len(samples)} samples, expected {len(SAMPLE_OFFSETS_S)}"
        )
    return samples


def frame_rotation(frame: str) -> np.ndarray:
    if frame == "J2000":
        return np.eye(3)
    if frame == "MeanEclpJ2000":
        obliquity = math.radians(J2000_MEAN_OBLIQUITY_DEG)
        return np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, math.cos(obliquity), math.sin(obliquity)],
                [0.0, -math.sin(obliquity), math.cos(obliquity)],
            ]
        )
    raise CrossValidationError(f"unsupported comparison frame: {frame!r}")


def skyfield_state(
    *,
    ephemeris: Any,
    target_name: str,
    offset_s: float,
    frame: str,
) -> tuple[np.ndarray, np.ndarray]:
    when = parse_time(START) + timedelta(seconds=offset_s)
    loader = skyfield_loader_from_env()
    time = loader.timescale(builtin=True).from_datetime(when)
    target = ephemeris[target_name.lower()]
    earth = ephemeris["earth"]
    rotation = frame_rotation(frame)
    position_km = np.asarray(target.at(time).position.km) - np.asarray(earth.at(time).position.km)
    velocity_km_s = np.asarray(target.at(time).velocity.km_per_s) - np.asarray(earth.at(time).velocity.km_per_s)
    return rotation @ position_km, rotation @ velocity_km_s


def compare_case(*, target_name: str, frame: str, ephemeris: Any) -> None:
    response = celestial.ephemeris(
        target_name=target_name,
        start=START,
        stop=STOP,
        observer_name="Earth",
        observer_frame=frame,
        step_s=SAMPLE_STEP_S,
    )
    samples = samples_from_response(response, frame=frame)
    position_errors: list[float] = []
    velocity_errors: list[float] = []
    for expected_offset_s, (actual_offset_s, position_m, velocity_m_s) in zip(
        SAMPLE_OFFSETS_S,
        samples,
        strict=True,
    ):
        if actual_offset_s != expected_offset_s:
            raise CrossValidationError(
                f"{target_name}/{frame} sample offset={actual_offset_s:g}, expected {expected_offset_s:g}"
            )
        expected_position_km, expected_velocity_km_s = skyfield_state(
            ephemeris=ephemeris,
            target_name=target_name,
            offset_s=expected_offset_s,
            frame=frame,
        )
        position_error_km = float(np.linalg.norm(position_m / 1000.0 - expected_position_km))
        velocity_error_km_s = float(
            np.linalg.norm(velocity_m_s / 1000.0 - expected_velocity_km_s)
        )
        position_errors.append(position_error_km)
        velocity_errors.append(velocity_error_km_s)
    max_position_error = max(position_errors)
    max_velocity_error = max(velocity_errors)
    if max_position_error > POSITION_ABS_KM[target_name]:
        raise CrossValidationError(
            f"{target_name}/{frame} position residual {max_position_error:.12g} km exceeds "
            f"{POSITION_ABS_KM[target_name]:g} km"
        )
    if max_velocity_error > VELOCITY_ABS_KM_S[target_name]:
        raise CrossValidationError(
            f"{target_name}/{frame} velocity residual {max_velocity_error:.12g} km/s exceeds "
            f"{VELOCITY_ABS_KM_S[target_name]:g} km/s"
        )
    print(
        f"EPHEMERIS_CASE={target_name}/{frame} "
        f"max_position_residual_km={max_position_error:.12g} "
        f"max_velocity_residual_km_s={max_velocity_error:.12g}"
    )


def test_ephemeris_matches_skyfield_geometric_states() -> None:
    configure_astrox_from_env()
    loader = skyfield_loader_from_env()
    ephemeris = load_skyfield_ephemeris(loader, "de421.bsp")
    for target_name in ("Moon", "Mars"):
        for frame in FRAMES:
            compare_case(target_name=target_name, frame=frame, ephemeris=ephemeris)


def main() -> int:
    try:
        test_ephemeris_matches_skyfield_geometric_states()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=12")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
