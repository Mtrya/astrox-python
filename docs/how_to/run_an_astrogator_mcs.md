# 如何运行一个 Astrogator 任务序列

本页解决一个具体任务：用 Astrogator RunMCS 跑一条最简单的任务——定义一个初始状态，用自定义二体传播器传播 1 秒，然后读懂返回结果。这也是搭建更复杂任务（机动、嵌套序列、目标序列）的基础。

## 三个必须知道的点

1. **传播器必须显式注册**：RunMCS 不提供默认传播器，`propagate` 段里的 `propagator_name` 必须指向你在 `run_mcs(propagators=...)` 里注册的 `propagator.hpop_config`。
2. **引力参数必须显式给出**：开普勒初始状态和自定义二体重力模型都需要 `gravitational_parameter_m3_s2`（地球取 `398600441500000.0`，单位 m³/s²）。不给或只给其中一处，结果都会不可信或直接被拒绝。
3. **结果按执行顺序返回**：`run_mcs` 返回 `RunMCSResult`，`main_sequence_results` 里是实际执行并产生输出的段结果，`final_state` 是段的结束状态。启用 Stop 时，Stop 段自身及其后的段不会产生结果。

## 完整示例

下面的脚本定义一条两段任务：先设置一个开普勒初始状态，再用显式注册的二体传播器传播 1 秒。

```python
from astrox import astrogator, propagator


START = "2026-01-01T00:00:00Z"
EARTH_MU_M3_S2 = 398600441500000.0
PROPAGATOR_NAME = "Earth_TwoBody_Example"


def two_body_propagator() -> propagator.HpopConfig:
    return propagator.hpop_config(
        name=PROPAGATOR_NAME,
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="RKF7th8th_Example",
            use_fixed_step=True,
            initial_step_s=0.1,
            max_step_s=0.1,
            min_step_s=0.1,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_two_body_gravity(
            name="TwoBody_Example",
            gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
        ),
    )


initial_orbit = astrogator.keplerian_state(
    semi_major_axis_m=7_000_000.0,
    eccentricity=0.01,
    inclination_deg=28.5,
    raan_deg=15.0,
    argument_of_periapsis_deg=20.0,
    true_anomaly_deg=30.0,
    gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
)

result = astrogator.run_mcs(
    [
        astrogator.initial_state("Initial State", initial_orbit, epoch=START),
        astrogator.propagate(
            "Coast",
            propagator_name=PROPAGATOR_NAME,
            stop_conditions=[astrogator.duration_stop("One Second", 1.0)],
        ),
    ],
    propagators=[two_body_propagator()],
)

coast = result.main_sequence_results[-1]
print(f"任务成功: {result.is_success}")
print(f"传播时长: {coast.duration_s:.3f} s")
print(f"停止条件: {coast.stopping_condition_name}")
print(f"终止历元: {coast.final_state.epoch}")
print(f"终止位置 X: {coast.final_state.cartesian.x_m:.3f} m")
```

## 运行结果

```bash
python run_an_astrogator_mcs.py
```

实际输出如下（数值来自 ASTROX 服务器，可能与你的运行略有差异）：

```text
任务成功: True
传播时长: 1.000 s
停止条件: One Second
终止历元: 2026-01-01T00:00:01.000Z
终止位置 X: 3092629.662 m
```

## 如何读取结果

`result` 是 `astrogator.RunMCSResult`，包含：

- `is_success`：任务是否成功。服务器返回失败时 SDK 会直接抛异常，所以能拿到结果时它总是 `True`。
- `main_sequence_results`：按执行顺序返回实际执行并产生输出的段结果元组。这里没有 Stop 段，最后一项 `coast` 就是传播段的结果，类型为 `PropagateResult`。
- `positions`：CZML 位置采样。未传 `compute_czml_positions` 时 SDK 不发送该字段，由服务器决定是否计算；需要轨迹采样做可视化时，显式传 `compute_czml_positions=True`。响应中没有采样时该字段为 `None`。

传播段结果里常用字段：

- `duration_s`：段耗时，秒。这里为 1.0，对应 `duration_stop("One Second", 1.0)` 的时长。
- `stopping_condition_name`：实际触发的停止条件名称，与请求中的名字一致。
- `final_state`：段的结束状态（`SegmentState`），`final_state.epoch` 是结束历元，`final_state.cartesian` 是笛卡尔位置/速度（`x_m`、`y_m`、`vx_m_s` 等，单位 m 与 m/s）。它同时提供 `keplerian`（开普勒根数，含 `period_s`）和 `spherical` 两种表示，可互相核验。

## 在此基础上扩展

- 加机动：`impulsive_maneuver`（沿速度方向用 `impulsive_velocity_vector`）或 `finite_maneuver`（需要注册发动机 `constant_engine`）。
- 换停止条件：`epoch_stop`、`periapsis_stop`、`apoapsis_stop`。
- 组合与目标：`sequence` 嵌套子序列，`target_sequence` + 差分修正器做变量调节。
- 取中间量：段的 `results` 参数加 `duration_scalar`、`keplerian_scalar` 等标量定义，结果在段的 `scalar_results` 字典里。

## 了解更多

- 概念、全部构造器、参数/单位、结果树与明确限制见 [Astrogator 手册](../manual/astrogator/README.md)。
- 传播器配置构造器见 [传播器手册](../manual/propagator/README.md)。
- 各分支的验证状态见[验证文档](../validation/README.md)。
