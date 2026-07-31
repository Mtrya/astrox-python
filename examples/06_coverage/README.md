# 覆盖示例

本目录包含可运行的覆盖分析示例。这些精选示例使用如下公共 SDK 风格：

```python
from astrox import coverage, components
```

用户指南请参阅 [覆盖手册](../../docs/manual/coverage/README.md)。

## 精选覆盖示例

| 示例 | 展示的公共 API |
| --- | --- |
| `grid_points.py` | `coverage.lat_lon_grid(...)` 与 `coverage.grid_points(...)` |
| `compute.py` | `coverage.compute(...)`、带 SGP4 位置源的卫星命名对象资产、资源计数选项与输出标志 |
| `reports.py` | `coverage.percent_coverage(...)` 与 `coverage.coverage_by_asset(...)` |
| `fom.py` | `coverage.simple_coverage`、`coverage.number_of_assets`、`coverage.coverage_time`、`coverage.response_time` 与 `coverage.revisit_time` 指标命名空间 |

这些示例使用带 SGP4 位置源的卫星命名对象作为覆盖资产。资源计数规则以 `minimum_assets` 演示；`exactly_assets` 也可用，二者语义与互斥关系请参阅覆盖手册。

先安装开发环境，然后从仓库根目录运行示例：

```bash
uv sync --group dev
uv run python examples/06_coverage/grid_points.py
uv run python examples/06_coverage/compute.py
uv run python examples/06_coverage/reports.py
uv run python examples/06_coverage/fom.py
```

这些示例通过包的默认客户端配置调用 ASTROX API。端到端运行需要能够连接到兼容的 ASTROX 服务器。
