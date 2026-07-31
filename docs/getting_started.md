# 快速上手

本页帮助你在五分钟内完成第一次轨道传播：安装 SDK、配置 ASTROX 服务地址、构造一组开普勒根数、调用 J2 传播器，并查看返回的位置。

## 安装

使用 Python 3.10 或更高版本：

```bash
pip install astrox-python
```

## 编写脚本

将以下代码保存为 `first_orbit.py`：

```python
import astrox
from astrox import orbits, propagator

# 配置 ASTROX 服务地址
astrox.configure(base_url="http://astrox.cn:8765")

# 构造一组开普勒根数：400 km 近圆轨道，51.6° 倾角
orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=51.6,
    argument_of_periapsis_deg=0.0,
    raan_deg=120.0,
    true_anomaly_deg=45.0,
)

# 使用 J2 模型传播 10 分钟
period_s, position = propagator.j2(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
)

print(f"轨道周期: {period_s:.3f} s")
print(f"历元: {position.epoch}")
print(f"中心天体: {position.central_body}")
print(f"参考系: {position.reference_frame}")
print(f"位置/速度采样数: {len(position.cartesian_velocity)}")
```

## 运行

```bash
python first_orbit.py
```

你会看到类似下面的输出：

```text
轨道周期: 5553.624 s
历元: 2024-01-01T00:00:00.000Z
中心天体: Earth
参考系: INERTIAL
位置/速度采样数: 77
```

## 刚才发生了什么

`orbits.keplerian` 用六个开普勒根数描述了一个轨道：半长轴 `semi_major_axis_m`、偏心率 `eccentricity`、倾角 `inclination_deg`、近地点幅角 `argument_of_periapsis_deg`、升交点赤经 `raan_deg` 和真近点角 `true_anomaly_deg`。`propagator.j2` 把这组根数从给定历元向前传播，返回轨道周期 `period_s` 和一个包含笛卡尔位置/速度采样的 `position` 对象。

## 下一步

了解更多任务导向的用法，请参阅 [How-To 指南](how_to/README.md)。
