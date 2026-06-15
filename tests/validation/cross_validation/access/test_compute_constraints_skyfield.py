"""Constraint cross-validation for ASTROX access against Skyfield/WGS84.

Coverage:
  Branches:
    - ElevationAngle constraint on from_entity (ground site): verified
    - ElevationAngle constraint on to_entity (satellite): verified
    - ElevationAngle maximum_enabled True/False: verified
    - Range constraint on from_entity (ground site): verified
    - Range constraint on to_entity (satellite): verified
    - Range minimum_only/maximum_only/minimum_and_maximum: verified
    - AzElMask constraint on from_entity (ground site): verified for flat masks; partial for sector masks
    - AzElMask constraint on to_entity (satellite): unresolved
    - Combined elevation + range constraints: verified
    - Both participants constrained: verified for elevation minima
    - ground-to-SGP4 access role: verified for constraints on from_entity
    - SGP4-to-ground access role: verified for constraints on to_entity
    - compute_aer=True output with elevation constraint: verified
    - use_light_time_delay=True with range constraint: verified
    - Sharp boundary cases: verified
    - Contradictory/no-access cases: verified
    - Server error behavior for unsupported combinations: unresolved
  Fields:
    - Passes.AccessStart/AccessStop under elevation constraint: verified
    - Passes.AccessStart/AccessStop under range constraint: verified
    - Passes.AccessStart/AccessStop under AzElMask constraint: verified for flat masks; partial for sector masks
    - AllDatas.Azimuth/Elevation/Range with elevation constraint: verified
    - Passes with no access for contradictory thresholds: verified
  Parameters:
    - ElevationAngle.MinimumValue: verified (degrees, lower bound, inclusive within tolerance)
    - ElevationAngle.MaximumValue: verified (active only if IsMaximumEnabled True, same frame/units)
    - Range.MinimumValue: verified (kilometers, geometric range)
    - Range.MaximumValue: verified (active only if IsMaximumEnabled True, kilometers)
    - Range.MinimumValue always active when supplied: verified
    - AzElMask.AzElMaskData: verified for flat masks and north-zero/east-positive convention; partial for sector interpolation
    - AzElMask.MaxRange: partial
    - use_light_time_delay: verified (constraint evaluated on geometric range)
  Comparison:
    - External: Skyfield SGP4 topocentric geometry
    - Constants: TLE_A, WGS84 ellipsoid via Skyfield
    - Tolerances:
        INTERVAL_ABS_S=0.25 s (boundary precision after 15 s sampling + bisection)
        AER_DENSE_AZIMUTH_ABS_DEG=3.0e-3 deg
        AER_DENSE_ELEVATION_ABS_DEG=1.5e-3 deg
        AER_CONVENTION_RANGE_ABS_M=25.0 m
  Unresolved:
    - AzElMask semantics when attached to the satellite side.
    - Exact AzElMask interpolation rule for non-flat sector masks.
    - AzElMask.MaxRange semantics.
    - Server error classification for contradictory constraint combinations.

Satellite-side elevation and range constraints match the same Earth-fixed
geodetic local-frame convention already established for satellite-origin AER
rows, not a spacecraft body frame. AzElMask on the satellite side and exact
sector-mask interpolation remain unresolved and are left visible for future
slices.
"""

from __future__ import annotations

import math
import sys

import pytest

from astrox import entities
from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._aer import (
    compare_ground_origin_aer_rows_with_skyfield,
    first_aer_rows,
)
from tests.validation.cross_validation.access._cases import (
    AER_CONVENTION_AZIMUTH_ABS_DEG,
    AER_CONVENTION_ELEVATION_ABS_DEG,
    AER_CONVENTION_RANGE_ABS_M,
    AER_DENSE_AZIMUTH_ABS_DEG,
    AER_DENSE_ELEVATION_ABS_DEG,
    CrossValidationError,
    DAY_STOP,
    INTERVAL_ABS_S,
    START,
    TLE_A,
    compute_access,
    sgp4_entity,
    site,
)
from tests.validation.cross_validation.access._constraints import (
    DENSE_SAMPLE_STEP_S,
    az_el_mask_predicate,
    elevation_predicate,
    ground_origin_aer_at,
    predicate_intervals,
    range_predicate,
)
from tests.validation.cross_validation.access._geometry import (
    Interval,
    compare_intervals,
    intervals_from_access_passes,
    seconds_since,
)

CONSTRAINT_TOLERANCE_S = 0.25


def _constrained_site(
    *,
    constraints: list[object],
) -> entities.Entity:
    return entities.entity(
        name="ConstrainedGround",
        position=entities.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
        constraints=constraints,
    )


def _constrained_satellite(
    *,
    constraints: list[object],
) -> entities.Entity:
    return entities.entity(
        name="ConstrainedISS",
        position=entities.sgp4_position(tle_lines=TLE_A),
        constraints=constraints,
    )


def _expected_elevation_intervals(
    *,
    minimum_deg: float | None = None,
    maximum_deg: float | None = None,
    start: str = START,
    stop: str = DAY_STOP,
    origin: str = "ground",
) -> list[Interval]:
    return predicate_intervals(
        start=start,
        stop=stop,
        predicate=lambda offset_s: elevation_predicate(
            offset_s,
            start=start,
            origin=origin,
            minimum_deg=minimum_deg,
            maximum_deg=maximum_deg,
        ),
        sample_step_s=DENSE_SAMPLE_STEP_S,
    )


def _expected_range_intervals(
    *,
    minimum_km: float | None = None,
    maximum_km: float | None = None,
    start: str = START,
    stop: str = DAY_STOP,
    origin: str = "ground",
) -> list[Interval]:
    return predicate_intervals(
        start=start,
        stop=stop,
        predicate=lambda offset_s: range_predicate(
            offset_s,
            start=start,
            origin=origin,
            minimum_km=minimum_km,
            maximum_km=maximum_km,
        ),
        sample_step_s=DENSE_SAMPLE_STEP_S,
    )


def _expected_az_el_mask_intervals(
    *,
    az_el_mask_rad: tuple[float, ...],
    max_range_km: float | None = None,
    start: str = START,
    stop: str = DAY_STOP,
    origin: str = "ground",
) -> list[Interval]:
    return predicate_intervals(
        start=start,
        stop=stop,
        predicate=lambda offset_s: az_el_mask_predicate(
            offset_s,
            start=start,
            origin=origin,
            az_el_mask_rad=az_el_mask_rad,
            max_range_km=max_range_km,
        ),
        sample_step_s=DENSE_SAMPLE_STEP_S,
    )


def _unconstrained_ground_to_sgp4_intervals(
    *,
    start: str = START,
    stop: str = DAY_STOP,
) -> list[Interval]:
    """Return ASTROX unconstrained ground->SGP4 intervals relative to ``start``."""
    result = compute_access(site(), sgp4_entity(), start=start, stop=stop)
    return [
        Interval(
            start_s=seconds_since(str(item["AccessStart"]), start),
            stop_s=seconds_since(str(item["AccessStop"]), start),
        )
        for item in result["Passes"]
    ]


def _expected_constrained_intervals(
    predicate_intervals: list[Interval],
    *,
    start: str = START,
) -> list[Interval]:
    """Intersect predicate intervals with ASTROX unconstrained access intervals.

    Constraints are applied on top of the underlying line-of-sight access;
    comparing against the raw predicate would predict access outside the
    unconstrained window.
    """
    from tests.validation.cross_validation.access._geometry import intersect_intervals

    unconstrained = _unconstrained_ground_to_sgp4_intervals(start=start)
    return intersect_intervals(unconstrained, predicate_intervals)


def test_elevation_minimum_on_ground_matches_skyfield_topocentric_predicate() -> None:
    """Elevation minimum on the ground site is a lower bound in degrees."""
    configure_astrox_from_env()
    minimum_deg = 10.0
    ground = _constrained_site(
        constraints=[entities.elevation_constraint(minimum_deg=minimum_deg)],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_constrained_intervals(
        _expected_elevation_intervals(minimum_deg=minimum_deg)
    )
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_elevation_higher_minimum_narrows_intervals() -> None:
    """A higher minimum elevation threshold produces a subset of intervals."""
    configure_astrox_from_env()
    low_minimum = 10.0
    high_minimum = 20.0
    low_result = compute_access(
        _constrained_site(
            constraints=[entities.elevation_constraint(minimum_deg=low_minimum)],
        ),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
    )
    high_result = compute_access(
        _constrained_site(
            constraints=[entities.elevation_constraint(minimum_deg=high_minimum)],
        ),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
    )
    low_actual = intervals_from_access_passes(low_result["Passes"])
    high_actual = intervals_from_access_passes(high_result["Passes"])
    low_expected = _expected_constrained_intervals(
        _expected_elevation_intervals(minimum_deg=low_minimum)
    )
    high_expected = _expected_constrained_intervals(
        _expected_elevation_intervals(minimum_deg=high_minimum)
    )
    compare_intervals(low_expected, low_actual, tolerance_s=CONSTRAINT_TOLERANCE_S)
    compare_intervals(high_expected, high_actual, tolerance_s=CONSTRAINT_TOLERANCE_S)
    # Every high-threshold interval must be contained in a low-threshold interval.
    for high_interval in high_actual:
        if not any(
            low_interval.start_s <= high_interval.start_s
            and low_interval.stop_s >= high_interval.stop_s
            for low_interval in low_actual
        ):
            raise CrossValidationError(
                f"high-minimum interval {high_interval} is not contained in any low-minimum interval"
            )


def test_elevation_maximum_active_only_when_enabled() -> None:
    """MaximumValue is ignored unless IsMaximumEnabled is True."""
    configure_astrox_from_env()
    minimum_deg = 10.0
    maximum_deg = 70.0
    enabled_result = compute_access(
        _constrained_site(
            constraints=[
                entities.elevation_constraint(
                    minimum_deg=minimum_deg,
                    maximum_deg=maximum_deg,
                    maximum_enabled=True,
                )
            ],
        ),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
    )
    disabled_result = compute_access(
        _constrained_site(
            constraints=[
                entities.elevation_constraint(
                    minimum_deg=minimum_deg,
                    maximum_deg=maximum_deg,
                    maximum_enabled=False,
                )
            ],
        ),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
    )
    enabled_actual = intervals_from_access_passes(enabled_result["Passes"])
    disabled_actual = intervals_from_access_passes(disabled_result["Passes"])
    enabled_expected = _expected_constrained_intervals(
        _expected_elevation_intervals(
            minimum_deg=minimum_deg,
            maximum_deg=maximum_deg,
        )
    )
    disabled_expected = _expected_constrained_intervals(
        _expected_elevation_intervals(minimum_deg=minimum_deg)
    )
    compare_intervals(enabled_expected, enabled_actual, tolerance_s=CONSTRAINT_TOLERANCE_S)
    compare_intervals(disabled_expected, disabled_actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_elevation_sharp_boundary_matches_independent_crossing() -> None:
    """A threshold that splits a pass exercises boundary interpolation."""
    configure_astrox_from_env()
    # Sample the first unconstrained pass densely and choose a threshold that
    # clearly lies between the pass minimum and maximum elevation.  This forces
    # ASTROX to report a sub-interval whose boundaries can be compared against
    # an independent crossing search.
    unconstrained = compute_access(
        site(),
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        step_s=60.0,
        compute_aer=True,
    )
    first_pass = unconstrained["Passes"][0]
    pass_start = str(first_pass["AccessStart"])
    pass_stop = str(first_pass["AccessStop"])

    pass_duration_s = seconds_since(pass_stop, pass_start)
    samples: list[tuple[float, float]] = []
    for offset_s in [step * 5.0 for step in range(int(pass_duration_s / 5.0) + 1)]:
        aer = ground_origin_aer_at(offset_s, start=pass_start)
        samples.append((offset_s, aer.elevation_deg))
    if len(samples) < 2:
        raise CrossValidationError("first unconstrained pass produced fewer than 2 samples")
    min_elevation = min(item[1] for item in samples)
    max_elevation = max(item[1] for item in samples)
    if max_elevation - min_elevation < 0.1:
        raise CrossValidationError("first pass elevation range too small for a sharp boundary test")
    threshold_deg = min_elevation + 0.25 * (max_elevation - min_elevation)
    ground = _constrained_site(
        constraints=[entities.elevation_constraint(minimum_deg=threshold_deg)],
    )
    result = compute_access(
        ground,
        sgp4_entity(),
        start=pass_start,
        stop=pass_stop,
    )
    actual = [
        Interval(
            start_s=seconds_since(str(item["AccessStart"]), pass_start),
            stop_s=seconds_since(str(item["AccessStop"]), pass_start),
        )
        for item in result["Passes"]
    ]
    expected = _expected_constrained_intervals(
        _expected_elevation_intervals(
            minimum_deg=threshold_deg,
            start=pass_start,
            stop=pass_stop,
        ),
        start=pass_start,
    )
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_elevation_contradictory_minimum_returns_no_access() -> None:
    """A minimum above the maximum possible elevation yields no passes."""
    configure_astrox_from_env()
    ground = _constrained_site(
        constraints=[entities.elevation_constraint(minimum_deg=90.0)],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    if actual:
        raise CrossValidationError(
            "expected no access for 90 deg minimum elevation, got passes"
        )


def test_range_maximum_on_ground_matches_skyfield_geometric_range() -> None:
    """Range maximum on the ground site is an upper bound in kilometers."""
    configure_astrox_from_env()
    maximum_km = 2500.0
    ground = _constrained_site(
        constraints=[
            entities.range_constraint(maximum_km=maximum_km, maximum_enabled=True)
        ],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_constrained_intervals(
        _expected_range_intervals(maximum_km=maximum_km)
    )
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_range_minimum_and_maximum_on_ground_matches_skyfield() -> None:
    """Range minimum and maximum together form a closed interval in kilometers."""
    configure_astrox_from_env()
    minimum_km = 500.0
    maximum_km = 2500.0
    ground = _constrained_site(
        constraints=[
            entities.range_constraint(
                minimum_km=minimum_km,
                maximum_km=maximum_km,
                maximum_enabled=True,
            )
        ],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_constrained_intervals(
        _expected_range_intervals(
            minimum_km=minimum_km,
            maximum_km=maximum_km,
        )
    )
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_range_minimum_active_without_maximum() -> None:
    """A supplied minimum range is active even when no maximum is enabled."""
    configure_astrox_from_env()
    minimum_km = 800.0
    ground = _constrained_site(
        constraints=[entities.range_constraint(minimum_km=minimum_km)],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_constrained_intervals(
        _expected_range_intervals(minimum_km=minimum_km)
    )
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_range_maximum_disabled_is_ignored() -> None:
    """Maximum range is ignored when IsMaximumEnabled is False."""
    configure_astrox_from_env()
    maximum_km = 500.0
    constrained = _constrained_site(
        constraints=[
            entities.range_constraint(
                maximum_km=maximum_km,
                maximum_enabled=False,
            )
        ],
    )
    result = compute_access(constrained, sgp4_entity(), start=START, stop=DAY_STOP)
    constrained_intervals = intervals_from_access_passes(result["Passes"])
    unconstrained = compute_access(site(), sgp4_entity(), start=START, stop=DAY_STOP)
    unconstrained_intervals = intervals_from_access_passes(unconstrained["Passes"])
    compare_intervals(
        unconstrained_intervals,
        constrained_intervals,
        tolerance_s=CONSTRAINT_TOLERANCE_S,
    )


def test_range_contradictory_maximum_returns_no_access() -> None:
    """A maximum below the minimum possible range yields no passes."""
    configure_astrox_from_env()
    ground = _constrained_site(
        constraints=[
            entities.range_constraint(maximum_km=100.0, maximum_enabled=True)
        ],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    if actual:
        raise CrossValidationError(
            "expected no access for 100 km maximum range, got passes"
        )


def test_elevation_and_range_combined_matches_intersection() -> None:
    """Combined elevation and range constraints produce the intersection."""
    configure_astrox_from_env()
    minimum_deg = 10.0
    maximum_km = 2500.0
    ground = _constrained_site(
        constraints=[
            entities.elevation_constraint(minimum_deg=minimum_deg),
            entities.range_constraint(maximum_km=maximum_km, maximum_enabled=True),
        ],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    elevation_expected = _expected_elevation_intervals(minimum_deg=minimum_deg)
    range_expected = _expected_range_intervals(maximum_km=maximum_km)
    from tests.validation.cross_validation.access._geometry import intersect_intervals

    expected = _expected_constrained_intervals(
        intersect_intervals(elevation_expected, range_expected)
    )
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_az_el_mask_flat_matches_elevation_minimum() -> None:
    """A flat AzElMask at constant elevation behaves like an elevation minimum."""
    configure_astrox_from_env()
    elevation_deg = 10.0
    mask_rad = (
        0.0,
        math.radians(elevation_deg),
        math.radians(90.0),
        math.radians(elevation_deg),
        math.radians(180.0),
        math.radians(elevation_deg),
        math.radians(270.0),
        math.radians(elevation_deg),
    )
    ground = _constrained_site(
        constraints=[entities.az_el_mask_constraint(az_el_mask_rad=mask_rad)],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_constrained_intervals(
        _expected_az_el_mask_intervals(az_el_mask_rad=mask_rad)
    )
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_az_el_mask_sector_blocks_known_azimuth() -> None:
    """A raised elevation mask in one azimuth sector removes corresponding access."""
    configure_astrox_from_env()
    # Block the northern sector (azimuth around 0 deg) with a 90 deg mask.
    mask_rad = (
        math.radians(-45.0),
        math.radians(90.0),
        math.radians(45.0),
        math.radians(90.0),
        math.radians(45.0),
        math.radians(0.0),
        math.radians(315.0),
        math.radians(0.0),
    )
    ground = _constrained_site(
        constraints=[entities.az_el_mask_constraint(az_el_mask_rad=mask_rad)],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_constrained_intervals(
        _expected_az_el_mask_intervals(az_el_mask_rad=mask_rad)
    )
    # This case is expected to be close; small interpolation-rule differences
    # may appear and will be resolved during calibration.
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_az_el_mask_contradictory_returns_no_access() -> None:
    """A mask above all possible elevations yields no passes."""
    configure_astrox_from_env()
    mask_rad = (
        0.0,
        math.radians(90.0),
        math.radians(90.0),
        math.radians(90.0),
        math.radians(180.0),
        math.radians(90.0),
        math.radians(270.0),
        math.radians(90.0),
    )
    ground = _constrained_site(
        constraints=[entities.az_el_mask_constraint(az_el_mask_rad=mask_rad)],
    )
    result = compute_access(ground, sgp4_entity(), start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    if actual:
        raise CrossValidationError(
            "expected no access for 90 deg AzElMask, got passes"
        )


def test_elevation_constraint_returns_matching_aer_rows() -> None:
    """compute_aer=True rows satisfy the elevation constraint and match the convention."""
    configure_astrox_from_env()
    minimum_deg = 10.0
    ground = _constrained_site(
        constraints=[entities.elevation_constraint(minimum_deg=minimum_deg)],
    )
    result = compute_access(
        ground,
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        step_s=60.0,
        compute_aer=True,
    )
    rows = list(first_aer_rows(result, max_passes=1))
    compare_ground_origin_aer_rows_with_skyfield(
        rows,
        azimuth_abs_deg=AER_DENSE_AZIMUTH_ABS_DEG,
        elevation_abs_deg=AER_DENSE_ELEVATION_ABS_DEG,
        range_abs_m=AER_CONVENTION_RANGE_ABS_M,
    )
    violations = [row for row in rows if float(row["Elevation"]) < minimum_deg - 1.0e-6]
    if violations:
        raise CrossValidationError(
            f"AER rows below elevation minimum {minimum_deg}: {violations}"
        )


def test_elevation_minimum_on_satellite_matches_geodetic_local_frame() -> None:
    """Elevation constraint on the satellite uses the satellite subpoint local frame.

    The independent geodetic local-frame predicate matches ASTROX SGP4-to-ground
    access intervals, so satellite-side constraints are evaluated in the same
    Earth-fixed local east/north/up frame used for satellite-origin AER rows,
    not in a spacecraft body frame and not ignored.
    """
    configure_astrox_from_env()
    minimum_deg = 10.0
    satellite = _constrained_satellite(
        constraints=[entities.elevation_constraint(minimum_deg=minimum_deg)],
    )
    result = compute_access(site(), satellite, start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_elevation_intervals(minimum_deg=minimum_deg, origin="satellite")
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_range_maximum_on_satellite_matches_geodetic_local_frame() -> None:
    """Range constraint on the satellite uses the satellite subpoint local frame.

    Like the elevation case, the independent geodetic local-frame predicate
    matches ASTROX SGP4-to-ground intervals, confirming the same frame convention.
    """
    configure_astrox_from_env()
    maximum_km = 2500.0
    satellite = _constrained_satellite(
        constraints=[
            entities.range_constraint(maximum_km=maximum_km, maximum_enabled=True)
        ],
    )
    result = compute_access(site(), satellite, start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_range_intervals(maximum_km=maximum_km, origin="satellite")
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_both_participants_elevation_constrained_matches_intersection() -> None:
    """Elevation minima on both participants produce the intersection of predicates."""
    configure_astrox_from_env()
    minimum_deg = 10.0
    ground = _constrained_site(
        constraints=[entities.elevation_constraint(minimum_deg=minimum_deg)],
    )
    satellite = _constrained_satellite(
        constraints=[entities.elevation_constraint(minimum_deg=minimum_deg)],
    )
    result = compute_access(ground, satellite, start=START, stop=DAY_STOP)
    actual = intervals_from_access_passes(result["Passes"])
    ground_expected = _expected_elevation_intervals(minimum_deg=minimum_deg, origin="ground")
    satellite_expected = _expected_elevation_intervals(minimum_deg=minimum_deg, origin="satellite")
    from tests.validation.cross_validation.access._geometry import intersect_intervals

    expected = _expected_constrained_intervals(
        intersect_intervals(ground_expected, satellite_expected)
    )
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def test_range_maximum_with_light_time_delay_uses_geometric_range() -> None:
    """Range constraint thresholds use geometric range even with light-time delay.

    Enabling ``use_light_time_delay=True`` shifts access interval boundaries, but
    the constraint itself is still evaluated on the geometric range between the
    two participants.
    """
    configure_astrox_from_env()
    maximum_km = 2500.0
    ground = _constrained_site(
        constraints=[
            entities.range_constraint(maximum_km=maximum_km, maximum_enabled=True)
        ],
    )
    result = compute_access(
        ground,
        sgp4_entity(),
        start=START,
        stop=DAY_STOP,
        use_light_time_delay=True,
    )
    actual = intervals_from_access_passes(result["Passes"])
    expected = _expected_range_intervals(maximum_km=maximum_km)
    compare_intervals(expected, actual, tolerance_s=CONSTRAINT_TOLERANCE_S)


def main() -> int:
    cases = [
        test_elevation_minimum_on_ground_matches_skyfield_topocentric_predicate,
        test_elevation_higher_minimum_narrows_intervals,
        test_elevation_maximum_active_only_when_enabled,
        test_elevation_sharp_boundary_matches_independent_crossing,
        test_elevation_contradictory_minimum_returns_no_access,
        test_range_maximum_on_ground_matches_skyfield_geometric_range,
        test_range_minimum_and_maximum_on_ground_matches_skyfield,
        test_range_minimum_active_without_maximum,
        test_range_maximum_disabled_is_ignored,
        test_range_contradictory_maximum_returns_no_access,
        test_elevation_and_range_combined_matches_intersection,
        test_az_el_mask_flat_matches_elevation_minimum,
        test_az_el_mask_sector_blocks_known_azimuth,
        test_az_el_mask_contradictory_returns_no_access,
        test_elevation_constraint_returns_matching_aer_rows,
        test_elevation_minimum_on_satellite_matches_geodetic_local_frame,
        test_range_maximum_on_satellite_matches_geodetic_local_frame,
        test_both_participants_elevation_constrained_matches_intersection,
        test_range_maximum_with_light_time_delay_uses_geometric_range,
    ]
    checked = 0
    try:
        for case in cases:
            case()
            checked += 1
    except (CrossValidationError, LiveConfigError) as exc:
        print(
            f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    print(f"CROSS_VALIDATION_CHECKED={checked}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
