"""Shared access mixed-model comparison helpers."""

# Coverage:
#   Branches:
#     - site-origin access interval comparison against sampled WGS84 obstruction: partial
#     - satellite-pair access interval comparison against sampled WGS84 obstruction: partial
#     - site-origin AER comparison against local ECEF topocentric geometry: partial
#   Fields:
#     - Passes.AccessStart/AccessStop: partial
#     - AllDatas.Azimuth/Elevation/Range: partial
#   Parameters:
#     - compute_aer: partial, exercised by importing scripts
#     - step_s: partial, exercised by importing scripts
#   Comparison path:
#     - External: local state functions, WGS84 segment obstruction, and ECEF topocentric frame math

from __future__ import annotations

import numpy as np

from tests.validation.cross_validation.access._aer import (
    first_aer_rows,
    site_topocentric_from_ecef,
)
from tests.validation.cross_validation.access._cases import (
    AER_CONVENTION_RANGE_ABS_M,
    CrossValidationError,
    INTERVAL_ABS_S,
    SITE_HEIGHT_M,
    SITE_LATITUDE_DEG,
    SITE_LONGITUDE_DEG,
    START,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    fixed_site_ecef,
    intervals_from_access_passes,
    sampled_satellite_visibility_intervals,
    seconds_since,
)


MIXED_MODEL_AZIMUTH_ABS_DEG = 2.0e-2
MIXED_MODEL_ELEVATION_ABS_DEG = 2.0e-2


def compare_site_origin_access(
    result: dict[str, object],
    *,
    state_ecef,
    start: str,
    stop: str,
) -> None:
    site_ecef = fixed_site_ecef(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M)
    expected = sampled_satellite_visibility_intervals(
        start=start,
        stop=stop,
        left_state=lambda _offset_s: site_ecef,
        right_state=state_ecef,
    )
    actual = intervals_from_access_passes(result["Passes"])
    compare_intervals(expected, actual, tolerance_s=INTERVAL_ABS_S)
    if actual:
        compare_site_origin_aer(result, state_ecef=state_ecef)


def compare_satellite_pair_access(
    result: dict[str, object],
    *,
    left_state_ecef,
    right_state_ecef,
    start: str,
    stop: str,
) -> None:
    expected = sampled_satellite_visibility_intervals(
        start=start,
        stop=stop,
        left_state=left_state_ecef,
        right_state=right_state_ecef,
    )
    actual = intervals_from_access_passes(result["Passes"])
    compare_intervals(expected, actual, tolerance_s=INTERVAL_ABS_S)


def compare_site_origin_aer(
    result: dict[str, object],
    *,
    state_ecef,
) -> None:
    site_ecef = fixed_site_ecef(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M)
    failures: list[str] = []
    rows = list(first_aer_rows(result, max_passes=1))
    for row in rows:
        offset_s = seconds_since(str(row["Time"]), START)
        azimuth_deg, elevation_deg, range_m = site_topocentric_from_ecef(
            site_ecef,
            np.array(state_ecef(offset_s)),
            latitude_deg=SITE_LATITUDE_DEG,
            longitude_deg=SITE_LONGITUDE_DEG,
        )
        azimuth_error = abs(wrapped_angle_error_deg(float(row["Azimuth"]), azimuth_deg))
        elevation_error = abs(float(row["Elevation"]) - elevation_deg)
        range_error = abs(float(row["Range"]) - range_m)
        if azimuth_error > MIXED_MODEL_AZIMUTH_ABS_DEG:
            failures.append(
                f"{row['Time']} azimuth error {azimuth_error:.12g} deg exceeds {MIXED_MODEL_AZIMUTH_ABS_DEG:.12g} deg"
            )
        if elevation_error > MIXED_MODEL_ELEVATION_ABS_DEG:
            failures.append(
                f"{row['Time']} elevation error {elevation_error:.12g} deg exceeds {MIXED_MODEL_ELEVATION_ABS_DEG:.12g} deg"
            )
        if range_error > AER_CONVENTION_RANGE_ABS_M:
            failures.append(
                f"{row['Time']} range error {range_error:.12g} m exceeds {AER_CONVENTION_RANGE_ABS_M:.12g} m"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def wrapped_angle_error_deg(actual_deg: float, expected_deg: float) -> float:
    return (actual_deg - expected_deg + 180.0) % 360.0 - 180.0
