# 传播器

`astrox.propagator` 提供轨道传播与弹道轨迹计算的公开 API，包括二体、J2、SGP4、简单上升、HPOP 和弹道等模型。推荐按如下方式导入：

```python
from astrox import orbits, propagator
```

本页按概念、返回值约定、函数族引用和示例组织。所有参数均采用 `snake_case`，带单位的参数使用 `_m`、`_deg`、`_s` 等显式后缀。可选参数在未提供时不会被发往 ASTROX，由服务器保留默认值。若需要完全控制请求载荷，请使用 `astrox.raw`。

## 轨道输入

传播函数接受 `orbits.KeplerianElements` 或 `orbits.CartesianState` 作为轨道描述；`propagator.sgp4` 接受 `orbits.Tle` 两行根数。`orbits.keplerian(...)` 用六个开普勒根数构造轨道，`orbits.cartesian_state(...)` 用位置/速度构造笛卡尔状态，`orbits.tle(...)` 用两行根数构造 TLE。历元 `orbit_epoch` 只适用于 `KeplerianElements` 或 `CartesianState` 轨道输入，与根数或状态分离，由传播函数单独接收；`propagator.sgp4` 不接受 `orbit_epoch`，其传播历元来自 TLE 内编码的 epoch。

```python
orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=0.0,
    true_anomaly_deg=0.0,
)
```

轨道构造器详见 [orbits 手册](../orbits/README.md)。

## 返回值

单个轨道传播函数返回 `(period_s, position)` 元组：

- `period_s`：`float`，ASTROX 返回的轨道周期，单位秒。
- `position`：`propagator.PropagatorPosition` 冻结数据类，字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `central_body` | `str` | 中心天体 |
| `epoch` | `str` | 位置采样起始历元 |
| `reference_frame` | `str` | 参考系，如 `INERTIAL`、`FIXED` |
| `interpolation_algorithm` | `str` | 插值算法 |
| `interpolation_degree` | `int` | 插值阶数 |
| `cartesian_velocity` | `tuple[float, ...]` | CZML 风格的 `[t, x, y, z, vx, vy, vz, ...]` 采样序列 |

`cartesian_velocity` 中的坐标与速度单位与 `reference_frame` 一致；`INERTIAL` 对应惯性参考系，`FIXED` 对应地固参考系。SGP4 返回的 `INERTIAL` 对应 GCRF/GCRS 风格的惯性坐标。

批量传播函数 `multi_j2`、`multi_two_body`、`multi_sgp4` 返回 `tuple[orbits.KeplerianElements, ...]`，即目标历元处的开普勒根数元组。ASTROX 原始响应中每条根数还包含 `GravitationalParameter` 字段，SDK 解析后的返回值省略该字段；需要完整原始响应时请使用 `astrox.raw`。

## J2 与二体传播

### `propagator.j2`

```python
propagator.j2(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
    j2_normalized_value: float | None = None,
    ref_distance_m: float | None = None,
) -> tuple[float, PropagatorPosition]
```

用 J2 模型从 `orbit_epoch` 开始传播开普勒根数。`j2_normalized_value` 为归一化 J2 系数，`ref_distance_m` 为参考距离，二者均用于覆盖服务器默认值。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 传播起始时间字符串 |
| `stop` | — | 传播结束时间字符串 |
| `orbit_epoch` | — | 轨道根数历元字符串 |
| `orbit` | — | `orbits.KeplerianElements` 实例 |
| `step_s` | s | 采样步长 |
| `central_body` | — | 中心天体名称 |
| `gravitational_parameter_m3_s2` | m³/s² | 引力参数 |
| `coord_system` | — | 坐标系，如 `Inertial` |
| `j2_normalized_value` | — | 归一化 J2 值 |
| `ref_distance_m` | m | J2 参考距离 |

```python
period_s, position = propagator.j2(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    step_s=300.0,
    coord_system="Inertial",
    gravitational_parameter_m3_s2=398600441500000.0,
    j2_normalized_value=0.000484165143790815,
    ref_distance_m=6378137.0,
)
```

完整可运行示例见 `examples/01_propagation/j2_classical.py`。

### `propagator.two_body`

```python
propagator.two_body(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
) -> tuple[float, PropagatorPosition]
```

用二体模型传播开普勒根数。参数与 `j2` 相同，但不接受 `j2_normalized_value` 和 `ref_distance_m`。

```python
period_s, position = propagator.two_body(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    gravitational_parameter_m3_s2=398600441500000.0,
)
```

完整可运行示例见 `examples/01_propagation/two_body_classical.py`。

## 批量传播

批量传播将多个状态或 TLE 统一到同一个目标历元 `epoch`。

### `propagator.multi_j2`

```python
propagator.multi_j2(
    *,
    epoch: str,
    states: Sequence[tuple[str, KeplerianElements]],
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[KeplerianElements, ...]
```

将多组开普勒根数用 J2 模型传播到 `epoch`。`states` 中每项为 `(orbit_epoch, orbit)`，其中 `orbit_epoch` 是该状态的历元字符串，`orbit` 为 `KeplerianElements`。

### `propagator.multi_two_body`

```python
propagator.multi_two_body(
    *,
    epoch: str,
    states: Sequence[tuple[str, KeplerianElements]],
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[KeplerianElements, ...]
```

用二体模型批量传播。`gravitational_parameter_m3_s2` 若提供，会写入每个输入状态。

### `propagator.multi_sgp4`

```python
propagator.multi_sgp4(
    *,
    epoch: str,
    tle_sets: Sequence[tuple[str, str]],
) -> tuple[KeplerianElements, ...]
```

将多组两行根数（TLE）用 SGP4 传播到 `epoch`。`tle_sets` 中每项为包含 TLE 第一行和第二行的二元组。

```python
leo = orbits.keplerian(...)
inclined = orbits.keplerian(...)

states = [
    ("2024-01-01T00:00:00.000Z", leo),
    ("2024-01-01T00:03:00.000Z", inclined),
]

elements = propagator.multi_two_body(
    epoch="2024-01-01T00:10:00.000Z",
    states=states,
    gravitational_parameter_m3_s2=398600441500000.0,
)
```

完整可运行示例见 `examples/01_propagation/batch_propagators.py`。

## SGP4 传播

### `propagator.sgp4`

```python
propagator.sgp4(
    *,
    start: str,
    stop: str,
    tle: Tle,
    step_s: float | None = None,
) -> tuple[float, PropagatorPosition]
```

从两行根数（TLE）出发，用 SGP4 模型传播卫星轨道。`tle` 必须是 `orbits.tle(...)` 构造的 `orbits.Tle` 实例；TLE 中提供 `catalog_number` 时，SDK 会将其作为卫星编号发送给 ASTROX，未提供时不发送。

| 参数 | 说明 |
| --- | --- |
| `start` | 传播起始时间字符串 |
| `stop` | 传播结束时间字符串 |
| `tle` | `orbits.Tle` 实例，包含 TLE 第一行与第二行 |
| `step_s` | 采样步长 |

```python
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
```

`orbits.tle(...)` 的字段说明见 [orbits 手册](../orbits/README.md)。完整可运行示例见 `examples/01_propagation/sgp4_tle.py`。

## 简单上升

### `propagator.simple_ascent`

```python
propagator.simple_ascent(
    *,
    start: str,
    stop: str,
    launch_latitude_deg: float,
    launch_longitude_deg: float,
    launch_altitude_m: float,
    burnout_velocity_m_s: float,
    burnout_latitude_deg: float,
    burnout_longitude_deg: float,
    burnout_altitude_m: float,
    step_s: float | None = None,
    central_body: str | None = None,
) -> tuple[float, PropagatorPosition]
```

从发射点与熄火点参数生成简单上升轨迹。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 起始时间字符串 |
| `stop` | — | 结束时间字符串 |
| `launch_latitude_deg` | deg | 发射点纬度 |
| `launch_longitude_deg` | deg | 发射点经度 |
| `launch_altitude_m` | m | 发射点高度 |
| `burnout_velocity_m_s` | m/s | 熄火点速度 |
| `burnout_latitude_deg` | deg | 熄火点纬度 |
| `burnout_longitude_deg` | deg | 熄火点经度 |
| `burnout_altitude_m` | m | 熄火点高度 |
| `step_s` | s | 采样步长 |
| `central_body` | — | 中心天体 |

```python
period_s, position = propagator.simple_ascent(
    start="2024-01-01T03:00:00.000Z",
    stop="2024-01-01T03:02:00.000Z",
    step_s=30.0,
    central_body="Earth",
    launch_latitude_deg=40.9575,
    launch_longitude_deg=100.2912,
    launch_altitude_m=1000.0,
    burnout_velocity_m_s=7800.0,
    burnout_latitude_deg=41.3,
    burnout_longitude_deg=101.0,
    burnout_altitude_m=200000.0,
)
```

完整可运行示例见 `examples/01_propagation/simple_ascent.py`。

## HPOP 高精度传播

HPOP 支持从开普勒根数或笛卡尔状态出发，通过力模型配置进行高精度数值传播。

### `propagator.hpop`

```python
propagator.hpop(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements | None = None,
    state: CartesianState | None = None,
    config: HpopConfig | Mapping[str, Any] | None = None,
    coord_system: str | None = None,
    coord_epoch: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coefficient_of_drag: float | None = None,
    area_mass_ratio_drag_m2_kg: float | None = None,
    coefficient_of_srp: float | None = None,
    area_mass_ratio_srp_m2_kg: float | None = None,
) -> tuple[float, PropagatorPosition]
```

`orbit` 与 `state` 必须且只能提供一个。`config` 可以是 `HpopConfig` 对象，也可以是已知 ASTROX 结构的原始字典映射。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 传播起始时间字符串 |
| `stop` | — | 传播结束时间字符串 |
| `orbit_epoch` | — | 轨道历元字符串 |
| `orbit` | — | 开普勒根数输入 |
| `state` | — | 笛卡尔状态输入 |
| `config` | — | HPOP 配置对象或映射 |
| `coord_system` | — | 坐标系 |
| `coord_epoch` | — | 坐标历元 |
| `gravitational_parameter_m3_s2` | m³/s² | 引力参数 |
| `coefficient_of_drag` | — | 阻力系数 |
| `area_mass_ratio_drag_m2_kg` | m²/kg | 阻力面积质量比 |
| `coefficient_of_srp` | — | 太阳辐射压系数 |
| `area_mass_ratio_srp_m2_kg` | m²/kg | 太阳辐射压面积质量比 |

### HPOP 配置构造器

这些构造器返回冻结的 SDK 值对象，只发送调用者显式提供的字段。

#### `propagator.hpop_config`

```python
propagator.hpop_config(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    central_body: str | None = None,
    integrator: HpopIntegrator | None = None,
    gravity: HpopGravity | None = None,
    atmosphere: HpopAtmosphere | None = None,
    srp: HpopSrp | None = None,
    third_bodies: Sequence[HpopThirdBody] | None = None,
) -> HpopConfig
```

#### `propagator.hpop_rkf78`

```python
propagator.hpop_rkf78(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    use_fixed_step: bool | None = None,
    initial_step_s: float | None = None,
    max_step_s: float | None = None,
    min_step_s: float | None = None,
    max_abs_error: float | None = None,
    max_rel_error: float | None = None,
    max_iterations: int | None = None,
) -> HpopIntegrator
```

配置 RKF7(8) 数值积分器。

#### `propagator.hpop_two_body_gravity`

```python
propagator.hpop_two_body_gravity(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
) -> HpopGravity
```

使用二体重力模型。`gravitational_parameter_m3_s2` 提供时会被写入请求中重力模型的 `Mu` 字段，用于覆盖中心天体的默认引力参数（单位 m³/s²）；未提供时该字段不会发往 ASTROX，由服务器采用中心天体默认值。显式提供 `Mu` 是已验证 RunMCS 二体传播场景使用的配置值；该场景下省略时不能宣称具有同样的二体物理语义。

#### `propagator.hpop_gravity_field`

```python
propagator.hpop_gravity_field(
    *,
    gravity_file_name: str,
    degree: int,
    order: int,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    use_secular_variations: bool | None = None,
    solid_tide_type: str | None = None,
    eop_file_path: str | None = None,
) -> HpopGravity
```

配置重力场模型。`gravity_file_name` 为重力场文件，`degree` 和 `order` 为阶次。

#### `propagator.hpop_jacchia_roberts`

```python
propagator.hpop_jacchia_roberts(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    drag_model_type: str | None = None,
    atmos_data_source: str | None = None,
    f10p7: float | None = None,
    f10p7_avg: float | None = None,
    kp: float | None = None,
) -> HpopAtmosphere
```

配置 Jacchia-Roberts 大气模型。

#### `propagator.hpop_srp_spherical`

```python
propagator.hpop_srp_spherical(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    shadow_model: str | None = None,
    sun_position: str | None = None,
    eclipsing_bodies: Sequence[str] | None = None,
) -> HpopSrp
```

配置球形太阳辐射压模型。

#### `propagator.hpop_third_body`

```python
propagator.hpop_third_body(
    third_body_name: str,
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    mode_type: str | None = None,
    ephem_source: str | None = None,
    grav_source: str | None = None,
    mu_m3_s2: float | None = None,
) -> HpopThirdBody
```

配置第三方天体摄动。`third_body_name` 为天体名称。

```python
config = propagator.hpop_config(
    central_body="Earth",
    integrator=propagator.hpop_rkf78(
        use_fixed_step=True,
        initial_step_s=60.0,
        max_step_s=60.0,
        min_step_s=0.001,
        max_abs_error=1e-10,
        max_rel_error=1e-12,
        max_iterations=50,
    ),
    gravity=propagator.hpop_gravity_field(
        gravity_file_name="EGM2008.grv",
        degree=4,
        order=4,
        use_secular_variations=False,
        solid_tide_type="Permanent tide only",
        eop_file_path="EOP-v1.1.txt",
    ),
)

period_s, position = propagator.hpop(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    coord_system="Inertial",
    gravitational_parameter_m3_s2=398600441500000.0,
    config=config,
)
```

笛卡尔状态输入：

```python
state = orbits.cartesian_state(
    x_m=7000000.0,
    y_m=1000.0,
    z_m=2000.0,
    vx_m_s=-1.0,
    vy_m_s=7500.0,
    vz_m_s=10.0,
)

period_s, position = propagator.hpop(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    state=state,
    config=propagator.hpop_config(
        central_body="Earth",
        gravity=propagator.hpop_two_body_gravity(),
    ),
)
```

完整可运行示例见 `examples/01_propagation/hpop.py`。

## 弹道传播

弹道传播计算从发射点到落点的次轨道轨迹。共有五个函数：一个名义函数和四个按不同约束条件求解的函数。所有函数都返回 `(period_s, position)`。

| 函数 | 额外必填参数 | 约束类型 |
| --- | --- | --- |
| `propagator.ballistic` | 无 | 名义弹道 |
| `propagator.ballistic_delta_v` | `delta_v_m_s` | 速度增量 |
| `propagator.ballistic_delta_v_min_ecc` | `delta_v_m_s` | 最小偏心率速度增量 |
| `propagator.ballistic_apogee_altitude` | `apogee_altitude_m` | 远地点高度 |
| `propagator.ballistic_time_of_flight` | `time_of_flight_s` | 飞行时间 |

共同参数：

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 起始时间字符串 |
| `impact_latitude_deg` | deg | 落点纬度 |
| `impact_longitude_deg` | deg | 落点经度 |
| `stop` | — | 结束时间字符串 |
| `step_s` | s | 采样步长 |
| `central_body` | — | 中心天体 |
| `gravitational_parameter_m3_s2` | m³/s² | 引力参数 |
| `launch_latitude_deg` | deg | 发射点纬度 |
| `launch_longitude_deg` | deg | 发射点经度 |
| `launch_altitude_m` | m | 发射点高度 |
| `impact_altitude_m` | m | 落点高度 |

### `propagator.ballistic`

```python
propagator.ballistic(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]
```

### `propagator.ballistic_delta_v`

```python
propagator.ballistic_delta_v(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    delta_v_m_s: float,
    ...
) -> tuple[float, PropagatorPosition]
```

### `propagator.ballistic_delta_v_min_ecc`

```python
propagator.ballistic_delta_v_min_ecc(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    delta_v_m_s: float,
    ...
) -> tuple[float, PropagatorPosition]
```

### `propagator.ballistic_apogee_altitude`

```python
propagator.ballistic_apogee_altitude(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    apogee_altitude_m: float,
    ...
) -> tuple[float, PropagatorPosition]
```

### `propagator.ballistic_time_of_flight`

```python
propagator.ballistic_time_of_flight(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    time_of_flight_s: float,
    ...
) -> tuple[float, PropagatorPosition]
```

```python
period_s, position = propagator.ballistic_delta_v(
    start="2024-01-01T12:00:00.000Z",
    impact_latitude_deg=30.0,
    impact_longitude_deg=-70.0,
    launch_latitude_deg=28.5721,
    launch_longitude_deg=-80.648,
    launch_altitude_m=10.0,
    impact_altitude_m=0.0,
    delta_v_m_s=3000.0,
    step_s=30.0,
)
```

完整可运行示例见 `examples/01_propagation/ballistic_delta_v.py`、`ballistic_min_ecc.py`、`ballistic_apogee_alt.py`、`ballistic_time_of_flight.py`。

## 与 `astrox.components` 位置源的对应关系

`astrox.components` 提供了与传播器参数对应的位置源对象，如 `J2Position`、`TwoBodyPosition`、`Sgp4Position`、`HpopPosition`、`SimpleAscentPosition`、`BallisticPosition`，用于在命名对象中组装位置源。它们的参数与 `propagator` 中的函数一一对应，但属于组件层的值对象。详见 [components 手册](../components/README.md)。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，所有传播函数都会抛出 `astrox.exceptions` 下的异常：服务器响应 `IsSuccess=false` 抛 `AstroxAPIError`，HTTP 4xx/5xx 抛 `AstroxHTTPError`，请求超时抛 `AstroxTimeoutError`，连接失败抛 `AstroxConnectionError`。它们都是 `AstroxError` 的并列子类。SDK 不会隐藏或改写服务器错误信息。需要完整原始响应时，请直接使用 `astrox.raw.post`。
