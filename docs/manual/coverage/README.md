# 覆盖

`astrox.coverage` 提供覆盖分析的公开 API：构造网格、生成网格点、计算网格上的覆盖区间、调用覆盖报告以及覆盖指标（FOM）路由。推荐按如下方式导入：

```python
from astrox import coverage, components
```

本页按概念、网格构造、覆盖计算、报告、覆盖指标和示例组织。所有参数均采用 `snake_case`，带单位的参数使用 `_deg`、`_m`、`_s` 等显式后缀。可选参数在未提供时不会被发往 ASTROX，由服务器保留默认值。覆盖函数返回 ASTROX 原始响应字典；需要完全控制请求载荷时请使用 `astrox.raw`。

## 概念

覆盖计算把一组资产（asset）映射到一个网格（grid）上，判断每个网格点（grid point）在分析时间窗口内是否被覆盖、被覆盖多久、由多少资产覆盖等。资产是 `components.Entity` 值，通常是带 SGP4 位置源的卫星；网格是中心天体表面或近地表的网格点集合；覆盖指标（figure of merit，FOM）则是在网格点或网格整体上统计覆盖质量的度量。

资产、网格点传感器、网格点约束都复用 `astrox.components` 的词汇表，详见 [components 手册](../components/README.md)。

## 网格构造

网格是覆盖请求的输入片段。`astrox.coverage` 提供四种网格构造器：

| 构造器 | ASTROX 分支 | 必填边界 |
| --- | --- | --- |
| `coverage.global_grid(...)` | `Global` | 无 |
| `coverage.latitude_grid(...)` | `LatitudeBounds` | 纬度范围 |
| `coverage.lat_lon_grid(...)` | `LatLonBounds` | 经纬度范围 |
| `coverage.cb_lat_lon_grid(...)` | `CbLatLonBounds` | 经纬度范围 |

所有网格都接受以下可选参数：

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `central_body` | — | 中心天体名称 |
| `resolution_deg` | deg | 网格分辨率 |
| `height_m` | m | 网格点海拔高度 |
| `use_cell_surface_area_for_weight` | — | 是否使用单元表面积作为权重 |

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

构造全球网格。可选参数用于覆盖服务器默认值。

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

构造纬度受限网格，经度方向覆盖整圈。

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

构造经纬度受限网格。

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

构造 `CbLatLonBounds` 分支的网格。该分支是可调用的 ASTROX 网格类型，但其生成的网格点集合与 `lat_lon_grid` 不同；当应用需要该分支的特定行为时使用它。

### `coverage.grid_points`

```python
coverage.grid_points(
    *,
    grid: CoverageGrid,
    text: str | None = None,
) -> dict[str, Any]
```

根据网格定义调用 `/Coverage/GetGridPoints`，返回 ASTROX 原始响应字典。响应中的 `Points.GridPoints` 是网格点列表，每个网格点包含 `Position`、`GridCellBoundaryVertices` 和 `Weight`。

```python
points = coverage.grid_points(
    grid=grid,
    text="Western US grid",
)
```

完整可运行示例见 `examples/06_coverage/grid_points.py`。

## 覆盖计算

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

调用 `/Coverage/ComputeCoverage`，对给定网格和资产计算覆盖。返回 ASTROX 原始响应字典。

| 参数 | 说明 |
| --- | --- |
| `start` | 分析起始时间字符串 |
| `stop` | 分析结束时间字符串 |
| `grid` | `coverage` 网格值 |
| `assets` | `components.Entity` 序列 |
| `minimum_assets` | 至少 N 个资产覆盖才算满足 |
| `exactly_assets` | 恰好 N 个资产覆盖才算满足 |
| `grid_point_sensor` | 网格点传感器，`components.conic_sensor` 或 `components.rectangular_sensor` |
| `grid_point_constraints` | 网格点约束序列，如仰角、距离、太阳/月球排除角约束 |
| `include_asset_access_results` | 是否在响应中包含每个资产对每个网格点的访问区间 |
| `include_coverage_points` | 是否在响应中回显网格点 |
| `step_s` | 采样步长 |
| `description` | 描述字符串 |

`minimum_assets` 对应 ASTROX 的 `AtLeastN` 规则，`exactly_assets` 对应 `ExactlyN` 规则；二者不能同时提供。`assets` 必须是 `components.Entity` 序列，字符串或原始字典不会被接受。

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

完整可运行示例见 `examples/06_coverage/compute.py`。

## 报告

覆盖核心 API 包含两个非 FOM 报告：`percent_coverage` 与 `coverage_by_asset`。二者接受与 `coverage.compute` 相同的核心选项，返回 ASTROX 原始响应字典。

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

调用 `/Coverage/Report/PercentCoverage`，返回按时间采样的覆盖百分比序列。响应 `PercentCoverageDatas` 中每个样本包含 `PercentCovered`（当前被覆盖网格点的加权百分比）和 `PercentAccumulated`（至少被覆盖过一次的网格点的加权百分比）。

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

调用 `/Coverage/Report/CoverageByAsset`，返回每个资产的最小、最大、平均和累计覆盖百分比，位于 `CoverageByAssetDatas` 中。

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

完整可运行示例见 `examples/06_coverage/reports.py`。

## 覆盖指标（FOM）

覆盖指标路由按指标组织为 `coverage` 下的子模块命名空间。每个子模块提供一组函数，返回 ASTROX 原始响应字典。

| 指标命名空间 | 每网格点 | 每网格点（指定时刻） | 网格统计 | 网格统计（时序） |
| --- | --- | --- | --- | --- |
| `coverage.simple_coverage` | `by_grid_point` | `by_grid_point_at_time` | `grid_stats` | `grid_stats_over_time` |
| `coverage.coverage_time` | `by_grid_point` | — | `grid_stats` | — |
| `coverage.number_of_assets` | `by_grid_point` | `by_grid_point_at_time` | `grid_stats` | `grid_stats_over_time` |
| `coverage.response_time` | `by_grid_point` | `by_grid_point_at_time` | `grid_stats` | `grid_stats_over_time` |
| `coverage.revisit_time` | `by_grid_point` | `by_grid_point_at_time` | `grid_stats` | `grid_stats_over_time` |

这些函数共享与 `coverage.compute` 相同的核心参数：`start`、`stop`、`grid`、`assets`、`minimum_assets`、`exactly_assets`、`grid_point_sensor`、`grid_point_constraints`、`include_asset_access_results`、`include_coverage_points`、`step_s`、`description`。需要指定时刻的函数额外要求 `time` 参数；支持 `ComputeType` 的函数接受可选 `compute_type` 字符串，SDK 原样发送，不提供时省略。

### `coverage.simple_coverage`

简单覆盖返回每个网格点在分析窗口内是否被覆盖至少一次，或指定时刻是否被覆盖。`grid_stats` 返回这些值的最小值、最大值和平均值。

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

覆盖时间返回每个网格点在分析窗口内的覆盖总时长。`compute_type` 使用 `"TotalTimeAbove"`。`grid_stats` 返回网格上的最小值、最大值和平均值。

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

资产数量返回每个网格点在同一时刻或整个窗口内同时覆盖它的资产数量统计。`by_grid_point` 与 `grid_stats` 支持 `compute_type` 如 `"Average"`、`"Maximum"`、`"Minimum"`。

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

响应时间返回每个网格点未被覆盖的间隙时长统计。`compute_type` 支持 `"Maximum"` 和 `"Minimum"`。

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

重访时间返回每个网格点未被覆盖的间隙时长统计，用法与响应时间类似。`compute_type` 支持 `"Average"`、`"Maximum"`、`"Minimum"`。

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

完整可运行示例见 `examples/06_coverage/fom.py`。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，所有覆盖函数都会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会隐藏或改写服务器错误信息。需要完整原始响应时，请直接使用 `astrox.raw.post`。

## 约定说明

- 可选参数在未提供时不会被发往 ASTROX，由服务器保留默认值。
- `assets` 必须是 `components.Entity` 序列，字符串或原始字典会被拒绝。
- `minimum_assets` 与 `exactly_assets` 不能同时提供。
- `grid_point_sensor` 与 `grid_point_constraints` 复用 `components` 中的传感器和约束构造器。
- 覆盖函数返回 ASTROX 原始响应字典，SDK 不做解析或封装。
