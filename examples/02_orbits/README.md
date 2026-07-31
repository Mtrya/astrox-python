# 轨道转换与轨道向导示例

本目录包含可运行的轨道示例。这些精选轨道示例采用如下公开 SDK 风格：

```python
from astrox import orbits
```

用户指南请参见[轨道手册](../../docs/manual/orbits/README.md)，其中记录了轨道转换、GEO/Molniya/SSO 辅助函数、Walker 星座辅助函数以及 Lambert 速度增量的参数、单位、返回值与说明。若需要按步骤在不同轨道表示之间转换，可参考[如何在不同轨道表示之间转换](../../docs/how_to/convert_between_orbit_representations.md)。

## 精选轨道示例

| 示例 | 展示的公开 API |
| --- | --- |
| `conversions.py` | `orbits.keplerian_to_cartesian(...)`、`orbits.cartesian_to_keplerian(...)`、`orbits.lla_at_ascending_node(...)`、`orbits.kozai_izsak_mean_elements(...)` |
| `wizards.py` | `orbits.geo(...)`、`orbits.molniya(...)`、`orbits.sso(...)`、`orbits.walker_delta(...)`、`orbits.walker_star(...)`、`orbits.walker_custom(...)` |
| `lambert_delta_v.py` | `orbits.lambert_delta_v(...)`、`orbits.geo_ym_lambert_delta_v(...)` |
| `orbit_system.py` | `orbits.convert_czml_position(...)`、`orbits.earth_moon_libration(...)` |

安装开发环境后，即可从仓库根目录运行示例：

```bash
uv sync --group dev
uv run python examples/02_orbits/conversions.py
uv run python examples/02_orbits/wizards.py
uv run python examples/02_orbits/lambert_delta_v.py
uv run python examples/02_orbits/orbit_system.py
```

这些示例通过包默认客户端配置调用 ASTROX API。端到端运行需要能够访问兼容的 ASTROX 服务器。
