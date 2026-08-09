# 天体星历、坐标轴旋转与 Lambert 转移窗口

`astrox.celestial` 提供天体星历与天体坐标系旋转的只读查询 API，以及天体间 Lambert 转移窗口计算：`celestial.ephemeris` 计算目标天体在时间窗口内的星历（`start`/`stop` 可选，省略时由服务端选择当年 1 月 1 日至 12 月 31 日），`celestial.cb_axes_rotation` 计算两个中心天体坐标轴之间的旋转，`celestial.mpc_ephemeris` 计算小行星（MPC 数据）星历，`celestial.lambert_transfer_window` 在出发/到达时间窗口上采样并返回每条 Lambert 转移结果。推荐导入方式：

```python
from astrox import celestial
```

四个函数都通过 `astrox.raw.post` 发出 HTTP POST 请求，返回原始 JSON 响应字典，不做 typed response 解析；返回中移除了传输层状态包装字段 `IsSuccess` 与 `Message`，保留其余服务器字段。服务端返回不成功响应（`IsSuccess=false`）时由 HTTP 层抛出 `astrox.exceptions.AstroxAPIError`（见下文错误处理）。星历输出是 CZML Position 结构：位置与速度打包在 `cartesianVelocity` 数组中，每个样本为 7 个数值 `[Time, X, Y, Z, dX, dY, dZ]`，其中 `Time` 是相对历元时刻的秒数，位置单位为 m、速度单位为 m/s。响应在 `Position.CentralBody` 中声明坐标中心天体、在 `referenceFrame` 中声明参考系；SDK 只转述响应自身的声明，不对服务端内部星历内核的绝对正确性作断言。

## 目标天体星历

### `celestial.ephemeris`

```python
celestial.ephemeris(
    *,
    target_name: str,
    start: str | None = None,
    stop: str | None = None,
    observer_name: str | None = None,
    observer_frame: str | None = None,
    step_s: float | None = None,
) -> dict[str, Any]
```

计算目标天体在时间窗口内的星历，返回原始 JSON 响应字典。`start` 与 `stop` 可选，省略时由服务端选择当年 1 月 1 日至 12 月 31 日作为窗口。

| 参数 | wire 参数 | 说明 |
| --- | --- | --- |
| `target_name` | `TargetName` | 目标天体名称，如 `Moon`、`Mars`（服务端支持 `Moon`、`Mars`、`Venus`、`Mercury`、`Jupiter`、`Saturn`、`Uranus`、`Neptune` 等） |
| `start` | `Start` | 分析开始时刻（UTC，`yyyy-MM-ddTHH:mm:ssZ`）。可选；服务端缺省为当年 1 月 1 日 |
| `stop` | `Stop` | 分析结束时刻（UTC）。可选；服务端缺省为当年 12 月 31 日 |
| `observer_name` | `ObserverName` | 观测者名称，如 `Earth`；服务端缺省为 `Sun` |
| `observer_frame` | `ObserverFrame` | 观测者坐标系，服务端可选 `FIXED`、`INERTIAL`、`MeanEclpJ2000`、`J2000`，缺省为 `MeanEclpJ2000` |
| `step_s` | `Step` | 采样步长，单位 s，服务端缺省 86400 s |

`target_name` 是本函数唯一必填的请求字段；`start` 与 `stop` 可选，省略时不会被发往 ASTROX，由服务端选择当年 1 月 1 日至 12 月 31 日作为窗口，其它未提供的可选字段同样不会被发往 ASTROX，由服务器保留默认值。

```python
from astrox import celestial

start = "2026-01-01T00:00:00.000Z"
stop = "2026-01-02T00:00:00.000Z"

for frame in ("J2000", "MeanEclpJ2000"):
    ephemeris = celestial.ephemeris(
        target_name="Moon",
        start=start,
        stop=stop,
        observer_name="Earth",
        observer_frame=frame,
        step_s=43200.0,
    )
    samples = ephemeris["Position"]["cartesianVelocity"]
    print(f"Moon {frame}: {len(samples) // 7} 个状态样本")
```

响应包含 `Position` 与 `Period`（轨道周期，服务端文档标注单位 s）。`Position` 的键为 `CentralBody`、`referenceFrame`、`epoch`、`interval`、`interpolationAlgorithm`、`interpolationDegree` 与 `cartesianVelocity`；样本数与 `Step` 及窗口长度相关。

## 天体坐标轴旋转

### `celestial.cb_axes_rotation`

```python
celestial.cb_axes_rotation(
    *,
    from_central_body: str,
    to_central_body: str,
    epoch: str,
    from_frame: str | None = None,
    to_frame: str | None = None,
    order: int | None = None,
) -> dict[str, Any]
```

计算某历元时刻从起始中心天体坐标轴到目标中心天体坐标轴的旋转，返回原始 JSON 响应字典。

| 参数 | wire 参数 | 说明 |
| --- | --- | --- |
| `from_central_body` | `FromCbName` | 起始中心天体名称，如 `Earth` |
| `to_central_body` | `ToCbName` | 目标中心天体名称，如 `Moon` |
| `epoch` | `Epoch` | 历元时刻（UTC） |
| `from_frame` | `FromCbFrame` | 起始坐标系，服务端可选 `FIXED`、`INERTIAL`、`J2000`、`ICRF`、`MeanEclpJ2000`，缺省为 `INERTIAL` |
| `to_frame` | `ToCbFrame` | 目标坐标系，选项同上，缺省为 `FIXED` |
| `order` | `Order` | 旋转运动阶数：`0` 仅返回四元数，`1` 返回四元数及角速度；整数原样传递 |

`order` 保留为整数并原样 lower 到服务端，SDK 不做分支改写。响应中的 `Rotation` 是数值数组：`order=0` 时长度为 4（四元数 `[qx, qy, qz, qw]`），`order=1` 时长度为 7（四元数加角速度分量，服务端文档标注角速度单位为 rad/s）。已验证的数值语义包括：同一中心天体、两侧均为 `INERTIAL` 时，服务端返回单位四元数且 `order=1` 时角速度为 0；`Earth` 的 `INERTIAL`→`FIXED` 四元数与角速度；`Earth`→`Moon` 的 `INERTIAL`→`FIXED` 在 `order=1` 时的角速度。`Earth`→`Moon` 的 `INERTIAL`→`FIXED` 四元数尚未确认，其它组合未验证，使用前请自行核对。

```python
rotation = celestial.cb_axes_rotation(
    from_central_body="Earth",
    to_central_body="Moon",
    epoch="2026-01-01T00:00:00.000Z",
    from_frame="INERTIAL",
    to_frame="INERTIAL",
    order=1,
)

print(f"Earth→Moon 旋转: {len(rotation['Rotation'])} 个数值")
```

示例仅演示请求方式与响应结构，不表示 Earth→Moon 四元数的数值语义已经验证。

## 小行星 MPC 星历

### `celestial.mpc_ephemeris`

```python
celestial.mpc_ephemeris(
    *,
    target_name: str,
    observer_frame: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> dict[str, Any]
```

按小行星名称或编号查询 MPC 小行星星历，返回原始 JSON 响应字典。

| 参数 | wire 参数 | 说明 |
| --- | --- | --- |
| `target_name` | `TargetName` | 小行星名称或编号，如 `Ceres`、`99942` |
| `observer_frame` | `ObserverFrame` | 日心坐标系，服务端可选 `FIXED`、`INERTIAL`、`MeanEclpJ2000`、`J2000`，缺省为 `MeanEclpJ2000` |
| `start` | `Start` | 开始时刻（UTC）；缺省为轨道历元时刻，不能早于轨道历元时刻（服务端规则） |
| `stop` | `Stop` | 结束时刻（UTC）；缺省为 `Start` 起 1 年 |

该路由从外部 MPC 数据源获取轨道根数（历元为 MJD TDT），由服务端以固定 1 天步长进行日心轨道递推，输出为日心系 CZML Position 结构。响应包含 `OrbitElements`（轨道根数，键为 `EpochMjdTdt`、`PeriTimeMjdTdt`、`Q`、`SemimajorAxis`、`Eccentricity`、`Inclination`、`Raan`、`ArgOfPeriapsis`、`MeanAnomaly`）与 `Position`（CZML 结构，同 `ephemeris`）。轨道根数的数值来自外部 MPC 数据，属于外部数据所有，可能随 MPC 数据更新而变化。省略 `start`/`stop` 时，服务端使用轨道历元默认窗口（`start` 为轨道历元时刻，`stop` 为其后 1 年）；显式固定窗口依赖查询时的轨道历元，外部 MPC 轨道历元更新后，先前固定的窗口可能早于新历元而被服务端拒绝，建议省略窗口参数或跟随当前历元选择。

```python
mpc = celestial.mpc_ephemeris(target_name="Ceres")

print(f"Ceres MPC 星历: {len(mpc['Position']['cartesianVelocity']) // 7} 个状态样本")
```

## 小行星 MPC 轨道根数

### `celestial.mpc_orbital_elements` 与 `celestial.MpcOrbitalElements`

```python
celestial.mpc_orbital_elements(
    *,
    epoch_mjd_tdt: float | None = None,
    periapsis_time_mjd_tdt: float | None = None,
    periapsis_distance_au: float | None = None,
    semi_major_axis_au: float | None = None,
    eccentricity: float | None = None,
    inclination_deg: float | None = None,
    raan_deg: float | None = None,
    argument_of_periapsis_deg: float | None = None,
    mean_anomaly_deg: float | None = None,
) -> MpcOrbitalElements
```

构造日心 MPC 轨道根数片段；当出发端或到达端为小行星时，可将片段分别传给 `lambert_transfer_window` 对应的 `departure_elements` 或 `arrival_elements`。工厂函数返回不可变（frozen）命名数据类 `celestial.MpcOrbitalElements`；所有字段都可选，未提供的字段不会出现在 `to_wire()` 片段中。SDK 只做 lowering 所需的类型检查（字段必须是数值），不做物理有效性校验。

| 字段 | wire 键 | 单位 |
| --- | --- | --- |
| `epoch_mjd_tdt` | `EpochMjdTdt` | MJD TDT |
| `periapsis_time_mjd_tdt` | `PeriTimeMjdTdt` | MJD TDT |
| `periapsis_distance_au` | `Q` | AU |
| `semi_major_axis_au` | `SemimajorAxis` | AU |
| `eccentricity` | `Eccentricity` | — |
| `inclination_deg` | `Inclination` | deg |
| `raan_deg` | `Raan` | deg |
| `argument_of_periapsis_deg` | `ArgOfPeriapsis` | deg |
| `mean_anomaly_deg` | `MeanAnomaly` | deg |

```python
from astrox import celestial

elements = celestial.mpc_orbital_elements(
    epoch_mjd_tdt=61000.0,
    periapsis_time_mjd_tdt=60900.0,
    periapsis_distance_au=0.6740515,
    semi_major_axis_au=0.9898367,
    eccentricity=0.3190276,
    inclination_deg=0.79379,
    raan_deg=209.81829,
    argument_of_periapsis_deg=100.88187,
    mean_anomaly_deg=120.0,
)

print(elements.to_wire())
```

`to_wire()` 返回 ASTROX `MpcOrbElements` 请求片段，上面的示例输出 `{'EpochMjdTdt': 61000.0, 'PeriTimeMjdTdt': 60900.0, 'Q': 0.6740515, 'SemimajorAxis': 0.9898367, 'Eccentricity': 0.3190276, 'Inclination': 0.79379, 'Raan': 209.81829, 'ArgOfPeriapsis': 100.88187, 'MeanAnomaly': 120.0}`。传入 `lambert_transfer_window` 后，服务端直接使用这些根数进行日心轨道递推，不再通过网络查询 MPC。显式根数的独立开普勒递推尚未验证，其元素系、参考系与时间约定未确认，使用前请自行核对。

## Lambert 转移窗口

### `celestial.lambert_transfer_window`

```python
celestial.lambert_transfer_window(
    *,
    departure_body: str,
    arrival_body: str,
    departure_start: str,
    departure_stop: str,
    arrival_start: str,
    arrival_stop: str,
    sun_frame: str | None = None,
    min_time_of_flight_days: int | None = None,
    departure_step_days: float | None = None,
    arrival_step_days: float | None = None,
    departure_elements: MpcOrbitalElements | None = None,
    arrival_elements: MpcOrbitalElements | None = None,
) -> dict[str, Any]
```

在出发时间窗口与到达时间窗口上采样，计算天体之间的 Lambert 转移，返回原始 JSON 响应字典。它不是单案例接口 `orbits.lambert_delta_v`：后者接收两个 `CartesianState` 与一个 `time_of_flight_s`，调用 `/orbit/lambert`，返回 `(DV1, DV2)` 两个三元组；本函数扫描整组出发/到达时间组合，返回 `TransferResults` 列表。

| 参数 | wire 参数 | 说明 |
| --- | --- | --- |
| `departure_body` | `DepartureCbName` | 出发天体名称（行星或小行星），如 `Earth` |
| `arrival_body` | `ArrivalCbName` | 到达天体名称（行星或小行星），如 `Mars` |
| `departure_start` | `DepartureInterval` | 出发时间窗口起点（UTC），与 `departure_stop` 一起 lower 为 `"start/stop"` |
| `departure_stop` | `DepartureInterval` | 出发时间窗口终点（UTC） |
| `arrival_start` | `ArrivalInterval` | 到达时间窗口起点（UTC），与 `arrival_stop` 一起 lower 为 `"start/stop"` |
| `arrival_stop` | `ArrivalInterval` | 到达时间窗口终点（UTC） |
| `sun_frame` | `SunFrameName` | 日心参考系，服务端可选 `MeanEclpJ2000`、`ICRF`，缺省为 `MeanEclpJ2000` |
| `min_time_of_flight_days` | `MinTofDays` | 最小转移时间，单位 d，整数；服务端缺省 10 |
| `departure_step_days` | `DepartureStepDay` | 出发时间采样步长，单位 d；服务端缺省 1 |
| `arrival_step_days` | `ArrivalStepDay` | 到达时间采样步长，单位 d；服务端缺省 1 |
| `departure_elements` | `DepartureElements` | 出发小行星的 MPC 轨道根数（`mpc_orbital_elements` 构造）；省略时服务端通过网络查询 MPC |
| `arrival_elements` | `ArrivalElements` | 到达小行星的 MPC 轨道根数；省略时服务端通过网络查询 MPC |

`departure_body`、`arrival_body` 与四个时间字符串是本函数必填的请求字段；`DepartureInterval`/`ArrivalInterval` 是 `"开始/结束"` 形式的单字符串，例如 `"2028-06-01T00:00:00Z/2028-06-03T00:00:00Z"`。其它可选参数省略时不会被发往 ASTROX，由服务器保留默认值。

```python
from astrox import celestial

transfer = celestial.lambert_transfer_window(
    departure_body="Earth",
    arrival_body="Mars",
    departure_start="2028-06-01T00:00:00Z",
    departure_stop="2028-06-03T00:00:00Z",
    arrival_start="2029-04-01T00:00:00Z",
    arrival_stop="2029-04-03T00:00:00Z",
    sun_frame="ICRF",
    min_time_of_flight_days=10,
    departure_step_days=2.0,
    arrival_step_days=1.0,
)

results = transfer["TransferResults"]
first = results[0]
print(f"{len(results)} 个转移结果")
print(
    f"首个: {first['DepartureTime']} → {first['ArrivalTime']}, "
    f"|DeltaV1|={first['DV1_Mag']:.1f} m/s, |DeltaV2|={first['DV2_Mag']:.1f} m/s"
)
```

响应包含 `TransferResults`（转移结果数组，每个元素对应一对被采样的出发/到达时刻；结果个数由两个时间窗口与采样步长共同决定）。每个结果的键为：

| 键 | 类型 | 单位/说明 |
| --- | --- | --- |
| `DepartureTime` / `ArrivalTime` | string | 出发/到达时刻（UTC 字符串） |
| `DeltaV1` / `DeltaV2` | number[3] | 出发/到达速度增量向量，m/s |
| `DV1_Mag` / `DV2_Mag` | number | 出发/到达速度增量大小，m/s；已验证为对应 `DeltaV` 向量的欧几里得范数 |
| `RV1` / `RV2` | number[6] | 出发/到达时的位置速度（日心系）`[x, y, z, vx, vy, vz]`，位置 m、速度 m/s |

已验证（独立交叉验证支持）：`sun_frame="ICRF"` 时，维护的 Earth→Mars 用例在 2 个出发采样日 × 3 个到达采样日的结果网格上，`RV1`/`RV2` 中的转移速度与独立零圈顺行 Lambert 解一致。未解决：`MeanEclpJ2000` 与 ICRF 之间的精确坐标关系、`DeltaV` 相对端点天体速度的物理含义、显式 MPC 根数的独立开普勒递推。这些分支目前只有请求构造与响应结构层面的证据，使用前请自行核对。

## 约定说明

- `ephemeris` 的 `start` 与 `stop` 可选；省略时不会被发往 ASTROX，由服务端选择当年 1 月 1 日至 12 月 31 日作为窗口。
- `cartesianVelocity` 每个样本为 `[Time, X, Y, Z, dX, dY, dZ]`，`Time` 为相对历元的秒数，位置 m、速度 m/s。
- `cb_axes_rotation` 的 `order` 是整数，SDK 原样传递；`Rotation` 长度与 `order` 对应（`0` → 4，`1` → 7）。
- `mpc_ephemeris` 省略 `start`/`stop` 时由服务端使用轨道历元默认窗口；显式固定窗口可能因外部 MPC 轨道历元更新而过期。
- 本页四个函数的返回都移除了传输层 `IsSuccess` 与 `Message`，保留其余服务器字段；错误仍由 HTTP 层抛出（见错误处理）。
- `lambert_transfer_window` 的 `departure_start`/`departure_stop` 与 `arrival_start`/`arrival_stop` 分别组合为 `DepartureInterval`/`ArrivalInterval` 的 `"start/stop"` 字符串。
- `mpc_orbital_elements` 只做 lowering 所需的类型检查，不做物理有效性校验；未提供的字段不出现在 `to_wire()` 片段中。
- 未提供的可选参数不会被发往 ASTROX，由服务器保留默认值。
- 验证证据见 [celestial 验证页](../../validation/celestial.md)。

完整可运行示例见 `examples/11_celestial/celestial_queries.py`。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，本模块函数会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会改写服务器错误信息。需要完全控制请求载荷或处理原始响应时，请使用 `astrox.raw.post`。
