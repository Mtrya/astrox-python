# 两行根数与碎片分析

`astrox.cat` 提供两行根数（TLE）生成、轨道寿命估算与空间碎片解体模拟的公开 API。推荐导入方式：

```python
from astrox import cat, orbits
```

本页按功能族组织：先用 `cat.generate_tle` 从开普勒根数生成 TLE，再用 `cat.estimate_tle_lifetime` 估算轨道寿命，或通过三个解体模拟函数生成碎片。所有 TLE 输入输出都使用 [orbits 手册](../orbits/README.md) 中的 `orbits.Tle` 值对象。

## 两行根数生成

### `cat.generate_tle`

```python
cat.generate_tle(
    *,
    name: str,
    catalog_number: str,
    epoch: str,
    bstar: float,
    semi_major_axis_km: float,
    eccentricity: float,
    inclination_deg: float,
    argument_of_perigee_deg: float,
    raan_deg: float,
    true_anomaly_deg: float,
    is_mean_elements: bool | None = None,
) -> Tle
```

由 TEME 参考系下的开普勒根数生成两行根数，返回 `orbits.Tle` 实例。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `name` | — | 空间目标名称 |
| `catalog_number` | — | 编目号（NORAD 编号） |
| `epoch` | — | 轨道历元字符串（UTC） |
| `bstar` | — | B* 大气阻力系数 |
| `semi_major_axis_km` | km | 半长轴 |
| `eccentricity` | — | 偏心率 |
| `inclination_deg` | deg | 倾角（TEME） |
| `argument_of_perigee_deg` | deg | 近地点幅角（TEME） |
| `raan_deg` | deg | 升交点赤经（TEME） |
| `true_anomaly_deg` | deg | 真近点角（TEME） |
| `is_mean_elements` | — | 输入是否为平均根数；`True` 为平均根数，`False` 或省略为瞬时根数 |

```python
tle = cat.generate_tle(
    name="probe",
    catalog_number="25545",
    epoch="2024-01-01T00:00:00.000Z",
    bstar=0.0001,
    semi_major_axis_km=6778.0,
    eccentricity=0.0005,
    inclination_deg=51.6,
    argument_of_perigee_deg=60.0,
    raan_deg=340.0,
    true_anomaly_deg=0.0,
)

print(tle.line1)
print(tle.line2)
```

`is_mean_elements=True` 时，服务端会把输入的真近点角转换为平近点角写入 TLE：中高偏心率（e=0.01、0.05）下，输出近地点幅角与平近点角之和保持输入对应的平经度（mean longitude，0.1° 容差）。近圆（e≈0.0001882）时服务端会重新分配近地点幅角与平近点角，并保留公里级状态残差，该分支仍是 strict xfail/unresolved，完整的真近点角→平近点角转换尚不能宣布已完全验证。

生成结果可直接用于 `propagator.sgp4`、`conjunction` 与下面的寿命估算、解体模拟函数。

## 轨道寿命估算

### `cat.estimate_tle_lifetime`

```python
cat.estimate_tle_lifetime(
    *,
    epoch: str,
    tle: Tle,
    sm: float | None = None,
    mass: float | None = None,
) -> TleLifetimeResult
```

估算给定 TLE 的轨道寿命。`sm` 与 `mass` 是服务端寿命模型的参数，未提供时由服务器保留默认值。

| 参数 | 说明 |
| --- | --- |
| `epoch` | 寿命计算历元字符串 |
| `tle` | 目标卫星的 `orbits.Tle` 实例 |
| `sm` | 服务端寿命模型参数（可选） |
| `mass` | 卫星质量（可选） |

`TleLifetimeResult` 是解析后的冻结数据类：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `is_success` | `bool` | 是否成功 |
| `message` | `str` | 服务器消息 |
| `life_years` | `float` | 轨道寿命，单位年 |

```python
result = cat.estimate_tle_lifetime(
    epoch="2024-01-01T00:00:00.000Z",
    tle=tle,
)

print(result.life_years)
```

`life_years` 不能作为绝对物理寿命预测。本轮已验证：输出由 `sm`/`mass` 的比值决定——固定 `sm` 或固定 `mass` 的 sweep 与等比值 case（如 `(0.1, 100)` 与 `(1, 1000)`）逐值一致；低比值（长寿命情形）返回 25 年上限；改变 `bstar` 不影响观测结果；解体模拟的碎片寿命与 `estimate_tle_lifetime` 在相同面积质量比下逐值一致。绝对寿命数值仍未验证。

## 碎片解体模拟

三个函数模拟母卫星解体产生碎片，都返回 `DebrisBreakupResult`。它们模拟母星解体事件本身，返回碎片的 TLE 与轨道参数；碎片轨道周期与近地点/远地点高度已与独立 SGP4 状态的轨道不变量对照一致，但碎片解体模型本身的科学性不在已验证范围内。

### `cat.simulate_debris_breakup_simple`

```python
cat.simulate_debris_breakup_simple(
    *,
    mother_tle: Tle,
    epoch: str,
    count: int | None = None,
    ssc_prefix: str | None = None,
    delta_v_m_s: float | None = None,
    area_to_mass_ratio_m2_kg: float | None = None,
    min_azimuth_deg: float | None = None,
    max_azimuth_deg: float | None = None,
    min_elevation_deg: float | None = None,
    max_elevation_deg: float | None = None,
    compute_lifetime: bool | None = None,
) -> DebrisBreakupResult
```

所有碎片使用相同的相对速度与面积质量比，方位角/仰角在给定范围内均匀生成。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `mother_tle` | — | 母卫星的 `orbits.Tle` 实例 |
| `epoch` | — | 解体时刻字符串（UTC） |
| `count` | — | 碎片数量，应小于 1000 |
| `ssc_prefix` | — | 碎片编目号前缀，如 `"AF"` |
| `delta_v_m_s` | m/s | 碎片相对母星的速度大小 |
| `area_to_mass_ratio_m2_kg` | m²/kg | 碎片面积质量比 |
| `min_azimuth_deg` | deg | 方位角最小值 |
| `max_azimuth_deg` | deg | 方位角最大值 |
| `min_elevation_deg` | deg | 仰角最小值 |
| `max_elevation_deg` | deg | 仰角最大值 |
| `compute_lifetime` | — | 是否计算碎片轨道寿命 |

方位角与仰角范围按服务端定义在 TEME 参考系下的 VVLH 轴系中。

```python
result = cat.simulate_debris_breakup_simple(
    mother_tle=tle,
    epoch="2024-01-01T00:00:00.000Z",
    count=50,
    ssc_prefix="AF",
    delta_v_m_s=400.0,
    area_to_mass_ratio_m2_kg=0.002,
)

print(len(result.debris_tles), result.periods_min[:3])
```

### `cat.simulate_debris_breakup`

```python
cat.simulate_debris_breakup(
    *,
    mother_tle: Tle,
    epoch: str,
    impulses: Sequence[DebrisImpulse],
    ssc_prefix: str | None = None,
    area_to_mass_ratio_m2_kg: float | None = None,
    compute_lifetime: bool | None = None,
) -> DebrisBreakupResult
```

逐条给出每块碎片的解体参数。`impulses` 是 `DebrisImpulse` 序列，每条对应一块碎片：

| 字段 | 单位 | 说明 |
| --- | --- | --- |
| `azimuth_deg` | deg | 方位角 |
| `elevation_deg` | deg | 仰角 |
| `delta_v_m_s` | m/s | 相对母星的速度大小 |
| `area_to_mass_ratio_m2_kg` | m²/kg | 面积质量比 |

```python
impulses = [
    cat.DebrisImpulse(
        azimuth_deg=90.0,
        elevation_deg=1.0,
        delta_v_m_s=400.0,
        area_to_mass_ratio_m2_kg=0.002,
    ),
    cat.DebrisImpulse(
        azimuth_deg=120.0,
        elevation_deg=0.0,
        delta_v_m_s=300.0,
        area_to_mass_ratio_m2_kg=0.01,
    ),
]

result = cat.simulate_debris_breakup(
    mother_tle=tle,
    epoch="2024-01-01T00:00:00.000Z",
    impulses=impulses,
    ssc_prefix="AF",
)
```

显式解体的 `AzElVel` 约定已经过验证：返回结果中的 `impulses` 行原样回显输入；`delta_v_m_s` 的速度范数与输入一致，单位为 m/s；解体时刻的方向符合 RTN 观测约定——方位角 0° → +沿迹（along-track），90° → −横向（cross-track），180° → −沿迹，正仰角 → +径向（radial）。改变 `area_to_mass_ratio_m2_kg` 不改变生成轨道的周期/近地点/远地点，但会改变返回的 `life_years`。

### `cat.simulate_debris_breakup_nasa`

```python
cat.simulate_debris_breakup_nasa(
    *,
    mother_tle: Tle,
    epoch: str,
    ssc_prefix: str | None = None,
    total_mass: float | None = None,
    minimum_characteristic_length: float | None = None,
) -> DebrisBreakupResult
```

使用 NASA 解体模型分支生成碎片。`total_mass` 为母星总质量，`minimum_characteristic_length` 为碎片最小特征长度；两者的单位与取值约束按服务端模型约定，SDK 只负责转发。

```python
result = cat.simulate_debris_breakup_nasa(
    mother_tle=tle,
    epoch="2024-01-01T00:00:00.000Z",
    ssc_prefix="AF",
    total_mass=100.0,
    minimum_characteristic_length=0.1,
)
```

### 返回值 `DebrisBreakupResult`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `is_success` | `bool` | 是否成功 |
| `message` | `str` | 服务器消息 |
| `debris_tles` | `tuple[Tle, ...]` | 所有碎片的 TLE |
| `impulses` | `tuple[DebrisImpulse, ...]` | 每块碎片的解体参数 |
| `life_years` | `tuple[float, ...]` | 每块碎片的轨道寿命，单位年；服务端在未计算或计算失败时回退为 25 年 |
| `altitude_of_perigee_km` | `tuple[float, ...]` | 每块碎片的近地点高度，单位 km |
| `altitude_of_apogee_km` | `tuple[float, ...]` | 每块碎片的远地点高度，单位 km |
| `periods_min` | `tuple[float, ...]` | 每块碎片的轨道周期，单位 min |

各数组与 `debris_tles` 按碎片位置对应，但 SDK 不强制各数组等长，长度以服务端返回为准。`life_years` 与寿命估算一样包含服务端回退，不能作为准确寿命预测。

## 已验证范围

- `generate_tle` 的瞬时根数分支（`is_mean_elements` 省略或为 `False`）与独立的 TEME 开普勒状态一致。
- `generate_tle` 的平均根数分支（`True`）：中高偏心率下验证了真近点角→平近点角的转换与平经度保持（0.1° 容差）；近圆（e≈0.0001882）的角度重分配与公里级状态残差仍保留为 strict xfail，完整转换尚未验证。
- `estimate_tle_lifetime` 的 `life_years` 只验证到参数比值语义：输出由 `sm`/`mass` 比值决定，等比值逐值一致，低比值返回 25 年上限，且与解体分支在同一面积质量比下逐值一致；绝对寿命数值未验证。
- 显式解体（`simulate_debris_breakup`）的 `AzElVel`：返回行回显输入，`delta_v_m_s` 速度范数单位为 m/s，解体时刻方向符合 RTN 约定（0° → +沿迹、90° → −横向、180° → −沿迹、正仰角 → +径向）；`area_to_mass_ratio_m2_kg` 不改变生成轨道（周期/近地点/远地点），只改变返回寿命。
- 三个解体模拟分支返回的碎片周期、近地点高度与远地点高度，与碎片的独立 SGP4 状态轨道不变量一致。
- 碎片解体模型本身（碎片数量、速度分布、质量分布的物理合理性）与绝对寿命数值均未验证。

## 约定说明

- 可选参数在未提供时不会被发往 ASTROX，由服务器保留默认值。
- 简单解体分支的方位角/仰角范围定义在 TEME 参考系下的 VVLH 轴系中。
- 显式解体分支的方位角/仰角遵循已验证的 RTN 约定：方位角 0° → +沿迹、90° → −横向、180° → −沿迹，正仰角 → +径向。

完整可运行示例见 `examples/09_cat/cat_workflows.py`。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，本模块函数会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会改写服务器错误信息。需要完全控制请求载荷或处理原始响应时，请使用 `astrox.raw.post`。
