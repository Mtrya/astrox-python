# Getting Started

This page gets you through your first orbit propagation in five minutes: install the SDK, configure the ASTROX service address, build a set of Keplerian elements, call the J2 propagator, and inspect the returned position.

## Install

Use Python 3.10 or later:

```bash
pip install astrox-python
```

## Write the script

Save the following code as `first_orbit.py`:

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

## Run

```bash
python first_orbit.py
```

You will see output similar to this:

```text
轨道周期: 5553.624 s
历元: 2024-01-01T00:00:00.000Z
中心天体: Earth
参考系: INERTIAL
位置/速度采样数: 77
```

## What just happened

`orbits.keplerian` describes an orbit with six Keplerian elements: semi-major axis `semi_major_axis_m`, eccentricity `eccentricity`, inclination `inclination_deg`, argument of periapsis `argument_of_periapsis_deg`, right ascension of the ascending node `raan_deg`, and true anomaly `true_anomaly_deg`. `propagator.j2` propagates these elements forward from the given epoch and returns the orbital period `period_s` and a `position` object containing Cartesian position/velocity samples.

## Next steps

For more task-oriented usage, see the [How-To guides](how_to/README.md).
