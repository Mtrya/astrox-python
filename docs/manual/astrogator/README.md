# Astrogator 任务序列（RunMCS）

`astrox.astrogator` 提供 ASTROX Astrogator 任务控制序列（RunMCS）的公开 API。你可以把「初始状态、传播、冲量机动、有限机动、嵌套序列、目标序列、停止」等段（segment）组合成一条有序的主序列，由 ASTROX 一次性执行，并返回实际执行并产生输出的段的初始状态、最终状态、耗时与标量结果。推荐按如下方式导入：

```python
from astrox import astrogator, propagator
```

本页按概念、验证状态、顶层调用、段构造器、初始状态、停止条件、传播器注册、机动与发动机、标量结果、差分修正、结果树和明确限制组织。所有参数均为 `snake_case`，带单位的参数使用 `_m`、`_m_s`、`_deg`、`_s`、`_kg`、`_m3_s2` 等显式后缀。可选参数在未提供时不会发往 ASTROX，由服务器保留默认值。若需要完全控制请求载荷，请使用 `astrox.raw`。

## 概念

一次 RunMCS 调用描述一条航天器任务：主序列（`main_sequence`）是一个按执行顺序排列的段列表，每个段执行一种操作，后一个段从前一个段的最终状态继续。段的结果沿主序列顺序返回，嵌套段（`sequence`、`target_sequence`）的段结果会递归展开。

段类型与用途：

| 段 | 构造器 | 用途 |
| --- | --- | --- |
| 初始状态 | `initial_state(...)` | 定义任务起点：历元、状态元素、质量与面积参数 |
| 传播 | `propagate(...)` | 用指定传播器推进到停止条件触发 |
| 冲量机动 | `impulsive_maneuver(...)` | 瞬时速度增量 |
| 有限机动 | `finite_maneuver(...)` | 持续一段时间的发动机点火 |
| 嵌套序列 | `sequence(...)` | 把一组段包成子序列 |
| 目标序列 | `target_sequence(...)` | 运行子序列，可附加差分修正算子调节变量 |
| 停止 | `stop(...)` | 启用时终止任务执行 |
| 跟随 | `follow(...)` | 跟随另一个实体运动（当前不可用，见限制） |

`run_mcs(...)` 接收主序列，并可通过 `propagators`、`engine_models` 显式注册传播器与发动机。任务中的传播段通过名称引用已注册的传播器。

## 验证状态

本文档把已经验证的行为写成确定性推荐；标注「部分验证」的分支可以构造请求，但 SDK 不为这些分支的物理语义提供保证；标注「未验证」或「不可用」的分支不应在任务中使用。例如，传播、停止条件、冲量沿速度方向的速度增量等分支已经过独立校验，可以放心使用；而 Follow 段在服务端无法成功执行，本文档明确标注为不可用。

## 顶层调用 `run_mcs`

```python
astrogator.run_mcs(
    main_sequence: Sequence[MCSSegment],
    *,
    central_body: str = "Earth",
    out_czml_frame_name: str = "INERTIAL",
    compute_czml_positions: bool | None = None,
    entities: Sequence[EntityPath] | None = None,
    propagators: Sequence[HpopConfig] | None = None,
    engine_models: Sequence[EngineConstant] | None = None,
    text: str | None = None,
) -> RunMCSResult
```

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `main_sequence` | `Sequence[MCSSegment]` | — | 主序列段列表，按顺序执行 |
| `central_body` | `str` | `"Earth"` | 中心天体。已验证路径均使用 `Earth`，其他天体的行为部分验证 |
| `out_czml_frame_name` | `str` | `"INERTIAL"` | CZML 输出参考系名称。`INERTIAL` 帧已验证；`FIXED`、`J2000`、`MEANECLPJ2000` 等帧的约定部分验证 |
| `compute_czml_positions` | `bool | None` | `None` | 是否计算 CZML 风格的位置采样（见下文 CZML 位置一节）。未提供时该字段不会发往 ASTROX，由服务器保留默认 |
| `entities` | `Sequence[EntityPath] | None` | 实体定义。当前仅与未验证的 Follow 段相关，见限制 |
| `propagators` | `Sequence[HpopConfig] | None` | 注册的自定义传播器，段通过 `propagator_name` 引用 |
| `engine_models` | `Sequence[EngineConstant] | None` | 注册的发动机，机动段通过 `propulsion_method_value` 引用 |
| `text` | `str | None` | 任务备注文本。部分验证：该输入被服务器接受，但除输入注解外的语义未验证 |

`main_sequence` 中的每一项都必须是段构造器返回的 SDK 值对象，原始字典不会被接受。请求构造完成后由 `raw.post("/Astrogator/RunMCS", ...)` 发送。

### 为什么必须显式注册传播器

RunMCS 不会从内置库中按名称查找传播器：默认名称（如 `TwoBody`、`J2`、`HPOP`）无法被传播段直接引用，省略 `propagator_name` 也会失败。因此必须在 `propagators` 中显式注册自定义传播器，并在传播段中引用注册时的名称：

```python
config = propagator.hpop_config(
    name="Earth_TwoBody_Example",
    central_body="Earth",
    integrator=propagator.hpop_rkf78(
        name="RKF7th8th_Example",
        use_fixed_step=True,
        initial_step_s=0.1,
        max_step_s=0.1,
        min_step_s=0.1,
        max_abs_error=1e-10,
        max_rel_error=1e-13,
        max_iterations=100,
    ),
    gravity=propagator.hpop_two_body_gravity(
        name="TwoBody_Example",
        gravitational_parameter_m3_s2=398600441500000.0,
    ),
)

result = astrogator.run_mcs(
    [
        astrogator.initial_state("Initial State", initial_orbit, epoch=START),
        astrogator.propagate(
            "Coast",
            propagator_name="Earth_TwoBody_Example",
            stop_conditions=[astrogator.duration_stop("One Second", 1.0)],
        ),
    ],
    propagators=[config],
)
```

`hpop_two_body_gravity` 的 `gravitational_parameter_m3_s2` 是可选的：提供时会被写入请求中重力模型的 `Mu` 字段。RunMCS 已校准的二体传播路径必须显式提供它——省略时服务器采用中心天体默认引力常数，传播结果会退化为近匀速漂移，与二体运动不符，不能宣称具有同样的二体物理语义；提供显式引力参数后，传播状态与独立二体传播一致。该参数也决定了停止条件（近地点/远地点）与开普勒元素换算使用的引力常数，因此应与初始状态元素中的 `gravitational_parameter_m3_s2` 保持一致。

RunMCS 中 `propagator.hpop_config` 的其余字段（大气、太阳辐射压、第三方天体摄动等）可以传入，但只有二体重力分支经过独立校准，其余力模型的数值行为部分验证，不作为语义保证。

## 初始状态元素

`initial_state` 段通过状态元素构造器定义任务起点。四种元素形式均已验证：开普勒根数、笛卡尔状态、球面状态与双曲出射渐近线（TargetVecOut）。

### `keplerian_state`

```python
astrogator.keplerian_state(
    *,
    semi_major_axis_m: float,
    eccentricity: float,
    inclination_deg: float,
    raan_deg: float,
    argument_of_periapsis_deg: float,
    gravitational_parameter_m3_s2: float,
    anomaly_type: str = "True",
    true_anomaly_deg: float | None = None,
    mean_anomaly_deg: float | None = None,
    element_type: str = "Osculating",
) -> KeplerianState
```

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `semi_major_axis_m` | m | 半长轴 |
| `eccentricity` | — | 偏心率 |
| `inclination_deg` | deg | 轨道倾角 |
| `raan_deg` | deg | 升交点赤经 |
| `argument_of_periapsis_deg` | deg | 近地点幅角 |
| `gravitational_parameter_m3_s2` | m³/s² | 引力参数，必须显式提供 |
| `anomaly_type` | — | 近点角类型：`True` 或 `Mean` |
| `true_anomaly_deg` | deg | 真近点角，与 `mean_anomaly_deg` 二选一 |
| `mean_anomaly_deg` | deg | 平近点角 |
| `element_type` | — | 元素类型：`Osculating` 或其他字符串 |

开普勒根数形式必须显式提供 `gravitational_parameter_m3_s2`：缺少引力参数时服务器无法表示该轨道并会拒绝请求。默认 `anomaly_type="True"`（真近点角）的解释已经验证；`"Mean"`（平近点角）分支部分验证。

### `cartesian_state`

```python
astrogator.cartesian_state(
    *,
    x_m: float,
    y_m: float,
    z_m: float,
    vx_m_s: float,
    vy_m_s: float,
    vz_m_s: float,
) -> CartesianState
```

位置单位 m，速度单位 m/s，与返回状态中的 `cartesian` 表示一致。

### `spherical_state`

```python
astrogator.spherical_state(
    *,
    right_ascension_deg: float,
    declination_deg: float,
    radius_m: float,
    horizontal_fpa_deg: float,
    velocity_azimuth_deg: float,
    velocity_magnitude_m_s: float,
) -> SphericalState
```

球面状态元素：赤经/赤纬/半径、水平飞行路径角、速度方位角与速度大小。该形式与笛卡尔形式的相互换算已经验证。

### `target_vector_out_state`

```python
astrogator.target_vector_out_state(
    *,
    radius_of_periapsis_km: float,
    c3_km2_s2: float,
    asymptote_ra_deg: float,
    asymptote_dec_deg: float,
    gravitational_parameter_m3_s2: float,
    velocity_azimuth_at_periapsis_deg: float = 0.0,
    true_anomaly_deg: float = 0.0,
) -> TargetVectorOutState
```

双曲出射渐近线元素。注意该形式沿用 ASTROX 的约定：`radius_of_periapsis_km` 单位为 km，`c3_km2_s2` 单位为 km²/s²，其余角度单位为 deg。SDK 发送前不做单位换算，请在调用时直接按 km 与 km²/s² 提供。

### `initial_state` 段

```python
astrogator.initial_state(
    name: str,
    state: InitialStateElement,
    *,
    epoch: str,
    coord_system_name: str = "Earth Inertial",
    dry_mass_kg: float = 500.0,
    fuel_mass_kg: float = 500.0,
    coefficient_of_drag: float | None = None,
    coefficient_of_srp: float | None = None,
    drag_area_m2: float | None = None,
    srp_area_m2: float | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> InitialStateSegment
```

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `name` | — | 段名称，会原样出现在结果中 |
| `state` | — | 上述四种状态元素之一 |
| `epoch` | — | 起始历元，UTC ISO 8601 字符串，如 `2026-01-01T00:00:00Z` |
| `coord_system_name` | — | 坐标系名称，默认 `Earth Inertial`。已验证路径使用该默认值，其他坐标系部分验证 |
| `dry_mass_kg` | kg | 干质量，默认 500 |
| `fuel_mass_kg` | kg | 燃料质量，默认 500 |
| `coefficient_of_drag` | — | 阻力系数。部分验证：请求与返回回显可构造，物理效果未独立校准 |
| `coefficient_of_srp` | — | 太阳辐射压系数。部分验证 |
| `drag_area_m2` | m² | 阻力面积。部分验证 |
| `srp_area_m2` | m² | 太阳辐射压面积。部分验证 |
| `results` | — | 标量结果定义列表，见「标量结果」一节 |

质量参数已经验证：段结果中的初始/最终干质量与燃料质量按请求值回显，机动段的燃料消耗从燃料质量中扣除。`description`、`user_comment` 与 `results` 对所有段通用，见「公共段参数」一节。

## 传播段与停止条件

### `propagate`

```python
astrogator.propagate(
    name: str,
    *,
    propagator_name: str,
    stop_conditions: Sequence[StoppingCondition],
    variable_names: str | None = None,
    max_propagation_time_s: float | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> PropagateSegment
```

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `propagator_name` | — | 必须与 `run_mcs(propagators=...)` 中注册的传播器名称一致 |
| `stop_conditions` | — | 停止条件列表，任一触发即停止（事件顺序已验证） |
| `variable_names` | — | 变量路径声明。部分验证：仅在差分修正场景有已验证的用法，见「差分修正」一节 |
| `max_propagation_time_s` | s | 最大传播时长。部分验证：超过时传播终止并置 `stopped_on_maximum_duration`，该标志的触发语义部分验证 |

传播结果返回 `PropagateResult`，其中 `stopping_condition_name` 是实际触发的停止条件名称，`duration_s` 是传播耗时。多个停止条件同时启用时，服务器返回先触发者的名称。

### 停止条件构造器

```python
astrogator.duration_stop(name: str, trip_s: float, *, tolerance_s: float = 1.0e-6, active: bool = True) -> DurationStop
astrogator.epoch_stop(name: str, trip_utc: str, *, active: bool = True) -> EpochStop
astrogator.periapsis_stop(
    name: str,
    *,
    gravitational_parameter_m3_s2: float,
    central_body_name: str = "Earth",
    repeat_count: int = 1,
    tolerance: float = 1.0e-6,
    active: bool = True,
) -> PeriapsisStop
astrogator.apoapsis_stop(
    name: str,
    *,
    gravitational_parameter_m3_s2: float,
    central_body_name: str = "Earth",
    repeat_count: int = 1,
    tolerance: float = 1.0e-6,
    active: bool = True,
) -> ApoapsisStop
```

| 构造器 | 参数 | 单位 | 说明 |
| --- | --- | --- | --- |
| `duration_stop` | `trip_s` | s | 相对段起始时刻的传播时长；已验证的用法为正值时长 |
| `duration_stop` | `tolerance_s` | s | 停止容差 |
| `epoch_stop` | `trip_utc` | — | 目标历元，UTC ISO 8601 字符串；到达目标历元时停止 |
| `periapsis_stop` | `gravitational_parameter_m3_s2` | m³/s² | 计算近地点事件使用的引力参数，必须显式提供 |
| `periapsis_stop` | `central_body_name` | — | 中心天体名称，默认 `Earth` |
| `periapsis_stop` | `repeat_count` | — | 事件重复次数，1 表示下一次 |
| `apoapsis_stop` | 同上 | — | 远地点事件，参数与近地点相同 |
| 全部 | `active` | — | 是否启用该停止条件 |

四种停止条件均已验证：`duration_stop` 在指定时长处停止并返回精确边界历元；`epoch_stop` 在目标历元处停止；`periapsis_stop` 在近地点停止（真近点角约为 0°），`apoapsis_stop` 在远地点停止（真近点角约为 180°）。`repeat_count` 大于 1 时等待第 N 次事件的用法部分验证。

## 机动段与发动机

### `impulsive_maneuver`

```python
astrogator.impulsive_maneuver(
    name: str,
    *,
    attitude_control: ImpulsiveAttitudeControl,
    propulsion_method_value: str,
    update_mass: bool = False,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> ImpulsiveManeuverSegment
```

冲量机动在瞬间施加速度增量。`propulsion_method_value` 是推进方法名称：`update_mass=False`（默认）时不消耗燃料，`FuelUsed == 0`，无需注册发动机（已验证路径使用 `"Constant_Thrust_Isp"`）；`update_mass=True` 时，服务器按名称查找推进方法，必须在 `run_mcs(engine_models=...)` 中注册名称一致的发动机，实际燃料消耗与估算值（火箭方程）一致。

### `finite_maneuver`

```python
astrogator.finite_maneuver(
    name: str,
    *,
    attitude_control: FiniteAttitudeControl,
    propagator_name: str,
    stop_conditions: Sequence[StoppingCondition],
    propulsion_method_value: str,
    thrust_efficiency: float = 1.0,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> FiniteManeuverSegment
```

有限机动持续一段物理时间，需要指定传播器与停止条件：点火期间使用 `propagator_name` 引用的传播器推进，直到 `stop_conditions` 触发。已验证的路径是：恒推力发动机（`constant_engine`）+ 自定义二体传播器（固定步长 RKF）+ 时长停止条件，且点火时长较短。有限机动始终消耗燃料，发动机名称通过 `propulsion_method_value` 引用。`thrust_efficiency` 参数可以传入，但其对结果的影响未经独立验证，不作为调节项推荐。

有限机动的积分设置会影响稳定性：自适应步长下长时间点火可能超时，已验证的用法采用固定小步长（如 0.1 s）与短时长（如 1 s）。

### 姿态控制构造器

冲量机动的姿态控制（`ImpulsiveAttitudeControl`）：

```python
astrogator.impulsive_velocity_vector(delta_v_m_s: float) -> ImpulsiveVelocityVector
astrogator.impulsive_anti_velocity_vector(delta_v_m_s: float) -> ImpulsiveAntiVelocityVector
```

这两个构造器已经验证：`impulsive_velocity_vector` 沿速度方向施加 `delta_v_m_s` 的速度增量，`impulsive_anti_velocity_vector` 沿速度反方向施加；返回的惯性/VNC 速度增量数组与独立向量重建一致。

```python
astrogator.impulsive_thrust_vector_cartesian(x_m_s: float, y_m_s: float, z_m_s: float, *, thrust_axes_name: str = "VNC(Earth)") -> ImpulsiveThrustVectorCartesian
astrogator.impulsive_thrust_vector_spherical(azimuth_deg: float, elevation_deg: float, magnitude_m_s: float, *, thrust_axes_name: str = "VNC(Earth)") -> ImpulsiveThrustVectorSpherical
astrogator.impulsive_attitude_quaternion(delta_v_m_s: float, *, qx: float = 0.0, qy: float = 0.0, qz: float = 0.0, qs: float = 1.0, reference_axes_name: str = "VNC(Earth)") -> ImpulsiveAttitudeQuaternion
astrogator.impulsive_attitude_euler(delta_v_m_s: float, a_deg: float, b_deg: float, c_deg: float, *, sequence: str = "313", reference_axes_name: str = "VNC(Earth)") -> ImpulsiveAttitudeEuler
```

推力矢量（笛卡尔/球面）与姿态（四元数/欧拉角）分支部分验证：请求可以成功执行并返回结果，但方向与姿态的参考系语义未经独立校准，不作为语义保证。

有限机动的姿态控制（`FiniteAttitudeControl`）：

```python
astrogator.finite_velocity_vector(*, attitude_update: str = "DuringBurn") -> FiniteVelocityVector
astrogator.finite_anti_velocity_vector(*, attitude_update: str = "DuringBurn") -> FiniteAntiVelocityVector
astrogator.finite_thrust_vector_cartesian(x: float, y: float, z: float, *, thrust_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteThrustVectorCartesian
astrogator.finite_thrust_vector_spherical(azimuth_deg: float, elevation_deg: float, magnitude: float, *, thrust_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteThrustVectorSpherical
astrogator.finite_attitude_quaternion(*, qx: float = 0.0, qy: float = 0.0, qz: float = 0.0, qs: float = 1.0, reference_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteAttitudeQuaternion
astrogator.finite_attitude_euler(a_deg: float, b_deg: float, c_deg: float, *, sequence: str = "313", reference_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteAttitudeEuler
```

`finite_velocity_vector` 已通过独立积分校验（沿当前速度方向点火）；其余有限姿态分支部分验证。

冲量推力矢量的分量与幅值单位为 m/s（参数名带 `_m_s` 后缀）。有限机动推力矢量的分量与幅值（`x`/`y`/`z`、`magnitude`）未经标定，SDK 不声明其单位；有限机动的推力大小由注册发动机模型的 `thrust_n` 提供。球面形式的角度单位为 deg。

### `constant_engine`

```python
astrogator.constant_engine(
    *,
    name: str,
    thrust_n: float,
    isp_s: float,
    gravitational_acceleration_m_s2: float = 9.80665,
) -> EngineConstant
```

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `name` | — | 发动机名称，机动段通过 `propulsion_method_value` 引用 |
| `thrust_n` | N | 恒定推力 |
| `isp_s` | s | 比冲 |
| `gravitational_acceleration_m_s2` | m/s² | 比冲换算使用的标准重力加速度，默认 9.80665 |

恒推力发动机已经验证：有限机动的燃料消耗满足 `FuelUsed = thrust_n / (isp_s * gravitational_acceleration_m_s2) * duration_s`，燃料质量边界与 `FuelUsed` 一致，有限机动的 `delta_v_magnitude_m_s` 满足齐奥尔科夫斯基方程；冲量机动开启质量更新时，实际燃料消耗与估算值一致。恒加速度发动机分支在服务端未实现，SDK 未提供构造器。

## 嵌套与目标序列

### `sequence`

```python
astrogator.sequence(name: str, segments: Sequence[MCSSegment], *, description: str | None = None, user_comment: str | None = None, results: Sequence[CalcScalar] | None = None) -> SequenceSegment
```

把一组段包成子序列。嵌套行为已经验证：返回 `SequenceResult`，其 `segment_results` 递归包含子段结果，子段顺序与请求一致，边界状态沿子序列传递。

### `target_sequence` 与差分修正

```python
astrogator.target_sequence(
    name: str,
    segments: Sequence[MCSSegment],
    *,
    action: str = "RunNominalSequence",
    profiles: Sequence[Profile] | None = None,
    continue_on_failure: str | None = None,
    when_profiles_finish: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> TargetSequenceSegment
```

`action="RunNominalSequence"`（默认）且不提供 `profiles` 时，目标序列按普通子序列执行，返回 `TargetSequenceResult` 与递归的子段结果，`operator_results` 为空；该模式已经验证，其结果形状与直接执行同一内层序列一致。`action` 的其他取值、`continue_on_failure` 与 `when_profiles_finish` 部分验证。

差分修正算子（`profiles`）的已验证用法是把传播段声明为变量载体，然后用差分修正器调节变量以满足约束：

```python
coast = astrogator.propagate(
    "Coast",
    propagator_name="Earth_HPOP_Example",
    stop_conditions=[astrogator.duration_stop("Duration", 60.0)],
    variable_names="StopConditions.Duration",
    results=[
        astrogator.keplerian_scalar(
            "FinalTA",
            "TrueAnomaly",
            gravitational_parameter_m3_s2=MU,
            coord_system_name="Earth Inertial",
        )
    ],
)
profile = astrogator.differential_corrector(
    "DC1",
    controls=[
        astrogator.differential_corrector_control(
            "StopConditions.Duration",
            10.0,
            parent_name="Coast",
            perturbation=1.0,
            max_step=600.0,
            tolerance=0.0001,
        )
    ],
    results=[
        astrogator.differential_corrector_constraint(
            "FinalTA", 36.0, parent_name="Coast", tolerance=0.1
        )
    ],
)
result = astrogator.run_mcs(
    [
        astrogator.initial_state("Init", initial_orbit, epoch=START),
        astrogator.target_sequence(
            "Target", [coast], action="RunActiveOperators", profiles=[profile]
        ),
    ],
    propagators=[config],
)
```

差分修正器的构造器：

```python
astrogator.differential_corrector_control(
    name: str,
    initial_value: float | str,
    *,
    parent_name: str,
    perturbation: float = 1.0,
    max_step: float = 600.0,
    tolerance: float = 1.0e-4,
    enable: bool = True,
) -> DifferentialCorrectorControl

astrogator.differential_corrector_constraint(
    name: str,
    desired_value: float | str,
    *,
    parent_name: str,
    tolerance: float = 0.1,
    enable: bool = True,
) -> DifferentialCorrectorConstraint

astrogator.differential_corrector(
    name: str,
    *,
    controls: Sequence[DifferentialCorrectorControl],
    results: Sequence[DifferentialCorrectorConstraint],
    maximum_iterations: int = 50,
    active: bool = True,
) -> DifferentialCorrector
```

已验证的约定：控制变量的 `name` 必须指向传播段停止条件的路径，以 `StopConditions.` 开头（如 `StopConditions.Duration`），而不是 `StoppingConditions.`；`parent_name` 是包含该停止条件的段名；被调节的传播段需要用 `variable_names` 声明同一个变量路径。约束的 `name` 引用段上注册的标量结果名。返回的 `DifferentialCorrectorResult` 提供 `converged`、`total_iterations`、控制变量轨迹与约束残差；在已验证的用法下，修正器收敛，`converged` 为 `True`，控制变量的最终值与约束的当前值在容差内满足约束。除此之外的算子配置部分验证。

### `stop`

```python
astrogator.stop(name: str, *, enable: bool = True, description: str | None = None, user_comment: str | None = None, results: Sequence[CalcScalar] | None = None) -> StopSegment
```

启用（默认）的 `stop` 段在到达时终止任务执行：该段自身及其后的段不产生段结果。`enable=False` 时该段透明，后续段正常执行。两种行为均已验证。

## 公共段参数

所有段构造器共享以下参数：

| 参数 | 说明 |
| --- | --- |
| `name` | 段名称，必须提供，原样出现在段结果中 |
| `description` | 描述文本。部分验证：作为元数据回显 |
| `user_comment` | 用户备注。部分验证：作为元数据回显 |
| `results` | 标量结果定义列表，见下节 |

## 标量结果

段可以通过 `results` 参数请求标量结果。已验证的标量构造器：

```python
astrogator.duration_scalar(name: str) -> DurationScalar
astrogator.epoch_scalar(name: str) -> EpochScalar
astrogator.keplerian_scalar(
    name: str, component_name: str, *, gravitational_parameter_m3_s2: float, coord_system_name: str, element_type: str = "Osculating",
) -> KeplerianScalar
astrogator.modified_keplerian_scalar(
    name: str, component_name: str, *, gravitational_parameter_m3_s2: float, coord_system_name: str,
) -> ModifiedKeplerianScalar
astrogator.spherical_scalar(name: str, component_name: str, *, coord_system_name: str) -> SphericalScalar
astrogator.point_scalar(name: str, component_name: str, *, coord_system_name: str) -> PointScalar
```

- `duration_scalar`：段的已耗时，秒。
- `epoch_scalar`：段的当前历元，UTC 字符串。
- `keplerian_scalar` / `modified_keplerian_scalar`：开普勒根数分量（如 `TrueAnomaly`、`SemiMajorAxis`），`component_name` 指定分量，`gravitational_parameter_m3_s2` 指定换算引力参数，`coord_system_name` 指定坐标系。已验证的分量值（如真近点角）与最终状态的独立换算一致。
- `spherical_scalar`：球面状态分量（如 `RightAscension`）。
- `point_scalar`：位置分量（如 `X`），`coord_system_name` 指定坐标系。

其余标量构造器：

```python
astrogator.cartographic_scalar(name: str, component_name: str, *, central_body_name: str) -> CartographicScalar
astrogator.delta_spherical_scalar(name: str, component_name: str, *, central_body_name: str, parent_central_body_name: str) -> DeltaSphericalScalar
astrogator.relative_scalar(name: str, calc_object: CalcScalar, *, reference_name: str | None = None) -> RelativeScalar
astrogator.b_plane_scalar(name: str, component_name: str, *, gravitational_parameter_m3_s2: float, central_body_name: str) -> BPlaneScalar
```

`cartographic_scalar` 部分验证：服务器返回值，但大地坐标的参考系旋转约定尚未完全解释，不作为语义保证。`delta_spherical_scalar`、`relative_scalar`、`b_plane_scalar` 未验证：构造器可以生成请求，但其结果的语义没有独立证据，不应在任务中依赖这些结果。

标量结果按名称出现在段结果的 `scalar_results` 字典中。值的形式随类型而变：数值标量直接是 `float`，`epoch_scalar` 是 UTC 字符串。

## 结果树

`run_mcs` 返回 `astrogator.RunMCSResult`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `is_success` | `bool` | 是否成功。服务器返回 `IsSuccess=false` 时传输层会抛出 `AstroxAPIError`，因此能拿到解析结果时该字段为 `True` |
| `message` | `str` | 服务器返回的消息文本。部分验证：仅为返回值的回显 |
| `main_sequence_results` | `tuple[SegmentResultValue, ...]` | 按执行顺序返回实际执行并产生输出的段结果。启用 Stop 时，Stop 段自身及其后的段不产生结果（见 `stop` 一节） |
| `positions` | `components.CzmlPositions | None` | CZML 位置采样。响应中包含该字段时解析为 `CzmlPositions`，否则为 `None`；未显式传 `compute_czml_positions` 时，是否返回由服务器默认决定（基线 OpenAPI 声明缺省为 `true`） |
| `unknown_fields` | `Mapping` | 解析器未消费的响应字段，原样保留 |

### 段结果

每个段结果共享以下字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `type_name` | `str` | 段类型名称，如 `InitialState`、`Propagate` |
| `wire_type` | `str | None` | 响应中的 `$type` 判别值（部分段结果没有该字段） |
| `name` | `str` | 请求中的段名称，原样回显 |
| `description` | `str | None` | 描述回显。部分验证 |
| `user_comment` | `str | None` | 备注回显。部分验证 |
| `initial_state` | `SegmentState` | 段起始状态 |
| `final_state` | `SegmentState` | 段结束状态 |
| `duration_s` | `float` | 段耗时，秒 |
| `scalar_results` | `Mapping` | 标量结果字典，键为请求的标量名称 |
| `unknown_fields` | `Mapping` | 未消费字段 |

按段类型返回的解析子类：

| 子类 | 附加字段 | 说明 |
| --- | --- | --- |
| `InitialStateResult` | — | 初始状态段结果，`duration_s == 0`，起始与结束状态相同 |
| `PropagateResult` | `stopped_on_maximum_duration`、`stopping_condition_name` | 传播段结果；`stopping_condition_name` 为触发的停止条件名称，`stopped_on_maximum_duration` 部分验证 |
| `ManeuverImpulsiveResult` | `maneuver_information` | 冲量机动结果 |
| `ManeuverFiniteResult` | `maneuver_information` | 有限机动结果 |
| `SequenceResult` | `segment_results` | 嵌套序列结果，子段结果递归展开 |
| `TargetSequenceResult` | `operator_results`、`segment_results` | 目标序列结果，算子轨迹与子段结果 |
| `FollowResult` | — | Follow 段结果类型。服务端当前无法产生该结果，见限制 |
| `SegmentResult` | — | 兜底基类 |

### 段状态 `SegmentState`

`initial_state` 与 `final_state` 是 `SegmentState`，同时包含多种表示：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `epoch` | `str` | 边界历元，UTC 字符串 |
| `coord_system_name` | `str` | 坐标系名称。部分验证：其表示的具体参考系含义未完全校准 |
| `cartesian` | `orbits.CartesianState` | 笛卡尔位置/速度，单位 m 与 m/s |
| `keplerian` | `ReturnedKeplerianState` | 开普勒根数表示，含 `period_s`（轨道周期，秒）与 `gravitational_parameter_m3_s2` |
| `spherical` | `ReturnedSphericalState` | 球面表示 |
| `dry_mass_kg` | `float` | 干质量 |
| `fuel_mass_kg` | `float` | 燃料质量 |
| `coefficient_of_drag` | `float` | 阻力系数。部分验证：为返回回显 |
| `coefficient_of_srp` | `float` | 太阳辐射压系数。部分验证 |
| `drag_area_m2` | `float` | 阻力面积。部分验证 |
| `srp_area_m2` | `float` | 太阳辐射压面积。部分验证 |
| `geodetic_latitude_deg` | `float` | 大地纬度。部分验证 |
| `geodetic_longitude_deg` | `float` | 大地经度。部分验证 |
| `geodetic_altitude_m` | `float` | 大地高度。部分验证 |
| `geocentric_latitude_deg` | `float` | 地心纬度。部分验证 |
| `geocentric_longitude_deg` | `float` | 地心经度。部分验证 |
| `unknown_fields` | `Mapping` | 未消费字段 |

笛卡尔、开普勒与球面三种表示之间已经过独立换算验证，可以互相核验。大地/地心经纬度字段服务器总是返回，但参考系约定部分验证。

### 机动信息 `ManeuverInformation`

冲量与有限机动结果的 `maneuver_information` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `start` / `stop` | `str` | 机动边界历元 |
| `duration_s` | `float` | 机动时长。冲量机动为 0 |
| `fuel_used_kg` | `float` | 实际燃料消耗。冲量机动 `update_mass=False` 时为 0 |
| `estimated_fuel_used_kg` | `float | None` | 估算燃料消耗，与火箭方程一致 |
| `delta_v_magnitude_m_s` | `float` | 标量速度增量大小。有限机动时等于火箭方程排气速度 |
| `delta_v_inertial` | `tuple[float, ...]` | 惯性系速度增量，六值数组 |
| `delta_v_vnc` | `tuple[float, ...]` | VNC 坐标速度增量，六值数组 |
| `maneuver_attitude_name` | `str` | 姿态实现名称 |
| `update_mass` | `bool | None` | 是否更新质量（有限机动不返回该字段） |
| `delta_v_body` | `tuple[float, ...] | None` | 本体坐标速度增量。服务器当前不返回该字段 |
| `quaternion` | `tuple[float, ...] | None` | 姿态四元数。服务器当前不返回该字段 |
| `unknown_fields` | `Mapping` | 未消费字段 |

六值数组的约定已经验证：前三个值是边界速度差（惯性系或 VNC 系，包含机动期间的重力作用），后三个值依次是前三个值的方位角、仰角与大小。`delta_v_magnitude_m_s` 只含推力贡献，不要与数组前三个值的模长混淆。

### CZML 位置

未提供 `compute_czml_positions` 时，SDK 不会把该字段发往 ASTROX，是否计算由服务器默认决定（基线 OpenAPI 声明缺省为 `true`）；显式 `compute_czml_positions=True` 时服务器计算采样，显式 `False` 时不计算。响应中没有位置数据时 `result.positions` 为 `None`。CZML 采样用于轨迹可视化（如 Cesium），已验证的 `INERTIAL` 帧采样与独立的二体传播逐点一致。

`components.CzmlPositions` 包含 `central_body` 与 `positions`（`tuple[components.CzmlPosition, ...]`）。每个 `CzmlPosition` 的字段：

| 字段 | 说明 |
| --- | --- |
| `epoch` | 采样起始历元 |
| `interval` | 采样时间区间 |
| `reference_frame` | 参考系，默认请求中的 `out_czml_frame_name` |
| `interpolation_algorithm` | 插值算法。部分验证：为服务器返回值 |
| `interpolation_degree` | 插值阶数。部分验证 |
| `cartesian` | 位置序列，当前为 `None` |
| `cartesian_velocity` | CZML 风格的 `[t, x, y, z, vx, vy, vz, ...]` 采样序列，每 7 个数一帧：时间偏移（秒）、位置 X/Y/Z（m）、速度 X/Y/Z（m/s） |

采样序列的布局与 `astrox.propagator` 返回的 `PropagatorPosition.cartesian_velocity` 一致，详见 [propagator 手册](../propagator/README.md)。

## 明确限制

- **Follow 段不可用**：`follow(...)` 构造器与 `entities`、`mission_position`、`entity_path` 可以构造请求，但 ASTROX 服务端当前无法执行 Follow 段（缺少所需的位置数据），任务会在创建 Follow 段时失败。不要把 Follow 段放入任务。
- **标量停止条件不支持**：基于标量阈值（如时长标量）的停止条件在服务端未实现，SDK 未提供对应构造器。
- **恒加速度发动机不支持**：该分支在服务端未实现，SDK 未提供构造器。
- **默认传播器名称不可用**：传播段必须引用显式注册的自定义传播器，不能引用内置名称。
- **已校准的二体路径必须显式提供引力参数**：RunMCS 中传播器重力模型与开普勒初始状态里的 `gravitational_parameter_m3_s2` 都必须显式提供，否则结果不可信或请求被拒绝。`hpop_two_body_gravity` 构造器本身允许省略该参数，但省略时不属于已校准的二体语义。
- **部分验证分支**：冲量/有限机动中的推力矢量与姿态分支、有限机动反速度方向分支、`thrust_efficiency`、非 `Earth` 中心天体、非 `INERTIAL` 的 CZML 输出帧、`cartographic_scalar`、`delta_spherical_scalar`、`relative_scalar`、`b_plane_scalar` 及大地/地心坐标字段均部分验证或未验证，SDK 不为这些分支的语义提供保证。

## 错误处理

所有 ASTROX 错误都继承 `astrox.exceptions.AstroxError`。服务器响应 `IsSuccess=false` 时 `run_mcs` 抛出 `AstroxAPIError`；HTTP 4xx/5xx 抛 `AstroxHTTPError`；请求超时抛 `AstroxTimeoutError`；连接失败抛 `AstroxConnectionError`。这四个异常是 `AstroxError` 下的并列分支，不存在子类关系。SDK 不隐藏或改写服务器错误信息。解析器遇到必需字段缺失时抛出 `KeyError`，字段类型不符时抛出 `TypeError`。需要完整原始响应时，请直接使用 `astrox.raw.post`。

## 完整示例

可运行的完整示例见 `examples/07_astrogator/run_mcs.py`，任务指南见 [如何运行一个 Astrogator 任务序列](../../how_to/run_an_astrogator_mcs.md)。
