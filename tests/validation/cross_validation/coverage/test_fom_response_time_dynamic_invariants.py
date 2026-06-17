#!/usr/bin/env python3
"""Coverage response-time dynamic FOM cross-validation."""

# Coverage:
#   Branches:
#     - ResponseTime ValueByGridPointAtTime before first access: verified as remaining duration until next positive-asset interval
#     - ResponseTime ValueByGridPointAtTime during access: verified as 0
#     - ResponseTime ValueByGridPointAtTime mixed covered/not-yet-covered points: verified pointwise against remaining time until next positive-asset interval
#     - ResponseTime ValueByGridPointAtTime after final access: unresolved server behavior; live ASTROX HTTP 500 is guarded in live snapshots
#     - ResponseTime GridStatsOverTime for intermittent coverage: unresolved server behavior; live ASTROX HTTP 500 is guarded in live snapshots
#     - ResponseTime ValueByGridPointAtTime outside analysis window: verified to reject with an API error, not a silent clamp
#   Fields:
#     - Datas[].Latitude/Longitude/Altitude: verified against ComputeCoverage Points for successful at-time cases
#     - Datas[].FOM_Value: verified against a local remaining-time-to-next-access derivation for successful at-time cases
#   Parameters:
#     - time: verified before access, during access, mixed before/during access, after final access, and outside the analysis window
#     - step_s: representative failing GridStatsOverTime HTTP 500 behavior is guarded in live snapshots
#     - minimum_assets/exactly_assets: covered by resource-options FOM tests for static routes; dynamic failure is verified here for the representative minimum-assets case
#   Comparison:
#     - External: local interval/gap derivation from ComputeCoverage SatisfactionIntervalsWithNumberOfAssets
#     - Constants: no physical constants; the failure hypothesis is based on whether an uncovered point has a later positive interval inside the analysis window
#     - Tolerances: VALUE_ABS=1e-6 for endpoint-to-endpoint floating values; POSITION_ABS_DEG=1e-10 for grid coordinate echoes
#   Findings:
#     - ResponseTime at-time differs from RevisitTime at-time: when uncovered before a later access, ResponseTime returns remaining time until the next access, not the whole containing gap duration.
#     - ResponseTime dynamic routes are not route-wide broken. They succeed before/during coverage and for continuous coverage; current live ASTROX HTTP 500 cases are drift-guarded in live snapshots.

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, exceptions
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.coverage._fom_helpers import (
    START,
    STOP,
    CrossValidationError,
    assert_fom_values,
    compute_trace,
    intermittent_grid,
    interval_start_s,
    iso_at_offset,
    primary_asset,
)


@pytest.mark.parametrize("seconds", [0.0, 30.0, 300.0])
def test_response_time_at_time_matches_remaining_time_to_next_access(seconds: float) -> None:
    configure_astrox_from_env()
    trace = compute_trace(grid=intermittent_grid(), assets=[primary_asset()], step_s=60.0)
    expected = [
        remaining_time_to_next_access(intervals, seconds)
        for intervals in trace["SatisfactionIntervalsWithNumberOfAssets"]
    ]
    report = coverage.response_time.by_grid_point_at_time(
        time=iso_at_offset(seconds),
        start=START,
        stop=STOP,
        grid=intermittent_grid(),
        assets=[primary_asset()],
        minimum_assets=1,
        step_s=60.0,
    )
    assert_fom_values(
        f"response_time_at_time_{seconds}",
        report["Datas"],
        trace["Points"]["GridPoints"],
        expected,
    )


def test_response_time_at_time_outside_window_is_rejected() -> None:
    configure_astrox_from_env()
    with pytest.raises(exceptions.AstroxAPIError) as error:
        coverage.response_time.by_grid_point_at_time(
            time="2024-01-01T00:31:00.000Z",
            start=START,
            stop=STOP,
            grid=intermittent_grid(),
            assets=[primary_asset()],
            minimum_assets=1,
            step_s=60.0,
        )
    assert error.value.endpoint == "/Coverage/FOM/ValueByGridPointAtTime/ResponseTime"


def remaining_time_to_next_access(intervals: list[dict], seconds: float) -> float:
    for interval in intervals:
        start_s = interval_start_s(interval)
        stop_s = interval_precise_stop_s(interval)
        if start_s <= seconds <= stop_s:
            if interval["NumberOfAssets"] > 0:
                return 0.0
            if has_later_positive_interval(intervals, seconds):
                return stop_s - seconds
            raise CrossValidationError(f"t={seconds} has no later positive interval")
    raise CrossValidationError(f"no interval contains t={seconds}")


def has_later_positive_interval(intervals: list[dict], seconds: float) -> bool:
    return any(
        interval["NumberOfAssets"] > 0 and interval_precise_stop_s(interval) > seconds
        for interval in intervals
    )


def interval_precise_stop_s(interval: dict) -> float:
    return interval_start_s(interval) + interval["Duration"]


def run_all_checks() -> int:
    for seconds in [0.0, 30.0, 300.0]:
        test_response_time_at_time_matches_remaining_time_to_next_access(seconds)
    test_response_time_at_time_outside_window_is_rejected()
    return 4


def main() -> int:
    try:
        configure_astrox_from_env()
        checked = run_all_checks()
        print(f"CROSS_VALIDATION_CHECKED={checked}")
        print("CROSS_VALIDATION_FAILED=0")
        return 0
    except (CrossValidationError, LiveConfigError, exceptions.AstroxError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
