# Coverage

This page documents the curated ASTROX Python coverage interface. The intended import style is:

```python
from astrox import coverage, entities
```

Coverage functions generate grid points, compute coverage over those grid points, and call the two non-FOM coverage report routes. The SDK assembles request payloads from coverage grid values, `entities.Entity` assets, optional `entities` sensor or constraint fragments, and ordinary Python options, then returns the ASTROX JSON-like response dictionary unchanged.

## Grids

Coverage grids are reusable request fragments with `to_wire()` methods:

```python
grid = coverage.lat_lon_grid(
    min_latitude_deg=20.0,
    max_latitude_deg=35.0,
    min_longitude_deg=-120.0,
    max_longitude_deg=-100.0,
    resolution_deg=5.0,
)
```

The available constructors are:

| Constructor | ASTROX branch |
| --- | --- |
| `coverage.global_grid(...)` | `Global` |
| `coverage.latitude_grid(...)` | `LatitudeBounds` |
| `coverage.lat_lon_grid(...)` | `LatLonBounds` |
| `coverage.cb_lat_lon_grid(...)` | `CbLatLonBounds` |

Bounded constructors require their latitude or latitude/longitude bounds. Optional settings such as `central_body`, `resolution_deg`, `height_m`, and `use_cell_surface_area_for_weight` are omitted unless supplied, leaving ASTROX defaults server-owned.

Validated `lat_lon_grid(...)` cases generate cell centers and boundary vertices in radians. For the covered bounded grids, each axis is split into `floor(span / resolution_deg) + 1` cells, including spans that are not evenly divisible by the resolution. Validated `latitude_grid(...)` cases generate latitude cells across the requested latitude band and longitude cells around the full globe, with the first longitude cell centered at 180 degrees across the seam. Validated `global_grid(...)` cases use latitude rows from south pole to north pole, collapse each pole row to one point, and vary the longitude count by latitude using ASTROX's rounded `360 * cos(latitude) / resolution_deg` rule.

`use_cell_surface_area_for_weight=False` is validated to return weight `1` for every grid point in representative bounded grids. With the default area-weighted behavior, `Weight` is a positive area-like value used by the report routes, but the exact area formula is not yet documented as a public guarantee. `height_m` is validated to echo back in grid-point responses; its effect on coverage membership is not yet claimed.

`cb_lat_lon_grid(...)` is exposed because it is a real ASTROX grid branch, but it does not generate the same point set as `lat_lon_grid(...)`. Validated cases show returned cells tile the requested latitude/longitude rectangle exactly, but the exact row and column count rule remains unresolved; rejected hypotheses include direct box subdivision and clipped `LatitudeBounds` or `Global` parent grids. Treat this branch as callable but not yet recommended when exact point-count semantics matter.

## Grid Points

`coverage.grid_points(...)` calls `/Coverage/GetGridPoints` and returns the raw ASTROX response:

```python
points = coverage.grid_points(
    grid=grid,
    text="Western US grid",
)
```

For representative `lat_lon_grid(...)`, `latitude_grid(...)`, and `global_grid(...)` inputs, validation checks returned point centers and cell boundaries against local derivations. The response `Weight` field is preserved unchanged.

## Compute

`coverage.compute(...)` calls `/Coverage/ComputeCoverage`:

```python
asset = entities.entity(
    name="Relay",
    position=entities.sgp4_position(tle_lines=TLE_LINES),
)

result = coverage.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    grid=grid,
    assets=[asset],
    minimum_assets=1,
    include_asset_access_results=True,
    include_coverage_points=True,
    step_s=60.0,
)
```

`assets` accepts a sequence of `entities.Entity` values. Strings and raw dictionaries are not accepted because coverage assets lower to full ASTROX entity objects, not name references. SGP4 satellite assets are the validated path for the examples below. An empty asset list lowers deterministically, but live ASTROX currently rejects it. Fixed-site assets currently result in a server worker error in the smallest tested coverage-compute case, so do not rely on fixed-site coverage assets until that server behavior is clarified.

Use `minimum_assets=N` for the ASTROX `AtLeastN` resource-count rule, or `exactly_assets=N` for `ExactlyN`. Supplying both is rejected by the SDK because it cannot lower to one unambiguous request. In validated coverage-compute cases, ASTROX returns `SatisfactionIntervalsWithNumberOfAssets` as a per-grid-point count trace: intervals below the requested count are reported as zero, and intervals meeting the requested count preserve the actual simultaneous asset count. The returned trace includes zero-asset intervals. In a duplicate two-asset case, `exactly_assets=1` matches `minimum_assets=1` and returns intervals with `NumberOfAssets=2`, so ASTROX `ExactlyN` behaves like the same at-least threshold rather than strict equality. Do not use it when strict equality is required.

`include_asset_access_results=True` returns per-grid-point, per-asset intervals. Validated cases show those intervals compose back into `SatisfactionIntervalsWithNumberOfAssets`, and duplicate identical assets are preserved as separate asset entries. For a representative SGP4 satellite over a surface `lat_lon_grid(...)`, those per-asset intervals match an independent Skyfield SGP4 plus WGS84 Earth-obstruction line-of-sight calculation within the calibrated live validation tolerance.

`grid_point_sensor` accepts `entities.conic_sensor(...)` or `entities.rectangular_sensor(...)`. Validated full-hemisphere sensor cases preserve the unconstrained coverage intervals, and slightly narrower representative sensors return interval subsets. Very narrow representative sensors currently return a server worker error instead of empty no-access intervals.

`grid_point_constraints` accepts shared `entities.Constraint` values such as `entities.elevation_constraint(...)` and `entities.range_constraint(...)`. Validated permissive range/elevation constraints preserve the unconstrained intervals, and validated restrictive range/elevation constraints return interval subsets. Over-restrictive representative constraints currently return a server worker error instead of empty no-access intervals. `entities.az_el_mask_constraint(...)` is accepted by the SDK, but ASTROX currently rejects it in this coverage role with a server message that the current object is not a ground-station object.

`include_asset_access_results`, `include_coverage_points`, `step_s`, and `description` are optional and omitted unless supplied.

## Reports

The coverage core surface includes the two non-FOM coverage reports:

```python
percent = coverage.percent_coverage(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    grid=grid,
    assets=[asset],
    minimum_assets=1,
    step_s=60.0,
)

by_asset = coverage.coverage_by_asset(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    grid=grid,
    assets=[asset],
    minimum_assets=1,
    step_s=60.0,
)
```

Both report functions accept the same core coverage input options as `compute(...)` and return raw ASTROX dictionaries. For validated one-asset cases, `percent_coverage(...)` samples at `step_s` seconds from the report epoch. `PercentCovered` is the grid-weighted percentage of currently covered points at each sample. `PercentAccumulated` is the grid-weighted percentage of points that have been covered at least once up to that sample. For the same one-asset cases, `coverage_by_asset(...)` returns minimum, maximum, average, and accumulated percentages that match the corresponding percent-coverage samples. FOM routes and metric-specific `ComputeType` options are intentionally not part of this coverage core surface.

## Validation Scope

SDK behavior tests cover exact request lowering, optional-key omission, type rejection, public imports, and raw response pass-through. Live snapshots cover representative callability and response shape for grid generation, compute, elevation/range grid-point constraints, and the two reports.

Validation currently verifies representative `LatLonBounds`, `LatitudeBounds`, and `Global` grid point centers and cell boundaries, representative `CbLatLonBounds` box-tiling invariants, the invariant that `ComputeCoverage` with `include_coverage_points=True` echoes the same point ordering as `GetGridPoints`, representative SGP4-to-grid membership against independent Skyfield/WGS84 line-of-sight geometry, resource-count composition from per-asset intervals, ASTROX `ExactlyN` threshold behavior in a duplicate two-asset case, grid-point sensor and range/elevation constraint interval-filter invariants, weighted percent-coverage samples, and one-asset coverage-by-asset summaries. The exact `CbLatLonBounds` count rule, fixed-site assets, and `AzElMask` coverage-role support remain caveated.
