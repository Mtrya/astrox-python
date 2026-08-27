#!/usr/bin/env python3
"""Live cross-validation for celestial axes-rotation output."""

# Coverage:
#   Branches:
#     - Same-body INERTIAL -> INERTIAL order 0/1: verified identity controls for
#       Earth and Moon at two explicit epochs
#     - Earth INERTIAL -> FIXED order 0/1: verified against an independent ERFA
#       Earth-orientation construction at two epochs
#     - Earth same-body EclpJ2000ICRF -> ICRF order 0/1: verified against the
#       analytic J2000 mean-obliquity rotation at two epochs
#     - Earth -> Moon INERTIAL -> FIXED order 1 angular velocity: verified against
#       an independent SPICE Moon orientation derivative at two epochs
#     - Earth -> Moon INERTIAL -> FIXED quaternion: unresolved; the SPICE DE440
#       orientation differs by 0.001-0.003 degrees, so the strict calibration
#       xfail remains visible
#   Fields:
#     - Rotation length, numeric values, quaternion norm: verified for maintained
#       non-identity cases
#     - Earth quaternion and angular velocity: verified against ERFA
#     - Moon order-1 angular velocity: verified against SPICE
#     - Moon fixed quaternion: unresolved after an independent model comparison
#     - EclpJ2000ICRF quaternion and zero angular velocity: verified analytically
#   Parameters:
#     - central-body/frame combinations above
#     - order 0 and 1 where the branch exposes both
#     - epoch: 2026-01-01 and 2026-06-01 UTC
#   Comparison:
#     - Earth oracle: ERFA c2i06a plus ERA evaluated with UTC, matching the
#       service's observed UTC rotation convention; angular velocity comes from
#       a centered one-second derivative of the same independent matrix
#     - Moon oracle: SPICE J2000 -> IAU_MOON transform and xf2rav angular velocity
#       from the maintained public PCK/DE440 data; the quaternion residual is kept
#       unresolved instead of absorbed by a loose tolerance
#     - Ecliptic oracle: fixed rotation by the standard J2000 mean obliquity
#     - Tolerances: matrix 1e-8, angular velocity 1e-10 rad/s, identity 1e-12;
#       these are precision bounds for independent comparisons, not model-fit
#       envelopes

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Callable

import erfa
import numpy as np
import pytest
from astropy.time import Time, TimeDelta
from scipy.spatial.transform import Rotation

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import celestial  # noqa: E402
from tests.validation._support import configure_astrox_from_env  # noqa: E402
from tests.validation.cross_validation.orbit_system._support import (  # noqa: E402
    _ensure_spice_kernels_loaded,
)


EPOCHS = ("2026-01-01T00:00:00.000Z", "2026-06-01T00:00:00.000Z")
CENTRAL_BODIES = ("Earth", "Moon")
ABS_TOL = 1.0e-12
MATRIX_ABS_TOL = 1.0e-8
ANGULAR_VELOCITY_ABS_TOL = 1.0e-10
QUATERNION_RESOLUTION_DEG = 1.0e-6
J2000_MEAN_OBLIQUITY_DEG = 23.43929111111111


class CrossValidationError(Exception):
    """Raised when ASTROX and the independent axes oracle disagree."""


class ResponseShapeError(Exception):
    """Raised when the live rotation response violates its maintained shape."""


def require_number(value: Any, *, field: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ResponseShapeError(f"{field} must be numeric")
    return float(value)


def rotation_response(
    *,
    from_central_body: str,
    to_central_body: str,
    epoch: str,
    from_frame: str,
    to_frame: str,
    order: int,
) -> np.ndarray:
    response = celestial.cb_axes_rotation(
        from_central_body=from_central_body,
        to_central_body=to_central_body,
        epoch=epoch,
        from_frame=from_frame,
        to_frame=to_frame,
        order=order,
    )
    if not isinstance(response, dict):
        raise ResponseShapeError(
            f"{from_central_body}->{to_central_body} {from_frame}->{to_frame} "
            f"order={order} response must be an object"
        )
    rotation = response.get("Rotation")
    expected_length = 4 if order == 0 else 7
    if not isinstance(rotation, list) or len(rotation) != expected_length:
        raise ResponseShapeError(
            f"Rotation must be a {expected_length}-value array for order={order}"
        )
    values = [require_number(value, field=f"Rotation[{index}]") for index, value in enumerate(rotation)]
    quaternion_norm = float(np.linalg.norm(values[:4]))
    if not math.isclose(quaternion_norm, 1.0, abs_tol=1.0e-12, rel_tol=0.0):
        raise ResponseShapeError(f"Rotation quaternion norm={quaternion_norm:g}, expected 1")
    return np.asarray(values, dtype=float)


def check_identity(*, central_body: str, epoch: str, order: int) -> None:
    rotation = rotation_response(
        from_central_body=central_body,
        to_central_body=central_body,
        epoch=epoch,
        from_frame="INERTIAL",
        to_frame="INERTIAL",
        order=order,
    )
    expected = (0.0, 0.0, 0.0, 1.0)
    for index, expected_value in enumerate(expected):
        actual = rotation[index]
        if not math.isclose(actual, expected_value, abs_tol=ABS_TOL, rel_tol=0.0):
            raise CrossValidationError(
                f"{central_body}/{epoch}/order={order} Rotation[{index}]={actual:g}, "
                f"expected {expected_value:g}"
            )
    if order == 1 and not np.allclose(rotation[4:], 0.0, atol=ABS_TOL, rtol=0.0):
        raise CrossValidationError(
            f"{central_body}/{epoch}/order=1 angular velocity={rotation[4:].tolist()}, expected zero"
        )


def _earth_inertial_to_fixed_matrix(time: Time) -> np.ndarray:
    c2i = np.asarray(erfa.c2i06a(time.tt.jd1, time.tt.jd2))
    era = erfa.era00(time.utc.jd1, time.utc.jd2)
    rotation = np.array(
        [
            [math.cos(era), math.sin(era), 0.0],
            [-math.sin(era), math.cos(era), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    return (rotation @ c2i).T


def _angular_velocity_from_matrix(
    matrix_at: Callable[[Time], np.ndarray],
    time: Time,
) -> np.ndarray:
    delta = TimeDelta(1.0, format="sec")
    matrix = matrix_at(time)
    derivative = (matrix_at(time + delta) - matrix_at(time - delta)) / 2.0
    skew = derivative @ matrix.T
    return np.array([skew[2, 1], skew[0, 2], skew[1, 0]])


def _assert_rotation_matrix_matches(
    actual_rotation: np.ndarray,
    expected_matrix: np.ndarray,
    *,
    label: str,
) -> float:
    actual_matrix = Rotation.from_quat(actual_rotation[:4]).as_matrix()
    error = float(np.max(np.abs(actual_matrix - expected_matrix)))
    if error > MATRIX_ABS_TOL:
        raise CrossValidationError(
            f"{label} rotation matrix residual={error:.12g}, "
            f"exceeds {MATRIX_ABS_TOL:g}"
        )
    return error


def test_same_body_inertial_rotations_are_identity() -> None:
    configure_astrox_from_env()
    for central_body in CENTRAL_BODIES:
        for epoch in EPOCHS:
            check_identity(central_body=central_body, epoch=epoch, order=0)
            check_identity(central_body=central_body, epoch=epoch, order=1)


def test_earth_inertial_to_fixed_matches_erfa() -> None:
    configure_astrox_from_env()
    for epoch in EPOCHS:
        time = Time(epoch, scale="utc")
        expected_matrix = _earth_inertial_to_fixed_matrix(time)
        expected_angular_velocity = _angular_velocity_from_matrix(
            _earth_inertial_to_fixed_matrix,
            time,
        )
        for order in (0, 1):
            actual = rotation_response(
                from_central_body="Earth",
                to_central_body="Earth",
                epoch=epoch,
                from_frame="INERTIAL",
                to_frame="FIXED",
                order=order,
            )
            _assert_rotation_matrix_matches(
                actual,
                expected_matrix,
                label=f"Earth/{epoch}/order={order}",
            )
            if order == 1 and not np.allclose(
                actual[4:],
                expected_angular_velocity,
                atol=ANGULAR_VELOCITY_ABS_TOL,
                rtol=0.0,
            ):
                raise CrossValidationError(
                    f"Earth/{epoch}/order=1 angular velocity residual="
                    f"{np.max(np.abs(actual[4:] - expected_angular_velocity)):.12g}"
                )


def _icrf_to_eclp_j2000_matrix() -> np.ndarray:
    obliquity = math.radians(J2000_MEAN_OBLIQUITY_DEG)
    return np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, math.cos(obliquity), math.sin(obliquity)],
            [0.0, -math.sin(obliquity), math.cos(obliquity)],
        ]
    )


def test_eclp_j2000_icrf_rotation_matches_mean_obliquity() -> None:
    configure_astrox_from_env()
    expected_matrix = _icrf_to_eclp_j2000_matrix()
    residuals: list[float] = []
    for epoch in EPOCHS:
        for order in (0, 1):
            actual = rotation_response(
                from_central_body="Earth",
                to_central_body="Earth",
                epoch=epoch,
                from_frame="EclpJ2000ICRF",
                to_frame="ICRF",
                order=order,
            )
            residuals.append(
                _assert_rotation_matrix_matches(
                    actual,
                    expected_matrix,
                    label=f"Earth/EclpJ2000ICRF->ICRF/{epoch}/order={order}",
                )
            )
            if order == 1 and not np.allclose(
                actual[4:],
                0.0,
                atol=ABS_TOL,
                rtol=0.0,
            ):
                raise CrossValidationError(
                    "fixed EclpJ2000ICRF/ICRF relation returned nonzero angular "
                    f"velocity at {epoch}: {actual[4:].tolist()}"
                )
    print(f"ECLIPTIC_ROTATION_MAX_MATRIX_RESIDUAL={max(residuals):.12g}")


def _moon_inertial_to_fixed_matrix(time: Time) -> np.ndarray:
    import spiceypy as spice

    et = spice.str2et(time.utc.isot.replace(".000", ""))
    return np.asarray(spice.pxform("J2000", "IAU_MOON", et)).T


def _moon_angular_velocity(time: Time) -> np.ndarray:
    import spiceypy as spice

    et = spice.str2et(time.utc.isot.replace(".000", ""))
    _rotation, angular_velocity = spice.xf2rav(spice.sxform("J2000", "IAU_MOON", et))
    return np.asarray(angular_velocity)


def test_earth_moon_inertial_to_fixed_angular_velocity_matches_spice() -> None:
    configure_astrox_from_env()
    _ensure_spice_kernels_loaded()
    for epoch in EPOCHS:
        time = Time(epoch, scale="utc")
        actual = rotation_response(
            from_central_body="Earth",
            to_central_body="Moon",
            epoch=epoch,
            from_frame="INERTIAL",
            to_frame="FIXED",
            order=1,
        )
        expected = _moon_angular_velocity(time)
        error = float(np.max(np.abs(actual[4:] - expected)))
        print(f"MOON_FIXED_CASE={epoch} angular_velocity_residual={error:.12g}")
        if error > ANGULAR_VELOCITY_ABS_TOL:
            raise CrossValidationError(
                f"Earth/Moon/{epoch}/order=1 angular velocity residual={error:.12g}, "
                f"exceeds {ANGULAR_VELOCITY_ABS_TOL:g}"
            )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Earth->Moon INERTIAL->FIXED quaternion remains unresolved: the independent "
        "SPICE DE440 IAU_MOON orientation differs by 0.001-0.003 degrees across "
        "the maintained epochs; reclassify only after the ASTROX Moon frame/model "
        "convention is identified."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_earth_moon_inertial_to_fixed_quaternion_remains_unresolved() -> None:
    configure_astrox_from_env()
    _ensure_spice_kernels_loaded()
    residuals: list[float] = []
    for epoch in EPOCHS:
        time = Time(epoch, scale="utc")
        actual = rotation_response(
            from_central_body="Earth",
            to_central_body="Moon",
            epoch=epoch,
            from_frame="INERTIAL",
            to_frame="FIXED",
            order=0,
        )
        expected_matrix = _moon_inertial_to_fixed_matrix(time)
        actual_matrix = Rotation.from_quat(actual[:4]).as_matrix()
        angle_deg = math.degrees(Rotation.from_matrix(actual_matrix.T @ expected_matrix).magnitude())
        print(f"MOON_FIXED_CASE={epoch} quaternion_residual_deg={angle_deg:.12g}")
        if angle_deg > QUATERNION_RESOLUTION_DEG:
            residuals.append(angle_deg)
    if residuals:
        raise CrossValidationError(
            "Earth->Moon INERTIAL->FIXED quaternion residuals remain unexplained: "
            + ", ".join(f"{value:.12g} deg" for value in residuals)
        )


def main() -> int:
    try:
        test_same_body_inertial_rotations_are_identity()
        test_earth_inertial_to_fixed_matches_erfa()
        test_eclp_j2000_icrf_rotation_matches_mean_obliquity()
        test_earth_moon_inertial_to_fixed_angular_velocity_matches_spice()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=18")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
