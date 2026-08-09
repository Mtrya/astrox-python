# 天体星历与坐标轴旋转

`astrox.celestial` 提供天体星历与天体坐标系旋转的只读查询 API：`celestial.ephemeris` 计算目标天体在显式时间窗口内的星历，`celestial.cb_axes_rotation` 计算两个中心天体坐标轴之间的旋转，`celestial.mpc_ephemeris` 计算小行星（MPC 数据）星历。推荐导入方式：

```python
from astrox import celestial
```

三个函数都通过 `astrox.raw.post` 发出 HTTP POST 请求，并返回 ASTROX 原始 JSON 响应字典，不做 typed response 解析。星历输出是 CZML Position 结构：位置与速度打包在 `cartesianVelocity` 数组中，每个样本为 7 个数值 `[Time, X, Y, Z, dX, dY, dZ]`，其中 `Time` 是相对历元时刻的秒数，位置单位为 m、速度单位为 m/s。响应在 `Position.CentralBody` 中声明坐标中心天体、在 `referenceFrame` 中声明参考系；SDK 只转述响应自身的声明，不对服务端内部星历内核的绝对正确性作断言。

## 目标天体星历

### `celestial.ephemeris`

```python
celestial.ephemeris(
    *,
    target_name: str,
    start: str,
    stop: str,
    observer_name: str | None = None,
    observer_frame: str | None = None,
    step_s: float | None = None,
) -> dict[str, Any]
```

计算目标天体在显式时间窗口内的星历，返回原始 JSON 响应字典。

| 参数 | wire 参数 | 说明 |
| --- | --- | --- |
| `target_name` | `TargetName` | 目标天体名称，如 `Moon`、`Mars`（服务端支持 `Moon`、`Mars`、`Venus`、`Mercury`、`Jupiter`、`Saturn`、`Uranus`、`Neptune` 等） |
| `start` | `Start` | 分析开始时刻（UTC，`yyyy-MM-ddTHH:mm:ssZ`）。在 curated surface 中显式必传；服务端缺省为当年 1 月 1 日，但显式传入窗口是受支持用法 |
| `stop` | `Stop` | 分析结束时刻（UTC）。在 curated surface 中显式必传；服务端缺省为当年 12 月 31 日 |
| `observer_name` | `ObserverName` | 观测者名称，如 `Earth`；服务端缺省为 `Sun` |
| `observer_frame` | `ObserverFrame` | 观测者坐标系，服务端可选 `FIXED`、`INERTIAL`、`MeanEclpJ2000`、`J2000`，缺省为 `MeanEclpJ2000` |
| `step_s` | `Step` | 采样步长，单位 s，服务端缺省 86400 s |

`start` 与 `stop` 是本函数唯一必填的两个请求字段；未提供的可选字段不会被发往 ASTROX，由服务器保留默认值。

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
    print(f"Moon {frame}: {ephemeris['IsSuccess']}, {len(samples) // 7} 个状态样本")
```

响应包含 `IsSuccess`、`Message`、`Position` 与 `Period`（轨道周期，服务端文档标注单位 s）。`Position` 的键为 `CentralBody`、`referenceFrame`、`epoch`、`interval`、`interpolationAlgorithm`、`interpolationDegree` 与 `cartesianVelocity`；样本数与 `Step` 及窗口长度相关。

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

`order` 保留为整数并原样 lower 到服务端，SDK 不做分支改写。响应中的 `Rotation` 是数值数组：`order=0` 时长度为 4（四元数 `[qx, qy, qz, qw]`），`order=1` 时长度为 7（四元数加角速度分量，服务端文档标注角速度单位为 rad/s）。同一中心天体、两侧均为 `INERTIAL` 时，服务端返回单位四元数且角速度为 0；任意中心天体/坐标系组合的变换数值不在 SDK 维护范围内，使用前请自行核对语义。

```python
rotation = celestial.cb_axes_rotation(
    from_central_body="Earth",
    to_central_body="Moon",
    epoch="2026-01-01T00:00:00.000Z",
    from_frame="INERTIAL",
    to_frame="INERTIAL",
    order=1,
)

print(f"Earth→Moon 旋转: {rotation['IsSuccess']}, {len(rotation['Rotation'])} 个数值")
```

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

该路由从外部 MPC 数据源获取轨道根数（历元为 MJD TDT），由服务端以固定 1 天步长进行日心轨道递推，输出为日心系 CZML Position 结构。响应包含 `IsSuccess`、`Message`、`OrbitElements`（轨道根数，键为 `EpochMjdTdt`、`PeriTimeMjdTdt`、`Q`、`SemimajorAxis`、`Eccentricity`、`Inclination`、`Raan`、`ArgOfPeriapsis`、`MeanAnomaly`）与 `Position`（CZML 结构，同 `ephemeris`）。轨道根数的数值来自外部 MPC 数据，属于外部数据所有，可能随 MPC 数据更新而变化；请在小行星轨道历元之后选择查询窗口，早于轨道历元的窗口可能被服务端拒绝。

```python
mpc = celestial.mpc_ephemeris(
    target_name="Ceres",
    start="2026-01-01T00:00:00.000Z",
    stop="2026-01-02T00:00:00.000Z",
)

print(f"Ceres MPC 星历: {mpc['IsSuccess']}, {mpc['Message']}")
```

## 约定说明

- `ephemeris` 的 `start` 与 `stop` 在 curated surface 中显式必传，不依赖服务端年度缺省窗口。
- `cartesianVelocity` 每个样本为 `[Time, X, Y, Z, dX, dY, dZ]`，`Time` 为相对历元的秒数，位置 m、速度 m/s。
- `cb_axes_rotation` 的 `order` 是整数，SDK 原样传递；`Rotation` 长度与 `order` 对应（`0` → 4，`1` → 7）。
- 未提供的可选参数不会被发往 ASTROX，由服务器保留默认值。
- 验证证据见 [celestial 验证页](../../validation/celestial.md)。

完整可运行示例见 `examples/11_celestial/celestial_queries.py`。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，本模块函数会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会改写服务器错误信息。需要完全控制请求载荷或处理原始响应时，请使用 `astrox.raw.post`。
