# 访问示例

本目录包含可运行的访问计算示例。这些精选示例使用如下公共 SDK 风格：

```python
from astrox import access, components
```

用户指南请参阅 [访问手册](../../docs/manual/access/README.md) 与 [组件手册](../../docs/manual/components/README.md)，它们介绍命名对象、命名对象组、访问函数、参数、单位、返回结构及注意事项。如何一步步计算访问区间，请参考 [计算访问区间](../../docs/how_to/compute_access_intervals.md)。

## 精选访问示例

| 示例 | 展示的公共 API |
| --- | --- |
| `compute.py` | `components.entity(...)`、`components.site_position(...)`、`components.sgp4_position(...)` 与 `access.compute(...)` |
| `chain.py` | `components.entity_group(...)`、`access.connection(...)` 与 `access.chain(...)` |
| `sensor_pointing.py` | `components.vvlh_axes(...)`、`components.conic_sensor(...)`、`components.fixed_sensor_pointing(...)`、四元数传感器指向与 `access.compute(...)` |
| `custom_axes.py` | `components.fixed_axes(...)`、`components.euler_rotation(...)`、基于 VVLH 校准的传感器轴系与 `access.compute(...)` |

先安装开发环境，然后从仓库根目录运行示例：

```bash
uv sync --group dev
uv run python examples/04_access/compute.py
uv run python examples/04_access/chain.py
uv run python examples/04_access/sensor_pointing.py
uv run python examples/04_access/custom_axes.py
```

这些示例通过包的默认客户端配置调用 ASTROX API。端到端运行需要能够连接到兼容的 ASTROX 服务器。
