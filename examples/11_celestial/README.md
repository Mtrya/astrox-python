# 天体查询示例

本目录展示 `astrox.celestial` 的显式时间窗口星历、中心天体坐标轴旋转、MPC 星历、Lambert 转移窗口与 MPC 轨道根数片段。

| 示例 | 展示的公开 API |
| --- | --- |
| `celestial_queries.py` | `celestial.ephemeris(...)`、`celestial.cb_axes_rotation(...)`、`celestial.mpc_ephemeris(...)`、`celestial.lambert_transfer_window(...)` 与 `celestial.mpc_orbital_elements(...)` |

从仓库根目录运行：

```bash
uv run python examples/11_celestial/celestial_queries.py
```

星历示例显式传入 `start` 和 `stop`，避免依赖服务端动态时间默认值。`cartesianVelocity` 是按 `[Time, X, Y, Z, dX, dY, dZ]` 展开的米和米每秒数组；坐标系和中心天体仍以响应中的字段为准。MPC 路由依赖服务端当前可用的 Minor Planet Center 数据，日期窗口可能受远端轨道历元限制。

Lambert 示例使用 `sun_frame="ICRF"`：该分支的转移速度已与独立零圈顺行 Lambert 解一致，`DV1_Mag`/`DV2_Mag` 已验证为对应 `DeltaV` 向量的欧几里得范数；`MeanEclpJ2000` 与 ICRF 的关系、`DeltaV` 的物理含义与显式 MPC 根数的开普勒递推尚未独立验证。MPC 根数示例只演示片段构造与 `to_wire()` lower 结果，不对根数数值语义作保证。

完整参数说明见[天体查询手册](../../docs/manual/celestial/README.md)，独立比较与不变量证据见[天体验证文档](../../docs/validation/celestial.md)。
