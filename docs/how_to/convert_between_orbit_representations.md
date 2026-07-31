# 在不同轨道表示之间转换

本页解决一个具体任务：利用 `astrox.orbits` 把轨道从一种表示转换到另一种表示，当前支持开普勒根数、笛卡尔状态以及 Kozai-Izsak 平均根数之间的转换。

## 要做的两个选择

1. **源表示决定调用哪个函数**：
   - 有开普勒根数，想得到笛卡尔状态 → `orbits.keplerian_to_cartesian`。
   - 有笛卡尔状态，想得到开普勒根数 → `orbits.cartesian_to_keplerian`。
   - 有密切根数（osculating elements），想得到 Kozai-Izsak 平均根数 → `orbits.kozai_izsak_mean_elements`。
   - 如果手头的输入是 两行根数（TLE），SDK 当前没有独立的 TLE ↔ 根数/状态转换函数；直接用 `propagator.sgp4` 进行传播即可，详见 [如何传播一条轨道](propagate_an_orbit.md)。
2. **是否指定引力参数**：`keplerian_to_cartesian` 可以通过 `gravitational_parameter_m3_s2` 传入中心天体引力参数；省略时由 ASTROX 服务器使用默认值。`cartesian_to_keplerian` 目前固定使用 ASTROX 默认地球引力参数。

## 完整示例

将以下代码保存为 `convert_between_orbit_representations.py`：

```python
import astrox
from astrox import orbits

astrox.configure(base_url="http://astrox.cn:8765")

EARTH_MU_M3_S2 = 398600441500000.0

orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=15.0,
    true_anomaly_deg=45.0,
)

print("原始开普勒根数:")
print(f"  半长轴 a={orbit.semi_major_axis_m:.3f} m")
print(f"  偏心率 e={orbit.eccentricity:.6f}")
print(f"  倾角 i={orbit.inclination_deg:.3f} deg")
print(f"  升交点赤经 RAAN={orbit.raan_deg:.3f} deg")
print(f"  近地点幅角 ω={orbit.argument_of_periapsis_deg:.3f} deg")
print(f"  真近点角 ν={orbit.true_anomaly_deg:.3f} deg")

cartesian = orbits.keplerian_to_cartesian(
    orbit,
    gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
)
print("\n转换为笛卡尔状态:")
print(f"  位置 (m): x={cartesian.x_m:.3f}, y={cartesian.y_m:.3f}, z={cartesian.z_m:.3f}")
print(f"  速度 (m/s): vx={cartesian.vx_m_s:.6f}, vy={cartesian.vy_m_s:.6f}, vz={cartesian.vz_m_s:.6f}")

round_trip = orbits.cartesian_to_keplerian(cartesian)
print("\n从笛卡尔状态转换回开普勒根数:")
print(f"  半长轴 a={round_trip.semi_major_axis_m:.3f} m")
print(f"  偏心率 e={round_trip.eccentricity:.6f}")
print(f"  倾角 i={round_trip.inclination_deg:.3f} deg")
print(f"  升交点赤经 RAAN={round_trip.raan_deg:.3f} deg")
print(f"  近地点幅角 ω={round_trip.argument_of_periapsis_deg:.3f} deg")
print(f"  真近点角 ν={round_trip.true_anomaly_deg:.3f} deg")

mean = orbits.kozai_izsak_mean_elements(orbit)
print("\n密切根数 -> Kozai-Izsak 平均根数:")
print(f"  半长轴 a={mean.semi_major_axis_m:.3f} m")
print(f"  偏心率 e={mean.eccentricity:.6f}")
print(f"  倾角 i={mean.inclination_deg:.3f} deg")
print(f"  升交点赤经 RAAN={mean.raan_deg:.3f} deg")
print(f"  近地点幅角 ω={mean.argument_of_perigee_deg:.3f} deg")
print(f"  平近点角 M={mean.mean_anomaly_deg:.3f} deg")
print(f"  纬度幅角 u={mean.argument_of_latitude_deg:.3f} deg")
print(f"  近地点经度 Π={mean.longitude_of_perigee_deg:.3f} deg")
print(f"  平经度 L={mean.mean_longitude_deg:.3f} deg")
```

## 运行

```bash
python convert_between_orbit_representations.py
```

## 实际输出

```text
原始开普勒根数:
  半长轴 a=6778137.000 m
  偏心率 e=0.001000
  倾角 i=28.500 deg
  升交点赤经 RAAN=15.000 deg
  近地点幅角 ω=0.000 deg
  真近点角 ν=45.000 deg

转换为笛卡尔状态:
  位置 (m): x=3536889.576, y=5305259.458, z=2285340.036
  速度 (m/s): vx=-6472.840331, vy=3206.067962, vz=2591.048776

从笛卡尔状态转换回开普勒根数:
  半长轴 a=6778136.995 m
  偏心率 e=0.001000
  倾角 i=28.500 deg
  升交点赤经 RAAN=15.000 deg
  近地点幅角 ω=360.000 deg
  真近点角 ν=45.000 deg

密切根数 -> Kozai-Izsak 平均根数:
  半长轴 a=6778136.238 m
  偏心率 e=0.000851
  倾角 i=28.500 deg
  升交点赤经 RAAN=14.964 deg
  近地点幅角 ω=-61.373 deg
  平近点角 M=106.310 deg
  纬度幅角 u=45.030 deg
  近地点经度 Π=313.591 deg
  平经度 L=59.900 deg
```

## 刚才发生了什么

`orbits.keplerian(...)` 构造了一个 `KeplerianElements` 对象，它只包含六个经典根数：半长轴、偏心率、倾角、升交点赤经、近地点幅角、真近点角，不带历元。

`orbits.keplerian_to_cartesian` 把开普勒根数发到 ASTROX 的 `/OrbitConvert/Kepler2RV`，返回 `CartesianState`，字段为 `x_m / y_m / z_m`（米）和 `vx_m_s / vy_m_s / vz_m_s`（米/秒）。`gravitational_parameter_m3_s2` 是可选的；本示例传入了地球引力参数，省略时由服务器使用默认值。

`orbits.cartesian_to_keplerian` 把笛卡尔状态发到 `/OrbitConvert/RV2Kepler`，返回 `KeplerianElements`。该函数目前固定使用 ASTROX 默认地球引力参数。注意：当偏心率接近 0 时，近地点幅角在 0°/360° 附近可能出现跳变，这是近圆轨道的角度歧义，不是转换错误。

`orbits.kozai_izsak_mean_elements` 把密切根数发到 `/OrbitConvert/GetKozaiIzsakMeanElements`，返回 `MeanKeplerianElements`。除了六个经典根数外，它还包含纬度幅角、近地点经度和平经度等派生量。

## 选型速查

| 你的输入 | 想得到的输出 | 使用的函数 |
| --- | --- | --- |
| 开普勒根数 | 笛卡尔状态 | `orbits.keplerian_to_cartesian` |
| 笛卡尔状态 | 开普勒根数 | `orbits.cartesian_to_keplerian` |
| 密切根数 | Kozai-Izsak 平均根数 | `orbits.kozai_izsak_mean_elements` |
| 两行根数（TLE） | 位置/速度采样 | `propagator.sgp4`（见 [如何传播一条轨道](propagate_an_orbit.md)） |

## 了解更多

- 各构造器与转换函数的完整签名、单位表和返回值约定，请参阅 [轨道手册](../manual/orbits/README.md)。
- 各分支的验证状态、交叉验证证据与已知残差见 [Orbits 验证页](../validation/orbits.md)。
- 完整可运行示例见 `examples/02_orbits/conversions.py`。
