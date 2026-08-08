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

`is_mean_elements=True` 时，服务端会把输入的真近点角转换为平近点角写入 TLE。该分支整体为`未解析`：非赤道案例已观察到真近点角→平近点角转换，且输出 TLE 的近地点幅角与平近点角保持输入的平均经度；赤道特例（如零倾角输入）的行为仍无法依赖，完整的转换语义尚不能宣布已验证。

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

`estimate_tle_lifetime` 整体为`未解析`：`life_years` 只能作为相对估计，不能作为绝对寿命预测。已验证的约定行为：

- 输出取决于 `sm` 与 `mass` 的比值：相同比值下逐值一致，比值增大时输出单调下降；低比值时服务端返回 25 年上限。
- `sm` 与解体接口的 `area_to_mass_ratio_m2_kg` 按同一比例解释：`sm=ratio, mass=1.0` 与 `area_to_mass_ratio_m2_kg=ratio` 的 `life_years` 逐值一致（已覆盖 ratio 0.001、0.002、0.01）。
- 未提供 `sm`/`mass` 时，服务端默认行为与 `sm=0.01, mass=1.0` 一致。
- 服务器未计算、计算失败与寿命超过上限都可能返回相同的 25 年值，因此 25 年不携带具体寿命语义。

## 碎片解体模拟

三个函数模拟母卫星解体产生碎片，都返回 `DebrisBreakupResult`。它们模拟母星解体事件本身，返回碎片的 TLE 与轨道参数；碎片解体模型本身的科学性（碎片数量、速度与质量分布等）不是 SDK 已验证的语义。

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

所有碎片使用相同的相对速度与面积质量比；方位角/仰角的具体分布由服务端决定，未在本 SDK 证据范围内验证。

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

逐条给出碎片的解体参数。`impulses` 是请求中的解体行（breakup rows），每一行是一组解体参数；返回的碎片数量与顺序由服务端决定：

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

显式解体的方向遵循 RTN 约定：方位角 0° → +沿迹（along-track），90° → −横向（cross-track），180° → −沿迹，正仰角 → +径向（radial）；`delta_v_m_s` 的速度范数单位为 m/s。`area_to_mass_ratio_m2_kg` 不改变生成轨道的周期/近地点/远地点，但会改变返回的 `life_years`。

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
| `impulses` | `tuple[DebrisImpulse, ...]` | 服务端返回的解体行（breakup rows） |
| `life_years` | `tuple[float, ...]` | 每块碎片的轨道寿命，单位年；`compute_lifetime=False` 时返回 25 年，未计算或计算失败时回退为 25 年 |
| `altitude_of_perigee_km` | `tuple[float, ...]` | 每块碎片的近地点高度，单位 km |
| `altitude_of_apogee_km` | `tuple[float, ...]` | 每块碎片的远地点高度，单位 km |
| `periods_min` | `tuple[float, ...]` | 每块碎片的轨道周期，单位 min |

返回数组必须同步等长：`debris_tles`、`impulses`、`life_years`、`altitude_of_perigee_km`、`altitude_of_apogee_km` 与 `periods_min` 按返回位置一一对应，SDK parser 在长度不一致时抛出 `TypeError`。`impulses` 是服务端返回的解体行（breakup rows）：只有 `simulate_debris_breakup` 会回显请求中的解体行，`simulate_debris_breakup_simple` 与 `simulate_debris_breakup_nasa` 分支的行来自服务端响应。返回的碎片数量与顺序由服务端决定。`life_years` 与寿命估算一样不能作为准确寿命预测：`compute_lifetime=False`、未计算或计算失败时都返回 25 年，此时 25 年不携带真实寿命语义。

## 验证状态

- `generate_tle` 的瞬时根数分支（`is_mean_elements` 省略或为 `False`）与返回碎片的轨道量（周期、近地点/远地点高度）有验证证据；平均根数分支（`is_mean_elements=True`）整体为`未解析`：非赤道案例已观察到真近点角→平近点角转换与平均经度保持，赤道特例仍无法依赖。
- `estimate_tle_lifetime` 整体为`未解析`：`life_years` 只有相对语义——依赖 `sm`/`mass` 比值、未提供参数时的默认面积质量比约定，以及解体分支的逐值一致；绝对寿命数值未验证，25 年封顶与服务器回退无法区分。
- 碎片解体模型本身的科学合理性（碎片数量、速度分布、质量分布）与绝对寿命数值均不是 SDK 已验证的语义。
- 具体比较路径、case 与容差见 [cat 验证页](../../validation/cat.md)。

## 约定说明

- 可选参数在未提供时不会被发往 ASTROX，由服务器保留默认值。
- 简单解体分支的方位角/仰角范围定义在 TEME 参考系下的 VVLH 轴系中。
- 显式解体分支的方位角/仰角遵循 RTN 约定：方位角 0° → +沿迹、90° → −横向、180° → −沿迹，正仰角 → +径向。

完整可运行示例见 `examples/09_cat/cat_workflows.py`。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，本模块函数会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会改写服务器错误信息。需要完全控制请求载荷或处理原始响应时，请使用 `astrox.raw.post`。
