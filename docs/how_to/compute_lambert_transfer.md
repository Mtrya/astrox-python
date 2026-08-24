# 计算天体之间的 Lambert 转移窗口

本页解决一个具体任务：给定出发天体、到达天体，以及各自的出发/到达时间窗口，扫描窗口内的转移机会，读取每条 Lambert 转移的出发/到达时刻、速度增量与转移轨道状态。

## 完整示例

下面的脚本计算 Earth→Mars 在 2028 年 6 月出发、2029 年 4 月到达的转移窗口，输出使用 ICRF 参考系。把代码保存为 `compute_lambert_transfer.py`：

```python
import astrox
from astrox import celestial

astrox.configure(base_url="http://astrox.cn:8765")

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
    # 该窗口出发双曲超速约 15 km/s，超出服务端 MaxDepartureDV 缺省值
    # （10000 m/s），需要显式放宽上限才能保留结果
    max_departure_delta_v_m_s=20000,
)

results = transfer["TransferResults"]
print(f"返回 {len(results)} 个转移结果")

for result in results:
    print(
        f"出发 {result['DepartureTime']} → 到达 {result['ArrivalTime']}: "
        f"|DeltaV1|={result['DV1_Mag']:.1f} m/s, "
        f"|DeltaV2|={result['DV2_Mag']:.1f} m/s, "
        f"TOF={result['TimeOfFlightDays']:.0f} d"
    )
```

## 运行

```bash
python compute_lambert_transfer.py
```

## 需要做的几个决定

1. **选出发与到达天体**：`departure_body`/`arrival_body` 接受服务端支持的天体名称（如 `Earth`、`Mars`、`Ceres`）以及 MPC 编号或名称（如 `2015 XF261`）。小行星省略对应的 `*_elements` 参数时，服务端通过网络查询 MPC 根数。
2. **定两个时间窗口**：`departure_start`/`departure_stop` 与 `arrival_start`/`arrival_stop` 各定义一个 UTC 时间窗口，SDK 分别组合为 `DepartureInterval`/`ArrivalInterval` 的 `"开始/结束"` 字符串。`departure_step_days` 与 `arrival_step_days`（单位 d）控制窗口内的采样步长，结果个数约等于两个窗口采样点数的乘积；示例中的 2 个出发日 × 3 个到达日产生 6 条结果。`min_time_of_flight_days`（单位 d，整数）过滤掉转移时间太短的组合，服务端缺省 10。
3. **选输出参考系**：`sun_frame` 服务端缺省 `MeanEclpJ2000`；`ICRF` 分支的转移速度已与独立零圈顺行 Lambert 解一致，端点位置方向也已识别为 ICRF 轴方向，而 `MeanEclpJ2000` 与 ICRF 的精确关系尚未独立确认，需要参考系明确的数值时建议显式传 `sun_frame="ICRF"`。
4. **按需调整过滤上限**：2026-08-20 起服务端按 `max_departure_delta_v_m_s`/`max_arrival_delta_v_m_s`（缺省各 10000 m/s，分别对应出发/到达双曲超速大小）与 `max_time_of_flight_days`（缺省 500 d）过滤算例，全部超界时返回空列表；扫描大 ΔV 或超长转移窗口时需显式放宽，示例中的 Earth→Mars 窗口就属于这种情况。

## 读懂结果

每个结果对象包含：

- `DepartureTime`/`ArrivalTime`：出发/到达时刻（UTC 字符串）。
- `DeltaV1`/`DeltaV2`：出发/到达速度增量向量（出发/到达双曲超速矢量，m/s）；`DV1_Mag`/`DV2_Mag` 是它们的欧几里得范数（m/s）。`DeltaV` 相对端点天体速度的物理含义尚未独立确认，需要严格物理解释时请先核对。
- `RV1`/`RV2`：出发/到达时的日心位置速度 `[x, y, z, vx, vy, vz]`（位置 m、速度 m/s）；ICRF 分支下转移速度与独立 Lambert 解一致，端点位置方向与 ICRF 轴方向一致。
- `TimeOfFlightDays`：飞行时间（d），已验证为到达与出发时刻的精确天数差。
- `ArrivalLightAngle`：到达时刻太阳光照角（deg），已验证为 `DeltaV2` 与 `RV2` 位置矢量的夹角。

## 小行星与显式 MPC 根数

要跳过服务端的 MPC 网络查询，可以显式传入轨道根数：

```python
elements = celestial.mpc_orbital_elements(
    epoch_mjd_tdt=61000.0,
    periapsis_distance_au=0.6740515,
    semi_major_axis_au=0.9898367,
    eccentricity=0.3190276,
    inclination_deg=0.79379,
    raan_deg=209.81829,
    argument_of_periapsis_deg=100.88187,
    mean_anomaly_deg=120.0,
)

transfer = celestial.lambert_transfer_window(
    departure_body="Earth",
    arrival_body="2015 XF261",
    departure_start="2028-06-01T00:00:00Z",
    departure_stop="2028-06-03T00:00:00Z",
    arrival_start="2029-04-01T00:00:00Z",
    arrival_stop="2029-04-03T00:00:00Z",
    sun_frame="ICRF",
    arrival_elements=elements,
)
```

注意：显式 MPC 根数在转移路由中的独立开普勒递推尚未验证，元素系与时间约定未确认（`reference_frame` 选项不改变该路由的到达状态）；这个分支可调用、响应结构已由 live 快照记录，但数值语义请自行核对。`mpc_ephemeris` 的 `target_elements` 分支已验证（见天体手册）。

## 了解更多

- `lambert_transfer_window` 与 `mpc_orbital_elements` 的完整参数表、`TransferResults` 字段说明见 [天体手册](../manual/celestial/README.md)。
- 单次转移的速度增量计算 `orbits.lambert_delta_v` 见 [orbits 手册](../manual/orbits/README.md)。
- 各分支的验证状态、已知残差与交叉验证证据详见 [Celestial 验证页](../validation/celestial.md)。
