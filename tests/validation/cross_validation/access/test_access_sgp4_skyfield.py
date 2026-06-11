#!/usr/bin/env python3
"""Live access cross-validation against Skyfield and response invariants."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pytest
from skyfield.api import EarthSatellite, load, wgs84

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import access, entities
from tests.validation._support import LiveConfigError, configure_astrox_from_env


START = "2024-01-01T00:00:00.000Z"
DAY_STOP = "2024-01-02T00:00:00.000Z"
TLE_A = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
TLE_B = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)
SITE_LONGITUDE_DEG = -155.468
SITE_LATITUDE_DEG = 19.821
SITE_HEIGHT_M = 4205.0
AER_CONVENTION_AZIMUTH_ABS_DEG = 5.0e-4
AER_CONVENTION_ELEVATION_ABS_DEG = 2.0e-4
AER_CONVENTION_RANGE_ABS_M = 25.0
AER_STRICT_ABS_DEG = 1.0e-4
INTERVAL_ABS_S = 5.0e-3


@dataclass(frozen=True, kw_only=True)
class Interval:
    start_s: float
    stop_s: float


class CrossValidationError(Exception):
    """Raised when ASTROX access behavior disagrees with an oracle."""


def site() -> entities.Entity:
    return entities.entity(
        name="Ground",
        position=entities.site_position(
            longitude_deg=SITE_LONGITUDE_DEG,
            latitude_deg=SITE_LATITUDE_DEG,
            height_m=SITE_HEIGHT_M,
        ),
    )


def sgp4_entity(name: str, tle_lines: tuple[str, str]) -> entities.Entity:
    return entities.entity(
        name=name,
        position=entities.sgp4_position(tle_lines=tle_lines),
    )


def direct_compute_sgp4(*, compute_aer: bool) -> dict[str, object]:
    return access.compute(
        start=START,
        stop=DAY_STOP,
        from_entity=site(),
        to_entity=sgp4_entity("ISS", TLE_A),
        step_s=600.0,
        compute_aer=compute_aer,
    )


def direct_chain_sgp4() -> dict[str, object]:
    ground = site()
    target = sgp4_entity("ISS", TLE_A)
    return access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, target],
        start_participant=ground,
        end_participant=target,
    )


def group_chain_anyof() -> dict[str, object]:
    ground = site()
    targets = entities.entity_group(
        name="Targets",
        members=[
            sgp4_entity("ISS", TLE_A),
            sgp4_entity("Hubble", TLE_B),
        ],
        to_restriction="AnyOf",
    )
    return access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, targets],
        start_participant=ground,
        end_participant=targets,
    )


def test_access_compute_aer_matches_skyfield_topocentric_convention() -> None:
    configure_astrox_from_env()
    result = direct_compute_sgp4(compute_aer=True)
    rows = list(first_aer_rows(result, max_passes=2))
    compare_aer_rows_with_skyfield(
        rows,
        azimuth_abs_deg=AER_CONVENTION_AZIMUTH_ABS_DEG,
        elevation_abs_deg=AER_CONVENTION_ELEVATION_ABS_DEG,
        range_abs_m=AER_CONVENTION_RANGE_ABS_M,
    )


@pytest.mark.calibration
@pytest.mark.xfail(
    reason="Access AER is currently a few arcseconds away from Skyfield topocentric SGP4 geometry; light-time correction does not explain the residual.",
    raises=CrossValidationError,
    strict=True,
)
def test_access_compute_aer_strict_skyfield_calibration() -> None:
    configure_astrox_from_env()
    result = direct_compute_sgp4(compute_aer=True)
    rows = list(first_aer_rows(result, max_passes=2))
    compare_aer_rows_with_skyfield(
        rows,
        azimuth_abs_deg=AER_STRICT_ABS_DEG,
        elevation_abs_deg=AER_STRICT_ABS_DEG,
        range_abs_m=AER_CONVENTION_RANGE_ABS_M,
    )


def test_direct_chain_intervals_match_direct_compute_intervals() -> None:
    configure_astrox_from_env()
    compute_result = direct_compute_sgp4(compute_aer=False)
    chain_result = direct_chain_sgp4()

    compute_intervals = intervals_from_access_passes(compute_result["Passes"])
    chain_intervals = intervals_from_chain(chain_result["CompleteChainAccess"])
    compare_intervals(compute_intervals, chain_intervals)


def test_entity_group_anyof_complete_access_is_union_of_member_strands() -> None:
    configure_astrox_from_env()
    result = group_chain_anyof()
    strand_access = result["IndividualStrandAccess"]

    member_intervals = []
    for strand_name in ("Ground>ISS", "Ground>Hubble"):
        member_intervals.extend(intervals_from_chain(strand_access[strand_name]))

    expected = merge_intervals(member_intervals)
    actual = intervals_from_chain(result["CompleteChainAccess"])
    compare_intervals(expected, actual)


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


def compare_aer_rows_with_skyfield(
    rows: list[dict[str, object]],
    *,
    azimuth_abs_deg: float,
    elevation_abs_deg: float,
    range_abs_m: float,
) -> None:
    ts = load.timescale(builtin=True)
    satellite = EarthSatellite(TLE_A[0], TLE_A[1], "ISS", ts)
    observer = wgs84.latlon(
        latitude_degrees=SITE_LATITUDE_DEG,
        longitude_degrees=SITE_LONGITUDE_DEG,
        elevation_m=SITE_HEIGHT_M,
    )
    failures: list[str] = []

    for row in rows:
        time = ts.from_datetime(datetime.fromisoformat(str(row["Time"]).replace("Z", "+00:00")))
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

    if failures:
        raise CrossValidationError("\n".join(failures))


def wrapped_angle_error_deg(actual: float, expected: float) -> float:
    return (actual - expected + 180.0) % 360.0 - 180.0


def intervals_from_access_passes(values: list[dict[str, object]]) -> list[Interval]:
    return [
        Interval(
            start_s=seconds_since_start(str(item["AccessStart"])),
            stop_s=seconds_since_start(str(item["AccessStop"])),
        )
        for item in values
    ]


def intervals_from_chain(values: list[dict[str, object]]) -> list[Interval]:
    return [
        Interval(
            start_s=seconds_since_start(str(item["Start"])),
            stop_s=seconds_since_start(str(item["Stop"])),
        )
        for item in values
    ]


def seconds_since_start(value: str) -> float:
    start = datetime.fromisoformat(START.replace("Z", "+00:00"))
    current = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (current - start).total_seconds()


def merge_intervals(values: list[Interval]) -> list[Interval]:
    if not values:
        return []
    intervals = sorted(values, key=lambda interval: interval.start_s)
    merged = [intervals[0]]
    for interval in intervals[1:]:
        last = merged[-1]
        if interval.start_s <= last.stop_s + INTERVAL_ABS_S:
            merged[-1] = Interval(
                start_s=last.start_s,
                stop_s=max(last.stop_s, interval.stop_s),
            )
        else:
            merged.append(interval)
    return merged


def compare_intervals(expected: list[Interval], actual: list[Interval]) -> None:
    failures: list[str] = []
    if len(expected) != len(actual):
        raise CrossValidationError(
            f"interval count mismatch: expected={len(expected)} actual={len(actual)}"
        )
    for index, (expected_interval, actual_interval) in enumerate(zip(expected, actual, strict=True)):
        start_error_s = abs(expected_interval.start_s - actual_interval.start_s)
        stop_error_s = abs(expected_interval.stop_s - actual_interval.stop_s)
        if start_error_s > INTERVAL_ABS_S:
            failures.append(
                f"interval {index} start error {start_error_s:.12g} s exceeds {INTERVAL_ABS_S:.12g} s"
            )
        if stop_error_s > INTERVAL_ABS_S:
            failures.append(
                f"interval {index} stop error {stop_error_s:.12g} s exceeds {INTERVAL_ABS_S:.12g} s"
            )
    if failures:
        raise CrossValidationError("\n".join(failures))


def main() -> int:
    try:
        test_access_compute_aer_matches_skyfield_topocentric_convention()
        test_direct_chain_intervals_match_direct_compute_intervals()
        test_entity_group_anyof_complete_access_is_union_of_member_strands()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=3")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
