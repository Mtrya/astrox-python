# astrox-python

astrox-python 是 ASTROX Web API 的 Python SDK。

## 安装

需要 Python 3.10 或更高版本。

```bash
pip install astrox-python
```

## 一分钟示例

用一组开普勒根数做 J2 传播：

```python
import astrox
from astrox import orbits, propagator

astrox.configure(base_url="http://astrox.cn:8765")

orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=51.6,
    argument_of_periapsis_deg=0.0,
    raan_deg=120.0,
    true_anomaly_deg=45.0,
)

period_s, position = propagator.j2(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
)

print(f"轨道周期: {period_s:.3f} s")
print(f"位置/速度采样数: {len(position.cartesian_velocity)}")
```

完整首次运行流程见 [快速上手](docs/getting_started.md)。

## 文档

- 完整文档导航：[docs/README.md](docs/README.md)
- 可运行示例：[examples/](examples/)
- 英文快照：[docs/i18n/en/README.md](docs/i18n/en/README.md)

## 参与开发

开发环境搭建与构建步骤见 [CONTRIBUTING.md](docs/CONTRIBUTING.md)。

## 许可

MIT 许可证，详见 [LICENSE](LICENSE)。

本项目目前处于 Alpha 阶段。
