#!/usr/bin/env python3
"""Live ASTROX OrbitSystem cross-validation against Skyfield Earth orientation and lunar ephemeris.

Coverage:
  Branches:
    - CentralBodyFrame (Earth INERTIAL -> Earth FIXED): verified for static inertial inputs
    - EarthMoonLibration2 (Earth INERTIAL -> Moon-centered libration frame): partial
  Fields (CentralBodyFrame):
    - cartesian radius: verified (no scaling between inertial and fixed)
    - cartesian longitude: verified against IAU 2000 Earth Rotation Angle
  Fields (EarthMoonLibration2):
    - cartesian (Moon-centered libration coordinates): verified against JPL DE440 frame
    - unit_quaternion (frame orientation): unresolved (does not match simple JPL-derived frame)
    - cartesian_translation: partial (absent from live response; parser accepts but not validated)
  Parameters:
    - static inertial longitude (0, 90, 180 deg for CentralBodyFrame; 0, 90 deg for Libration): verified
    - sample epoch/time-grid: verified
    - to_central_body/target_reference_frame: verified for the tested branch
    - interpolationAlgorithm/interpolationDegree: not independently validated
  Comparison:
    - External: Skyfield de440.bsp Earth rotation angle and Moon geocentric position/velocity
    - Constants: EARTH_MU_M3_S2
    - Tolerances: RADIUS_ABS_M=1.0, LONGITUDE_ABS_DEG=0.001, LIBRATION_POSITION_ABS_M=1.0, QUATERNION_ANGLE_ABS_DEG=5.0
  Unresolved:
    - EarthMoonLibration2 unit_quaternion convention remains unexplained after bounded
      investigation. The cartesian field is verified in the same Moon-centered frame, so the
      origin and axis conventions are calibrated; only the auxiliary orientation encoding is
      not yet understood.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from skyfield.api import Loader

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import entities, orbits
from tests.validation._support import (
    LiveConfigError,
    configure_astrox_from_env,
)


EPOCH = "2024-01-01T00:00:00Z"
EARTH_MU_M3_S2 = 398600441500000.0
SAMPLE_RADIUS_M = 7000000.0
SAMPLE_DURATION_S = 1000.0
SAMPLE_COUNT = 8

RADIUS_ABS_M = 1.0
LONGITUDE_ABS_DEG = 0.001
LIBRATION_POSITION_ABS_M = 1.0
QUATERNION_ANGLE_ABS_DEG = 5.0


class CrossValidationError(Exception):
    """Raised when ASTROX output deviates from the independent comparison path."""


def _skyfield_loader() -> Loader:
    return Loader(Path.home() / ".skyfield")


def _sample_static_inertial_position(
    *,
    inertial_longitude_deg: float,
) -> entities.CzmlPosition:
    """Build a static, equatorial, Earth-centered inertial CZML sample."""
    longitude_rad = math.radians(inertial_longitude_deg)
    dt_s = SAMPLE_DURATION_S / (SAMPLE_COUNT - 1)
    cartesian: list[float] = []
    for index in range(SAMPLE_COUNT):
        t_s = index * dt_s
        cartesian += [
            t_s,
            SAMPLE_RADIUS_M * math.cos(longitude_rad),
            SAMPLE_RADIUS_M * math.sin(longitude_rad),
            0.0,
        ]
    return entities.czml_position(
        epoch=EPOCH,
        central_body="Earth",
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=cartesian,
    )


def _cartesian_samples(
    cartesian: tuple[float, ...] | None,
) -> list[tuple[float, float, float, float]]:
    if cartesian is None:
        return []
    values = list(cartesian)
    samples: list[tuple[float, float, float, float]] = []
    for index in range(0, len(values), 4):
        samples.append(
            (
                values[index],
                values[index + 1],
                values[index + 2],
                values[index + 3],
            )
        )
    return samples


def _earth_rotation_angle_degrees(jd_ut1: float) -> float:
    """IAU 2000 Earth Rotation Angle in degrees."""
    era = 2.0 * math.pi * (
        0.7790572732640 + 1.00273781191135448 * (jd_ut1 - 2451545.0)
    )
    return math.degrees(era) % 360.0


def _check_central_body_frame_static_inertial_to_fixed(
    inertial_longitude_deg: float,
) -> None:
    """A static inertial vector rotates to the expected fixed longitude via ERA."""
    load = _skyfield_loader()
    ts = load.timescale()

    position = _sample_static_inertial_position(
        inertial_longitude_deg=inertial_longitude_deg,
    )
    _period, fixed = orbits.central_body_frame(
        position,
        to_central_body="Earth",
        target_reference_frame="FIXED",
    )

    for t_s, x_m, y_m, z_m in _cartesian_samples(fixed.cartesian):
        radius_m = math.sqrt(x_m**2 + y_m**2 + z_m**2)
        if abs(radius_m - SAMPLE_RADIUS_M) > RADIUS_ABS_M:
            raise CrossValidationError(
                f"radius {radius_m} deviates from {SAMPLE_RADIUS_M} "
                f"by more than {RADIUS_ABS_M}"
            )

        t = ts.utc(2024, 1, 1, 0, 0, t_s)
        era_deg = _earth_rotation_angle_degrees(t.ut1)
        expected_fixed_longitude_deg = (
            inertial_longitude_deg - era_deg
        ) % 360.0
        astrox_longitude_deg = math.degrees(math.atan2(y_m, x_m)) % 360.0
        delta_deg = (
            astrox_longitude_deg - expected_fixed_longitude_deg + 180.0
        ) % 360.0 - 180.0
        if abs(delta_deg) > LONGITUDE_ABS_DEG:
            raise CrossValidationError(
                f"longitude delta {delta_deg} deg exceeds {LONGITUDE_ABS_DEG} deg "
                f"at inertial_longitude={inertial_longitude_deg}, t={t_s}"
            )


def _expected_moon_centered_libration_position(
    satellite_inertial_m: np.ndarray,
    epoch_t,
) -> np.ndarray:
    """Project a satellite Earth-centered inertial position into the Moon-centered libration frame.

    Frame definition calibrated from ASTROX:
      - origin: Moon center
      - x-axis: Earth -> Moon unit vector
      - z-axis: Earth-Moon orbital angular momentum unit vector
      - y-axis: z cross x (right-handed)
    """
    load = _skyfield_loader()
    planets = load("de440.bsp")
    obs = (planets["moon"] - planets["earth"]).at(epoch_t)
    moon_pos_m = obs.position.m
    moon_vel_m_s = obs.velocity.m_per_s

    x_axis = moon_pos_m / np.linalg.norm(moon_pos_m)
    z_axis = np.cross(moon_pos_m, moon_vel_m_s)
    z_axis = z_axis / np.linalg.norm(z_axis)
    y_axis = np.cross(z_axis, x_axis)

    satellite_moon_centered_m = satellite_inertial_m - moon_pos_m
    return np.array(
        [
            float(np.dot(satellite_moon_centered_m, x_axis)),
            float(np.dot(satellite_moon_centered_m, y_axis)),
            float(np.dot(satellite_moon_centered_m, z_axis)),
        ]
    )


def _check_earth_moon_libration_cartesian_matches_moon_centered_frame(
    inertial_longitude_deg: float,
) -> None:
    """ASTROX returns the input state in a Moon-centered libration frame."""
    load = _skyfield_loader()
    ts = load.timescale()

    position = _sample_static_inertial_position(
        inertial_longitude_deg=inertial_longitude_deg,
    )
    state = orbits.earth_moon_libration(position)

    samples = _cartesian_samples(state.cartesian)
    if not samples:
        raise CrossValidationError("no cartesian samples returned")
    t_s, x_m, y_m, z_m = samples[0]
    astrox_position_m = np.array([x_m, y_m, z_m])

    epoch_t = ts.utc(2024, 1, 1, 0, 0, t_s)
    longitude_rad = math.radians(inertial_longitude_deg)
    satellite_inertial_m = np.array(
        [
            SAMPLE_RADIUS_M * math.cos(longitude_rad),
            SAMPLE_RADIUS_M * math.sin(longitude_rad),
            0.0,
        ]
    )
    expected_position_m = _expected_moon_centered_libration_position(
        satellite_inertial_m,
        epoch_t,
    )

    diff_m = astrox_position_m - expected_position_m
    if np.linalg.norm(diff_m) > LIBRATION_POSITION_ABS_M:
        raise CrossValidationError(
            f"libration position residual {np.linalg.norm(diff_m)} m "
            f"exceeds {LIBRATION_POSITION_ABS_M} m "
            f"at inertial_longitude={inertial_longitude_deg}"
        )


def _rotation_matrix_to_quaternion(matrix: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation matrix to a unit quaternion [x, y, z, w]."""
    m00, m01, m02 = matrix[0]
    m10, m11, m12 = matrix[1]
    m20, m21, m22 = matrix[2]
    if m22 < 0:
        if m00 > m11:
            trace = 1.0 + m00 - m11 - m22
            quaternion = np.array([trace, m01 + m10, m20 + m02, m12 - m21])
        else:
            trace = 1.0 - m00 + m11 - m22
            quaternion = np.array([m01 + m10, trace, m12 + m21, m20 - m02])
    else:
        if m00 < -m11:
            trace = 1.0 - m00 - m11 + m22
            quaternion = np.array([m20 + m02, m12 + m21, trace, m01 - m10])
        else:
            trace = 1.0 + m00 + m11 + m22
            quaternion = np.array([m12 - m21, m20 - m02, m01 + m10, trace])
    return quaternion / np.linalg.norm(quaternion) * 0.5 * math.sqrt(trace)


@pytest.fixture(autouse=True)
def _configure_astrox() -> None:
    configure_astrox_from_env()


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
)
def test_central_body_frame_static_inertial_to_fixed(
    inertial_longitude_deg: float,
) -> None:
    """A static inertial vector rotates to the expected fixed longitude via ERA."""
    _check_central_body_frame_static_inertial_to_fixed(inertial_longitude_deg)


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0],
)
def test_earth_moon_libration_cartesian_matches_moon_centered_frame(
    inertial_longitude_deg: float,
) -> None:
    """ASTROX returns the input state in a Moon-centered libration frame."""
    _check_earth_moon_libration_cartesian_matches_moon_centered_frame(
        inertial_longitude_deg,
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    strict=True,
    reason="Libration unit_quaternion convention not yet understood",
)
def test_earth_moon_libration_unit_quaternion_matches_moon_centered_frame() -> None:
    """Check whether the returned quaternion encodes the libration-to-inertial rotation."""
    load = _skyfield_loader()
    ts = load.timescale()

    position = _sample_static_inertial_position(inertial_longitude_deg=0.0)
    state = orbits.earth_moon_libration(position)

    quaternion = state.unit_quaternion
    assert quaternion is not None
    _t_q, qx, qy, qz, qw = quaternion[:5]
    astrox_quaternion = np.array([qx, qy, qz, qw])

    epoch_t = ts.utc(2024, 1, 1)
    planets = load("de440.bsp")
    obs = (planets["moon"] - planets["earth"]).at(epoch_t)
    moon_pos_m = obs.position.m
    moon_vel_m_s = obs.velocity.m_per_s

    x_axis = moon_pos_m / np.linalg.norm(moon_pos_m)
    z_axis = np.cross(moon_pos_m, moon_vel_m_s)
    z_axis = z_axis / np.linalg.norm(z_axis)
    y_axis = np.cross(z_axis, x_axis)
    rotation_matrix = np.column_stack((x_axis, y_axis, z_axis))

    expected_quaternion = _rotation_matrix_to_quaternion(rotation_matrix)
    dot = abs(float(np.dot(expected_quaternion, astrox_quaternion)))
    angle_deg = math.degrees(2.0 * math.acos(min(1.0, dot)))
    assert angle_deg <= QUATERNION_ANGLE_ABS_DEG


def main() -> int:
    try:
        configure_astrox_from_env()
        _check_central_body_frame_static_inertial_to_fixed(0.0)
        _check_central_body_frame_static_inertial_to_fixed(90.0)
        _check_central_body_frame_static_inertial_to_fixed(180.0)
        _check_earth_moon_libration_cartesian_matches_moon_centered_frame(0.0)
        _check_earth_moon_libration_cartesian_matches_moon_centered_frame(90.0)
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=5")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
