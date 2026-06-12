"""Cross-validation for orbits.transform_frame."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.validation._support import configure_astrox_from_env
from tests.validation.cross_validation.orbit_system._support import (
    EARTH_ICRF_ABS_M,
    EARTH_J2000_ABS_M,
    CrossValidationError,
    _check_earth_fixed_to_inertial,
    _check_earth_inertial_to_fixed,
    _check_earth_inertial_to_target,
    _check_mars_fixed_orientation,
    _check_mars_inertial,
    _check_moon_fixed,
    _check_moon_inertial,
    _check_moon_inertial_origin,
    _check_sun_fixed,
    _check_sun_inertial,
)


@pytest.fixture(autouse=True)
def _configure_astrox() -> None:
    configure_astrox_from_env()


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_earth_inertial_to_fixed_matches_era(
    inertial_longitude_deg: float,
) -> None:
    _check_earth_inertial_to_fixed(inertial_longitude_deg)


@pytest.mark.parametrize(
    "fixed_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_earth_fixed_to_inertial_matches_era(
    fixed_longitude_deg: float,
) -> None:
    _check_earth_fixed_to_inertial(fixed_longitude_deg)


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_earth_inertial_to_j2000_matches_fk5(
    inertial_longitude_deg: float,
) -> None:
    _check_earth_inertial_to_target(
        inertial_longitude_deg,
        target_frame="J2000",
        tolerance_m=EARTH_J2000_ABS_M,
    )


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_earth_inertial_to_icrf_matches_icrs(
    inertial_longitude_deg: float,
) -> None:
    _check_earth_inertial_to_target(
        inertial_longitude_deg,
        target_frame="ICRF",
        tolerance_m=EARTH_ICRF_ABS_M,
    )


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_moon_inertial_to_inertial_matches_mmej2000(
    inertial_longitude_deg: float,
) -> None:
    _check_moon_inertial(inertial_longitude_deg)


def test_moon_inertial_origin_matches_mmej2000() -> None:
    _check_moon_inertial_origin()


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_moon_inertial_to_fixed_matches_iau_moon(
    inertial_longitude_deg: float,
) -> None:
    _check_moon_fixed(inertial_longitude_deg)


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_mars_inertial_to_inertial_matches_marsiau(
    inertial_longitude_deg: float,
) -> None:
    _check_mars_inertial(inertial_longitude_deg)


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_mars_fixed_to_fixed_matches_iau_mars_orientation(
    inertial_longitude_deg: float,
) -> None:
    _check_mars_fixed_orientation(inertial_longitude_deg)


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_sun_inertial_to_inertial_matches_j2000(
    inertial_longitude_deg: float,
) -> None:
    _check_sun_inertial(inertial_longitude_deg)


@pytest.mark.parametrize(
    "inertial_longitude_deg",
    [0.0, 90.0, 180.0],
    ids=lambda v: f"lon{v:.0f}",
)
def test_sun_fixed_to_fixed_matches_iau_sun(
    inertial_longitude_deg: float,
) -> None:
    _check_sun_fixed(inertial_longitude_deg)


def main() -> int:
    """Run transform_frame cross-checks and report counts."""
    try:
        configure_astrox_from_env()
        checked = 0
        for longitude_deg in (0.0, 90.0, 180.0):
            _check_earth_inertial_to_fixed(longitude_deg)
            checked += 1
            _check_earth_fixed_to_inertial(longitude_deg)
            checked += 1
            _check_earth_inertial_to_target(
                longitude_deg, target_frame="J2000", tolerance_m=EARTH_J2000_ABS_M
            )
            checked += 1
            _check_earth_inertial_to_target(
                longitude_deg, target_frame="ICRF", tolerance_m=EARTH_ICRF_ABS_M
            )
            checked += 1
            _check_moon_inertial(longitude_deg)
            checked += 1
            _check_moon_fixed(longitude_deg)
            checked += 1
            _check_mars_inertial(longitude_deg)
            checked += 1
            _check_mars_fixed_orientation(longitude_deg)
            checked += 1
            _check_sun_inertial(longitude_deg)
            checked += 1
            _check_sun_fixed(longitude_deg)
            checked += 1
        _check_moon_inertial_origin()
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
