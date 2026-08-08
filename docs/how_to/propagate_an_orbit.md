# 如何传播一条轨道

本页解决一个具体任务：根据你手头的轨道描述，选择对应的传播器，拿到位置/速度采样，并读懂返回结果。

## 要做的两个选择

1. **输入决定传播器**：
   - 有开普勒根数 → 用 `propagator.j2` 或 `propagator.two_body`。
   - 有两行根数（TLE） → 用 `propagator.sgp4`。
   - 有力模型配置 → 用 `propagator.hpop`。
2. **读取采样**：所有单轨传播函数都返回 `(period_s, position)`，其中 `position.cartesian_velocity` 是 CZML 风格的扁平序列 `[t, x, y, z, vx, vy, vz, ...]`。

## 完整示例

下面的脚本用三种不同输入各传播一次，并打印第一个采样点。

```python
import astrox
from astrox import orbits, propagator

astrox.configure(base_url="http://astrox.cn:8765")


def print_first_sample(label, period_s, position):
    samples = position.cartesian_velocity
    t = samples[0]
    x, y, z, vx, vy, vz = samples[1:7]
    print(f"\n{label}")
    print(f"  轨道周期: {period_s:.3f} s")
    print(f"  参考系: {position.reference_frame}")
    print(f"  首个采样 t={t:.3f} s")
    print(f"  位置 (m): x={x:.3f}, y={y:.3f}, z={z:.3f}")
    print(f"  速度 (m/s): vx={vx:.6f}, vy={vy:.6f}, vz={vz:.6f}")


# 1. 开普勒根数 + J2 模型
orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=0.0,
    true_anomaly_deg=0.0,
)

period_s, position = propagator.j2(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T01:00:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    step_s=300.0,
)
print_first_sample("J2 传播", period_s, position)


# 2. 两行根数（TLE）+ SGP4 模型
ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

period_s, position = propagator.sgp4(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    step_s=300.0,
    tle=orbits.tle(
        line1=ISS_TLE[0],
        line2=ISS_TLE[1],
        catalog_number="25544",
    ),
)
print_first_sample("SGP4 传播", period_s, position)


# 3. 开普勒根数 + HPOP 力模型配置
config = propagator.hpop_config(
    central_body="Earth",
    gravity=propagator.hpop_two_body_gravity(),
)

period_s, position = propagator.hpop(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    coord_system="Inertial",
    config=config,
)
print_first_sample("HPOP 传播", period_s, position)
```

## 运行结果

```bash
python propagate_an_orbit.py
```

实际输出如下：

```text
J2 传播
  轨道周期: 5553.624 s
  参考系: INERTIAL
  首个采样 t=0.000 s
  位置 (m): x=6771358.863, y=0.000, z=0.000
  速度 (m/s): vx=-0.000000, vy=6746.002785, vz=3662.780662

SGP4 传播
  轨道周期: 5578.082 s
  参考系: INERTIAL
  首个采样 t=0.000 s
  位置 (m): x=6367734.323, y=-2380661.222, z=-13622.073
  速度 (m/s): vx=1669.577611, vy=4453.974636, vz=6005.161261

HPOP 传播
  轨道周期: 6000.000 s
  参考系: INERTIAL
  首个采样 t=0.000 s
  位置 (m): x=6771358.863, y=0.000, z=0.000
  速度 (m/s): vx=0.000000, vy=6746.002785, vz=3662.780662
```

## 返回值说明

`period_s` 是 ASTROX 返回的轨道周期，单位秒。`position` 是 `PropagatorPosition` 对象，包含以下字段：

- `central_body`：中心天体。
- `epoch`：位置采样的起始历元。
- `reference_frame`：参考系，如 `INERTIAL`、`FIXED`。
- `interpolation_algorithm`：插值算法。
- `interpolation_degree`：插值阶数。
- `cartesian_velocity`：CZML 风格的 `[t, x, y, z, vx, vy, vz, ...]` 采样序列。

`cartesian_velocity` 每 7 个数为一帧：时间偏移（秒）、位置 X/Y/Z（米）、速度 X/Y/Z（米/秒）。`reference_frame` 为 `INERTIAL` 时对应惯性参考系；SGP4 返回的 `INERTIAL` 对应 GCRF/GCRS 风格的惯性坐标。

## 何时选哪个传播器

| 你的输入 | 推荐传播器 | 说明 |
| --- | --- | --- |
| 开普勒根数 | `propagator.j2` | 考虑 J2 摄动，适合大多数低轨任务。 |
| 开普勒根数，纯二体 | `propagator.two_body` | 只考虑中心天体引力，计算最快。 |
| 两行根数（TLE） | `propagator.sgp4` | 直接从 TLE 传播，无需手动构造根数。 |
| 需要配置力模型 | `propagator.hpop` | 支持重力场、大气、太阳辐射压、第三方天体摄动等配置。 |

批量传播场景请使用 `propagator.multi_j2`、`propagator.multi_two_body`、`propagator.multi_sgp4`，它们把多个状态统一到同一个目标历元。

## 了解更多

- 各传播器的完整参数、单位与返回值详见 [传播器手册](../manual/propagator/README.md)。
- 轨道构造器与转换函数详见 [轨道手册](../manual/orbits/README.md)。
- 各分支的验证状态与交叉验证证据详见 [传播器验证](../validation/propagator.md)。
