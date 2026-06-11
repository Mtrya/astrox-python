"""Access cross-validation for fixed-ground and SGP4 branches."""

# Coverage:
#   Branches:
#     - ground site -> SGP4 satellite: verified for intervals, AER convention, and light-time shift
#     - SGP4 satellite -> ground site: verified for interval/range symmetry and satellite-origin AER convention
#     - ground site -> ground site: verified for a blocked WGS84 segment case
#   Fields:
#     - Passes.AccessStart/AccessStop: verified (Skyfield SGP4 plus WGS84 segment-obstruction oracle)
#     - AllDatas.Azimuth/Elevation/Range: partial (ground-origin and satellite-origin conventions calibrated; strict dense residual unresolved)
#     - Passes with no access: verified (blocked WGS84 ground segment returns no passes)
#   Parameters:
#     - compute_aer: verified for true on AER comparisons; false/omitted field-shape behavior lives in live snapshot tests
#     - step_s: partial (60 s dense AER sample compared; cadence semantics live in live snapshot tests)
#     - use_light_time_delay: verified for ground -> SGP4 range-over-c shift in the covered case
#   Comparison:
#     - External: Skyfield SGP4 topocentric geometry, WGS84 segment obstruction, range-over-c light-time derivation, geodetic local satellite frame
#     - Constants: TLE_A, WGS84 ellipsoid, SPEED_OF_LIGHT_M_S from helper diagnostics
#     - Tolerances: INTERVAL_ABS_S, CHAIN_INTERVAL_ABS_S, AER_* constants, LIGHT_TIME_* constants
#   Unresolved:
#     - strict dense ground-origin AER residual: unresolved after same-epoch, light-time, manual ITRS, ellipsoid-horizon, and site/time-offset diagnostics

from __future__ import annotations

import sys

import pytest

from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._aer import (
    compare_ground_origin_aer_rows_with_skyfield,
    compare_light_time_aer_effect,
    compare_light_time_interval_shift,
    compare_range_symmetry,
    compare_satellite_origin_aer_rows_with_geodetic_local_frame,
    first_aer_rows,
    ground_origin_aer_failures,
    strict_ground_aer_diagnostics,
)
from tests.validation.cross_validation.access._cases import (
    AER_CONVENTION_AZIMUTH_ABS_DEG,
    AER_CONVENTION_ELEVATION_ABS_DEG,
    AER_CONVENTION_RANGE_ABS_M,
    AER_DENSE_AZIMUTH_ABS_DEG,
    AER_DENSE_ELEVATION_ABS_DEG,
    AER_STRICT_ABS_DEG,
    CHAIN_INTERVAL_ABS_S,
    CrossValidationError,
    DAY_STOP,
    INTERVAL_ABS_S,
    REMOTE_HEIGHT_M,
    REMOTE_LATITUDE_DEG,
    REMOTE_LONGITUDE_DEG,
    SATELLITE_LOCAL_AER_ABS_DEG,
    SITE_HEIGHT_M,
    SITE_LATITUDE_DEG,
    SITE_LONGITUDE_DEG,
    START,
    TLE_A,
    compute_access,
    remote_site,
    sgp4_entity,
    site,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    fixed_site_ecef,
    intervals_from_access_passes,
    segment_intersects_wgs84,
    sgp4_site_visibility_intervals,
    skyfield_satellite,
    skyfield_site,
)


def test_ground_to_sgp4_intervals_matches_ellipsoid_obstruction_oracle() -> None:
    configure_astrox_from_env()
    result = compute_access(site(), sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = sgp4_site_visibility_intervals(
        start=START,
        stop=DAY_STOP,
        satellite=skyfield_satellite(TLE_A, "ISS"),
        site_position=skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M),
    )
    compare_intervals(expected, actual, tolerance_s=INTERVAL_ABS_S)


def test_ground_to_sgp4_aer_matches_skyfield_topocentric_convention() -> None:
    configure_astrox_from_env()
    result = compute_access(
        site(),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        compute_aer=True,
    )
    rows = list(first_aer_rows(result, max_passes=2))
    compare_ground_origin_aer_rows_with_skyfield(
        rows,
        azimuth_abs_deg=AER_CONVENTION_AZIMUTH_ABS_DEG,
        elevation_abs_deg=AER_CONVENTION_ELEVATION_ABS_DEG,
        range_abs_m=AER_CONVENTION_RANGE_ABS_M,
    )


def test_ground_to_sgp4_dense_aer_matches_skyfield_topocentric_convention() -> None:
    configure_astrox_from_env()
    result = compute_access(
        site(),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        step_s=60.0,
        compute_aer=True,
    )
    rows = list(first_aer_rows(result, max_passes=3))
    compare_ground_origin_aer_rows_with_skyfield(
        rows,
        azimuth_abs_deg=AER_DENSE_AZIMUTH_ABS_DEG,
        elevation_abs_deg=AER_DENSE_ELEVATION_ABS_DEG,
        range_abs_m=AER_CONVENTION_RANGE_ABS_M,
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Ground-origin access AER keeps a residual against Skyfield; same-epoch, "
        "range-over-c light-time, manual ITRS topocentric, ellipsoid-horizon, "
        "and simple site/time offset diagnostics do not explain the dense-row mismatch."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_ground_to_sgp4_strict_aer_matches_skyfield_topocentric_diagnostics() -> None:
    configure_astrox_from_env()
    result = compute_access(
        site(),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        step_s=60.0,
        compute_aer=True,
    )
    rows = list(first_aer_rows(result, max_passes=3))
    failures = ground_origin_aer_failures(
        rows,
        azimuth_abs_deg=AER_STRICT_ABS_DEG,
        elevation_abs_deg=AER_STRICT_ABS_DEG,
        range_abs_m=AER_CONVENTION_RANGE_ABS_M,
    )
    diagnostics = strict_ground_aer_diagnostics(rows)
    if failures:
        raise CrossValidationError("\n".join([*failures, *diagnostics]))


def test_sgp4_to_ground_matches_ground_to_sgp4_symmetry_invariant() -> None:
    configure_astrox_from_env()
    forward = compute_access(site(), sgp4_entity(), start=START, stop=DAY_STOP, compute_aer=True)
    reverse = compute_access(sgp4_entity(), site(), start=START, stop=DAY_STOP, compute_aer=True)
    compare_intervals(
        intervals_from_access_passes(forward["Passes"]),
        intervals_from_access_passes(reverse["Passes"]),
        tolerance_s=CHAIN_INTERVAL_ABS_S,
    )
    compare_range_symmetry(
        list(first_aer_rows(forward, max_passes=2)),
        list(first_aer_rows(reverse, max_passes=2)),
    )


def test_sgp4_to_ground_satellite_origin_aer_matches_geodetic_local_frame() -> None:
    configure_astrox_from_env()
    result = compute_access(sgp4_entity(), site(), start=START, stop=DAY_STOP, compute_aer=True)
    rows = list(first_aer_rows(result, max_passes=2))
    compare_satellite_origin_aer_rows_with_geodetic_local_frame(
        rows,
        azimuth_abs_deg=SATELLITE_LOCAL_AER_ABS_DEG,
        elevation_abs_deg=SATELLITE_LOCAL_AER_ABS_DEG,
        range_abs_m=AER_CONVENTION_RANGE_ABS_M,
    )


def test_ground_to_sgp4_light_time_delay_matches_range_over_c_shift() -> None:
    configure_astrox_from_env()
    plain = compute_access(
        site(),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        compute_aer=True,
        use_light_time_delay=False,
    )
    delayed = compute_access(
        site(),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        compute_aer=True,
        use_light_time_delay=True,
    )
    compare_light_time_interval_shift(plain["Passes"], delayed["Passes"])
    compare_light_time_aer_effect(
        list(first_aer_rows(plain, max_passes=1)),
        list(first_aer_rows(delayed, max_passes=1)),
    )


def test_blocked_ground_to_ground_matches_wgs84_obstruction_oracle() -> None:
    configure_astrox_from_env()
    ground_a = site("Hawaii")
    ground_b = remote_site()
    if not segment_intersects_wgs84(
        fixed_site_ecef(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M),
        fixed_site_ecef(REMOTE_LATITUDE_DEG, REMOTE_LONGITUDE_DEG, REMOTE_HEIGHT_M),
    ):
        raise CrossValidationError("independent WGS84 segment check expected a blocked site pair")
    result = compute_access(ground_a, ground_b)
    actual = intervals_from_access_passes(result["Passes"])
    if actual:
        raise CrossValidationError(
            "ASTROX returned access for a ground-to-ground pair whose straight segment intersects WGS84"
        )


def main() -> int:
    try:
        test_ground_to_sgp4_intervals_matches_ellipsoid_obstruction_oracle()
        test_ground_to_sgp4_aer_matches_skyfield_topocentric_convention()
        test_ground_to_sgp4_dense_aer_matches_skyfield_topocentric_convention()
        test_sgp4_to_ground_matches_ground_to_sgp4_symmetry_invariant()
        test_sgp4_to_ground_satellite_origin_aer_matches_geodetic_local_frame()
        test_ground_to_sgp4_light_time_delay_matches_range_over_c_shift()
        test_blocked_ground_to_ground_matches_wgs84_obstruction_oracle()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=7")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
