# Build an HPOP force model config

This page solves a specific task: build an HPOP force model config using the `propagator.hpop_config(...)` family of constructors, and run one high-precision orbit propagation with it.

## Two decisions to make

1. **Choose force-model components for the task**: an HPOP config is built by stacking optional components: integrator, gravity field, atmosphere, solar radiation pressure, third-body perturbations, and more. For simple tasks you can use two-body gravity alone; when higher precision is needed, add gravity-field degree/order, atmospheric drag, solar radiation pressure, and lunar/solar third-body perturbations layer by layer.
2. **Choose the coordinate system**: `coord_system` determines the reference frame of the output positions. `"Inertial"` corresponds to inertial-frame output, and `"Fixed"` corresponds to Earth-fixed-frame output. As with J2/two-body propagation, the default is determined by the server, but it is recommended to specify it explicitly in the call.

## Complete example

The script below builds an HPOP force model config with all optional components enabled, then runs a 10-minute propagation from Keplerian elements. Save it as `build_an_hpop_configuration.py`:

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

## Run

```bash
python build_an_hpop_configuration.py
```

## Actual output

```text
轨道周期: 6000.000 s
中心天体: Earth
参考系: INERTIAL
采样点数: 11
首个采样 t=0.000 s
位置 (m): x=6771358.863, y=0.000, z=0.000
速度 (m/s): vx=0.000000, vy=6746.002785, vz=3662.780662
```

## What just happened

The example above enables every optional component once so you can see how they fit together. In real tasks, trim the config to the precision you need; verification coverage for each branch is in the [propagator validation page](../../../validation/propagator.md).

`propagator.hpop_config(...)` assembles multiple force-model components into an `HpopConfig` object. Each component has a matching constructor:

- `hpop_rkf78`: configures the RKF7(8) numerical integrator; supports fixed step size, error tolerances, and maximum iterations.
- `hpop_two_body_gravity`: uses only central-body two-body gravity.
- `hpop_gravity_field`: uses a gravity-field file; supports degree/order, tide model, and Earth-orientation parameter file.
- `hpop_jacchia_roberts`: configures the Jacchia-Roberts atmosphere model for drag computation.
- `hpop_srp_spherical`: configures the spherical solar-radiation-pressure model; supports shadow model (`shadow_model`), Sun position, and eclipsing bodies.
- `hpop_third_body`: enables third-body perturbation for a specified body (e.g. Sun, Moon).

`propagator.hpop(...)` sends these settings to ASTROX and returns `(period_s, position)`. `position.cartesian_velocity` is a CZML-style flat `[t, x, y, z, vx, vy, vz, ...]` sequence, with one frame every 7 numbers; units are seconds, meters, and meters per second. Unlike `propagator.j2`, HPOP does not expose a `step_s` parameter; sampling is controlled internally by the integrator and the server.

## Simplified version: two-body gravity only

If the task does not yet need a gravity-field file, the minimal config can be simplified to:

```python
config = propagator.hpop_config(
    central_body="Earth",
    gravity=propagator.hpop_two_body_gravity(),
)
```

At this point `hpop` is equivalent to propagating the two-body problem with the HPOP numerical integrator, which is useful for verifying the interface before adding perturbation models one by one.

## Learn more

- For full parameters, units, and return-value descriptions of each constructor, see the [propagator manual](../manual/propagator/README.md).
- For verification status, GMAT cross-validation evidence, and known residuals for HPOP branches, see the [propagator validation page](../../../validation/propagator.md).
- More runnable examples are available at `examples/01_propagation/hpop.py`.
