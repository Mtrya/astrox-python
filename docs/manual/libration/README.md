# 平动点与 CRTBP 动力学

`astrox.libration` 提供圆形限制性三体问题（CRTBP）的平动点、单位系、轨迹积分、地月周期轨道族与固定 X 的微分修正功能。推荐按如下方式导入：

```python
from astrox import libration
```

> 本模块中的 CRTBP 位置、速度、时间和周期均为无量纲值。只有 `LibrationUnitSystem` 的引力参数与单位尺度带有显式的 SI 单位。

本页按坐标与单位约定、返回值对象、函数引用和完整示例组织。未提供的可选参数不会被发送给 ASTROX，由服务器保留默认值。

## 坐标、质量比与单位

CRTBP 的质量比定义为：

```text
mass_ratio = m2 / (m1 + m2)
```

其中 `m1` 是主天体质量，`m2` 是次级天体质量。`positions` 返回质心会合坐标系中的平动点。`crtbp_trajectory` 和 `correct_periodic_orbit_fixed_x` 同时支持质心会合坐标系与主天体中心会合坐标系。对同一个状态，两种原点约定的关系为：

```text
x_barycentric = x_primary_centered - mass_ratio
```

`y`、`z` 和三个速度分量不变。在主天体中心会合坐标系中，主天体位于 `x=0`，次级天体位于 `x=1`。

`libration.units()` 把主、次天体引力参数和平均间距转换为 CRTBP 的长度、时间和速度尺度。用户可按如下关系在无量纲值与 SI 值之间转换：

```text
position_m = position * length_unit_m
time_s = time * time_unit_s
velocity_m_s = velocity * velocity_unit_m_s
```

`libration.units()` 的默认引力参数所产生的 `mass_ratio` 与地月周期轨道族使用的质量比 `0.01215058560962404` 不同。把单位系、平动点、轨迹积分和地月轨道族串联起来时，必须显式复用同一个 `mass_ratio`；不要把 `libration.units()` 默认返回的质量比直接与 `earth_moon_l1_halo`、`earth_moon_l2_halo` 或 `earth_moon_dro` 的状态混用。

## 返回值与状态对象

### `libration.CrtbpState` / `libration.crtbp_state(...)`

```python
libration.crtbp_state(
    *,
    x: float,
    y: float,
    z: float,
    vx: float,
    vy: float,
    vz: float,
) -> CrtbpState
```

`crtbp_state(...)` 创建不可变的 `CrtbpState`，字段顺序为位置 `x, y, z` 和会合坐标系速度 `vx, vy, vz`，全部为无量纲值。

```python
state = libration.crtbp_state(
    x=1.189017399646985,
    y=0.0,
    z=0.06060558718057466,
    vx=0.0,
    vy=-0.17403902743307584,
    vz=0.0,
)

print(state.x, state.y, state.z)
print(state.vx, state.vy, state.vz)
```

### 其它返回类型

| 类型 | 主要字段 | 说明 |
| --- | --- | --- |
| `LibrationPoint` | `x`, `y` | 一个无量纲平动点坐标 |
| `LibrationPoints` | `l1`–`l5`, `l1_distance_to_secondary`, `l2_distance_to_secondary`, `l3_distance_to_primary` | 五个平动点及三个共线点到附近天体的无量纲距离 |
| `LibrationUnitSystem` | `primary_gravitational_parameter_m3_s2`, `secondary_gravitational_parameter_m3_s2`, `mass_ratio`, `length_unit_m`, `time_unit_s`, `velocity_unit_m_s` | 一组 CRTBP 有量纲尺度 |
| `CrtbpSample` | `time`, `state` | 某个无量纲时刻的 CRTBP 状态 |
| `CrtbpTrajectory` | `mass_ratio`, `is_barycentric`, `samples` | 数值积分轨迹；`samples` 是 `CrtbpSample` 元组 |
| `PeriodicOrbit` | `is_barycentric`, `period`, `initial_state`, `corrected_state`, `samples` | 周期轨道的原始初猜、修正后初始状态及一个完整周期的样本 |

`PeriodicOrbit.initial_state` 是用于轨道生成或修正的初猜，`corrected_state` 是修正后用于积分的初始状态。`period` 与每个样本的 `time` 都是无量纲时间。

## 平动点

### `libration.positions`

```python
libration.positions(*, mass_ratio: float) -> LibrationPoints
```

计算给定质量比的 L1–L5 平动点，返回质心会合坐标系中的无量纲坐标。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `mass_ratio` | — | 必填，`m2 / (m1 + m2)` |

```python
EARTH_MOON_MASS_RATIO = 0.01215058560962404

points = libration.positions(mass_ratio=EARTH_MOON_MASS_RATIO)
print(points.l1.x, points.l1.y)
print(points.l4.x, points.l4.y)
```

`l1_distance_to_secondary` 与 `l2_distance_to_secondary` 分别是 L1、L2 到次级天体的距离，`l3_distance_to_primary` 是 L3 到主天体的距离。

## 单位系

### `libration.units`

```python
libration.units(
    *,
    primary_gravitational_parameter_m3_s2: float | None = None,
    secondary_gravitational_parameter_m3_s2: float | None = None,
    mean_separation_m: float | None = None,
) -> LibrationUnitSystem
```

计算一组主、次天体系统的质量比和无量纲化尺度。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `primary_gravitational_parameter_m3_s2` | m³/s² | 主天体引力参数，可选 |
| `secondary_gravitational_parameter_m3_s2` | m³/s² | 次级天体引力参数，可选 |
| `mean_separation_m` | m | 两天体的平均间距，可选 |

```python
unit_system = libration.units(
    primary_gravitational_parameter_m3_s2=398600441800000.0,
    secondary_gravitational_parameter_m3_s2=4904869500000.0,
    mean_separation_m=384400000.0,
)

print(unit_system.mass_ratio)
print(unit_system.length_unit_m)
print(unit_system.time_unit_s)
print(unit_system.velocity_unit_m_s)
```

三个参数都可以省略；省略时由服务器使用默认值。若需要在自定义主、次天体系统中连续调用 `positions` 与 `crtbp_trajectory`，应把返回的 `unit_system.mass_ratio` 传给后续函数。

## CRTBP 轨迹积分

### `libration.crtbp_trajectory`

```python
libration.crtbp_trajectory(
    *,
    initial_state: CrtbpState,
    mass_ratio: float,
    start_time: float | None = None,
    end_time: float | None = None,
    barycentric: bool | None = None,
    output_step: float | None = None,
) -> CrtbpTrajectory
```

在 CRTBP 会合坐标系中对一个无量纲初始状态做数值积分。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `initial_state` | 无量纲 | 必填，`CrtbpState` 实例 |
| `mass_ratio` | — | 必填，必须与初始状态所属的主、次天体系统一致 |
| `start_time` | 无量纲 | 积分起始时刻，可选 |
| `end_time` | 无量纲 | 积分结束时刻，可小于 `start_time` 以做逆向积分 |
| `barycentric` | — | `True` 表示质心会合坐标系，`False` 表示主天体中心会合坐标系 |
| `output_step` | 无量纲 | 输出步长；`0.0` 返回自适应积分节点，其它值按指定步长输出 |

```python
trajectory = libration.crtbp_trajectory(
    initial_state=state,
    mass_ratio=0.01215058560962404,
    start_time=0.0,
    end_time=0.2,
    barycentric=False,
    output_step=0.05,
)

for sample in trajectory.samples:
    print(sample.time, sample.state.x, sample.state.y, sample.state.z)
```

`trajectory.mass_ratio` 和 `trajectory.is_barycentric` 记录返回轨迹采用的质量比与原点约定。

## 地月周期轨道族

### `libration.earth_moon_l1_halo`

```python
libration.earth_moon_l1_halo(
    *,
    z_amplitude: float | None = None,
    southern: bool | None = None,
) -> PeriodicOrbit
```

返回地月 L1 Halo 周期轨道。`z_amplitude` 是修正后初始状态的 Z 幅值，为无量纲值；建议范围为 `0.022`–`0.199`。`southern=False` 选择北半球 Halo，`southern=True` 选择南半球 Halo。

### `libration.earth_moon_l2_halo`

```python
libration.earth_moon_l2_halo(
    *,
    x_amplitude: float | None = None,
    southern: bool | None = None,
) -> PeriodicOrbit
```

返回地月 L2 Halo 周期轨道。`x_amplitude` 定义为主天体中心会合坐标系中的 `corrected_state.x - 1.0`，为无量纲值；建议使用略高于 `0.026` 且不高于 `0.1928` 的值。精确传入四舍五入的下界 `0.026` 会被服务器拒绝，可从 `0.0261` 起选值。`southern` 选择北、南半球 Halo 分支。

### `libration.earth_moon_dro`

```python
libration.earth_moon_dro(*, x_amplitude: float | None = None) -> PeriodicOrbit
```

返回地月平面远距离逆行轨道（DRO）。`x_amplitude` 是远离月球一侧的无量纲幅值，定义同样为 `corrected_state.x - 1.0`；建议使用略高于 `0.078` 且不高于 `0.520` 的值。精确传入四舍五入的下界 `0.078` 会被服务器拒绝，可从 `0.0781` 起选值。

```python
l1 = libration.earth_moon_l1_halo(z_amplitude=0.05, southern=False)
l2 = libration.earth_moon_l2_halo(x_amplitude=0.10, southern=True)
dro = libration.earth_moon_dro(x_amplitude=0.1801)

print(l1.period, l1.corrected_state)
print(l2.period, l2.corrected_state)
print(dro.period, dro.corrected_state)
```

这三个函数均返回主天体中心会合坐标系中的 `PeriodicOrbit`，因此 `is_barycentric` 为 `False`。L1 Halo 的 `z_amplitude` 和 L2 Halo/DRO 的 `x_amplitude` 不是同一种轨道族参数，调用时应保留它们各自的定义。

## 固定 X 的周期轨道修正

### `libration.correct_periodic_orbit_fixed_x`

```python
libration.correct_periodic_orbit_fixed_x(
    *,
    initial_state: CrtbpState,
    period_guess: float,
    mass_ratio: float,
    barycentric: bool | None = None,
    output_step: float | None = None,
) -> PeriodicOrbit
```

固定初始状态的 X 坐标，修正 Z 位置、Y 速度与周期，生成关于 XZ 平面对称的 CRTBP 周期轨道。`initial_state` 应是 XZ 平面穿越状态，即 `y`、`vx` 和 `vz` 接近零。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `initial_state` | 无量纲 | 必填，待修正的 XZ 平面穿越状态 |
| `period_guess` | 无量纲 | 必填，完整周期的初猜；不要传入半周期 |
| `mass_ratio` | — | 必填，必须与初始状态所属系统一致 |
| `barycentric` | — | `True` 表示输入和输出都采用质心会合坐标系，`False` 表示主天体中心会合坐标系 |
| `output_step` | 无量纲 | 返回轨道的输出步长；`0.0` 返回自适应积分节点 |

```python
EARTH_MOON_MASS_RATIO = 0.01215058560962404

family_member = libration.earth_moon_l1_halo(
    z_amplitude=0.05,
    southern=False,
)

corrected = libration.correct_periodic_orbit_fixed_x(
    initial_state=family_member.corrected_state,
    period_guess=family_member.period,
    mass_ratio=EARTH_MOON_MASS_RATIO,
    barycentric=False,
    output_step=0.05,
)

print(corrected.period)
print(corrected.corrected_state)
```

修正结果中的 `initial_state` 保留调用者传入的初猜，`corrected_state.x` 与初猜的 `x` 相同。初猜偏离目标轨道过大或周期初猜不合适时，ASTROX 会拒绝未收敛的结果。

## 坐标原点转换

若要把主天体中心状态改为质心状态，只需将 X 坐标减去质量比：

```python
mass_ratio = 0.01215058560962404
primary_centered = l1.corrected_state

barycentric = libration.crtbp_state(
    x=primary_centered.x - mass_ratio,
    y=primary_centered.y,
    z=primary_centered.z,
    vx=primary_centered.vx,
    vy=primary_centered.vy,
    vz=primary_centered.vz,
)
```

调用 `crtbp_trajectory` 或 `correct_periodic_orbit_fixed_x` 时，应同时传入 `barycentric=True`，使坐标数值与原点声明保持一致。

## 错误处理与相关资料

`crtbp_trajectory` 和 `correct_periodic_orbit_fixed_x` 只接受 `CrtbpState` 作为状态输入。类型不匹配时抛出 `TypeError`；服务器返回 `IsSuccess=false` 时抛出 `astrox.exceptions.AstroxAPIError`；HTTP 错误、请求超时与连接失败分别抛出 `AstroxHTTPError`、`AstroxTimeoutError` 与 `AstroxConnectionError`。SDK 不对幅值、初猜或质量比做额外的物理合理性判断。

- 按任务操作的完整步骤见[如何生成并检查一条 CRTBP 周期轨道](../../how_to/generate_a_crtbp_periodic_orbit.md)。
- 可运行示例见 `examples/13_libration/libration_dynamics.py`。
- 各分支的验证范围与已知限制见 [libration 验证页](../../validation/libration.md)。
