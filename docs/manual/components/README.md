# 组件

`astrox.components` 提供 ASTROX 分析对象的公共词汇表：命名对象、位置源、传感器、约束、姿态轴系、旋转以及矢量几何工具（VGT）。这些值对象本身不发起网络请求，只负责把 Python 参数组装成 ASTROX 可识别的请求片段。推荐按如下方式导入：

```python
from astrox import components
```

组件通常嵌入到 `astrox.access` 的访问计算、覆盖计算等请求中。本页按概念分组介绍每个公开构造器及其参数；各端点如何使用这些值，请参阅 [access 手册](../access/README.md) 与 [propagator 手册](../propagator/README.md)。

所有构造器均使用 `snake_case` 参数名，带单位的参数使用 `_m`、`_deg`、`_s`、`_km` 等显式后缀。未提供的可选参数不会发往 ASTROX，由服务器保留默认值。每个值对象都有 `to_wire()` 方法，可在需要时查看生成的请求片段；普通 SDK 调用直接传入值对象即可。

## 命名对象

### `components.entity`

```python
components.entity(
    *,
    name: str,
    position: EntityPosition,
    description: str | None = None,
    vgt: VgtProvider | None = None,
    orientation: EntityAxes | None = None,
    sensor: EntitySensor | None = None,
    sensor_pointing: SensorPointing | None = None,
    constraints: Sequence[Constraint] | None = None,
) -> Entity
```

`entity` 构造一个命名对象（Entity），它是位置源与元数据的组合。`Entity` 是冻结数据类，字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `str` | 对象名称，在访问链路中用于标识该对象 |
| `position` | `EntityPosition` | 位置源，必填 |
| `description` | `str \| None` | 描述 |
| `vgt` | `VgtProvider \| None` | 附着的 VGT 命名几何定义 |
| `orientation` | `EntityAxes \| None` | 命名对象的姿态轴系 |
| `sensor` | `EntitySensor \| None` | 传感器形状 |
| `sensor_pointing` | `SensorPointing \| None` | 传感器指向 |
| `constraints` | `tuple[Constraint, ...] \| None` | 约束条件 |

```python
satellite = components.entity(
    name="ISS",
    position=components.sgp4_position(
        tle_lines=(
            "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
            "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
        )
    ),
    description="Representative spacecraft",
)
```

### `components.entity_group`

```python
components.entity_group(
    *,
    name: str,
    members: Sequence[Entity],
    from_restriction: str | None = None,
    from_number: int | None = None,
    to_restriction: str | None = None,
    to_number: int | None = None,
) -> EntityGroup
```

`entity_group` 把多个命名对象组合成一个命名对象组（EntityGroup），用于访问链路等需要成组参与者的场景。`from_restriction` 与 `to_restriction` 的可选值为 `"AnyOf"` 或 `"AtLeastN"`；当取值 `"AtLeastN"` 时，需同时提供对应的 `from_number` 或 `to_number`。

```python
targets = components.entity_group(
    name="Targets",
    members=[satellite],
    to_restriction="AnyOf",
)
```

### `astrox.access.connection`

访问链路的显式连接片段由 `astrox.access.connection` 构造，对应类型为 `astrox.access.Connection`。它不在 `astrox.components` 中导出，但与命名对象组配合使用：

```python
from astrox import access, components

link = access.connection(ground, satellite)
```

`connection` 的完整签名与用法见 [access 手册](../access/README.md)。

## 位置源

位置源描述对象随时间变化的空间位置，是命名对象的 `position` 字段。`astrox.components` 中的位置源与 `astrox.propagator` 中的传播函数一一对应，但属于组件层的值对象，用于嵌入访问等请求。

### 地面站位置

```python
components.site_position(
    *,
    longitude_deg: float,
    latitude_deg: float,
    height_m: float,
    central_body: str | None = None,
    clamp_to_ground: bool | None = None,
    height_above_ground_m: float | None = None,
) -> SitePosition
```

`site_position` 用大地经纬度高描述固定地面站。`longitude_deg`、`latitude_deg` 为角度，`height_m` 为海拔高度（米）。

```python
site = components.site_position(
    longitude_deg=-155.468,
    latitude_deg=19.821,
    height_m=4205.0,
)
```

### CZML 采样位置

```python
components.czml_position(
    *,
    epoch: str,
    central_body: str | None = None,
    interpolation_algorithm: str | None = None,
    interpolation_degree: int | None = None,
    reference_frame: str | None = None,
    interval: str | None = None,
    cartesian: Sequence[float] | None = None,
    cartesian_velocity: Sequence[float] | None = None,
) -> CzmlPosition
```

`czml_position` 用 CZML 风格的采样序列描述位置。`cartesian` 为 `[t, x, y, z, ...]` 形式，`cartesian_velocity` 为 `[t, x, y, z, vx, vy, vz, ...]` 形式。

```python
sampled = components.czml_position(
    epoch="2024-01-01T00:00:00.000Z",
    reference_frame="INERTIAL",
    cartesian_velocity=[
        0.0, 7000000.0, 0.0, 0.0, 0.0, 7500.0, 0.0,
    ],
)
```

### 复合 CZML 位置

```python
components.czml_positions(
    positions: Sequence[CzmlPosition],
    *,
    central_body: str | None = None,
) -> CzmlPositions
```

`czml_positions` 把多个 `CzmlPosition` 组合成一个复合位置源。

```python
track = components.czml_positions([sampled], central_body="Earth")
```

### 中心天体位置

```python
components.central_body_position(name: str) -> CentralBodyPosition
```

`central_body_position` 构造一个以指定中心天体本身为位置源的值。

```python
sun = components.central_body_position("Sun")
```

### 传播型位置源

以下构造器的参数与 `astrox.propagator` 中同名传播函数一致，区别是返回组件值对象而非直接发起传播请求。完整参数含义与单位请参阅 [propagator 手册](../propagator/README.md)。

```python
components.j2_position(
    *,
    orbit_epoch: str,
    orbit: KeplerianElements,
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
    j2_normalized_value: float | None = None,
    ref_distance_m: float | None = None,
) -> J2Position

components.two_body_position(
    *,
    orbit_epoch: str,
    orbit: KeplerianElements,
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
) -> TwoBodyPosition

components.sgp4_position(
    *,
    tle_lines: tuple[str, str] | list[str],
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    satellite_number: str | None = None,
) -> Sgp4Position
```

```python
j2 = components.j2_position(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    step_s=300.0,
)

iss = components.sgp4_position(
    tle_lines=(
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
        "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    ),
)
```

### HPOP、简单上升与弹道位置源

```python
components.hpop_position(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements | None = None,
    state: CartesianState | None = None,
    config: HpopConfig | Mapping[str, Any] | None = None,
    coord_epoch: str | None = None,
    coord_system: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coefficient_of_drag: float | None = None,
    area_mass_ratio_drag_m2_kg: float | None = None,
    coefficient_of_srp: float | None = None,
    area_mass_ratio_srp_m2_kg: float | None = None,
) -> HpopPosition

components.simple_ascent_position(
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
) -> SimpleAscentPosition

components.ballistic_position(
    *,
    start: str,
    ballistic_type: str,
    ballistic_type_value: float,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_latitude_deg: float | None = None,
    impact_longitude_deg: float | None = None,
    impact_altitude_m: float | None = None,
) -> BallisticPosition
```

`hpop_position` 的 `orbit` 与 `state` 必须且只能提供一个；`config` 可以是 `propagator.hpop_config(...)` 对象，也可以是已知 ASTROX 结构的原始字典映射。`ballistic_position` 的 `ballistic_type` 与 `ballistic_type_value` 对应 propagator 中不同弹道求解分支：

| `ballistic_type` | `ballistic_type_value` 含义 |
| --- | --- |
| `"DeltaV"` | 速度增量 `delta_v_m_s` |
| `"MinEccentricity"` | 速度增量 `delta_v_m_s` |
| `"ApogeeAltitude"` | 远地点高度 `apogee_altitude_m` |
| `"TimeOfFlight"` | 飞行时间 `time_of_flight_s` |

弹道传播的完整分支说明见 [propagator 手册](../propagator/README.md)。

```python
ascent = components.simple_ascent_position(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    launch_latitude_deg=40.0,
    launch_longitude_deg=100.0,
    launch_altitude_m=1000.0,
    burnout_velocity_m_s=7800.0,
    burnout_latitude_deg=41.0,
    burnout_longitude_deg=101.0,
    burnout_altitude_m=200000.0,
)

ballistic = components.ballistic_position(
    start="2024-01-01T00:00:00.000Z",
    ballistic_type="DeltaV",
    ballistic_type_value=5000.0,
)
```

## 传感器与传感器指向

### 圆锥传感器与矩形传感器

```python
components.conic_sensor(
    *,
    inner_half_angle_deg: float | None = None,
    outer_half_angle_deg: float | None = None,
    minimum_clock_angle_deg: float | None = None,
    maximum_clock_angle_deg: float | None = None,
    text: str | None = None,
) -> ConicSensor

components.rectangular_sensor(
    *,
    x_half_angle_deg: float | None = None,
    y_half_angle_deg: float | None = None,
    text: str | None = None,
) -> RectangularSensor
```

角度参数单位为度。`outer_half_angle_deg` 是圆锥传感器最常用的半张角；矩形传感器用 `x_half_angle_deg` 与 `y_half_angle_deg` 分别描述两个方向的半张角。

```python
camera = components.conic_sensor(outer_half_angle_deg=30.0)
rect_camera = components.rectangular_sensor(
    x_half_angle_deg=5.0,
    y_half_angle_deg=10.0,
)
```

### 固定传感器指向

```python
components.fixed_sensor_pointing(
    *,
    rotation: Rotation,
    text: str | None = None,
) -> FixedSensorPointing
```

`fixed_sensor_pointing` 用旋转片段定义传感器相对于载体轴系的固定指向。`Rotation` 可以是 `az_el_rotation`、`quaternion_rotation` 或 `euler_rotation`。

```python
sensor_pointing = components.fixed_sensor_pointing(
    rotation=components.quaternion_rotation(
        scalar=1.0,
        x=0.0,
        y=0.0,
        z=0.0,
    ),
)
```

### 指向方向

```python
components.ra_dec_direction(
    *,
    ra_deg: float,
    dec_deg: float,
    magnitude: float | None = None,
) -> RaDecDirection

components.xyz_direction(
    *,
    x: float,
    y: float,
    z: float,
) -> XyzDirection
```

`ra_dec_direction` 与 `xyz_direction` 用于构造 VGT 固定矢量的方向，见下文 [矢量几何工具 VGT](#矢量几何工具-vgt)。

## 约束

约束作为 `Entity.constraints` 列表嵌入命名对象，被访问等计算使用。

### 仰角约束

```python
components.elevation_constraint(
    *,
    minimum_deg: float | None = None,
    maximum_deg: float | None = None,
    maximum_enabled: bool | None = None,
    text: str | None = None,
) -> ElevationConstraint
```

角度单位为度。`maximum_deg` 仅在同时提供 `maximum_enabled=True` 时才会生效。

### 距离约束

```python
components.range_constraint(
    *,
    minimum_km: float | None = None,
    maximum_km: float | None = None,
    maximum_enabled: bool | None = None,
    text: str | None = None,
) -> RangeConstraint
```

距离单位为千米。`maximum_km` 仅在同时提供 `maximum_enabled=True` 时才会生效。

### 方位-仰角遮罩约束

```python
components.az_el_mask_constraint(
    *,
    az_el_mask_rad: Sequence[float],
    max_range_km: float | None = None,
    text: str | None = None,
) -> AzElMaskConstraint
```

`az_el_mask_rad` 为交替排列的方位角与仰角采样序列，单位为弧度。该约束只对 `SitePosition` 位置源有效。

### 太阳/月球排除角约束

```python
components.sun_exclusion_angle_constraint(
    *,
    minimum_deg: float | None = None,
    text: str | None = None,
) -> SunExclusionAngleConstraint

components.moon_exclusion_angle_constraint(
    *,
    minimum_deg: float | None = None,
    text: str | None = None,
) -> MoonExclusionAngleConstraint
```

角度单位为度，表示被约束对象与太阳/月球方向之间的最小允许夹角。

```python
constraints = [
    components.elevation_constraint(minimum_deg=10.0),
    components.range_constraint(maximum_km=2500.0, maximum_enabled=True),
    components.az_el_mask_constraint(az_el_mask_rad=[0.0, 0.1]),
    components.sun_exclusion_angle_constraint(minimum_deg=25.0),
    components.moon_exclusion_angle_constraint(minimum_deg=15.0),
]
```

## 姿态轴系

命名对象级姿态轴系用于描述命名对象的体轴或参考坐标系。`astrox.components` 用 `Axes` 表示这一层，与下文旋转片段 `Rotation` 区分。

### 轨道相关轴系

```python
components.vvlh_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> VvlhAxes

components.lvlh_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> LvlhAxes

components.vnc_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> VncAxes
```

`relative_to` 的可选值为 `"Earth"`、`"Moon"`、`"Mars"`、`"Sun"`、`"CBF"`。若被其他轴系或 VGT 矢量引用，必须通过 `name` 参数命名。

```python
body_axes = components.vvlh_axes(name="BodyVVLH")
lvlh = components.lvlh_axes()
vnc = components.vnc_axes(relative_to="Earth")
```

### 固定轴系与历元固定轴系

```python
components.fixed_axes(
    *,
    reference_axes: EntityAxes | str,
    rotation: Rotation,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> FixedAxes

components.fixed_at_epoch_axes(
    *,
    source_axes: EntityAxes | str,
    reference_axes: EntityAxes | str,
    epoch: str,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> FixedAtEpochAxes
```

`fixed_axes` 把参考轴系按给定旋转固定。`fixed_at_epoch_axes` 在指定历元把源轴系冻结到参考轴系。被引用的 `EntityAxes` 对象必须已命名。

```python
camera_axes = components.fixed_axes(
    reference_axes=body_axes,
    rotation=components.euler_rotation(
        sequence="321",
        a_deg=0.0,
        b_deg=-20.0,
        c_deg=0.0,
    ),
    name="CameraAxes",
)

frozen = components.fixed_at_epoch_axes(
    source_axes=camera_axes,
    reference_axes="ICRF",
    epoch="2024-01-01T00:00:00.000Z",
)
```

### 对齐约束轴系

```python
components.aligned_and_constrained_axes(
    *,
    principal: VgtVector | str,
    principal_axis: str,
    reference: VgtVector | str,
    reference_axis: str,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> AlignedAndConstrainedAxes
```

`principal_axis` 与 `reference_axis` 的可选值为 `"+X"`、`"-X"`、`"+Y"`、`"-Y"`、`"+Z"`、`"-Z"`。该轴系使 `principal_axis` 对齐到 `principal` 矢量方向，同时让 `reference_axis` 尽量指向 `reference` 矢量方向。

### CZML 轴系与组合轴系

```python
components.czml_axes(
    *,
    epoch: str,
    unit_quaternion_xyzw: Sequence[float],
    central_body: str | None = None,
    interpolation_algorithm: str | None = None,
    interpolation_degree: int | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> CzmlAxes

components.composite_axes(
    *,
    intervals: Sequence[EntityAxes],
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> CompositeAxes
```

`czml_axes` 用 CZML 风格的单位四元数采样序列描述姿态，四元数顺序为 `xyzw`。`composite_axes` 把多个轴系按时间区间拼接。

```python
czml_attitude = components.czml_axes(
    epoch="2024-01-01T00:00:00.000Z",
    unit_quaternion_xyzw=[0.0, 0.0, 0.0, 1.0],
    central_body="Earth",
)

piecewise = components.composite_axes(
    intervals=[
        components.vvlh_axes(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T00:00:20.000Z",
        ),
        camera_axes,
    ],
)
```

## 旋转

旋转片段用于 `fixed_axes` 的 `rotation` 参数、传感器指向，以及其它需要小姿态偏移的地方。

### 方位-仰角旋转

```python
components.az_el_rotation(
    *,
    azimuth_deg: float,
    elevation_deg: float,
) -> AzElRotation
```

### 四元数旋转

```python
components.quaternion_rotation(
    *,
    scalar: float,
    x: float,
    y: float,
    z: float,
) -> QuaternionRotation
```

参数为标量在前、向量在后的顺序；SDK 将其转换为 ASTROX 的 `QS/QX/QY/QZ` 字段。

### 欧拉旋转

```python
components.euler_rotation(
    *,
    sequence: str,
    a_deg: float,
    b_deg: float,
    c_deg: float,
) -> EulerRotation
```

`sequence` 为旋转顺序字符串，如 `"321"`、 `"123"`。

```python
az_el = components.az_el_rotation(azimuth_deg=0.0, elevation_deg=-20.0)
quat = components.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0)
euler = components.euler_rotation(sequence="321", a_deg=0.0, b_deg=-20.0, c_deg=0.0)
```

## 矢量几何工具 VGT

VGT（Vector Geometry Tool）是附在命名对象上的命名几何定义集合，通过 `entity(..., vgt=...)` 使用。`VgtProvider` 是 `vgt(...)` 构造器返回的值对象。

```python
components.vgt(
    *,
    axes: Sequence[EntityAxes],
    vectors: Sequence[VgtVector] | None = None,
    points: Sequence[VgtPoint] | None = None,
    systems: Sequence[VgtSystem] | None = None,
    angles: Sequence[VgtAngle] | None = None,
    planes: Sequence[VgtPlane] | None = None,
) -> VgtProvider
```

`axes` 必填，其余集合可选。集合中的元素必须提供 `name`，以便在轴系定义中被引用。

### 固定矢量

```python
components.vgt_fixed_vector(
    *,
    name: str,
    reference_axes: EntityAxes | str,
    direction: VgtDirection,
    description: str | None = None,
) -> VgtFixedVector
```

`direction` 为 `xyz_direction(...)` 或 `ra_dec_direction(...)`。

### 点、系统、角与平面

```python
components.vgt_point(
    *,
    name: str,
    description: str | None = None,
) -> VgtPoint

components.vgt_system(
    *,
    name: str,
    description: str | None = None,
) -> VgtSystem

components.vgt_angle(
    *,
    name: str,
    from_vector: VgtVector | str,
    to_vector: VgtVector | str,
    description: str | None = None,
) -> VgtAngle

components.vgt_plane(
    *,
    name: str,
    plane_type: str | None = None,
    description: str | None = None,
) -> VgtPlane
```

### 完整示例

```python
body_axes = components.vvlh_axes(name="BodyVVLH")

boresight = components.vgt_fixed_vector(
    name="Boresight",
    reference_axes=body_axes,
    direction=components.xyz_direction(x=0.0, y=0.0, z=1.0),
)

clock = components.vgt_fixed_vector(
    name="Clock",
    reference_axes=body_axes,
    direction=components.xyz_direction(x=1.0, y=0.0, z=0.0),
)

sensor_axes = components.aligned_and_constrained_axes(
    name="AlignedCamera",
    principal=boresight,
    principal_axis="+Z",
    reference=clock,
    reference_axis="+X",
)

observer = components.entity(
    name="Observer",
    position=components.two_body_position(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
    ),
    vgt=components.vgt(
        axes=[body_axes],
        vectors=[boresight, clock],
    ),
    orientation=sensor_axes,
)
```

## 组合到访问请求

组件值对象通常直接传给 `astrox.access.compute` 或 `astrox.access.chain`：

```python
from astrox import access, components

satellite = components.entity(
    name="ISS",
    position=components.sgp4_position(tle_lines=ISS_TLE),
)

ground = components.entity(
    name="Ground",
    position=components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    from_entity=ground,
    to_entity=satellite,
    step_s=600.0,
)
```

完整示例见 `examples/04_access/compute.py`、`constraints.py`、`custom_axes.py`、`sensor_pointing.py` 与 `chain.py`。访问计算的语义与返回值说明见 [access 手册](../access/README.md)。

## 约定说明

- 可选参数在未提供时不会被发往 ASTROX，由服务器保留默认值。
- 被其它轴系或 VGT 定义引用的 `EntityAxes` 与 `VgtVector` 对象必须提供 `name`。
- `az_el_mask_constraint` 的 `az_el_mask_rad` 单位为弧度，且只对 `SitePosition` 有效。
- `range_constraint` 使用千米，仰角与排除角约束使用度。
- `quaternion_rotation` 使用标量在前的 Python 参数顺序。
