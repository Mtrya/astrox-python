# 近距离交会示例

本目录展示如何使用 `astrox.conjunction` 对 TLE 主飞行器和目标执行近距离交会筛查，以及如何把公开 `propagator.sgp4` 的采样轨迹作为 CZML 主飞行器输入。

| 示例 | 展示的公开 API |
| --- | --- |
| `close_approaches.py` | `orbits.tle(...)`、`conjunction.find_tle_close_approaches(...)`、`propagator.sgp4(...)`、`components.czml_position(...)` 与 `conjunction.find_czml_close_approaches(...)` |

从仓库根目录运行：

```bash
uv run python examples/08_conjunction/close_approaches.py
```

示例使用兼容的 ASTROX 服务地址和已验证的 TLE 输入。交会容差显式设置为宽松值，以便演示服务端筛选和结果解析；`collision_probability` 不作为示例决策依据。

完整参数说明见[交会分析手册](../../docs/manual/conjunction/README.md)，任务导向说明见[如何筛查卫星与空间目标的近距离交会](../../docs/how_to/screen_close_approaches.md)。
