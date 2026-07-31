# 光照示例

本目录包含可运行的光照计算示例。这些精选光照示例采用如下公开 SDK 风格：

```python
from astrox import components, lighting
```

用户指南请参见[光照手册](../../docs/manual/lighting/README.md)，其中记录了位置源、光照函数、参数、单位与返回结构。若需要按步骤计算光照条件，可参考[如何计算光照条件](../../docs/how_to/compute_lighting_conditions.md)。

该示例打印卫星光照区间段数、地面站太阳辐射强度采样中的可见/阴影比例，以及同一地面站的太阳方位角/仰角/距离。

## 精选光照示例

| 示例 | 展示的公开 API |
| --- | --- |
| `lighting.py` | `components.site_position(...)`、`components.sgp4_position(...)`、`lighting.lighting_times(...)`、`lighting.solar_intensity(...)`、`lighting.solar_aer(...)` |

安装开发环境后，即可从仓库根目录运行示例：

```bash
uv sync --group dev
uv run python examples/03_lighting/lighting.py
```

这些示例通过包默认客户端配置调用 ASTROX API。端到端运行需要能够访问兼容的 ASTROX 服务器。
