# 火箭

`astrox.rocket` 提供火箭弹道与着陆分析相关的公开 API。当前模块只暴露一个函数 `landing_zone`，用于从发射点、着陆点和局部偏移量计算着陆区边界的地理坐标。

推荐按如下方式导入：

```python
from astrox import rocket
```

## 着陆区

### `rocket.landing_zone`

```python
rocket.landing_zone(
    *,
    launch_longitude_deg: float,
    launch_latitude_deg: float,
    launch_height_m: float,
    impact_longitude_deg: float,
    impact_latitude_deg: float,
    impact_height_m: float,
    zone_xys_km: Sequence[float],
) -> dict[str, Any]
```

从发射点、着陆点和局部下程/横程偏移量计算着陆区边界顶点的地理坐标。其中下程（downrange）沿发射点至着陆点方向，横程（crossrange）垂直于该方向。

| 参数 | 单位 | 说明 |
| --- | --- | --- |
| `launch_longitude_deg` | deg | 发射点经度 |
| `launch_latitude_deg` | deg | 发射点纬度 |
| `launch_height_m` | m | 发射点高度 |
| `impact_longitude_deg` | deg | 着陆点经度 |
| `impact_latitude_deg` | deg | 着陆点纬度 |
| `impact_height_m` | m | 着陆点高度 |
| `zone_xys_km` | km | 局部偏移量展平序列，按 `[+X1, +Y1, +X2, +Y2, ...]` 成对给出 |

`zone_xys_km` 必须包含偶数个数值；若为奇数个，`rocket.landing_zone` 会抛出 `ValueError`。若传入非数值序列，会抛出 `TypeError`。

## 返回值

`rocket.landing_zone` 返回 ASTROX 原始响应字典，不对响应体做解析或改写。典型响应包含以下字段：

| 字段 | 说明 |
| --- | --- |
| `IsSuccess` | 布尔值，表示请求是否成功 |
| `Message` | 服务器返回的消息字符串 |
| `cartographicDegrees` | 展平的边界顶点数组，按 `[经度, 纬度, 高度, ...]` 排列，单位为 deg/deg/m |

## 约定说明

`zone_xys_km` 中的 `+X` 沿发射点至着陆点方向，`+Y` 垂直于该方向，成对顺序为 `[+X1, +Y1, +X2, +Y2, ...]`。返回的 `cartographicDegrees` 按 `[经度, 纬度, 高度, ...]` 展平排列。

## 示例

以下示例与 `examples/05_rocket/landing_zone.py` 一致：

```python
from astrox import rocket


result = rocket.landing_zone(
    launch_longitude_deg=100.0,
    launch_latitude_deg=30.0,
    launch_height_m=0.0,
    impact_longitude_deg=101.0,
    impact_latitude_deg=30.5,
    impact_height_m=100.0,
    zone_xys_km=[
        1.0,
        0.5,
        -1.0,
        0.5,
        -1.0,
        -0.5,
        1.0,
        -0.5,
    ],
)

print(f"Success: {result['IsSuccess']}")
print(f"Message: {result['Message']}")

cartographic = result["cartographicDegrees"]
num_vertices = len(cartographic) // 3
print(f"Boundary vertices: {num_vertices}")
for index in range(num_vertices):
    lon = cartographic[index * 3]
    lat = cartographic[index * 3 + 1]
    height = cartographic[index * 3 + 2]
    print(f"  {index}: lon={lon:.6f} deg, lat={lat:.6f} deg, height={height:.3f} m")
```

运行结果：

```text
Success: True
Message: Success
Boundary vertices: 4
  0: lon=101.006448 deg, lat=30.491602 deg, height=100.098 m
  1: lon=100.988372 deg, lat=30.500570 deg, height=100.098 m
  2: lon=100.993550 deg, lat=30.508397 deg, height=100.098 m
  3: lon=101.011627 deg, lat=30.499429 deg, height=100.098 m
```

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，`rocket.landing_zone` 会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会隐藏或改写服务器错误信息。
