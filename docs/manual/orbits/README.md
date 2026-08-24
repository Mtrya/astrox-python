# 轨道

`astrox.orbits` 提供轨道描述、轨道转换、轨道向导、Lambert 转移以及参考系转换的公开 API。推荐按如下方式导入：

```python
from astrox import orbits
```

本页按概念、返回值约定、函数族引用和示例组织。所有公开参数均采用 `snake_case`，带单位的参数使用 `_m`、`_deg`、`_s` 等显式后缀；未提供的可选参数不会被发往 ASTROX，由服务器保留默认值。若需要完整 ASTROX 原始响应字典，请直接使用 `astrox.raw`。

> 本页示例均为可运行片段，需配合已配置的 ASTROX 服务地址使用：设置环境变量 `ASTROX_BASE_URL`，或在脚本开头调用 `astrox.configure(base_url=...)`。完整可运行脚本见 `examples/02_orbits/`。

## 轨道值对象

`astrox.orbits` 中的轨道描述由冻结数据类承载，构造器只发送调用者显式提供的字段。

### `orbits.KeplerianElements` / `orbits.keplerian(...)`

```python
orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=15.0,
    true_anomaly_deg=45.0,
)
```

`orbits.keplerian(...)` 返回 `orbits.KeplerianElements` 冻结数据类，字段如下：

| 字段 | 单位 | 说明 |
| --- | --- | --- |
| `semi_major_axis_m` | m | 半长轴 |
| `eccentricity` | — | 偏心率 |
| `inclination_deg` | deg | 倾角 |
| `argument_of_periapsis_deg` | deg | 近地点幅角 |
| `raan_deg` | deg | 升交点赤经 |
| `true_anomaly_deg` | deg | 真近点角 |

### `orbits.CartesianState` / `orbits.cartesian_state(...)`

```python
state = orbits.cartesian_state(
    x_m=6114454.0,
    y_m=2870352.0,
    z_m=3308542.0,
    vx_m_s=-3548.0,
    vy_m_s=6463.0,
    vz_m_s=1830.0,
)
```

`orbits.cartesian_state(...)` 返回 `orbits.CartesianState` 冻结数据类，字段如下：

| 字段 | 单位 | 说明 |
| --- | --- | --- |
| `x_m` | m | X 方向位置 |
| `y_m` | m | Y 方向位置 |
| `z_m` | m | Z 方向位置 |
| `vx_m_s` | m/s | X 方向速度 |
| `vy_m_s` | m/s | Y 方向速度 |
| `vz_m_s` | m/s | Z 方向速度 |

### `orbits.MeanKeplerianElements`

`orbits.MeanKeplerianElements` 是 `kozai_izsak_mean_elements(...)` 返回的冻结数据类，表示 Kozai-Izsak 平均根数，字段如下：

| 字段 | 单位 | 说明 |
| --- | --- | --- |
| `semi_major_axis_m` | m | 半长轴 |
| `eccentricity` | — | 偏心率 |
| `inclination_deg` | deg | 倾角 |
| `argument_of_perigee_deg` | deg | 近地点幅角 |
| `raan_deg` | deg | 升交点赤经 |
| `mean_anomaly_deg` | deg | 平近点角 |
| `argument_of_latitude_deg` | deg | 纬度幅角 |
| `longitude_of_perigee_deg` | deg | 近地点经度 |
| `mean_longitude_deg` | deg | 平经度 |

### `orbits.Tle` / `orbits.tle(...)`

```python
tle = orbits.tle(
    line1="1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    line2="2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    name="ISS",
    catalog_number="25544",
)
```

`orbits.tle(...)` 返回 `orbits.Tle` 冻结数据类，用于携带两行根数（TLE）及可选编目元数据。SDK 不校验校验和或轨道物理合理性。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `line1` | `str` | TLE 第一行（必填） |
| `line2` | `str` | TLE 第二行（必填） |
| `name` | `str \| None` | 名称（可选） |
| `catalog_number` | `str \| None` | 编目号（可选） |

`name` 与 `catalog_number` 未提供时不会被发往 ASTROX，由服务器保留默认值。`Tle` 用于 `propagator.sgp4`、`astrox.cat` 与 `astrox.conjunction` 的 TLE 输入；需要查看 SDK 将发送的请求片段时，可使用 `to_lines_wire()` 或 `to_tle_info_wire()`。

## 轨道转换

### `orbits.keplerian_to_cartesian`

```python
orbits.keplerian_to_cartesian(
    orbit: KeplerianElements,
    *,
    gravitational_parameter_m3_s2: float | None = None,
) -> CartesianState
```

将开普勒根数转换为笛卡尔状态。`gravitational_parameter_m3_s2` 为可选引力参数；未提供时由 ASTROX 使用默认值。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `orbit` | — | `orbits.KeplerianElements` 实例 |
| `gravitational_parameter_m3_s2` | m³/s² | 引力参数 |

```python
state = orbits.keplerian_to_cartesian(
    orbit,
    gravitational_parameter_m3_s2=398600441500000.0,
)

print(state.x_m, state.y_m, state.z_m)
print(state.vx_m_s, state.vy_m_s, state.vz_m_s)
```

### `orbits.cartesian_to_keplerian`

```python
orbits.cartesian_to_keplerian(state: CartesianState) -> KeplerianElements
```

将笛卡尔状态转换为开普勒根数。ASTROX 使用其默认地球引力参数进行转换。

| 参数 | 说明 |
| --- | --- |
| `state` | `orbits.CartesianState` 实例 |

```python
elements = orbits.cartesian_to_keplerian(state)
print(elements.semi_major_axis_m, elements.eccentricity)
```

### `orbits.lla_at_ascending_node`

```python
orbits.lla_at_ascending_node(
    orbit: KeplerianElements,
    *,
    orbit_epoch: str,
) -> tuple[float, float, float]
```

返回给定历元轨道升交点处的经纬高，顺序为 `(longitude_deg, latitude_deg, height_m)`。

| 参数 | 说明 |
| --- | --- |
| `orbit` | `orbits.KeplerianElements` 实例 |
| `orbit_epoch` | 轨道历元字符串 |

```python
longitude_deg, latitude_deg, height_m = orbits.lla_at_ascending_node(
    orbit,
    orbit_epoch="2024-01-01T00:00:00.000Z",
)
```

### `orbits.kozai_izsak_mean_elements`

```python
orbits.kozai_izsak_mean_elements(orbit: KeplerianElements) -> MeanKeplerianElements
```

将瞬时开普勒根数转换为 Kozai-Izsak 平均根数。

| 参数 | 说明 |
| --- | --- |
| `orbit` | `orbits.KeplerianElements` 实例 |

```python
mean_elements = orbits.kozai_izsak_mean_elements(orbit)
print(mean_elements.semi_major_axis_m, mean_elements.mean_anomaly_deg)
```

## 轨道向导

轨道向导根据常见设计约束生成开普勒根数。GEO、Molniya、SSO 返回 `(elements_tod, elements_inertial)` 二元组，其中 TOD 为历元时刻的真赤道与真春分点结果，inertial 为 ASTROX 对应的惯性参考系输出。

### `orbits.geo`

```python
orbits.geo(
    *,
    orbit_epoch: str,
    inclination_deg: float,
    subsatellite_longitude_deg: float,
) -> tuple[KeplerianElements, KeplerianElements]
```

生成地球静止轨道（GEO）根数。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `orbit_epoch` | — | 轨道历元字符串 |
| `inclination_deg` | deg | 倾角 |
| `subsatellite_longitude_deg` | deg | 星下点经度 |

```python
elements_tod, elements_inertial = orbits.geo(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    inclination_deg=10.0,
    subsatellite_longitude_deg=120.0,
)
```

### `orbits.molniya`

```python
orbits.molniya(
    *,
    orbit_epoch: str,
    perigee_altitude_km: float,
    apogee_longitude_deg: float,
    argument_of_periapsis_deg: float,
) -> tuple[KeplerianElements, KeplerianElements]
```

生成 Molniya 轨道根数。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `orbit_epoch` | — | 轨道历元字符串 |
| `perigee_altitude_km` | km | 近地点高度 |
| `apogee_longitude_deg` | deg | 远地点经度 |
| `argument_of_periapsis_deg` | deg | 近地点幅角 |

```python
elements_tod, elements_inertial = orbits.molniya(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    perigee_altitude_km=600.0,
    apogee_longitude_deg=100.0,
    argument_of_periapsis_deg=270.0,
)
```

### `orbits.sso`

```python
orbits.sso(
    *,
    orbit_epoch: str,
    altitude_km: float,
    local_time_of_descending_node_hours: float,
) -> tuple[KeplerianElements, KeplerianElements]
```

生成太阳同步轨道（SSO）根数。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `orbit_epoch` | — | 轨道历元字符串 |
| `altitude_km` | km | 轨道高度 |
| `local_time_of_descending_node_hours` | h | 降交点地方时 |

```python
elements_tod, elements_inertial = orbits.sso(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    altitude_km=600.0,
    local_time_of_descending_node_hours=14.5,
)
```

### `orbits.walker_delta` / `orbits.walker_star` / `orbits.walker_custom`

```python
orbits.walker_delta(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_phase_increment: int | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]

orbits.walker_star(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_phase_increment: int | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]

orbits.walker_custom(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_true_anomaly_increment_deg: float | None = None,
    raan_increment_deg: float | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]
```

生成 Walker 星座。外层元组按轨道面索引，每个内层元组包含该面的卫星根数。

| 参数 | 说明 |
| --- | --- |
| `seed_orbit` | 种子轨道，`orbits.KeplerianElements` 实例 |
| `num_planes` | 轨道面数量 |
| `num_sats_per_plane` | 每面卫星数量 |
| `inter_plane_phase_increment` | 平面间相位增量（Delta/Star） |
| `inter_plane_true_anomaly_increment_deg` | 相邻轨道面真近点角增量（Custom） |
| `raan_increment_deg` | 相邻轨道面升交点赤经增量（Custom） |

```python
seed = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=53.0,
    argument_of_periapsis_deg=0.0,
    raan_deg=15.0,
    true_anomaly_deg=0.0,
)

walker = orbits.walker_delta(
    seed_orbit=seed,
    num_planes=3,
    num_sats_per_plane=2,
    inter_plane_phase_increment=1,
)

first_plane_first_sat = walker[0][0]
```

## Lambert 转移

### `orbits.lambert_delta_v`

```python
orbits.lambert_delta_v(
    *,
    departure_state: CartesianState,
    arrival_state: CartesianState,
    time_of_flight_s: float,
    gravitational_parameter_m3_s2: float | None = None,
    get_path_points: bool = False,
    path_point_count: int | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]] | LambertResult
```

求解两个笛卡尔状态之间的单圈 Lambert 转移。默认返回 `(departure_delta_v_m_s, arrival_delta_v_m_s)`，每个速度增量均为 `(x, y, z)` 三元组，单位 m/s。`get_path_points=True` 时返回 `orbits.LambertResult`，除速度增量外还携带 `positions` 转移轨道位置采样（扁平 `(x, y, z, ...)` 序列，单位 m，含首尾端点，点数为 `path_point_count`，服务端缺省 100）。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `departure_state` | — | 出发时刻笛卡尔状态 |
| `arrival_state` | — | 到达时刻笛卡尔状态 |
| `time_of_flight_s` | s | 转移飞行时间 |
| `gravitational_parameter_m3_s2` | m³/s² | 引力参数 |
| `get_path_points` | — | 是否输出转移轨道位置采样；仅单算例时有效 |
| `path_point_count` | — | 位置采样点数（含首尾端点）；服务端缺省 100，仅在 `get_path_points=True` 时传递 |

```python
departure_delta_v_m_s, arrival_delta_v_m_s = orbits.lambert_delta_v(
    departure_state=departure_state,
    arrival_state=arrival_state,
    time_of_flight_s=817.4257,
    gravitational_parameter_m3_s2=398600441500000.0,
)

result = orbits.lambert_delta_v(
    departure_state=departure_state,
    arrival_state=arrival_state,
    time_of_flight_s=817.4257,
    gravitational_parameter_m3_s2=398600441500000.0,
    get_path_points=True,
    path_point_count=5,
)
print(result.positions)  # 5 个采样点的扁平 (x, y, z, ...) 序列
```

位置采样已经过交叉验证：首末端点复现输入 `RV1`/`RV2` 的位置三元组，中间采样点落在以出发速度叠加返回速度增量后的二体转移轨道上（与 Brahe 独立递推一致）。验证证据见 [orbits 验证页](../../validation/orbits.md)。

### `orbits.geo_ym_lambert_delta_v`

```python
orbits.geo_ym_lambert_delta_v(
    *,
    platform_orbit: KeplerianElements,
    target_orbit: KeplerianElements,
    time_of_flight_s: float,
    platform_gravitational_parameter_m3_s2: float | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]
```

基于平台轨道与目标轨道计算 GEO-YM Lambert 转移速度增量。`platform_gravitational_parameter_m3_s2` 仅作用于平台轨道；未提供时由 ASTROX 保留默认值。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `platform_orbit` | — | 平台开普勒根数 |
| `target_orbit` | — | 目标开普勒根数 |
| `time_of_flight_s` | s | 转移飞行时间 |
| `platform_gravitational_parameter_m3_s2` | m³/s² | 平台轨道引力参数 |

```python
departure_delta_v_m_s, arrival_delta_v_m_s = orbits.geo_ym_lambert_delta_v(
    platform_orbit=platform_orbit,
    target_orbit=target_orbit,
    time_of_flight_s=3600.0,
    platform_gravitational_parameter_m3_s2=398600441500000.0,
)
```

## 参考系与天平动

### `orbits.convert_czml_position`

```python
orbits.convert_czml_position(
    position: components.CzmlPosition,
    *,
    to_central_body: str,
    target_reference_frame: str,
) -> tuple[float, components.CzmlPosition]
```

将采样 CZML 位置从当前中心天体与参考系转换到另一个中心天体参考系，返回 `(period_s, transformed_position)`。

| 参数 | 说明 |
| --- | --- |
| `position` | `astrox.components.CzmlPosition` 实例 |
| `to_central_body` | 目标中心天体 |
| `target_reference_frame` | 目标参考系，如 `FIXED`、`INERTIAL`、`J2000` |

```python
from astrox import components, orbits

position = components.czml_position(
    epoch="2024-01-01T00:00:00Z",
    central_body="Earth",
    reference_frame="INERTIAL",
    interpolation_algorithm="LAGRANGE",
    interpolation_degree=7,
    cartesian=[0.0, 7000000.0, 0.0, 0.0],
)

period_s, fixed_position = orbits.convert_czml_position(
    position,
    to_central_body="Earth",
    target_reference_frame="FIXED",
)
```

### `orbits.earth_moon_libration`

```python
orbits.earth_moon_libration(position: components.CzmlPosition) -> components.CzmlPositionSTM
```

将采样 CZML 位置转换到地月天平动参考系，返回 `astrox.components.CzmlPositionSTM`。该对象在 `components.CzmlPosition` 字段基础上额外包含 `unit_quaternion` 和 `cartesian_translation`。

| 参数 | 说明 |
| --- | --- |
| `position` | `astrox.components.CzmlPosition` 实例 |

```python
libration_state = orbits.earth_moon_libration(position)
print(libration_state.central_body, libration_state.reference_frame)
print(libration_state.unit_quaternion)
```

## 返回值

`astrox.orbits` 的函数返回解析后的 SDK 值对象或元组，而非 ASTROX 原始响应字典。构造器与转换函数返回冻结数据类，向导与 Lambert 函数返回嵌套元组，`convert_czml_position` 返回 `(period_s, components.CzmlPosition)`，`earth_moon_libration` 返回 `components.CzmlPositionSTM`。需要未解析的原始响应时，请使用 `astrox.raw`。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，所有函数都会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会隐藏或改写服务器错误信息。

## 完整示例

完整可运行示例见 `examples/02_orbits/`：

- `conversions.py`：开普勒根数与笛卡尔状态互转、升交点经纬高、Kozai-Izsak 平均根数。
- `wizards.py`：GEO、Molniya、SSO 与 Walker 星座生成。
- `lambert_delta_v.py`：笛卡尔 Lambert 与 GEO-YM Lambert 速度增量。
- `orbit_system.py`：CZML 位置参考系转换与地月天平动转换。
