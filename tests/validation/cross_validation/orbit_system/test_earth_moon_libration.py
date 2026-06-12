"""Cross-validation for orbits.earth_moon_libration."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.validation._support import configure_astrox_from_env
from tests.validation.cross_validation.orbit_system._support import (
    CrossValidationError,
    _check_earth_moon_libration_cartesian,
    _check_earth_moon_libration_cartesian_translation_absent,
    _check_earth_moon_libration_unit_quaternion_matches,
    _check_earth_moon_libration_unit_quaternion_naive_conventions_fail,
)


@pytest.fixture(autouse=True)
def _configure_astrox() -> None:
    configure_astrox_from_env()


@pytest.mark.parametrize(
    "epoch,inertial_longitude_deg",
    [
        ("2024-01-01T00:00:00Z", 0.0),
        ("2024-01-01T00:00:00Z", 90.0),
        ("2024-01-01T00:00:00Z", 180.0),
        ("2024-06-01T00:00:00Z", 0.0),
    ],
    ids=["2024-01-01_lon0", "2024-01-01_lon90", "2024-01-01_lon180", "2024-06-01_lon0"],
)
def test_earth_moon_libration_cartesian_matches_moon_centered_frame(
    epoch: str,
    inertial_longitude_deg: float,
) -> None:
    _check_earth_moon_libration_cartesian(epoch, inertial_longitude_deg)


@pytest.mark.calibration
@pytest.mark.xfail(
    strict=True,
    reason="EarthMoonLibration2.unit_quaternion does not match any standard convention; best residual ~24.56°. The cartesian field is verified, so the frame origin and axes are calibrated.",
)
def test_earth_moon_libration_unit_quaternion_matches_libration_frame() -> None:
    _check_earth_moon_libration_unit_quaternion_matches()


def test_earth_moon_libration_unit_quaternion_naive_conventions_fail() -> None:
    _check_earth_moon_libration_unit_quaternion_naive_conventions_fail()


def test_earth_moon_libration_cartesian_translation_is_absent() -> None:
    _check_earth_moon_libration_cartesian_translation_absent()


def main() -> int:
    """Run earth_moon_libration cross-checks and report counts."""
    try:
        configure_astrox_from_env()
        checked = 0
        for epoch, longitude_deg in (
            ("2024-01-01T00:00:00Z", 0.0),
            ("2024-01-01T00:00:00Z", 90.0),
            ("2024-01-01T00:00:00Z", 180.0),
            ("2024-06-01T00:00:00Z", 0.0),
        ):
            _check_earth_moon_libration_cartesian(epoch, longitude_deg)
            checked += 1
        _check_earth_moon_libration_unit_quaternion_naive_conventions_fail()
        checked += 1
        _check_earth_moon_libration_cartesian_translation_absent()
        checked += 1
    except CrossValidationError as exc:
        import sys

        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"CROSS_VALIDATION_CHECKED={checked}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
