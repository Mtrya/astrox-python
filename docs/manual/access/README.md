# 访问

`astrox.access` 计算两个命名对象（entity）之间的访问区间（access interval），也可以把多个命名对象与命名对象组（entity group）串成多跳链路（chain）求解端到端访问。推荐导入方式：

```python
from astrox import access, components
```

所有访问函数都接收 `components` 构造的命名对象，返回 ASTROX 原始响应字典。SDK 只负责把 Python 参数组装成 ASTROX 请求片段并转发服务器结果，不对响应做二次解析。

## 直接访问

### `access.compute`

```python
access.compute(
    *,
    start: str,
    stop: str,
    from_entity: components.Entity,
    to_entity: components.Entity,
    step_s: float | None = None,
    compute_aer: bool | None = None,
    use_light_time_delay: bool | None = None,
) -> dict[str, Any]
```

计算从 `from_entity` 到 `to_entity` 的直接访问。两个参数都必须是 `components.entity(...)` 构造的命名对象；字符串、原始字典或命名对象组会被 SDK 拒绝。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 计算起始时间字符串，ISO 8601 格式 |
| `stop` | — | 计算结束时间字符串，ISO 8601 格式 |
| `from_entity` | — | 起始命名对象，`components.Entity` 值 |
| `to_entity` | — | 目标命名对象，`components.Entity` 值 |
| `step_s` | s | 输出采样步长，对应 ASTROX 的 `OutStep` |
| `compute_aer` | — | 是否请求 AER 输出；`True` 时每个访问区间附带 AER 数据 |
| `use_light_time_delay` | — | 是否启用光行时（light-time）选项 |

返回字典包含 `IsSuccess`、`Message`、`Passes` 三个字段。`Passes` 是访问区间列表，每个区间的字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `AccessStart` | `str` | 区间开始时间 |
| `AccessStop` | `str` | 区间结束时间 |
| `Duration` | `float` | 区间持续时间，单位 s |
| `AccessBeginData` | `dict` | 区间开始处的 AER 数据（仅在 `compute_aer=True` 时出现） |
| `AccessEndData` | `dict` | 区间结束处的 AER 数据（仅在 `compute_aer=True` 时出现） |
| `AllDatas` | `list[dict]` | 区间内按 `step_s` 采样的 AER 数据（仅在 `compute_aer=True` 时出现） |
| `MaxElevationData` | `dict` | 最大仰角样本（仅在 `compute_aer=True` 时出现） |
| `MinElevationData` | `dict` | 最小仰角样本（仅在 `compute_aer=True` 时出现） |
| `MaxRangeData` | `dict` | 最大距离样本（仅在 `compute_aer=True` 时出现） |
| `MinRangeData` | `dict` | 最小距离样本（仅在 `compute_aer=True` 时出现） |

AER 数据行中的 `Azimuth`、`Elevation` 单位为 deg，`Range` 单位为 m，`Time` 为 ISO 8601 字符串；当 `compute_aer` 省略或为 `False` 时，上述 AER 字段不会出现。

```python
ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

ground = components.entity(
    name="Ground",
    position=components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
)
iss = components.entity(
    name="ISS",
    position=components.sgp4_position(tle_lines=ISS_TLE),
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    from_entity=ground,
    to_entity=iss,
    step_s=600.0,
    compute_aer=True,
)

print(f"Direct access intervals: {len(result['Passes'])}")
```

完整可运行示例见 `examples/04_access/compute.py`。

## 约束与传感器

`access.compute(...)` 没有独立的 `constraints=` 参数；约束通过命名对象的 `constraints` 列表传入，随对象一起发往 ASTROX。可使用的约束包括仰角约束、距离约束、方位-仰角遮罩约束、太阳排除角约束和月球排除角约束，详见 [components 手册](../components/README.md)。

```python
constrained_ground = components.entity(
    name="Ground",
    position=components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
    constraints=[
        components.elevation_constraint(minimum_deg=10.0),
        components.range_constraint(maximum_km=2500.0, maximum_enabled=True),
    ],
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    from_entity=constrained_ground,
    to_entity=iss,
    step_s=60.0,
    compute_aer=True,
)
```

完整可运行示例见 `examples/04_access/constraints.py`。

如果访问应由航天器传感器视场决定，可在起始命名对象上附加 `orientation`、`sensor` 和 `sensor_pointing`：

```python
observer = components.entity(
    name="ObserverSat",
    position=components.two_body_position(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T02:00:00.000Z",
        step_s=120.0,
    ),
    orientation=components.vvlh_axes(),
    sensor=components.conic_sensor(outer_half_angle_deg=8.0),
    sensor_pointing=components.fixed_sensor_pointing(
        rotation=components.quaternion_rotation(
            scalar=1.0,
            x=0.0,
            y=0.0,
            z=0.0,
        ),
    ),
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T02:00:00.000Z",
    from_entity=observer,
    to_entity=target_site,
    step_s=120.0,
    compute_aer=True,
)
```

完整可运行示例见 `examples/04_access/sensor_pointing.py`、`examples/04_access/custom_axes.py`。

## 访问链路

### `access.chain`

```python
access.chain(
    *,
    start: str,
    stop: str,
    participants: Sequence[components.Entity | components.EntityGroup],
    start_participant: components.Entity | components.EntityGroup | str,
    end_participant: components.Entity | components.EntityGroup | str,
    connections: Sequence[Connection] | None = None,
    use_light_time_delay: bool | None = None,
) -> dict[str, Any]
```

在显式给出的参与者之间计算多跳访问链路。`participants` 列出所有可用对象，可以是命名对象或命名对象组；`start_participant` 和 `end_participant` 可以是这些对象本身，也可以是它们的名称字符串。

| 参数 | 说明 |
| --- | --- |
| `start` | 计算起始时间字符串 |
| `stop` | 计算结束时间字符串 |
| `participants` | 所有参与对象，元素为 `Entity` 或 `EntityGroup` |
| `start_participant` | 链路起点，可以是对象、对象组或名称字符串 |
| `end_participant` | 链路终点，可以是对象、对象组或名称字符串 |
| `connections` | 显式连接列表；省略时发送直接链路形式 |
| `use_light_time_delay` | 是否启用光行时选项 |

返回字典包含以下字段：

| 字段 | 说明 |
| --- | --- |
| `IsSuccess` | 是否成功 |
| `Message` | 服务器消息 |
| `ComputedStrands` | 实际计算的链路列表，每项为名称序列 |
| `CompleteChainAccess` | 整条链路的访问区间列表 |
| `IndividualStrandAccess` | 每条链路段的访问区间，键为 `"A>B"` 或 `"A>B>C"` 形式的字符串 |
| `IndividualObjectAccess` | 每个单独对象的访问区间，键为对象名称 |

### 命名对象组与限制语义

命名对象组通过 `components.entity_group(...)` 构造，可在链路中把多个对象当作一个端点。`from_restriction` 与 `to_restriction` 的可选值为 `"AnyOf"` 或 `"AtLeastN"`：

- `"AnyOf"`：只要组内任一成员满足访问条件即可。
- `"AtLeastN"`：需要至少 `from_number` 或 `to_number` 个成员同时满足条件；使用此值时必须同时提供对应的数量参数。

```python
targets = components.entity_group(
    name="Targets",
    members=[iss, hubble],
    to_restriction="AnyOf",
)

group_chain = access.chain(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    participants=[ground, targets],
    start_participant=ground,
    end_participant=targets,
)
```

### 显式连接

当需要指定链路必须经过哪些方向性连接时，使用 `access.connection(...)` 构造 `Connection` 列表：

```python
access.connection(
    from_participant: Entity | EntityGroup | str,
    to_participant: Entity | EntityGroup | str,
    *,
    min_uses: int | None = None,
    max_uses: int | None = None,
) -> Connection
```

`from_participant` 和 `to_participant` 可以是对象、对象组或名称字符串；`min_uses` 与 `max_uses` 会原样转发给 ASTROX。`connections=[]` 会被保留为空列表，而不是改写为直接链路形式。

```python
explicit_chain = access.chain(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    participants=[ground, iss, hubble],
    start_participant=ground,
    end_participant=hubble,
    connections=[
        access.connection(ground, iss),
        access.connection(iss, hubble),
    ],
)
```

完整可运行示例见 `examples/04_access/chain.py`。

## 可组合的位置源

访问计算本身不限制位置源类型，任何 `components` 支持的位置源都可以嵌入到命名对象中：地面站、SGP4 两行根数、J2/二体/HPOP 传播位置、CZML 采样位置、简单上升、弹道轨迹、中心天体等。各位置源的构造方式与单位请参阅 [components 手册](../components/README.md)。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，访问函数会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会改写服务器错误信息。需要完全控制请求载荷或处理原始响应时，请使用 `astrox.raw.post`。

## 约定说明

- 可选参数在未提供时不会被发往 ASTROX，由服务器保留默认值。
- `compute_aer=True` 才会在每个访问区间中产生 AER 数据；省略或显式设为 `False` 时只返回区间起止。
- 约束必须作为命名对象的字段传入，`access.compute(...)` 不接受独立的约束参数。
- 链路中的名称引用会原样转发给 ASTROX；SDK 不检查字符串名称是否出现在 `participants` 中。
