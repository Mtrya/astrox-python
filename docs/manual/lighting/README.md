# 光照

`astrox.lighting` 计算位置源上的光照时间、太阳辐射强度采样与太阳方位-仰角-距离（AER）采样。推荐按如下方式导入：

```python
from astrox import components, lighting
```

光照函数本身不定义轨道或位置，它们消费 `astrox.components` 中的位置源（position source）。可用于光照计算的位置源包括固定地面站、SGP4 两行根数（TLE）位置、J2/二体开普勒位置以及 CZML 采样位置。位置源的构造方式详见 [components 手册](../components/README.md)。

## 返回值

`astrox.lighting` 中的三个函数均直接返回 ASTROX 原始响应字典，不做解析或封装。调用者按字段名读取结果：

- `lighting_times(...)` 返回包含 `SunLight`、`Penumbra`、`Umbra` 等键的字典。
- `solar_intensity(...)` 返回包含 `Datas` 列表的字典，列表元素为采样点。
- `solar_aer(...)` 返回包含 `Datas` 列表的字典，列表元素为 `Time`、`Azimuth`、`Elevation`、`Range`。

需要完全控制请求或响应时，请直接使用 `astrox.raw.post`。

## 光照时间

### `lighting.lighting_times`

```python
lighting.lighting_times(
    *,
    start: str,
    stop: str,
    position: components.EntityPosition,
    description: str | None = None,
    az_el_mask_data: Sequence[float] | None = None,
    occultation_bodies: Sequence[str] | None = None,
) -> dict[str, Any]
```

计算指定位置源在 `start` 到 `stop` 之间的光照、半影和本影区间。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 起始时间字符串 |
| `stop` | — | 结束时间字符串 |
| `position` | — | `astrox.components` 位置源 |
| `description` | — | 描述文本 |
| `az_el_mask_data` | rad | 方位-仰角遮罩数据，交替排列 |
| `occultation_bodies` | — | 遮挡天体名称列表，如 `["Earth", "Moon"]` |

返回字典中的主要字段：

| 字段 | 说明 |
| --- | --- |
| `SunLight` | 光照区间，含 `Intervals`、`TotalDuration`、`MeanDuration`、`MinDuration`、`MaxDuration` |
| `Penumbra` | 半影区间与统计 |
| `Umbra` | 本影区间与统计 |

```python
iss = components.sgp4_position(
    tle_lines=(
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
        "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    ),
)

intervals = lighting.lighting_times(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    position=iss,
    occultation_bodies=["Earth", "Moon"],
)

print(f"ISS sunlight intervals: {len(intervals['SunLight']['Intervals'])}")
```

完整可运行示例见 `examples/03_lighting/lighting.py`。

## 太阳辐射强度

### `lighting.solar_intensity`

```python
lighting.solar_intensity(
    *,
    start: str,
    stop: str,
    position: components.EntityPosition,
    description: str | None = None,
    az_el_mask_data: Sequence[float] | None = None,
    step_s: float | None = None,
    occultation_bodies: Sequence[str] | None = None,
) -> dict[str, Any]
```

计算指定位置源在 `start` 到 `stop` 之间的太阳辐射强度采样。每个采样点包含 `Intensity`（太阳盘可见比例，`1` 为完全可见，`0` 为完全遮挡）与 `PercentShadow`（被遮挡比例）等字段。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 起始时间字符串 |
| `stop` | — | 结束时间字符串 |
| `position` | — | `astrox.components` 位置源 |
| `description` | — | 描述文本 |
| `az_el_mask_data` | rad | 方位-仰角遮罩数据，交替排列 |
| `step_s` | s | 采样步长 |
| `occultation_bodies` | — | 遮挡天体名称列表 |

返回字典中的 `Datas` 列表元素通常包含 `Time`、`Intensity`、`PercentShadow`、`CurrentCondition`、`Obstruction`、`ApparentSolarRange` 等字段。

```python
site = components.site_position(
    longitude_deg=-155.468,
    latitude_deg=19.821,
    height_m=4205.0,
)

intensity = lighting.solar_intensity(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    position=site,
    step_s=900.0,
)

first = intensity["Datas"][0]
print(
    f"First site intensity sample: "
    f"{first['Intensity']:.3f} visible, "
    f"{first['PercentShadow']:.3f} shadow"
)
```

完整可运行示例见 `examples/03_lighting/lighting.py`。

## 太阳 AER

### `lighting.solar_aer`

```python
lighting.solar_aer(
    *,
    start: str,
    stop: str,
    position: components.EntityPosition,
    text: str | None = None,
    step_s: int | None = None,
) -> dict[str, Any]
```

计算指定位置源在 `start` 到 `stop` 之间的太阳方位-仰角-距离（AER）采样。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `start` | — | 起始时间字符串 |
| `stop` | — | 结束时间字符串 |
| `position` | — | `astrox.components` 位置源 |
| `text` | — | 文本标签 |
| `step_s` | s | 采样步长 |

返回字典中的 `Datas` 列表元素包含 `Time`、`Azimuth`、`Elevation`、`Range` 字段，单位分别为时间字符串、度、度、千米。

```python
aer = lighting.solar_aer(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    position=site,
    step_s=900,
)

first = aer["Datas"][0]
print(
    f"First site solar AER sample: "
    f"az={first['Azimuth']:.3f} deg, "
    f"el={first['Elevation']:.3f} deg, "
    f"range={first['Range']:.1f} km"
)
```

完整可运行示例见 `examples/03_lighting/lighting.py`。

## 输入类型说明

三个函数均接受 `astrox.components` 位置源作为 `position` 参数，不接受原始字典或完整的 `components.entity(...)` 命名对象。`az_el_mask_data` 与 `occultation_bodies` 等可选参数仅在提供时才会发往 ASTROX。

## 约定说明

- 时间字符串采用 ISO 8601 格式，如 `2024-01-01T00:00:00.000Z`。
- `az_el_mask_data` 单位为弧度，按 `[az1, el1, az2, el2, ...]` 交替排列。
- `solar_aer` 返回的 `Azimuth`、`Elevation` 单位为度，`Range` 单位为千米。
