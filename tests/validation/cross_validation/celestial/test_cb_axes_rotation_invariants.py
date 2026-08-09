#!/usr/bin/env python3
"""Live invariant validation for celestial axes-rotation output."""

# Coverage:
#   Branches:
#     - CbAxesRotation order 0 and order 1: verified for same-body inertial
#       identity cases covering Earth and Moon at two explicit epochs
#   Fields:
#     - Rotation quaternion and optional angular-velocity suffix: verified only
#       for the identity invariant; arbitrary central-body/frame transformations
#       remain outside this check
#   Parameters:
#     - from/to central body: Earth and Moon, with the same value on both sides
#     - from/to frame: INERTIAL on both sides
#     - order: explicit 0 and 1
#     - epoch: two maintained UTC epochs
#   Comparison:
#     - Independent invariant: a same-body, same-frame rotation is identity and
#       its angular velocity is zero
#     - Tolerance: 1e-12 for the dimensionless quaternion and angular-velocity
#       values returned by the maintained identity cases

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import celestial  # noqa: E402
from tests.validation._support import configure_astrox_from_env  # noqa: E402


EPOCHS = ("2026-01-01T00:00:00.000Z", "2026-06-01T00:00:00.000Z")
CENTRAL_BODIES = ("Earth", "Moon")
ABS_TOL = 1.0e-12


class CrossValidationError(Exception):
    """Raised when a same-body inertial rotation is not the identity."""


def require_number(value: Any, *, field: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise CrossValidationError(f"{field} must be numeric")
    return float(value)


def check_identity(*, central_body: str, epoch: str, order: int) -> None:
    response = celestial.cb_axes_rotation(
        from_central_body=central_body,
        to_central_body=central_body,
        epoch=epoch,
        from_frame="INERTIAL",
        to_frame="INERTIAL",
        order=order,
    )
    if response.get("IsSuccess") is not True:
        raise CrossValidationError(
            f"{central_body}/{epoch}/order={order} returned "
            f"IsSuccess={response.get('IsSuccess')!r}: {response.get('Message')!r}"
        )
    rotation = response.get("Rotation")
    if not isinstance(rotation, list):
        raise CrossValidationError("Rotation must be an array")
    expected_length = 4 if order == 0 else 7
    if len(rotation) != expected_length:
        raise CrossValidationError(
            f"{central_body}/{epoch}/order={order} returned Rotation length "
            f"{len(rotation)}, expected {expected_length}"
        )
    expected = (0.0, 0.0, 0.0, 1.0)
    for index, expected_value in enumerate(expected):
        actual = require_number(rotation[index], field=f"Rotation[{index}]")
        if not math.isclose(actual, expected_value, abs_tol=ABS_TOL, rel_tol=0.0):
            raise CrossValidationError(
                f"{central_body}/{epoch}/order={order} Rotation[{index}]={actual:g}, "
                f"expected {expected_value:g}"
            )
    if order == 1:
        for index, value in enumerate(rotation[4:], start=4):
            actual = require_number(value, field=f"Rotation[{index}]")
            if not math.isclose(actual, 0.0, abs_tol=ABS_TOL, rel_tol=0.0):
                raise CrossValidationError(
                    f"{central_body}/{epoch}/order=1 Rotation[{index}]={actual:g}, expected 0"
                )


def test_same_body_inertial_rotations_are_identity() -> None:
    configure_astrox_from_env()
    for central_body in CENTRAL_BODIES:
        for epoch in EPOCHS:
            check_identity(central_body=central_body, epoch=epoch, order=0)
            check_identity(central_body=central_body, epoch=epoch, order=1)


def main() -> int:
    try:
        test_same_body_inertial_rotations_are_identity()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=8")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
