# 地形遮罩示例

本目录展示 `astrox.terrain` 的完整和简化方位角-仰角遮罩查询，以及显式的 `TerrainMaskConfig`。

| 示例 | 展示的公开 API |
| --- | --- |
| `terrain_masks.py` | `components.site_position(...)`、`terrain.TerrainMaskConfig(...)`、`terrain.azimuth_elevation_mask(...)` 与 `terrain.azimuth_elevation_mask_simple(...)` |

从仓库根目录运行：

```bash
uv run python examples/12_terrain/terrain_masks.py
```

示例使用 Moon 极区 DEM 配置，因为服务端默认地形元数据在当前验证环境中可能不可用。完整遮罩返回带 `Items` 的对象数组；简化遮罩返回交替排列的方位角和仰角数值。两种返回值的结构关系已验证，但地形数据的物理含义和覆盖范围仍由服务端地形源负责。

完整参数说明见[地形遮罩手册](../../docs/manual/terrain/README.md)，结构与跨路由不变量证据见[地形验证文档](../../docs/validation/terrain.md)。
