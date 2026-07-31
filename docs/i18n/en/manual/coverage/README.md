# Coverage

`astrox.coverage` provides the public API for coverage analysis: constructing grids, generating grid points, computing coverage intervals over grids, invoking coverage reports, and figure-of-merit (FOM) routes. The recommended import pattern is:

```python
from astrox import coverage, components
```

This page is organized by concept, grid construction, coverage computation, reports, coverage metrics, and examples. All parameters use `snake_case`, and parameters with units use explicit suffixes such as `_deg`, `_m`, and `_s`. Optional parameters are not sent to ASTROX when not provided; the server retains its defaults. Coverage functions return ASTROX raw response dicts; use `astrox.raw` when you need full control over the request payload.

## Concepts

Coverage computation maps a set of assets onto a grid, determining for each grid point whether it is covered during the analysis window, how long it is covered, how many assets cover it, and so on. Assets are `components.Entity` values, usually satellites with SGP4 position sources; grids are collections of grid points on or near the surface of a central body; and coverage metrics (figure of merit, FOM) are measures that summarize coverage quality at individual grid points or over the grid as a whole.

Assets, grid-point sensors, and grid-point constraints all reuse the vocabulary from `astrox.components`; see the [components manual](../components/README.md) for details.

## Grid Construction

A grid is an input fragment for coverage requests. `astrox.coverage` provides four grid constructors:

| Constructor | ASTROX branch | Required bounds |
| --- | --- | --- |
| `coverage.global_grid(...)` | `Global` | None |
| `coverage.latitude_grid(...)` | `LatitudeBounds` | Latitude range |
| `coverage.lat_lon_grid(...)` | `LatLonBounds` | Latitude and longitude range |
| `coverage.cb_lat_lon_grid(...)` | `CbLatLonBounds` | Latitude and longitude range |

All grids accept the following optional parameters:

| Parameter | Unit | Description |
| --- | --- | --- |
| `central_body` | — | Central body name |
| `resolution_deg` | deg | Grid resolution |
| `height_m` | m | Grid point altitude |
| `use_cell_surface_area_for_weight` | — | Whether to use cell surface area as weight |

### `coverage.global_grid`

```python
coverage.global_grid(
    *,
    central_body: str | None = None,
    resolution_deg: float | None = None,
    height_m: float | None = None,
    use_cell_surface_area_for_weight: bool | None = None,
) -> GlobalGrid
```

Constructs a global grid. Optional parameters override server defaults.

```python
grid = coverage.global_grid(
    central_body="Earth",
    resolution_deg=5.0,
)
```

### `coverage.latitude_grid`

```python
coverage.latitude_grid(
    *,
    min_latitude_deg: float,
    max_latitude_deg: float,
    central_body: str | None = None,
    resolution_deg: float | None = None,
    height_m: float | None = None,
    use_cell_surface_area_for_weight: bool | None = None,
) -> LatitudeGrid
```

Constructs a latitude-bounded grid, covering the full longitude circle.

```python
grid = coverage.latitude_grid(
    min_latitude_deg=-30.0,
    max_latitude_deg=30.0,
    resolution_deg=10.0,
)
```

### `coverage.lat_lon_grid`

```python
coverage.lat_lon_grid(
    *,
    min_latitude_deg: float,
    max_latitude_deg: float,
    min_longitude_deg: float,
    max_longitude_deg: float,
    central_body: str | None = None,
    resolution_deg: float | None = None,
    height_m: float | None = None,
    use_cell_surface_area_for_weight: bool | None = None,
) -> LatLonGrid
```

Constructs a latitude/longitude-bounded grid.

```python
grid = coverage.lat_lon_grid(
    min_latitude_deg=20.0,
    max_latitude_deg=35.0,
    min_longitude_deg=-120.0,
    max_longitude_deg=-100.0,
    resolution_deg=5.0,
)
```

### `coverage.cb_lat_lon_grid`

```python
coverage.cb_lat_lon_grid(
    *,
    min_latitude_deg: float,
    max_latitude_deg: float,
    min_longitude_deg: float,
    max_longitude_deg: float,
    central_body: str | None = None,
    resolution_deg: float | None = None,
    height_m: float | None = None,
    use_cell_surface_area_for_weight: bool | None = None,
) -> CbLatLonGrid
```

Constructs a grid for the `CbLatLonBounds` branch. This branch is a callable ASTROX grid type, but the set of grid points it generates differs from `lat_lon_grid`; use it when an application needs the specific behavior of this branch.

### `coverage.grid_points`

```python
coverage.grid_points(
    *,
    grid: CoverageGrid,
    text: str | None = None,
) -> dict[str, Any]
```

Invokes `/Coverage/GetGridPoints` from a grid definition and returns the ASTROX raw response dict. In the response, `Points.GridPoints` is the list of grid points; each grid point contains `Position`, `GridCellBoundaryVertices`, and `Weight`.

```python
points = coverage.grid_points(
    grid=grid,
    text="Western US grid",
)
```

A complete runnable example is available at `examples/06_coverage/grid_points.py`.

## Coverage Computation

### `coverage.compute`

```python
coverage.compute(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[components.Entity],
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: components.EntitySensor | None = None,
    grid_point_constraints: Sequence[components.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]
```

Invokes `/Coverage/ComputeCoverage` and computes coverage for the given grid and assets. Returns the ASTROX raw response dict.

| Parameter | Description |
| --- | --- |
| `start` | Analysis start time string |
| `stop` | Analysis stop time string |
| `grid` | A `coverage` grid value |
| `assets` | A sequence of `components.Entity` |
| `minimum_assets` | At least N assets must cover for satisfaction |
| `exactly_assets` | Exactly N assets must cover for satisfaction |
| `grid_point_sensor` | Grid-point sensor, `components.conic_sensor` or `components.rectangular_sensor` |
| `grid_point_constraints` | Sequence of grid-point constraints, such as elevation angle, range, or sun/moon exclusion angle constraints |
| `include_asset_access_results` | Whether to include per-asset access intervals for each grid point in the response |
| `include_coverage_points` | Whether to echo grid points in the response |
| `step_s` | Sampling step size |
| `description` | Description string |

`minimum_assets` corresponds to ASTROX's `AtLeastN` rule, and `exactly_assets` corresponds to `ExactlyN`; the two cannot be provided together. `assets` must be a sequence of `components.Entity`; strings or raw dicts are not accepted.

```python
relay = components.entity(
    name="Relay",
    position=components.sgp4_position(
        tle_lines=(
            "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
            "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
        )
    ),
)

result = coverage.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
    include_asset_access_results=True,
    include_coverage_points=True,
    step_s=60.0,
)
```

A complete runnable example is available at `examples/06_coverage/compute.py`.

## Reports

The core coverage API includes two non-FOM reports: `percent_coverage` and `coverage_by_asset`. Both accept the same core options as `coverage.compute` and return the ASTROX raw response dict.

### `coverage.percent_coverage`

```python
coverage.percent_coverage(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[components.Entity],
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: components.EntitySensor | None = None,
    grid_point_constraints: Sequence[components.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]
```

Invokes `/Coverage/Report/PercentCoverage` and returns a time-sampled coverage percentage sequence. In the response `PercentCoverageDatas`, each sample contains `PercentCovered` (weighted percentage of currently covered grid points) and `PercentAccumulated` (weighted percentage of grid points covered at least once).

### `coverage.coverage_by_asset`

```python
coverage.coverage_by_asset(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[components.Entity],
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: components.EntitySensor | None = None,
    grid_point_constraints: Sequence[components.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]
```

Invokes `/Coverage/Report/CoverageByAsset` and returns minimum, maximum, average, and accumulated coverage percentages per asset, located in `CoverageByAssetDatas`.

```python
percent = coverage.percent_coverage(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
    step_s=60.0,
)

by_asset = coverage.coverage_by_asset(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
    step_s=60.0,
)
```

A complete runnable example is available at `examples/06_coverage/reports.py`.

## Coverage Metrics (FOM)

Coverage-metric routes are organized as sub-module namespaces under `coverage`. Each sub-module provides a set of functions that return the ASTROX raw response dict.

| Metric namespace | Per grid point | Per grid point (at specified time) | Grid statistics | Grid statistics (time series) |
| --- | --- | --- | --- | --- |
| `coverage.simple_coverage` | `by_grid_point` | `by_grid_point_at_time` | `grid_stats` | `grid_stats_over_time` |
| `coverage.coverage_time` | `by_grid_point` | — | `grid_stats` | — |
| `coverage.number_of_assets` | `by_grid_point` | `by_grid_point_at_time` | `grid_stats` | `grid_stats_over_time` |
| `coverage.response_time` | `by_grid_point` | `by_grid_point_at_time` | `grid_stats` | `grid_stats_over_time` |
| `coverage.revisit_time` | `by_grid_point` | `by_grid_point_at_time` | `grid_stats` | `grid_stats_over_time` |

These functions share the same core parameters as `coverage.compute`: `start`, `stop`, `grid`, `assets`, `minimum_assets`, `exactly_assets`, `grid_point_sensor`, `grid_point_constraints`, `include_asset_access_results`, `include_coverage_points`, `step_s`, `description`. Functions that require a specified time additionally require the `time` parameter; functions that support `ComputeType` accept an optional `compute_type` string, which the SDK passes through as-is and omits when not provided.

### `coverage.simple_coverage`

Simple coverage returns whether each grid point is covered at least once during the analysis window, or whether it is covered at the specified time. `grid_stats` returns the minimum, maximum, and average of these values.

```python
simple = coverage.simple_coverage.by_grid_point(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
)

at_time = coverage.simple_coverage.by_grid_point_at_time(
    time="2024-01-01T00:10:00.000Z",
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
)
```

### `coverage.coverage_time`

Coverage time returns the total coverage duration of each grid point within the analysis window. `compute_type` uses `"TotalTimeAbove"`. `grid_stats` returns the minimum, maximum, and average over the grid.

```python
duration = coverage.coverage_time.by_grid_point(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
    compute_type="TotalTimeAbove",
)
```

### `coverage.number_of_assets`

Number of assets returns statistics on how many assets simultaneously cover each grid point at a given instant or over the entire window. `by_grid_point` and `grid_stats` support `compute_type` such as `"Average"`, `"Maximum"`, `"Minimum"`.

```python
count = coverage.number_of_assets.by_grid_point(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
    compute_type="Average",
)

count_now = coverage.number_of_assets.by_grid_point_at_time(
    time="2024-01-01T00:10:00.000Z",
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
)
```

### `coverage.response_time`

Response time returns statistics on uncovered gap durations for each grid point. `compute_type` supports `"Maximum"` and `"Minimum"`.

```python
response = coverage.response_time.grid_stats(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
    compute_type="Maximum",
)
```

### `coverage.revisit_time`

Revisit time returns statistics on uncovered gap durations for each grid point, and is used similarly to response time. `compute_type` supports `"Average"`, `"Maximum"`, `"Minimum"`.

```python
revisit = coverage.revisit_time.grid_stats(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    grid=grid,
    assets=[relay],
    minimum_assets=1,
    compute_type="Average",
)
```

A complete runnable example is available at `examples/06_coverage/fom.py`.

## Error Handling

All coverage functions raise `astrox.exceptions.AstroxAPIError` when ASTROX returns an unsuccessful response or the network request fails. The SDK does not hide or rewrite server error messages. Use `astrox.raw.post` directly when you need the complete raw response.

## Conventions

- Optional parameters are not sent to ASTROX when not provided; the server retains its defaults.
- `assets` must be a sequence of `components.Entity`; strings or raw dicts are rejected.
- `minimum_assets` and `exactly_assets` cannot be provided together.
- `grid_point_sensor` and `grid_point_constraints` reuse sensor and constraint constructors from `components`.
- Coverage functions return ASTROX raw response dicts; the SDK does not parse or wrap them.
