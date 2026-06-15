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

`cb_lat_lon_grid(...)` is exposed because it is a real ASTROX grid branch. Current cross-validation shows it does not generate the same point set as `lat_lon_grid(...)`; its exact point-generation rule is still a calibration target, so do not treat it as an alias.

## Grid Points

`coverage.grid_points(...)` calls `/Coverage/GetGridPoints` and returns the raw ASTROX response:

```python
points = coverage.grid_points(
    grid=grid,
    text="Western US grid",
)
```

For representative `lat_lon_grid(...)` inputs, cross-validation checks returned point centers and cell boundaries against a local cell-subdivision derivation. The response `Weight` field is preserved but its exact weighting/area semantics are not yet calibrated.

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

`assets` accepts a sequence of `entities.Entity` values. Strings and raw dictionaries are not accepted because coverage assets lower to full ASTROX entity objects, not name references. An empty asset list lowers deterministically, but live ASTROX currently rejects it.

Use `minimum_assets=N` for the ASTROX `AtLeastN` resource-count rule, or `exactly_assets=N` for `ExactlyN`. Supplying both is rejected by the SDK because it cannot lower to one unambiguous request. The detailed coverage semantics of those two server rules are a cross-validation target.

`grid_point_sensor` accepts `entities.conic_sensor(...)` or `entities.rectangular_sensor(...)`. `grid_point_constraints` accepts shared `entities.Constraint` values such as `entities.elevation_constraint(...)` and `entities.range_constraint(...)`. These fragments reuse SDK dataclasses, but their grid-point role is calibrated separately from entity/access constraints.

`include_asset_access_results`, `include_coverage_points`, `step_s`, and `description` are optional and omitted unless supplied.

## Reports

PR-09B covers the two non-FOM coverage reports:

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

Both report functions accept the same core coverage input options as `compute(...)` and return raw ASTROX dictionaries. FOM routes and metric-specific `ComputeType` options are intentionally not part of this coverage core surface.

## Validation Scope

SDK behavior tests cover exact request lowering, optional-key omission, type rejection, public imports, and raw response pass-through. Live snapshots cover representative callability and response shape for grid generation, compute, elevation/range grid-point constraints, and the two reports.

Cross-validation currently verifies representative `LatLonBounds` grid point centers and cell boundaries, plus the invariant that `ComputeCoverage` with `include_coverage_points=True` echoes the same point ordering as `GetGridPoints` for the covered grid. `CbLatLonBounds`, `Global`, `LatitudeBounds`, resource-count semantics, grid-point sensor behavior, grid-point constraint membership semantics, `Step`, and report aggregation remain calibration targets.
