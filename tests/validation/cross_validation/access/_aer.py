"""AER comparison helpers for access cross-validation."""

from __future__ import annotations

import math
from datetime import timedelta
from typing import Iterable

import numpy as np
from skyfield.api import wgs84
from skyfield.framelib import itrs

from tests.validation.cross_validation.access._cases import (
    AER_CONVENTION_RANGE_ABS_M,
    LIGHT_TIME_AER_ABS_DEG,
    LIGHT_TIME_RANGE_ABS_M,
    LIGHT_TIME_SHIFT_ABS_S,
    RANGE_SYMMETRY_ABS_M,
    SITE_HEIGHT_M,
    SITE_LATITUDE_DEG,
    SITE_LONGITUDE_DEG,
    SPEED_OF_LIGHT_M_S,
    TLE_A,
    CrossValidationError,
)
from tests.validation.cross_validation.access._geometry import (
    parse_time,
    segment_intersects_wgs84,
    seconds_since,
    skyfield_satellite,
    skyfield_site,
    skyfield_time,
    ts,
    wrapped_angle_error_deg,
)


def first_aer_rows(
    result: dict[str, object],
    *,
    max_passes: int,
) -> Iterable[dict[str, object]]:
    passes = result["Passes"]
    if not isinstance(passes, list) or not passes:
        raise CrossValidationError("ASTROX access result did not include passes")
    for access_pass in passes[:max_passes]:
        all_datas = access_pass["AllDatas"]
        if not isinstance(all_datas, list) or not all_datas:
            raise CrossValidationError("ASTROX access pass did not include AllDatas")
        yield from all_datas


def compare_ground_origin_aer_rows_with_skyfield(
    rows: list[dict[str, object]],
    *,
    azimuth_abs_deg: float,
    elevation_abs_deg: float,
    range_abs_m: float,
) -> None:
    failures = ground_origin_aer_failures(
        rows,
        azimuth_abs_deg=azimuth_abs_deg,
        elevation_abs_deg=elevation_abs_deg,
        range_abs_m=range_abs_m,
    )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_satellite_origin_aer_rows_with_geodetic_local_frame(
    rows: list[dict[str, object]],
    *,
    azimuth_abs_deg: float,
    elevation_abs_deg: float,
    range_abs_m: float,
) -> None:
    failures = satellite_origin_aer_failures(
        rows,
        azimuth_abs_deg=azimuth_abs_deg,
        elevation_abs_deg=elevation_abs_deg,
        range_abs_m=range_abs_m,
    )
    if failures:
        raise CrossValidationError("\n".join(failures))


def ground_origin_aer_failures(
    rows: list[dict[str, object]],
    *,
    azimuth_abs_deg: float,
    elevation_abs_deg: float,
    range_abs_m: float,
) -> list[str]:
    satellite = skyfield_satellite(TLE_A, "ISS")
    observer = skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M)
    failures: list[str] = []
    for row in rows:
        time = skyfield_time(str(row["Time"]))
        altitude, azimuth, distance = (satellite - observer).at(time).altaz()
        azimuth_error_deg = abs(wrapped_angle_error_deg(float(row["Azimuth"]), azimuth.degrees))
        elevation_error_deg = abs(float(row["Elevation"]) - altitude.degrees)
        range_error_m = abs(float(row["Range"]) - distance.m)
        if azimuth_error_deg > azimuth_abs_deg:
            failures.append(
                f"{row['Time']} azimuth error {azimuth_error_deg:.12g} deg exceeds {azimuth_abs_deg:.12g} deg"
            )
        if elevation_error_deg > elevation_abs_deg:
            failures.append(
                f"{row['Time']} elevation error {elevation_error_deg:.12g} deg exceeds {elevation_abs_deg:.12g} deg"
            )
        if range_error_m > range_abs_m:
            failures.append(
                f"{row['Time']} range error {range_error_m:.12g} m exceeds {range_abs_m:.12g} m"
            )
    return failures


def satellite_origin_aer_failures(
    rows: list[dict[str, object]],
    *,
    azimuth_abs_deg: float,
    elevation_abs_deg: float,
    range_abs_m: float,
) -> list[str]:
    satellite = skyfield_satellite(TLE_A, "ISS")
    target = skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M)
    failures: list[str] = []
    for row in rows:
        time = skyfield_time(str(row["Time"]))
        satellite_state = satellite.at(time)
        satellite_subpoint = wgs84.geographic_position_of(satellite_state)
        satellite_ecef = np.array(satellite_state.frame_xyz(itrs).m)
        target_ecef = np.array(target.at(time).frame_xyz(itrs).m)
        azimuth, elevation, range_m = site_topocentric_from_ecef(
            satellite_ecef,
            target_ecef,
            latitude_deg=satellite_subpoint.latitude.degrees,
            longitude_deg=satellite_subpoint.longitude.degrees,
        )
        azimuth_error_deg = abs(wrapped_angle_error_deg(float(row["Azimuth"]), azimuth))
        elevation_error_deg = abs(float(row["Elevation"]) - elevation)
        range_error_m = abs(float(row["Range"]) - range_m)
        if azimuth_error_deg > azimuth_abs_deg:
            failures.append(
                f"{row['Time']} azimuth error {azimuth_error_deg:.12g} deg exceeds {azimuth_abs_deg:.12g} deg"
            )
        if elevation_error_deg > elevation_abs_deg:
            failures.append(
                f"{row['Time']} elevation error {elevation_error_deg:.12g} deg exceeds {elevation_abs_deg:.12g} deg"
            )
        if range_error_m > range_abs_m:
            failures.append(
                f"{row['Time']} range error {range_error_m:.12g} m exceeds {range_abs_m:.12g} m"
            )
    return failures


def strict_ground_aer_diagnostics(rows: list[dict[str, object]]) -> list[str]:
    satellite = skyfield_satellite(TLE_A, "ISS")
    observer = skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M)
    diagnostics = ["strict residual diagnostics:"]
    for row in rows[:4]:
        row_time = parse_time(str(row["Time"]))
        instant = skyfield_time(str(row["Time"]))
        altitude, azimuth, distance = (satellite - observer).at(instant).altaz()
        light_time_s = float(row["Range"]) / SPEED_OF_LIGHT_M_S
        shifted = ts().from_datetime(row_time - timedelta(seconds=light_time_s))
        shifted_altitude, shifted_azimuth, shifted_distance = (satellite - observer).at(shifted).altaz()
        observer_ecef = np.array(observer.at(instant).frame_xyz(itrs).m)
        satellite_ecef = np.array(satellite.at(instant).frame_xyz(itrs).m)
        manual_azimuth, manual_elevation, manual_range = site_topocentric_from_ecef(
            observer_ecef,
            satellite_ecef,
            latitude_deg=SITE_LATITUDE_DEG,
            longitude_deg=SITE_LONGITUDE_DEG,
        )
        horizon_blocked = segment_intersects_wgs84(observer_ecef, satellite_ecef)
        diagnostics.append(
            (
                f"{row['Time']} same_epoch_az={wrapped_angle_error_deg(float(row['Azimuth']), azimuth.degrees):.12g}deg "
                f"same_epoch_el={float(row['Elevation']) - altitude.degrees:.12g}deg "
                f"same_epoch_range={float(row['Range']) - distance.m:.12g}m "
                f"manual_itrs_az={wrapped_angle_error_deg(float(row['Azimuth']), manual_azimuth):.12g}deg "
                f"manual_itrs_el={float(row['Elevation']) - manual_elevation:.12g}deg "
                f"manual_itrs_range={float(row['Range']) - manual_range:.12g}m "
                f"range_over_c_s={light_time_s:.12g} "
                f"shifted_az={wrapped_angle_error_deg(float(row['Azimuth']), shifted_azimuth.degrees):.12g}deg "
                f"shifted_el={float(row['Elevation']) - shifted_altitude.degrees:.12g}deg "
                f"shifted_range={float(row['Range']) - shifted_distance.m:.12g}m "
                f"ellipsoid_blocked={horizon_blocked}"
            )
        )
    return diagnostics


def compare_range_symmetry(
    forward_rows: list[dict[str, object]],
    reverse_rows: list[dict[str, object]],
) -> None:
    failures: list[str] = []
    if len(forward_rows) != len(reverse_rows):
        raise CrossValidationError(
            f"AER sample count mismatch: forward={len(forward_rows)} reverse={len(reverse_rows)}"
        )
    for index, (forward, reverse) in enumerate(zip(forward_rows, reverse_rows, strict=True)):
        if forward["Time"] != reverse["Time"]:
            failures.append(f"sample {index} time mismatch: {forward['Time']} vs {reverse['Time']}")
        range_error_m = abs(float(forward["Range"]) - float(reverse["Range"]))
        if range_error_m > RANGE_SYMMETRY_ABS_M:
            failures.append(
                f"sample {index} range symmetry error {range_error_m:.12g} m exceeds {RANGE_SYMMETRY_ABS_M:.12g} m"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_light_time_interval_shift(
    plain_passes: list[dict[str, object]],
    delayed_passes: list[dict[str, object]],
) -> None:
    if len(plain_passes) != len(delayed_passes):
        raise CrossValidationError(
            f"light-time interval count mismatch: plain={len(plain_passes)} delayed={len(delayed_passes)}"
        )
    failures: list[str] = []
    for index, (plain_pass, delayed_pass) in enumerate(zip(plain_passes, delayed_passes, strict=True)):
        start_shift_s = seconds_since(str(delayed_pass["AccessStart"]), str(plain_pass["AccessStart"]))
        stop_shift_s = seconds_since(str(delayed_pass["AccessStop"]), str(plain_pass["AccessStop"]))
        expected_start_shift_s = -float(plain_pass["AccessBeginData"]["Range"]) / SPEED_OF_LIGHT_M_S
        expected_stop_shift_s = -float(plain_pass["AccessEndData"]["Range"]) / SPEED_OF_LIGHT_M_S
        start_error_s = abs(start_shift_s - expected_start_shift_s)
        stop_error_s = abs(stop_shift_s - expected_stop_shift_s)
        if start_error_s > LIGHT_TIME_SHIFT_ABS_S:
            failures.append(
                f"pass {index} start light-time shift error {start_error_s:.12g} s exceeds {LIGHT_TIME_SHIFT_ABS_S:.12g} s"
            )
        if stop_error_s > LIGHT_TIME_SHIFT_ABS_S:
            failures.append(
                f"pass {index} stop light-time shift error {stop_error_s:.12g} s exceeds {LIGHT_TIME_SHIFT_ABS_S:.12g} s"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def compare_light_time_aer_effect(
    plain_rows: list[dict[str, object]],
    delayed_rows: list[dict[str, object]],
) -> None:
    if len(plain_rows) != len(delayed_rows):
        raise CrossValidationError(
            f"light-time AER sample count mismatch: plain={len(plain_rows)} delayed={len(delayed_rows)}"
        )
    failures: list[str] = []
    for index, (plain, delayed) in enumerate(zip(plain_rows, delayed_rows, strict=True)):
        azimuth_delta = abs(wrapped_angle_error_deg(float(plain["Azimuth"]), float(delayed["Azimuth"])))
        elevation_delta = abs(float(plain["Elevation"]) - float(delayed["Elevation"]))
        range_delta = abs(float(plain["Range"]) - float(delayed["Range"]))
        simple_delay_s = float(plain["Range"]) / SPEED_OF_LIGHT_M_S
        if (
            azimuth_delta <= LIGHT_TIME_AER_ABS_DEG
            and elevation_delta <= LIGHT_TIME_AER_ABS_DEG
            and range_delta <= LIGHT_TIME_RANGE_ABS_M
        ):
            failures.append(
                f"sample {index} no measurable AER shift; range_over_c_s={simple_delay_s:.12g}"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def site_topocentric_from_ecef(
    observer_ecef_m: np.ndarray,
    target_ecef_m: np.ndarray,
    *,
    latitude_deg: float,
    longitude_deg: float,
) -> tuple[float, float, float]:
    latitude_rad = math.radians(latitude_deg)
    longitude_rad = math.radians(longitude_deg)
    east = np.array([-math.sin(longitude_rad), math.cos(longitude_rad), 0.0])
    north = np.array(
        [
            -math.sin(latitude_rad) * math.cos(longitude_rad),
            -math.sin(latitude_rad) * math.sin(longitude_rad),
            math.cos(latitude_rad),
        ]
    )
    up = np.array(
        [
            math.cos(latitude_rad) * math.cos(longitude_rad),
            math.cos(latitude_rad) * math.sin(longitude_rad),
            math.sin(latitude_rad),
        ]
    )
    vector_m = target_ecef_m - observer_ecef_m
    east_m = float(np.dot(vector_m, east))
    north_m = float(np.dot(vector_m, north))
    up_m = float(np.dot(vector_m, up))
    range_m = float(np.linalg.norm(vector_m))
    return (
        math.degrees(math.atan2(east_m, north_m)),
        math.degrees(math.asin(up_m / range_m)),
        range_m,
    )
