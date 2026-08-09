# 地形遮罩

`astrox.terrain` 提供站点地形遮罩（azimuth-elevation mask）查询 API：请求服务端计算站点周围 360° 方位角上的地形遮罩数据。服务端把这些数据描述为各方位角、各距离处地形遮挡的最大高度角；SDK 只负责请求构造与原始响应返回，不对这些数值做物理语义验证。推荐导入方式：

```python
from astrox import components, terrain
```

本页按概念、配置对象、完整遮罩与简化遮罩组织。两个查询函数都通过 `astrox.raw.post` 发出 HTTP POST 请求，并返回 ASTROX 原始 JSON 响应字典，不做 typed response 解析。服务端地形数据支持地球、月球、火星与月球南极（服务端文档）；遮罩输入未提供 `TerrainMaskConfig` 时，服务端使用其缺省配置（appsettings.json），该缺省路径依赖服务端部署，可能失败，推荐显式传入配置（见下文示例）。

## 概念

地形遮罩响应描述一个固定地面站点周围的方位角-仰角数据。SDK 提供两条路由，请求相同、返回结构不同：

- `terrain.azimuth_elevation_mask`：完整响应，每个方位角一条记录，附不同距离的明细条目。
- `terrain.azimuth_elevation_mask_simple`：简化响应，扁平数值数组，方位角与仰角交替排列。

站点位置使用 [components 手册](../components/README.md) 中的 `components.site_position` 构造；服务端对月球极区站点使用极区 DEM 文件（如 `Moon_LDEM_80s_20m`）进行遮罩计算。

## 遮罩配置

### `terrain.TerrainMaskConfig`

```python
terrain.TerrainMaskConfig(
    *,
    text: str | None = None,
    terrain_server_url: str | None = None,
    flag_pole: int | None = None,
    polar_dem_file_name: str | None = None,
    terrain_zoom_level: int | None = None,
    step_size_m: float | None = None,
    max_search_range_km: float | None = None,
) -> TerrainMaskConfig
```

服务端地形数据源与采样配置，是不可变（frozen）的命名数据类。`to_wire()` 返回 ASTROX `TerrainMaskConfig` 请求片段；未提供的字段不会出现在片段中。

| 字段 | wire 键 | 单位 | 说明 |
| --- | --- | --- | --- |
| `text` | `Text` | — | 配置说明 |
| `terrain_server_url` | `TerrainServerUrl` | — | 地形服务地址（stkTerrainServer 完整路径，到 layer.json 之前） |
| `flag_pole` | `FlagPole` | — | 地形投影类型：`0` 为 4326，`1` 为南极，`-1` 为北极；服务端文档标注该参数暂时无效 |
| `polar_dem_file_name` | `PolarDemFileName` | — | 极区地形文件名称；非空时优先于 `terrain_server_url`，目前仅支持月球极区 DEM，典型名称为 `Moon_LDEM_80s_20m` |
| `terrain_zoom_level` | `TerrainZoomLevel` | — | 地形最大级别，`-1` 表示自动；月球极区直接使用 tif 数据时此参数无效 |
| `step_size_m` | `StepSize` | m | 某方向计算步长，服务端缺省 30 m |
| `max_search_range_km` | `MaxSearchRange` | km | 某方向计算的最大距离，服务端缺省 15 km |

```python
config = terrain.TerrainMaskConfig(
    text="terrain example",
    terrain_server_url="",
    flag_pole=1,
    polar_dem_file_name="Moon_LDEM_80s_20m",
    terrain_zoom_level=-1,
    step_size_m=30.0,
    max_search_range_km=15.0,
)
```

## 完整遮罩

### `terrain.azimuth_elevation_mask`

```python
terrain.azimuth_elevation_mask(
    *,
    site_position: components.SitePosition,
    config: TerrainMaskConfig | None = None,
    text: str | None = None,
) -> dict[str, Any]
```

请求站点完整地形遮罩，返回原始 JSON 响应字典。

| 参数 | wire 键 | 说明 |
| --- | --- | --- |
| `site_position` | `sitePosition` | 遮罩计算点位置，`components.site_position` 构造的 `SitePosition` 值 |
| `config` | `TerrainMaskPara` | 遮罩计算参数；省略时服务端使用缺省配置 |
| `text` | `Text` | 请求说明 |

响应包含 `IsSuccess`、`Message`、`sitePosition`（请求位置回显）与 `AzElMaskData`。`AzElMaskData` 是记录数组，每条记录键为 `Azimuth`（方位角，rad）、`Elevation`（仰角数值，rad）与 `Items`（不同距离对应的明细数组）；`Items` 中每条含 `Distance`（距中心点的距离，m）与 `Elevation`（该距离对应的仰角数值，rad）。服务端文档把这些仰角数值描述为对应方位角/距离处地形遮挡的最大高度角。使用本页示例的月球极区配置时，服务端返回 361 个方位条目，方位角从 0 单调增加到 2π。

```python
site = components.site_position(
    longitude_deg=0.0,
    latitude_deg=-89.0,
    height_m=0.0,
    central_body="Moon",
)

full = terrain.azimuth_elevation_mask(site_position=site, config=config)

print(f"完整遮罩: {full['IsSuccess']}, {len(full['AzElMaskData'])} 个方位条目")
print(f"首个完整条目: {full['AzElMaskData'][0]}")
```

## 简化遮罩

### `terrain.azimuth_elevation_mask_simple`

```python
terrain.azimuth_elevation_mask_simple(
    *,
    site_position: components.SitePosition,
    config: TerrainMaskConfig | None = None,
    text: str | None = None,
) -> dict[str, Any]
```

请求站点简化地形遮罩，返回原始 JSON 响应字典。请求参数与 `azimuth_elevation_mask` 相同，发送到 `/Terrain/AzElMaskSimple` 路由。

```python
simple = terrain.azimuth_elevation_mask_simple(site_position=site, config=config)

print(f"简化遮罩: {simple['IsSuccess']}, {len(simple['AzElMaskData']) // 2} 个方位-仰角对")
```

响应中的 `AzElMaskData` 是扁平数值数组，按 `[方位角1, 仰角1, 方位角2, 仰角2, ...]` 交替排列，单位均为 rad。使用本页示例的月球极区配置时，服务端返回 722 个数值，即 361 个方位-仰角对；简化响应与完整响应携带相同的方位角-仰角数值。

## 约定说明

- 本页示例显式传入 `terrain_server_url=""`（空字符串）与 `polar_dem_file_name="Moon_LDEM_80s_20m"` 的月球极区配置。
- `Azimuth`、`Elevation` 与简化数组数值的单位为 rad；`Items[].Distance` 单位为 m。
- `TerrainMaskPara` 省略时服务端使用缺省配置（appsettings.json），该路径依赖服务端部署，可能失败。
- 验证证据见 [terrain 验证页](../../validation/terrain.md)。

完整可运行示例见 `examples/12_terrain/terrain_masks.py`。

## 错误处理

当 ASTROX 调用失败时，本模块函数抛出 `astrox.exceptions` 下对应的异常：

- `astrox.exceptions.AstroxAPIError`：ASTROX 返回不成功响应（如 `IsSuccess` 为 false）。
- `astrox.exceptions.AstroxHTTPError`：ASTROX 返回不成功的 HTTP 状态码。
- `astrox.exceptions.AstroxTimeoutError`：请求超时。
- `astrox.exceptions.AstroxConnectionError`：连接 ASTROX 失败。

SDK 不会改写服务器错误信息。需要完全控制请求载荷或处理原始响应时，请使用 `astrox.raw.post`。
