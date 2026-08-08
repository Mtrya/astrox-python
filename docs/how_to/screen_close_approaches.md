# 如何筛查卫星与空间目标的近距离交会

本页解决一个具体任务：给定主卫星的两行根数（TLE）和一批目标的 TLE，找出分析窗口内双方可能发生的近距离交会，并读出最近距离时刻、最近距离、相对速度与轨道面夹角。

## 完整示例

下面的脚本用一颗主卫星与一个目标 TLE 做一次交会筛查，并打印每次交会的结果。

```python
import astrox
from astrox import conjunction, orbits

astrox.configure(base_url="http://astrox.cn:8765")

primary = orbits.tle(
    line1="1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    line2="2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    name="ISS",
    catalog_number="25544",
)

target = orbits.tle(
    line1="1 25545U 99999A   24001.00000000  .00000000  00000-0  00000-0 0  9993",
    line2="2 25545  51.6264 339.8059 0009386 217.1816 140.0000 15.52489080    03",
    name="probe",
    catalog_number="25545",
)

result = conjunction.find_tle_close_approaches(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    tle=primary,
    targets=[target],
    tol_max_distance_km=1000.0,
    tol_cross_dt_s=1000.0,
    tol_theta_deg=180.0,
    tol_dh_km=1000.0,
)

print(f"目标总数: {result.total_number}")
print(f"高度筛选后: {result.after_apo_peri_filter_number}")
print(f"轨道面筛选后: {result.after_cross_plane_number}")
print(f"报告交会数: {len(result.results)}")

for approach in result.results:
    print(f"\n最近距离时刻: {approach.min_range_time}")
    print(f"最近距离: {approach.min_range_km:.3f} km")
    print(f"相对速度: {approach.relative_speed_km_s:.4f} km/s")
    print(f"轨道面夹角: {approach.orbital_plane_angle_deg:.4f} deg")
```

## 需要做的两个决定

1. **主飞行器的形态**：主飞行器有 TLE 时用 `conjunction.find_tle_close_approaches`，结果里同时包含主飞行器与目标的 TLE；主飞行器是 CZML 采样轨迹（例如没有 TLE 的火箭等对象）时用 `conjunction.find_czml_close_approaches`，结果只包含目标。后者可以先 `propagator.sgp4` 传播，再把返回的采样序列直接构造成 `components.czml_position` 传入。
2. **交会容差**：`tol_max_distance_km` 决定多近才算一次交会；其余容差（交点时刻、轨道面夹角、近地点/远地点高度）可以使用服务器默认值，但默认筛选也可能在距离计算前排除目标。本页示例为复现已验证的结果，显式放宽了其余三个筛选容差。目标数量很大时，收紧 `tol_max_distance_km` 能明显减少计算量。

## 读懂结果

`total_number` 是目标总数，`after_apo_peri_filter_number` 与 `after_cross_plane_number` 是经过高度、轨道面两道筛选后剩余的目标数，`results` 是实际报告的交会列表。每个结果项的字段含义与单位见[交会分析手册](../manual/conjunction/README.md)。

`collision_probability`（碰撞概率）字段保留为 unresolved：重复调用并改变目标距离、轨道面角度、相对速度与筛选阈值，观测到的值始终为 0.0；它只是服务端返回的稳定但不可解释的标量（opaque scalar），不承担统计学碰撞概率语义，不要把它当作决策依据。筛查决策请基于最近距离与相对速度。

## 了解更多

- 交会函数的全部参数、容差语义与已验证范围详见[交会分析手册](../manual/conjunction/README.md)。
- TLE 的构造与字段说明详见[轨道手册](../manual/orbits/README.md)。
- 用 CZML 采样轨迹做主飞行器时，先读[传播器手册](../manual/propagator/README.md)了解如何生成采样位置。
