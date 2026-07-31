# 计算光照条件

本页解决一个具体任务：给定时间窗口内，计算一个位置源上的光照/半影/本影区间、太阳辐射强度采样，以及太阳方位-仰角-距离（AER）采样。

## 要做的两个选择

1. **选择位置源**：你想看卫星还是地面站？
   - 地面站 → 用 `components.site_position(...)` 给出经纬度和海拔高度。
   - 卫星 → 用 `components.sgp4_position(...)` 传入两行根数（TLE），或用 `j2_position`、`two_body_position` 等传播位置源。
2. **选择输出类型**：
   - 要光照/半影/本影区间 → 用 `lighting.lighting_times(...)`。
   - 要按时间采样的太阳辐射强度 → 用 `lighting.solar_intensity(...)`。
   - 要太阳 AER 采样 → 用 `lighting.solar_aer(...)`。

这三个函数直接把 `astrox.components` 位置源作为 `position` 参数，不需要先包成 `components.entity(...)` 命名对象。

## 完整示例

下面的脚本同时演示卫星光照区间与地面站的太阳辐射强度、太阳 AER。把代码保存为 `compute_lighting_conditions.py`：

```python
import astrox
from astrox import components, lighting

astrox.configure(base_url="http://astrox.cn:8765")

ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

site = components.site_position(
    longitude_deg=-155.468,
    latitude_deg=19.821,
    height_m=4205.0,
)

iss = components.sgp4_position(tle_lines=ISS_TLE)

intervals = lighting.lighting_times(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T06:00:00.000Z",
    position=iss,
    occultation_bodies=["Earth", "Moon"],
)

intensity = lighting.solar_intensity(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T06:00:00.000Z",
    position=site,
    step_s=900.0,
)

aer = lighting.solar_aer(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T06:00:00.000Z",
    position=site,
    step_s=900,
)

print("=== ISS 光照区间 ===")
for name in ("SunLight", "Penumbra", "Umbra"):
    data = intervals[name]
    print(f"{name}: {len(data['Intervals'])} 段，总时长 {data['TotalDuration']:.1f} s")

print("\n=== 地面站太阳辐射强度（前 3 个采样） ===")
for sample in intensity["Datas"][:3]:
    print(
        f"  {sample['Time']}: Intensity={sample['Intensity']:.3f}, "
        f"PercentShadow={sample['PercentShadow']:.3f}"
    )

print("\n=== 地面站太阳 AER（前 3 个采样） ===")
for sample in aer["Datas"][:3]:
    print(
        f"  {sample['Time']}: "
        f"Azimuth={sample['Azimuth']:.3f} deg, "
        f"Elevation={sample['Elevation']:.3f} deg, "
        f"Range={sample['Range']:.1f} km"
    )
```

## 运行

```bash
python compute_lighting_conditions.py
```

## 实际输出

```text
=== ISS 光照区间 ===
SunLight: 5 段，总时长 13131.7 s
Penumbra: 8 段，总时长 73.0 s
Umbra: 4 段，总时长 8395.3 s

=== 地面站太阳辐射强度（前 3 个采样） ===
  2024-01-01T00:00:00.000Z: Intensity=1.000, PercentShadow=0.000
  2024-01-01T00:15:00.000Z: Intensity=1.000, PercentShadow=0.000
  2024-01-01T00:30:00.000Z: Intensity=1.000, PercentShadow=0.000

=== 地面站太阳 AER（前 3 个采样） ===
  2024-01-01T00:00:00.000Z: Azimuth=209.548 deg, Elevation=41.253 deg, Range=147098121.7 km
  2024-01-01T00:15:00.000Z: Azimuth=213.376 deg, Elevation=39.412 deg, Range=147098260.4 km
  2024-01-01T00:30:00.000Z: Azimuth=216.934 deg, Elevation=37.381 deg, Range=147098420.2 km
```

## 刚才发生了什么

`lighting.lighting_times` 向 `/Lighting/LightingTimes` 发送请求，返回 ASTROX 原始响应字典，包含 `SunLight`、`Penumbra`、`Umbra` 三个键。每个键下面有 `Intervals` 区间列表以及 `TotalDuration`、`MeanDuration` 等统计量。`occultation_bodies=["Earth", "Moon"]` 让计算同时考虑地球和月球遮挡；对地面站光照计算通常不需要这个参数。

`lighting.solar_intensity` 返回的 `Datas` 是按 `step_s` 采样的列表，每个元素包含 `Time`、`Intensity`（太阳盘可见比例，`1` 为完全可见）、`PercentShadow`（被遮挡比例）等字段。`step_s` 单位为秒。

`lighting.solar_aer` 返回的 `Datas` 同样按 `step_s` 采样，每个元素包含 `Time`、`Azimuth`（方位角，度）、`Elevation`（仰角，度）、`Range`（距离，千米）。

这三个函数都不会在 SDK 内部解析或封装响应结构，直接返回 ASTROX 原始响应字典。

## 下一步

- 如果只需要某一颗卫星的进出地影时间，把示例中的 `position` 换成 `sgp4_position(...)` 或 `j2_position(...)`，其余调用方式不变。
- 光照函数的完整参数、可选的方位-仰角遮罩数据 `az_el_mask_data`、遮挡天体列表等说明，请参阅 [光照计算手册](../manual/lighting/README.md)。
- 位置源构造器的完整列表请参阅 [components 手册](../manual/components/README.md)。
- 各分支的验证状态、已知残差与交叉验证证据详见 [Lighting 验证页](../validation/lighting.md)。
