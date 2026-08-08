# 交会分析

`astrox.conjunction` 在一个时间窗口内筛查主飞行器与一组空间目标之间的近距离交会（close approach），返回每次交会的最近距离时刻、最近距离、相对速度、轨道面夹角与碰撞概率。推荐导入方式：

```python
from astrox import components, conjunction, orbits, propagator
```

主飞行器有两种来源，决定使用哪个函数：

- 主飞行器是两行根数（TLE）→ `conjunction.find_tle_close_approaches`。
- 主飞行器是 CZML 采样轨迹（例如火箭等没有 TLE 的对象）→ `conjunction.find_czml_close_approaches`。

目标列表在两种入口下都是 `orbits.Tle` 序列。两个函数返回相同的 `CloseApproachesResult` 结构，只是结果项类型不同。

## 参数与容差

两个函数共享同一组参数：

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 分析起始时间字符串（UTC，`yyyy-MM-ddTHH:mm:ss.fffZ` 格式） |
| `stop` | — | 分析结束时间字符串（UTC） |
| `tle` / `position` | — | 主飞行器：`orbits.Tle` 实例或 `components.CzmlPosition` 实例 |
| `targets` | — | 目标列表，`orbits.Tle` 序列；省略时不发往 ASTROX |
| `tol_max_distance_km` | km | 交会判定最大距离，服务器缺省 5 km |
| `tol_cross_dt_s` | s | 交点时刻筛选时间误差，服务器缺省 10 s |
| `tol_theta_deg` | deg | 轨道面夹角阈值，服务器缺省 1°；低于该值时服务端不做轨道面筛选 |
| `tol_dh_km` | km | 近地点/远地点高度筛选误差，服务器缺省 30 km |

可选参数在未提供时不会被发往 ASTROX，由服务器保留默认值；这些默认筛选可能在距离搜索前排除目标。`tol_max_distance_km` 决定距离阈值，目标数量很大时，收紧该值可以明显减少候选数量。要复现本页示例，示例代码显式设置了其余三个筛选容差。

## `conjunction.find_tle_close_approaches`

```python
conjunction.find_tle_close_approaches(
    *,
    start: str,
    stop: str,
    tle: Tle,
    tol_max_distance_km: float | None = None,
    tol_cross_dt_s: float | None = None,
    tol_theta_deg: float | None = None,
    tol_dh_km: float | None = None,
    targets: Sequence[Tle] | None = None,
) -> CloseApproachesResult
```

主飞行器与目标均为 TLE。结果项为 `TleCloseApproach`，同时包含主飞行器与目标的 TLE。

```python
ISS_TLE = orbits.tle(
    line1="1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    line2="2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    name="ISS",
    catalog_number="25544",
)
probe_tle = orbits.tle(
    line1="1 25545U 99999A   24001.00000000  .00000000  00000-0  00000-0 0  9993",
    line2="2 25545  51.6264 339.8059 0009386 217.1816 140.0000 15.52489080    03",
    name="probe",
    catalog_number="25545",
)

result = conjunction.find_tle_close_approaches(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    tle=ISS_TLE,
    targets=[probe_tle],
    tol_max_distance_km=1000.0,
    tol_cross_dt_s=1000.0,
    tol_theta_deg=180.0,
    tol_dh_km=1000.0,
)

for approach in result.results:
    print(approach.min_range_time, approach.min_range_km, approach.relative_speed_km_s)
```

## `conjunction.find_czml_close_approaches`

```python
conjunction.find_czml_close_approaches(
    *,
    start: str,
    stop: str,
    position: components.CzmlPosition,
    tol_max_distance_km: float | None = None,
    tol_cross_dt_s: float | None = None,
    tol_theta_deg: float | None = None,
    tol_dh_km: float | None = None,
    targets: Sequence[Tle] | None = None,
) -> CloseApproachesResult
```

主飞行器是 CZML 采样轨迹，目标仍为 TLE。结果项为 `CzmlCloseApproach`，只包含目标的 TLE，不包含主飞行器信息。采样轨迹可用 `propagator.sgp4` 传播后直接构造：

```python
period_s, position = propagator.sgp4(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    step_s=60.0,
    tle=ISS_TLE,
)

czml = components.czml_position(
    epoch=position.epoch,
    central_body=position.central_body,
    interpolation_algorithm=position.interpolation_algorithm,
    interpolation_degree=position.interpolation_degree,
    reference_frame=position.reference_frame,
    cartesian_velocity=position.cartesian_velocity,
)

result = conjunction.find_czml_close_approaches(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    position=czml,
    targets=[probe_tle],
    tol_max_distance_km=1000.0,
    tol_cross_dt_s=1000.0,
    tol_theta_deg=180.0,
    tol_dh_km=1000.0,
)
```

## 返回值

`CloseApproachesResult` 是解析后的冻结数据类：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `is_success` | `bool` | 是否成功 |
| `message` | `str` | 服务器消息 |
| `total_number` | `int` | 目标总数 |
| `after_apo_peri_filter_number` | `int` | 近地点/远地点高度筛选后的目标数 |
| `after_cross_plane_number` | `int` | 轨道面夹角筛选后的目标数 |
| `results` | `tuple[TleCloseApproach, ...]` 或 `tuple[CzmlCloseApproach, ...]` | 交会结果列表 |

`TleCloseApproach` 与 `CzmlCloseApproach` 的字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `primary` | `orbits.Tle` | 主飞行器 TLE（仅 `TleCloseApproach`） |
| `target` | `orbits.Tle` | 目标 TLE |
| `min_range_time` | `str` | 最近距离时刻（UTCG 字符串） |
| `min_range_km` | `float` | 最近距离，单位 km |
| `orbital_plane_angle_deg` | `float` | 轨道面夹角，单位 deg |
| `relative_speed_km_s` | `float` | 相对速度，单位 km/s |
| `collision_probability` | `float` | 碰撞概率，0 到 1；未验证，按服务器原样返回 |

## 已验证范围

- TLE 入口：最近距离时刻与 60 秒采样下的独立 SGP4 最近采样时刻一致，最近距离与三维几何距离一致，相对速度与几何相对速度一致；轨道面夹角与两条 TLE 的倾角差一致（按服务器小数精度返回）。开始与结束时刻的采样点都会参与报告。
- CZML 入口：使用 60 秒采样的公开 SGP4 轨迹验证了最近距离、相对速度与轨道面夹角；服务端报告的最近距离时刻通常落在 Stop 前一个采样点上，Stop 时刻的采样点不参与报告。
- 碰撞概率（`collision_probability`）没有独立的概率计算依据可对照，属于未验证字段，文档与示例均不把它作为推荐依据。

## 约定说明

- `min_range_time` 的时刻粒度与采样方式由服务端决定；CZML 入口下与输入轨迹的采样间隔相关。
- 交会判定受四个容差共同约束：先按近地点/远地点高度与轨道面夹角筛选候选目标，再在时间窗口内寻找距离极小值；`total_number` 是目标总数，两个筛选计数只统计目标个数，不代表交会次数。
- 轨道面夹角与相对速度的单位在返回对象中已通过字段后缀标明（`_deg`、`_km_s`）。

完整可运行示例见 `examples/08_conjunction/close_approaches.py`。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，交会函数会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会改写服务器错误信息。需要完全控制请求载荷或处理原始响应时，请使用 `astrox.raw.post`。
