#!/usr/bin/env python3
"""Coverage Sun/Moon grid-point constraint cross-validation against Skyfield."""

# Coverage:
#   Branches:
#     - ComputeCoverage grid_point_constraints SunExclusionAngle over LatLonBounds grid: verified against independent Skyfield topocentric body-separation geometry
#     - ComputeCoverage grid_point_constraints MoonExclusionAngle over LatLonBounds grid: verified against independent Skyfield topocentric body-separation geometry
#   Fields:
#     - AssetAccessResults[point][asset][] under Sun/Moon exclusion constraints: verified as per-grid-point SGP4 line-of-sight intervals intersected with the exclusion predicate
#     - SatisfactionIntervalsWithNumberOfAssets under Sun/Moon exclusion constraints: verified as the one-asset positive interval trace derived from AssetAccessResults
#     - Points.GridPoints[].Position: representative corner/center/corner live ASTROX grid-point coordinates are used; grid generation itself is calibrated in test_grid_generation_local.py
#   Parameters:
#     - SunExclusionAngle.MinimumValue: verified at 0 deg as permissive and 60 deg as restrictive
#     - MoonExclusionAngle.MinimumValue: verified at 0 deg as permissive and 25/60 deg as restrictive
#     - include_asset_access_results: verified to expose the same constrained per-point intervals as the positive satisfaction trace in this one-asset fixture
#   Comparison:
#     - External: Skyfield SGP4, DE421 Sun/Moon ephemerides, apparent topocentric body altitude gate, astrometric topocentric body-separation angle, and topocentric asset-horizon visibility for zero-altitude grid points
#     - Constants: TLE_A, de421.bsp, live ASTROX grid-point centers from GetGridPoints
#     - Tolerances: EXCLUSION_INTERVAL_ABS_S=0.35 s inherited from fixed-site access exclusion calibration after dense sampling plus bisection and ASTROX/Skyfield ephemeris/vector convention residuals
#   Findings:
#     - Coverage grid-point Sun/Moon exclusion constraints use the grid point as the constrained observer: the constraint is satisfied when the body is below that grid point's apparent horizon or when the asset line of sight is separated from the topocentric astrometric body vector by at least MinimumValue degrees.
#     - The representative Hawaii-area grid makes MoonExclusionAngle restrictive, unlike the shorter mainland fixture in test_grid_point_modifiers_invariants.py.

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

from skyfield.api import wgs84

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import coverage, components
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import (
    DAY_STOP,
    START,
    TLE_A,
    CrossValidationError,
)
from tests.validation.cross_validation.access._exclusion import (
    EXCLUSION_INTERVAL_ABS_S,
    expected_site_exclusion_intervals,
    load_exclusion_ephemeris,
    sgp4_site_elevation_intervals,
)
from tests.validation.cross_validation.access._geometry import (
    Interval,
    compare_intervals,
    seconds_since,
    skyfield_satellite,
)

STOP = DAY_STOP
REPRESENTATIVE_POINT_INDICES = (0, 4, 8)
EXCLUSION_PREDICATE_SAMPLE_STEP_S = 30.0


def hawaii_grid() -> coverage.LatLonGrid:
    return coverage.lat_lon_grid(
        min_latitude_deg=19.0,
        max_latitude_deg=21.0,
        min_longitude_deg=-156.0,
        max_longitude_deg=-154.0,
        resolution_deg=1.0,
    )


def sgp4_asset() -> components.Entity:
    return components.entity(
        name="RelayA",
        position=components.sgp4_position(tle_lines=TLE_A),
    )


def compute_with_constraint(constraint: components.Constraint) -> dict[str, Any]:
    return coverage.compute(
        start=START,
        stop=STOP,
        grid=hawaii_grid(),
        assets=[sgp4_asset()],
        minimum_assets=1,
        grid_point_constraints=[constraint],
        include_asset_access_results=True,
        step_s=300.0,
    )


def test_grid_point_exclusion_constraints_match_skyfield_body_separation() -> None:
    configure_astrox_from_env()
    cases = [
        (
            "sun0",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=0.0),
            0.0,
        ),
        (
            "sun60",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
        ),
        (
            "moon0",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=0.0),
            0.0,
        ),
        (
            "moon25",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=25.0),
            25.0,
        ),
        (
            "moon60",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
        ),
    ]
    points = coverage.grid_points(grid=hawaii_grid())["Points"]["GridPoints"]
    representative_points = [points[index] for index in REPRESENTATIVE_POINT_INDICES]
    ephemeris = load_exclusion_ephemeris()
    for label, body_name, constraint, minimum_deg in cases:
        result = compute_with_constraint(constraint)
        compare_constrained_coverage_result(
            label=label,
            body_name=body_name,
            minimum_deg=minimum_deg,
            points=representative_points,
            point_indices=REPRESENTATIVE_POINT_INDICES,
            result=result,
            ephemeris=ephemeris,
        )


def compare_constrained_coverage_result(
    *,
    label: str,
    body_name: str,
    minimum_deg: float,
    points: list[dict[str, Any]],
    point_indices: tuple[int, ...],
    result: dict[str, Any],
    ephemeris: object,
) -> None:
    asset_results = result["AssetAccessResults"]
    satisfaction = result["SatisfactionIntervalsWithNumberOfAssets"]
    if len(asset_results) <= max(point_indices):
        raise CrossValidationError(f"{label}: asset result has too few point traces")
    if len(satisfaction) <= max(point_indices):
        raise CrossValidationError(
            f"{label}: satisfaction result has too few point traces"
        )

    for point, point_index in zip(points, point_indices, strict=True):
        point_assets = asset_results[point_index]
        point_satisfaction = satisfaction[point_index]
        if len(point_assets) != 1:
            raise CrossValidationError(
                f"{label}: point {point_index} expected one asset trace, got {len(point_assets)}"
            )
        latitude_deg = math.degrees(point["Position"][0])
        longitude_deg = math.degrees(point["Position"][1])
        expected = expected_grid_point_exclusion_intervals(
            body_name=body_name,
            minimum_deg=minimum_deg,
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            ephemeris=ephemeris,
        )
        compare_labeled_intervals(
            f"{label} point {point_index} AssetAccessResults",
            expected,
            coverage_intervals(point_assets[0]),
        )
        compare_labeled_intervals(
            f"{label} point {point_index} SatisfactionIntervalsWithNumberOfAssets",
            expected,
            coverage_intervals(point_satisfaction),
        )


def expected_grid_point_exclusion_intervals(
    *,
    body_name: str,
    minimum_deg: float,
    latitude_deg: float,
    longitude_deg: float,
    ephemeris: object,
) -> list[Interval]:
    if minimum_deg == 0.0:
        site_position = wgs84.latlon(
            latitude_degrees=latitude_deg,
            longitude_degrees=longitude_deg,
            elevation_m=0.0,
        )
        return sgp4_site_elevation_intervals(
            start=START,
            stop=STOP,
            satellite=skyfield_satellite(TLE_A, "RelayA"),
            site_position=site_position,
        )
    return expected_site_exclusion_intervals(
        body_name=body_name,
        minimum_deg=minimum_deg,
        start=START,
        stop=STOP,
        tle_lines=TLE_A,
        satellite_name="RelayA",
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        height_m=0.0,
        visibility_mode="topocentric_elevation",
        predicate_sample_step_s=EXCLUSION_PREDICATE_SAMPLE_STEP_S,
        ephemeris=ephemeris,
    )


def compare_labeled_intervals(
    label: str,
    expected: list[Interval],
    actual: list[Interval],
) -> None:
    try:
        compare_intervals(expected, actual, tolerance_s=EXCLUSION_INTERVAL_ABS_S)
    except CrossValidationError as exc:
        raise CrossValidationError(f"{label}: {exc}") from exc


def coverage_intervals(values: list[dict[str, Any]]) -> list[Interval]:
    return [
        Interval(
            start_s=seconds_since(str(interval["Start"]), START),
            stop_s=seconds_since(str(interval["Stop"]), START),
        )
        for interval in values
        if interval["NumberOfAssets"] > 0
    ]


def run_all_checks() -> int:
    test_grid_point_exclusion_constraints_match_skyfield_body_separation()
    return 5


def main() -> int:
    try:
        configure_astrox_from_env()
        checked = run_all_checks()
        print(f"CROSS_VALIDATION_CHECKED={checked}")
        print("CROSS_VALIDATION_FAILED=0")
        return 0
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
