# Coverage Validation Evidence

This page records the cross-validation status of the `astrox.coverage` surface. It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/coverage/README.md`](../manual/coverage/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) are taken directly from the coverage checklists in the cross-validation scripts listed under each family.

| Family | Cross-validation script | Live snapshot sidecar |
| --- | --- | --- |
| Grid generation | [`tests/validation/cross_validation/coverage/test_grid_generation_local.py`](../../tests/validation/cross_validation/coverage/test_grid_generation_local.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| SGP4 grid membership | [`tests/validation/cross_validation/coverage/test_sgp4_grid_membership_skyfield.py`](../../tests/validation/cross_validation/coverage/test_sgp4_grid_membership_skyfield.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| Grid-point constraints/modifiers | [`tests/validation/cross_validation/coverage/test_grid_point_modifiers_invariants.py`](../../tests/validation/cross_validation/coverage/test_grid_point_modifiers_invariants.py), [`tests/validation/cross_validation/coverage/test_exclusion_grid_constraints_skyfield.py`](../../tests/validation/cross_validation/coverage/test_exclusion_grid_constraints_skyfield.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| Resource-count reports | [`tests/validation/cross_validation/coverage/test_resource_reports_invariants.py`](../../tests/validation/cross_validation/coverage/test_resource_reports_invariants.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| FOM interval invariants | [`tests/validation/cross_validation/coverage/test_fom_interval_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_interval_invariants.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| FOM at-time boundaries | [`tests/validation/cross_validation/coverage/test_fom_at_time_boundaries_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_at_time_boundaries_invariants.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| FOM edge cases | [`tests/validation/cross_validation/coverage/test_fom_edge_cases_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_edge_cases_invariants.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| FOM grid options | [`tests/validation/cross_validation/coverage/test_fom_grid_options_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_grid_options_invariants.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| FOM resource options | [`tests/validation/cross_validation/coverage/test_fom_resource_options_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_resource_options_invariants.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| FOM response shapes | [`tests/validation/cross_validation/coverage/test_fom_response_shapes_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_response_shapes_invariants.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |
| FOM response-time dynamic | [`tests/validation/cross_validation/coverage/test_fom_response_time_dynamic_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_response_time_dynamic_invariants.py) | [`tests/validation/live_snapshot/coverage/coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json) |

Helpers: [`tests/validation/cross_validation/coverage/_fom_helpers.py`](../../tests/validation/cross_validation/coverage/_fom_helpers.py).

## Grid Generation

Coverage status from [`test_grid_generation_local.py`](../../tests/validation/cross_validation/coverage/test_grid_generation_local.py):

| Branch / Field | Status |
| --- | --- |
| `LatLonBounds` grid point centers and cell boundaries | verified |
| `LatitudeBounds` grid point centers and cell boundaries | verified |
| `Global` grid point centers and cell boundaries | verified |
| `CbLatLonBounds` grid tiling bounds | partial (cells tile the requested box in representative cases) |
| `CbLatLonBounds` exact row/column count rule | unresolved |
| `ComputeCoverage` with `include_coverage_points=True` grid echo | verified against `GetGridPoints` ordering and geometry |
| `Points.GridPoints[].Position` | verified for `LatLonBounds`, `LatitudeBounds`, and `Global`; verified as cell midpoints for `CbLatLonBounds` |
| `Points.GridPoints[].GridCellBoundaryVertices` | verified for `LatLonBounds`, `LatitudeBounds`, and `Global`; verified to tile the requested box for `CbLatLonBounds` |
| `Points.GridPoints[].Weight` | partial (positive and present for area weighting; equal-weight branch verified to return `1` for all points) |
| `Points.Height` | verified to echo supplied `height_m` |
| `min/max latitude/longitude` | verified for representative positive, negative, and non-divisible bounds |
| `resolution_deg` | verified for `LatLonBounds`, `LatitudeBounds`, and `Global`; unresolved for `CbLatLonBounds` |
| `use_cell_surface_area_for_weight` | partial (`False` verified as equal weights; area formula not calibrated) |
| `height_m` | partial (response echo verified; access/coverage effect not calibrated) |
| `central_body` | partial (Earth default observed; non-Earth values not calibrated) |

Comparison path: local derivation of equally spaced cell centers and boundary vertices in radians; cross-endpoint invariant for `ComputeCoverage` point echo. No tuned physical constants are used; positions derive directly from public degree inputs. Tolerance: `ANGLE_ABS_RAD = 1.0e-12` for degree-to-radian conversion and JSON float roundoff.

Known findings:

- `LatLonBounds` subdivides each axis into `floor(span / resolution_deg) + 1` cells in the covered cases, including spans that are not evenly divisible by the resolution.
- `LatitudeBounds` uses latitude cells spanning the requested latitude band and longitude cells around the full globe, with the first longitude cell centered at 180 degrees across the seam.
- `Global` uses `round-half-up(180 / resolution_deg)` latitude intervals, collapses each pole row to one point, and uses `round-half-up(360 * cos(latitude) / resolution_deg)` longitude cells on interior rows.
- `CbLatLonBounds` tiles the requested latitude/longitude rectangle exactly in representative cases, but its count rule remains unresolved. Rejected hypotheses include direct `LatLonBounds`-style subdivision, clipped `LatitudeBounds`/`Global` parent grids, span-only `ceil`/`floor` rules, and `UseCellSurfaceAreaForWeight`-driven topology.

Live snapshot sidecar: `coverage.snap.json` records `grid_points_lat_lon` and `grid_points_cb_lat_lon`.

## Grid Membership / Compute Coverage

Coverage status from [`test_sgp4_grid_membership_skyfield.py`](../../tests/validation/cross_validation/coverage/test_sgp4_grid_membership_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| `ComputeCoverage` one SGP4 asset over a `LatLonBounds` grid | verified against independent Skyfield SGP4 plus WGS84 segment-obstruction oracle |
| `AssetAccessResults[point][asset][]` | verified as per-grid-point, per-asset line-of-sight intervals |
| `include_asset_access_results=True` | verified to expose intervals that match independently derived per-point membership |
| `minimum_assets=1` | used only to produce the coverage result; resource-count composition is calibrated separately |
| `step_s=60` | verified not to limit interval boundaries to the output cadence in this case |

Comparison path: Skyfield `EarthSatellite` state from the same TLE, Skyfield WGS84 grid-point position, and WGS84 ellipsoid segment-obstruction visibility. Constants: WGS84 ellipsoid constants from the shared access geometry oracle. Tolerance: `INTERVAL_ABS_S = 0.25` s, inherited from calibrated access SGP4 interval comparisons; observed residuals are millisecond-scale in the covered case.

Known findings:

- For the representative SGP4/`LatLonBounds` case, coverage asset intervals match geometric satellite-to-grid line of sight, not a coarse `step_s`-sampled cadence.

Live snapshot sidecar: `coverage.snap.json` covers `compute_basic` and `compute_with_grid_point_constraints`.

## Grid-Point Constraints and Modifiers

Coverage status from [`test_grid_point_modifiers_invariants.py`](../../tests/validation/cross_validation/coverage/test_grid_point_modifiers_invariants.py) and [`test_exclusion_grid_constraints_skyfield.py`](../../tests/validation/cross_validation/coverage/test_exclusion_grid_constraints_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| `Range` constraint (permissive/restrictive) | verified for permissive max/min equality and restrictive max/min pointwise subset behavior |
| `ElevationAngle` constraint (permissive/restrictive) | verified for permissive minimum equality and restrictive minimum/maximum pointwise subset behavior |
| `SunExclusionAngle` constraint | verified for permissive equality and restrictive pointwise subset behavior |
| `MoonExclusionAngle` constraint | verified callable as a non-filtering equality case in the representative mainland fixture; restrictive interval filtering verified against Skyfield in the Hawaii-area fixture |
| `AzElMask` constraint | unresolved server role behavior; smallest repro returns a clear non-ground-station server error |
| `Conic` grid-point sensor | verified for 90 degree full-hemisphere equality and 89 degree restrictive pointwise subset behavior |
| `Rectangular` grid-point sensor | verified for 90 degree full-hemisphere equality and 89 degree restrictive pointwise subset behavior |
| `SatisfactionIntervalsWithNumberOfAssets` under modifiers | verified for equality/subset relations against the unconstrained baseline |
| `AssetAccessResults` under modifiers | verified for equality/subset relations against the unconstrained baseline |

Comparison path: for invariants, local interval-set equality/subset arithmetic over the unconstrained baseline intervals plus physical monotonicity invariant for applying additional constraints or narrowing sensor field of view. For Sun/Moon exclusion, Skyfield SGP4, DE421 Sun/Moon ephemerides, apparent topocentric body altitude gate, astrometric topocentric body-separation angle, and topocentric asset-horizon visibility for zero-altitude grid points. Constants: TLE_A, `de421.bsp`, live ASTROX grid-point centers from `GetGridPoints`. Tolerances: `TIME_ABS_S = 0.002` s for invariant comparisons because ASTROX interval strings are millisecond-formatted while `Duration` carries sub-millisecond internal values; `EXCLUSION_INTERVAL_ABS_S = 0.35` s inherited from fixed-site access exclusion calibration.

Known findings:

- Permissive range/elevation/sensor branches preserve baseline intervals exactly in the covered cases.
- Restrictive but still-accessible range/elevation/sensor branches return pointwise subsets of the baseline intervals.
- For grid-point Sun/Moon exclusion constraints, the grid point is the constrained observer: the constraint is satisfied when the body is below that grid point's apparent horizon or when the asset line of sight is separated from the topocentric astrometric body vector by at least `MinimumValue` degrees.
- Over-restrictive range/elevation/sensor branches and very narrow sensors currently reduce to a worker "Index was out of range" error instead of empty zero-asset intervals.
- `AzElMask` in the coverage grid-point modifier role currently fails with a server message that the current object is not a ground-station object.

Live snapshot sidecar: `coverage.snap.json` covers `compute_with_grid_point_constraints`.

## Resource-Count and Reports

Coverage status from [`test_resource_reports_invariants.py`](../../tests/validation/cross_validation/coverage/test_resource_reports_invariants.py):

| Branch / Field | Status |
| --- | --- |
| `ComputeCoverage` one SGP4 asset with `AtLeastN=1` | verified against per-asset interval composition |
| `ComputeCoverage` duplicate SGP4 assets with `AtLeastN=2` | verified against per-asset interval composition |
| `ComputeCoverage` two SGP4 assets where only one reaches the grid with `AtLeastN=2` | verified as all-zero aggregate intervals while individual asset intervals remain present |
| `ComputeCoverage` `ExactlyN` | verified for covered cases to behave as an at-least threshold, not strict equality |
| `PercentCoverage` report | verified against weighted grid-point membership sampled at `Step` seconds |
| `CoverageByAsset` report | verified against summary statistics from the matching percent-coverage report for a one-asset case |
| `SatisfactionIntervalsWithNumberOfAssets` | verified as thresholded count trace derived from `AssetAccessResults` in covered cases |
| `AssetAccessResults` | verified to preserve per-grid-point, per-asset intervals and duplicate identical assets independently |
| `PercentCoverageDatas[].EpochSeconds` | verified to follow `Step` samples from the report epoch |
| `PercentCoverageDatas[].PercentCovered` | verified as area-weighted active grid-point coverage at the sample epoch |
| `PercentCoverageDatas[].PercentAccumulated` | verified as area-weighted ever-covered grid-point coverage up to the sample epoch |
| `CoverageByAssetDatas[].Minimum/Maximum/Average/AccumulatedCoveragePercent` | verified against `PercentCoverageDatas` summary for one asset |

Comparison path: local interval composition over per-asset intervals, weighted grid-point percentage arithmetic, and cross-report summary invariants. Constants: no physical constants; grid weights are ASTROX output fields whose area formula is calibrated separately. Tolerances: `TIME_ABS_S = 0.002` s because ASTROX interval strings are millisecond-formatted while `Duration` carries sub-millisecond internal values; `PERCENT_ABS = 1.0e-7` for floating-point weighted averages.

Known findings:

- `ComputeCoverage` keeps zero-asset intervals in `SatisfactionIntervalsWithNumberOfAssets`.
- Aggregate intervals include the actual number of simultaneously covering assets when that count meets the requested threshold; segments below the threshold are returned as zero.
- `ExactlyN` is not strict equality in the duplicate two-asset `N=1` case. It preserves `NumberOfAssets=2` intervals, matching `AtLeastN=1` and differing from a strict `ExactlyN=1` local composition.
- `PercentCoverage` uses grid-point `Weight` values, not a simple point count, for representative `LatLonBounds` grids.

Live snapshot sidecar: `coverage.snap.json` covers `percent_coverage` and `coverage_by_asset`.

## Figure of Merit Families

FOM cross-validation is organized across [`test_fom_interval_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_interval_invariants.py), [`test_fom_at_time_boundaries_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_at_time_boundaries_invariants.py), [`test_fom_edge_cases_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_edge_cases_invariants.py), [`test_fom_grid_options_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_grid_options_invariants.py), [`test_fom_resource_options_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_resource_options_invariants.py), [`test_fom_response_shapes_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_response_shapes_invariants.py), and [`test_fom_response_time_dynamic_invariants.py`](../../tests/validation/cross_validation/coverage/test_fom_response_time_dynamic_invariants.py). Shared helpers live in [`_fom_helpers.py`](../../tests/validation/cross_validation/coverage/_fom_helpers.py). Unless noted, evidence is invariant-based: local interval/gap derivation from `ComputeCoverage` `SatisfactionIntervalsWithNumberOfAssets` plus cross-route aggregation invariants.

### Simple Coverage

| Branch / Field | Status |
| --- | --- |
| `ValueByGridPoint` | verified as `1` when a grid point has any positive-asset interval, otherwise `0` |
| `ValueByGridPointAtTime` | verified as active positive-asset coverage at `time` |
| `GridStats` | verified as arithmetic min/max/average of `ValueByGridPoint` FOM values |
| `GridStatsOverTime` | verified as arithmetic min/max/average of `ValueByGridPointAtTime` at `Step` samples |

### Coverage Time

| Branch / Field | Status |
| --- | --- |
| `ValueByGridPoint` with `ComputeType=TotalTimeAbove` | verified as total positive-asset interval duration |
| `GridStats` | verified as arithmetic min/max/average of `ValueByGridPoint` values |

### Number of Assets

| Branch / Field | Status |
| --- | --- |
| `ValueByGridPoint` with `Average/Maximum/Minimum` | verified from the positive-asset count trace |
| `ValueByGridPointAtTime` | verified as the active asset count at `time` |
| `GridStats` | verified as arithmetic min/max/average of `ValueByGridPoint` values |
| `GridStatsOverTime` | verified as arithmetic min/max/average of `ValueByGridPointAtTime` at `Step` samples |

### Response Time

| Branch / Field | Status |
| --- | --- |
| `ValueByGridPoint` with `Maximum` | verified as maximum zero-asset gap duration, including boundary gaps |
| `ValueByGridPoint` with `Minimum` | verified as `0` for grid points covered at least once in the representative case |
| `GridStats` | verified as arithmetic min/max/average of `ValueByGridPoint` values |
| `ValueByGridPointAtTime` before first access | verified as remaining duration until next positive-asset interval |
| `ValueByGridPointAtTime` during access | verified as `0` |
| `ValueByGridPointAtTime` mixed covered/not-yet-covered | verified pointwise against remaining time to next access |
| `ValueByGridPointAtTime` after final access | unresolved; live ASTROX HTTP 500 is guarded in live snapshots |
| `GridStatsOverTime` for intermittent coverage | unresolved; live ASTROX HTTP 500 is guarded in live snapshots |
| `ValueByGridPointAtTime` outside analysis window | verified to reject with an API error, not a silent clamp |

### Revisit Time

| Branch / Field | Status |
| --- | --- |
| `ValueByGridPoint` with `Average/Maximum/Minimum` | verified as average/max/min zero-asset gap duration, including boundary gaps |
| `ValueByGridPointAtTime` | verified as the containing zero-asset gap duration, or `0` when covered at `time` |
| `GridStats` | verified as arithmetic min/max/average of `ValueByGridPoint` values |
| `GridStatsOverTime` | verified as arithmetic min/max/average of `ValueByGridPointAtTime` at `Step` samples |

### Shared FOM Findings

Comparison path: local interval/gap derivation from `ComputeCoverage` `SatisfactionIntervalsWithNumberOfAssets`. Constants: no physical constants; grid geometry is calibrated separately and interval semantics are calibrated against `ComputeCoverage`. Tolerances: `VALUE_ABS = 1.0e-6` for endpoint-to-endpoint floating values; `POSITION_ABS_DEG = 1.0e-10` for grid coordinate echoes.

Known findings:

- FOM grid statistics use simple arithmetic statistics over point values, not coverage grid weights. This is verified on a representative `LatLonBounds` grid where arithmetic and weighted averages differ.
- At-time FOM routes use ASTROX's internal transition precision, not the rounded millisecond strings returned in `ComputeCoverage` intervals. A rounded access-start timestamp can still evaluate as uncovered when the precise transition occurs a fraction of a millisecond later.
- `ResponseTime` differs from `RevisitTime`: when uncovered before a later access, `ResponseTime` returns remaining time until the next access, while `RevisitTime` returns the whole containing gap duration.
- For no-coverage cases, `ComputeCoverage` itself currently returns a worker "Index was out of range" error, but most FOM static, at-time, and over-time routes return meaningful edge-case values: `0` for `SimpleCoverage`, `CoverageTime`, and `NumberOfAssets`; full-window duration for `ResponseTime` and `RevisitTime`.
- For continuous-coverage cases, `ComputeCoverage` also returns a worker error in the covered fixture, but the FOM routes return `1` for `SimpleCoverage` and `NumberOfAssets`, full-window duration for `CoverageTime`, and `0` for `ResponseTime` and `RevisitTime`.
- Unsupported `ComputeType` strings are rejected by ASTROX for routes that expose `ComputeType`; they are not ignored, defaulted, or silently remapped.
- `AzElMask` is rejected consistently across representative FOM routes and `ComputeCoverage` in the coverage grid-point role.

Live snapshot sidecar: `coverage.snap.json` covers all public FOM routes, including drift guards for the `ResponseTime` dynamic HTTP 500 cases.

## Live Snapshot Coverage

The live snapshot layer proves maintained response shape, not semantic correctness. Coverage from [`tests/validation/live_snapshot/coverage/test_coverage.py`](../../tests/validation/live_snapshot/coverage/test_coverage.py) / [`coverage.snap.json`](../../tests/validation/live_snapshot/coverage/coverage.snap.json):

- Grid-point generation for `LatLonBounds` and `CbLatLonBounds`.
- Coverage compute with one SGP4 asset and output inclusion flags.
- Coverage compute with elevation and range grid-point constraints.
- `percent_coverage` and `coverage_by_asset` reports for one SGP4 asset.
- All 18 public FOM functions: `simple_coverage`, `coverage_time`, `number_of_assets`, `response_time`, and `revisit_time` across `by_grid_point`, `by_grid_point_at_time`, `grid_stats`, and `grid_stats_over_time` where exposed.
- Drift guards for `response_time.by_grid_point_at_time` and `response_time.grid_stats_over_time` HTTP 500 behavior in intermittent and no-coverage cases.
- Drift guard for site-entity coverage assets currently returning a worker error.

The snapshot tolerance is `COVERAGE_SNAPSHOT_ABS_TOL = 2.0e-3`; cross-validation owns semantic precision.

## Dropped Material

The following narratives from [`docs/sdk/coverage.md`](../../docs/sdk/coverage.md) were intentionally omitted because this page is an evidence register, not a usage guide or API reference: function signatures and argument tables for every `coverage` constructor and endpoint function; example code blocks; installation and import guidance; recommendations for which grid constructor or FOM route to use; and usage explanations for `minimum_assets`, `exactly_assets`, grid-point sensors, and grid-point constraints. Convention statements that are already covered in [`docs/manual/coverage/README.md`](../manual/coverage/README.md) are not repeated here.
