# 如何生成并检查一条 CRTBP 周期轨道

本页解决一个具体任务：从地月 L1 Halo 轨道族生成一条周期轨道，用固定 X 的微分修正重新构造它，再积分一个完整周期检查首尾状态。所有 CRTBP 状态、时间、周期和步长都是无量纲值。

## 完整示例

```python
import os

import astrox
from astrox import libration


EARTH_MOON_MASS_RATIO = 0.01215058560962404

if base_url := os.environ.get("ASTROX_BASE_URL"):
    astrox.configure(base_url=base_url)

family_member = libration.earth_moon_l1_halo(
    z_amplitude=0.05,
    southern=False,
)

orbit = libration.correct_periodic_orbit_fixed_x(
    initial_state=family_member.corrected_state,
    period_guess=family_member.period,
    mass_ratio=EARTH_MOON_MASS_RATIO,
    barycentric=False,
    output_step=0.05,
)

trajectory = libration.crtbp_trajectory(
    initial_state=orbit.corrected_state,
    mass_ratio=EARTH_MOON_MASS_RATIO,
    start_time=0.0,
    end_time=orbit.period,
    barycentric=False,
    output_step=0.05,
)

def state_values(state: libration.CrtbpState) -> tuple[float, ...]:
    return (state.x, state.y, state.z, state.vx, state.vy, state.vz)


first = state_values(trajectory.samples[0].state)
last = state_values(trajectory.samples[-1].state)
closure = max(abs(first_value - last_value) for first_value, last_value in zip(first, last))

print(f"周期: {orbit.period:.12f}")
print(f"修正后初始状态: {state_values(orbit.corrected_state)}")
print(f"样本数: {len(trajectory.samples)}")
print(f"首尾状态最大绝对差: {closure:.3e}")
```

从仓库根目录运行保存后的脚本：

```bash
uv run python generate_a_crtbp_periodic_orbit.py
```

## 需要做的两个决定

### 1. 选择轨道族与幅值定义

三个地月周期轨道族使用不同的参数定义：

| 轨道族 | 函数 | 幅值定义 |
| --- | --- | --- |
| L1 Halo | `earth_moon_l1_halo(z_amplitude=..., southern=...)` | `z_amplitude` 是修正后初始状态的 Z 幅值 |
| L2 Halo | `earth_moon_l2_halo(x_amplitude=..., southern=...)` | `x_amplitude = corrected_state.x - 1.0` |
| DRO | `earth_moon_dro(x_amplitude=...)` | `x_amplitude = corrected_state.x - 1.0`，表示远离月球一侧的 X 幅值 |

L1 Halo 不使用 `x_amplitude`，L2 Halo 和 DRO 也不使用 `z_amplitude`。不要把它们合并为一个含义模糊的通用幅值。

当选择 L2 Halo 时，不要精确传入四舍五入的下界 `0.026`，可从 `0.0261` 起选值。当选择 DRO 时，不要精确传入 `0.078`，可从 `0.0781` 起选值。

### 2. 保持坐标原点与质量比一致

`earth_moon_l1_halo`、`earth_moon_l2_halo` 和 `earth_moon_dro` 都返回主天体中心会合坐标系中的状态，因此示例在修正和积分时都显式传入 `barycentric=False`。地月轨道族使用的质量比是 `0.01215058560962404`，示例在两个后续函数中复用同一个常量。

`libration.units()` 的默认引力参数会产生另一个质量比，不能把该默认值与地月轨道族的状态混用。若要处理自定义主、次天体系统，先用显式引力参数和平均间距调用 `libration.units(...)`，然后在 `positions(...)`、`crtbp_trajectory(...)` 和 `correct_periodic_orbit_fixed_x(...)` 中复用 `unit_system.mass_ratio`。

如果已有质心会合坐标系中的初猜，在后续调用中使用 `barycentric=True`。主天体中心与质心原点之间只平移 X 坐标：

```text
x_barycentric = x_primary_centered - mass_ratio
```

速度不变。

## 修正初猜时的要点

`correct_periodic_orbit_fixed_x` 要求 `initial_state` 位于 XZ 平面穿越处，即 `y`、`vx` 和 `vz` 接近零。函数固定 X 坐标，对其它状态分量与周期进行修正。

`period_guess` 必须是完整周期的初猜，不是半周期。对轨道族结果做二次修正时，直接使用 `family_member.period` 是最清晰的起点。对自定义初猜，偏离目标轨道过大可能导致不收敛，此时 ASTROX 会抛出 `AstroxAPIError`。

## 读懂结果

`orbit` 是 `PeriodicOrbit`：

- `initial_state` 是用于修正的初猜。
- `corrected_state` 是修正后的周期轨道初始状态。
- `period` 是无量纲完整周期。
- `samples` 包含一个完整周期的 `CrtbpSample`。
- `is_barycentric` 记录返回状态是否使用质心原点。

示例另外调用 `crtbp_trajectory` 积分一个完整周期，并计算首尾六个状态分量的最大绝对差。这个数值用于直观检查返回轨道是否闭合，不应单独作为其它轨道的通用判定阈值。

## 了解更多

- 全部函数、参数、返回值和坐标约定见[平动点与 CRTBP 动力学手册](../manual/libration/README.md)。
- 仓库内的可运行版本见 `examples/13_libration/libration_dynamics.py`。
- 各轨道族、坐标分支和数值范围的验证状态见 [libration 验证页](../validation/libration.md)。
