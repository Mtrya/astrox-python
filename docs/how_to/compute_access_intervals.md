# 计算地面站与卫星之间的访问区间

本页完成一个具体任务：计算给定时间窗口内，一个固定地面站能够看到一颗卫星的访问区间（access interval）。

## 你需要做的两个选择

1. **为两端选择合适的位置源**：地面站使用 `components.site_position(...)`，卫星使用 `components.sgp4_position(...)` 传入两行根数（TLE），然后把它们分别包成 `components.entity(...)` 命名对象。
2. **是否添加约束**：主路径保持无约束，先拿到几何可见区间；若需要过滤低仰角等情况，可在地面站命名对象上附加 `constraints`，详见下文“下一步：添加仰角约束”。

## 完整示例

将以下代码保存为 `access_intervals.py` 并运行：

```python
import astrox
from astrox import access, components

astrox.configure(base_url="http://astrox.cn:8765")

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

print(f"访问区间数量: {len(result['Passes'])}")
for i, interval in enumerate(result["Passes"][:5], start=1):
    print(
        f"  区间 {i}: {interval['AccessStart']} 至 {interval['AccessStop']} "
        f"(持续 {interval['Duration']:.1f} s)"
    )
```

运行：

```bash
python access_intervals.py
```

你会看到类似下面的输出：

```text
访问区间数量: 6
  区间 1: 2024-01-01T01:33:10.636Z 至 2024-01-01T01:38:07.276Z (持续 296.6 s)
  区间 2: 2024-01-01T03:06:00.213Z 至 2024-01-01T03:17:55.654Z (持续 715.4 s)
  区间 3: 2024-01-01T04:44:17.416Z 至 2024-01-01T04:53:38.665Z (持续 561.2 s)
  区间 4: 2024-01-01T11:21:40.718Z 至 2024-01-01T11:30:20.788Z (持续 520.1 s)
  区间 5: 2024-01-01T12:57:07.455Z 至 2024-01-01T13:09:06.964Z (持续 719.5 s)
```

## 刚才发生了什么

`access.compute` 向 ASTROX 发起一次直接访问计算。`from_entity` 和 `to_entity` 必须是 `components.entity(...)` 构造的命名对象：

- 地面站用 `site_position` 给出经纬度和海拔高度；
- 卫星用 `sgp4_position` 传入 TLE 两行根数，服务器会按 SGP4 模型推算卫星位置。

`step_s=600.0` 控制 AER 输出的采样步长，`compute_aer=True` 要求每个访问区间附带方位角、仰角、距离数据。如果只需要区间起止时间，可以省略 `compute_aer` 或设为 `False`。

返回的 `result` 是 ASTROX 原始响应字典，`result["Passes"]` 为访问区间列表，每个区间包含 `AccessStart`、`AccessStop` 和 `Duration`（单位 s）。

## 下一步：添加仰角约束

实际任务通常要求卫星至少达到某一仰角。把约束挂在地面站命名对象上即可，主代码其余部分不变：

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
    ],
)
```

上述片段不能单独运行，需要替换完整示例中的 `ground` 对象后再执行。

## 延伸阅读与验证

- 访问计算的完整参数、返回值字段以及链路（chain）用法，请参阅 [access 手册](../manual/access/README.md)。
- 命名对象、位置源、约束的构造细节请参阅 [components 手册](../manual/components/README.md)。
- 访问区间与 AER 输出的验证证据、约束校准状态见 [Access 验证页](../validation/access.md)。
