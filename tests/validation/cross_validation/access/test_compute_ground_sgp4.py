"""Access cross-validation for fixed-ground and SGP4 branches."""

from __future__ import annotations

import pytest

from tests.validation._support import configure_astrox_from_env
from tests.validation.cross_validation.access._aer import (
    compare_ground_origin_aer_rows_with_skyfield,
    compare_light_time_aer_effect,
    compare_light_time_interval_shift,
    compare_range_symmetry,
    first_aer_rows,
    ground_origin_aer_failures,
    spacecraft_frame_residuals,
    strict_ground_aer_diagnostics,
)
from tests.validation.cross_validation.access._cases import (
    AER_CONVENTION_AZIMUTH_ABS_DEG,
    AER_CONVENTION_ELEVATION_ABS_DEG,
    AER_CONVENTION_RANGE_ABS_M,
    AER_STRICT_ABS_DEG,
    CHAIN_INTERVAL_ABS_S,
    CrossValidationError,
    DAY_STOP,
    INTERVAL_ABS_S,
    REMOTE_HEIGHT_M,
    REMOTE_LATITUDE_DEG,
    REMOTE_LONGITUDE_DEG,
    SATELLITE_AER_FRAME_ABS_DEG,
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


def test_ground_to_sgp4_intervals_match_ellipsoid_obstruction_oracle() -> None:
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


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Ground-origin access AER keeps a small residual against Skyfield; same-epoch, "
        "range-over-c light-time, manual ITRS topocentric, and ellipsoid-horizon diagnostics "
        "do not explain the sub-arcsecond mismatch."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_ground_to_sgp4_aer_strict_residual_diagnostics() -> None:
    configure_astrox_from_env()
    result = compute_access(
        site(),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        compute_aer=True,
    )
    rows = list(first_aer_rows(result, max_passes=2))
    failures = ground_origin_aer_failures(
        rows,
        azimuth_abs_deg=AER_STRICT_ABS_DEG,
        elevation_abs_deg=AER_STRICT_ABS_DEG,
        range_abs_m=AER_CONVENTION_RANGE_ABS_M,
    )
    diagnostics = strict_ground_aer_diagnostics(rows)
    if failures:
        raise CrossValidationError("\n".join([*failures, *diagnostics]))


def test_sgp4_to_ground_intervals_and_ranges_are_symmetric() -> None:
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


@pytest.mark.calibration
@pytest.mark.xfail(
    reason=(
        "Satellite-origin access AER range is symmetric, but angle samples do not fit the "
        "tested RSW, TNW, VVLH, LVLH, or nadir/velocity candidate frames closely enough."
    ),
    raises=CrossValidationError,
    strict=True,
)
def test_sgp4_to_ground_satellite_origin_aer_frame_calibration() -> None:
    configure_astrox_from_env()
    result = compute_access(sgp4_entity(), site(), start=START, stop=DAY_STOP, compute_aer=True)
    rows = list(first_aer_rows(result, max_passes=2))
    residuals = spacecraft_frame_residuals(rows)
    best = min(residuals, key=lambda item: max(item.azimuth_error_deg, item.elevation_error_deg))
    if (
        best.azimuth_error_deg > SATELLITE_AER_FRAME_ABS_DEG
        or best.elevation_error_deg > SATELLITE_AER_FRAME_ABS_DEG
        or best.range_error_m > AER_CONVENTION_RANGE_ABS_M
    ):
        details = [
            (
                f"{item.name}: az={item.azimuth_error_deg:.12g} deg "
                f"el={item.elevation_error_deg:.12g} deg range={item.range_error_m:.12g} m"
            )
            for item in sorted(residuals, key=lambda item: max(item.azimuth_error_deg, item.elevation_error_deg))
        ]
        raise CrossValidationError(
            "best tested spacecraft frame does not explain ASTROX satellite-origin AER:\n"
            + "\n".join(details)
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


def test_blocked_ground_to_ground_returns_no_access() -> None:
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
