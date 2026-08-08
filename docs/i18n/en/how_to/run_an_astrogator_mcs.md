# How to run an Astrogator mission sequence

This page solves one specific task: run the simplest possible mission with Astrogator RunMCS — define an initial state, propagate for 1 second with a custom two-body propagator, then understand the returned result. This is also the foundation for building more complex missions (maneuvers, nested sequences, target sequences).

## Three things you must know

1. **The propagator must be registered explicitly**: RunMCS provides no default propagator; the `propagator_name` in the `propagate` segment must point to the `propagator.hpop_config` you registered in `run_mcs(propagators=...)`.
2. **The gravitational parameter must be given explicitly**: both the Keplerian initial state and the custom two-body gravity model need `gravitational_parameter_m3_s2` (use `398600441500000.0` for Earth, in m³/s²). If you omit it in either place, the results are unreliable or the request is rejected outright.
3. **Results are returned in execution order**: `run_mcs` returns a `RunMCSResult`; `main_sequence_results` holds the segment results that actually execute and produce output, and `final_state` is the segment's final state. With an enabled Stop, the Stop segment itself and the segments after it produce no results.

## Full example

The script below defines a two-segment mission: first set up a Keplerian initial state, then propagate for 1 second with the explicitly registered two-body propagator.

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
print(f"Mission succeeded: {result.is_success}")
print(f"Propagation duration: {coast.duration_s:.3f} s")
print(f"Stopping condition: {coast.stopping_condition_name}")
print(f"Final epoch: {coast.final_state.epoch}")
print(f"Final position X: {coast.final_state.cartesian.x_m:.3f} m")
```

## Running the example

```bash
python examples/07_astrogator/run_mcs.py
```

The actual output is as follows (values come from the ASTROX server and may differ slightly from your run):

```text
Mission succeeded: True
Propagation duration: 1.000 s
Stopping condition: One Second
Final epoch: 2026-01-01T00:00:01.000Z
Final position X: 3092629.662 m
```

## How to read the result

`result` is an `astrogator.RunMCSResult`, which contains:

- `is_success`: whether the mission succeeded. When the server returns a failure, the SDK raises an exception directly, so whenever you can get a result it is always `True`.
- `main_sequence_results`: the tuple of segment results in execution order for the segments that actually execute and produce output. There is no Stop segment here; the last item `coast` is the propagation segment's result, of type `PropagateResult`.
- `positions`: CZML position samples. When `compute_czml_positions` is not passed, the SDK does not send the field and the server decides whether samples are computed; pass explicit `compute_czml_positions=True` to `run_mcs` when you need trajectory samples for visualization. When the response contains no samples, this field is `None`.

Commonly used fields on the propagation segment result:

- `duration_s`: segment duration, in seconds. Here it is 1.0, matching the duration of `duration_stop("One Second", 1.0)`.
- `stopping_condition_name`: the name of the stopping condition that actually triggered, matching the name in the request.
- `final_state`: the segment's final state (`SegmentState`); `final_state.epoch` is the final epoch, and `final_state.cartesian` is the Cartesian position/velocity (`x_m`, `y_m`, `vx_m_s`, etc., in m and m/s). It also provides `keplerian` (Keplerian elements, including `period_s`) and `spherical` representations, which can cross-check each other.

## Extending from here

- Add a maneuver: `impulsive_maneuver` (along the velocity direction with `impulsive_velocity_vector`) or `finite_maneuver` (requires registering an engine with `constant_engine`).
- Change the stopping condition: `epoch_stop`, `periapsis_stop`, `apoapsis_stop`.
- Composition and targeting: nest subsequences with `sequence`, or use `target_sequence` plus a differential corrector for variable adjustment.
- Get intermediate values: add scalar definitions such as `duration_scalar` and `keplerian_scalar` to a segment's `results` parameter; the values are in the segment's `scalar_results` dictionary.

## Learn more

- For concepts, all constructors, parameters/units, the result tree, and explicit limitations, see the [Astrogator manual](../manual/astrogator/README.md).
- For the propagator configuration constructors, see the [propagator manual](../manual/propagator/README.md).
- For the verification status of each branch, see the [validation documents](../../../validation/README.md).
