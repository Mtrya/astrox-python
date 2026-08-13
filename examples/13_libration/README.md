# 平动点与 CRTBP 动力学示例

本目录展示 `astrox.libration` 的平动点、CRTBP 单位系与轨迹积分，以及地月 L1/L2 Halo、远距离逆行轨道（DRO）和固定 X 的周期轨道修正。示例中的 CRTBP 状态、时间和周期都是无量纲值。

| 示例 | 展示的公开 API |
| --- | --- |
| `libration_dynamics.py` | `libration.units(...)`、`libration.positions(...)`、`libration.crtbp_state(...)`、`libration.crtbp_trajectory(...)`、三个地月周期轨道族函数与 `libration.correct_periodic_orbit_fixed_x(...)` |

安装开发环境后，从仓库根目录运行：

```bash
uv sync --group dev
uv run python examples/13_libration/libration_dynamics.py
```

示例通过包默认客户端配置调用 ASTROX API，端到端运行需要能够访问兼容的 ASTROX 服务器。要指定服务地址，请在运行前设置 `ASTROX_BASE_URL`。

地月周期轨道族使用固定的地月质量比。把返回的状态传给轨迹积分或周期轨道修正时，示例显式复用同一个 `mass_ratio` 和主天体中心会合坐标系约定。`period_guess` 按完整周期传入。

全部参数与返回值见[平动点与 CRTBP 动力学手册](../../docs/manual/libration/README.md)，周期轨道的任务步骤见[如何生成并检查一条 CRTBP 周期轨道](../../docs/how_to/generate_a_crtbp_periodic_orbit.md)，各分支的验证范围与已知限制见 [libration 验证页](../../docs/validation/libration.md)。
