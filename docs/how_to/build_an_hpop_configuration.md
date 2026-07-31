# 搭建 HPOP 力模型配置

本页解决一个具体任务：用 `propagator.hpop_config(...)` 系列构造器搭一套 HPOP 力模型配置，并用它运行一次高精度轨道传播。

## 要做的两个选择

1. **为任务选择力模型分量**：HPOP 配置由积分器、重力场、大气、太阳辐射压、第三方天体摄动等可选分量叠加而成。简单任务可以只用二体重力；需要更高精度时，再逐层加入重力场阶次、大气阻力、太阳辐射压和日月第三方天体摄动。
2. **选择坐标系**：`coord_system` 决定输出位置的参考系。`"Inertial"` 对应惯性参考系输出，`"Fixed"` 对应地固参考系输出；与 J2/二体传播一样，默认由服务器决定，但建议在调用中显式指定。

## 完整示例

下面的脚本构造一个包含全部可选分量的 HPOP 力模型配置，并用开普勒根数运行一次 10 分钟传播。将代码保存为 `build_an_hpop_configuration.py`：

```python
import astrox
from astrox import orbits, propagator

astrox.configure(base_url="http://astrox.cn:8765")

orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=0.0,
    true_anomaly_deg=0.0,
)

config = propagator.hpop_config(
    central_body="Earth",
    integrator=propagator.hpop_rkf78(
        use_fixed_step=True,
        initial_step_s=60.0,
        max_step_s=60.0,
        min_step_s=0.001,
        max_abs_error=1e-10,
        max_rel_error=1e-12,
        max_iterations=50,
    ),
    gravity=propagator.hpop_gravity_field(
        gravity_file_name="EGM2008.grv",
        degree=4,
        order=4,
        use_secular_variations=False,
        solid_tide_type="Permanent tide only",
        eop_file_path="EOP-v1.1.txt",
    ),
    atmosphere=propagator.hpop_jacchia_roberts(
        drag_model_type="Spherical",
        atmos_data_source="Constant Values",
        f10p7=150.0,
        f10p7_avg=150.0,
        kp=3.0,
    ),
    srp=propagator.hpop_srp_spherical(
        shadow_model="DualCone",
        sun_position="Apparent",
        eclipsing_bodies=["Earth", "Moon"],
    ),
    third_bodies=[
        propagator.hpop_third_body(
            "Sun",
            mode_type="PointMass",
            ephem_source="DeFile",
            grav_source="DeFile",
            mu_m3_s2=1.3271244004193938e20,
        ),
        propagator.hpop_third_body("Moon"),
    ],
)

period_s, position = propagator.hpop(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    coord_system="Inertial",
    gravitational_parameter_m3_s2=398600441500000.0,
    coefficient_of_drag=2.2,
    area_mass_ratio_drag_m2_kg=0.01,
    coefficient_of_srp=1.3,
    area_mass_ratio_srp_m2_kg=0.02,
    config=config,
)

samples = position.cartesian_velocity
print(f"轨道周期: {period_s:.3f} s")
print(f"中心天体: {position.central_body}")
print(f"参考系: {position.reference_frame}")
print(f"采样点数: {len(samples) // 7}")
t = samples[0]
x, y, z, vx, vy, vz = samples[1:7]
print(f"首个采样 t={t:.3f} s")
print(f"位置 (m): x={x:.3f}, y={y:.3f}, z={z:.3f}")
print(f"速度 (m/s): vx={vx:.6f}, vy={vy:.6f}, vz={vz:.6f}")
```

## 运行

```bash
python build_an_hpop_configuration.py
```

## 实际输出

```text
轨道周期: 6000.000 s
中心天体: Earth
参考系: INERTIAL
采样点数: 11
首个采样 t=0.000 s
位置 (m): x=6771358.863, y=0.000, z=0.000
速度 (m/s): vx=0.000000, vy=6746.002785, vz=3662.780662
```

## 刚才发生了什么

上面的示例把所有可选分量都启用了一次，方便你看懂组装方式；实际任务中应根据精度需求裁剪，各分支的验证范围见 [传播器验证](../validation/propagator.md)。

`propagator.hpop_config(...)` 把多个力模型分量组装成一个 `HpopConfig` 对象。每个分量都有对应的构造器：

- `hpop_rkf78`：配置 RKF7(8) 数值积分器，可指定固定步长、误差容限和最大迭代次数。
- `hpop_two_body_gravity`：只使用中心天体二体引力。
- `hpop_gravity_field`：使用重力场文件，可指定阶次、潮汐模型和地球定向参数文件。
- `hpop_jacchia_roberts`：配置 Jacchia-Roberts 大气模型，用于大气阻力计算。
- `hpop_srp_spherical`：配置球形太阳辐射压模型，可指定阴影模型（`shadow_model`）、太阳位置和遮挡天体。
- `hpop_third_body`：为指定天体（如 Sun、Moon）开启第三方天体摄动。

`propagator.hpop(...)` 把这些配置发往 ASTROX，返回 `(period_s, position)`。`position.cartesian_velocity` 是 CZML 风格的 `[t, x, y, z, vx, vy, vz, ...]` 扁平序列，每 7 个数一帧，单位分别为秒、米、米/秒。与 `propagator.j2` 不同，HPOP 不暴露 `step_s` 参数，采样由积分器和服务器内部控制。

## 简化版：只配二体重力

如果任务暂时不需要重力场文件，最小配置可以简化为：

```python
config = propagator.hpop_config(
    central_body="Earth",
    gravity=propagator.hpop_two_body_gravity(),
)
```

此时 `hpop` 等价于用 HPOP 数值积分器传播二体问题，适合先验证接口再逐步加入摄动模型。

## 了解更多

- 各构造器的完整参数、单位与返回值说明请参阅 [传播器手册](../manual/propagator/README.md)。
- HPOP 各分支的验证状态、GMAT 交叉验证证据与已知残差请参阅 [传播器验证](../validation/propagator.md)。
- 更多可运行示例见 `examples/01_propagation/hpop.py`。
