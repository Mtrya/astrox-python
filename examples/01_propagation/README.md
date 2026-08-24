# 轨道传播示例

本目录包含可运行的轨道传播示例。这些精选传播器示例采用如下公开 SDK 风格：

```python
from astrox import orbits, propagator
```

用户指南请参见[传播器手册](../../docs/manual/propagator/README.md)，其中记录了 `orbits.keplerian(...)`、`orbits.cartesian_state(...)`、`propagator.j2(...)`、`propagator.two_body(...)`、`propagator.two_body_rv(...)`、`propagator.multi_j2(...)`、`propagator.multi_two_body(...)`、`propagator.sgp4(...)`、`propagator.multi_sgp4(...)`、`propagator.simple_ascent(...)`、`propagator.hpop(...)` 以及精选弹道函数的参数、单位、返回值与注意事项。若需要按步骤选择传播器，可参考[如何传播一条轨道](../../docs/how_to/propagate_an_orbit.md)；若需要搭建 HPOP 力模型配置，可参考[如何搭建 HPOP 力模型配置](../../docs/how_to/build_an_hpop_configuration.md)。

## 精选传播器示例

| 示例 | 展示的公开 API |
| --- | --- |
| `propagator_reference.py` | 紧凑地遍历 `orbits.keplerian(...)`、`propagator.j2(...)`、`propagator.two_body(...)`、`propagator.hpop(...)`、`propagator.ballistic_delta_v(...)`、`propagator.sgp4(...)`、`propagator.simple_ascent(...)` |
| `j2_classical.py` | 由经典开普勒根数进行 J2 传播 |
| `two_body_classical.py` | 由经典开普勒根数进行二体传播 |
| `two_body_rv.py` | 由初始位置速度进行二体递推（扁平星历序列） |
| `batch_propagators.py` | 批量 J2、二体与 SGP4 传播至同一目标历元 |
| `sgp4_tle.py` | 由两行根数（TLE）数据进行 SGP4 传播 |
| `simple_ascent.py` | 由发射点到熄火点进行简单上升传播 |
| `hpop.py` | 由经典开普勒根数与笛卡尔状态进行 HPOP 传播 |
| `ballistic_delta_v.py` | 弹道 `DeltaV` 分支 |
| `ballistic_min_ecc.py` | 弹道 `DeltaV_MinEcc` 分支 |
| `ballistic_apogee_alt.py` | 弹道 `ApogeeAlt` 分支 |
| `ballistic_time_of_flight.py` | 弹道 `TimeOfFlight` 分支 |

安装开发环境后，即可从仓库根目录运行示例：

```bash
uv sync --group dev
uv run python examples/01_propagation/propagator_reference.py
uv run python examples/01_propagation/j2_classical.py
uv run python examples/01_propagation/two_body_classical.py
uv run python examples/01_propagation/two_body_rv.py
uv run python examples/01_propagation/batch_propagators.py
uv run python examples/01_propagation/sgp4_tle.py
uv run python examples/01_propagation/simple_ascent.py
uv run python examples/01_propagation/hpop.py
uv run python examples/01_propagation/ballistic_delta_v.py
```

这些示例通过包默认客户端配置调用 ASTROX API。端到端运行需要能够访问兼容的 ASTROX 服务器。

## 输出形式

单个结果的精选传播器函数返回 `(period_s, position)`。`period_s` 为服务器返回的轨道周期。`position` 是 `propagator.PropagatorPosition` 数据类，包含 `central_body`、`epoch`、`reference_frame`、`interpolation_algorithm`、`interpolation_degree` 与 `cartesian_velocity`。批量传播器函数返回 `tuple[orbits.KeplerianElements, ...]`。

对于 SGP4 示例，ASTROX 报告的 `position.reference_frame` 为 `INERTIAL`。应将这些坐标作为 GCRF/GCRS 风格的惯性状态来理解，而非底层 SGP4 库返回的原始 TEME 状态。
