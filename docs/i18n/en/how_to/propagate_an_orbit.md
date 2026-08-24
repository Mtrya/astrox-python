# How to propagate an orbit

This page solves a specific task: choose the right propagator from the orbit description you have, get position/velocity samples, and understand the returned results.

## Two decisions to make

1. **Input determines the propagator**:
   - You have Keplerian elements → use `propagator.j2` or `propagator.two_body`.
   - You have a Cartesian position/velocity state → use `propagator.two_body_rv` (pure two-body; returns a flat ephemeris sequence, not `(period_s, position)`).
   - You have a two-line element set (TLE) → use `propagator.sgp4`.
   - You have a force model config → use `propagator.hpop`.
2. **Reading the samples**: except for `two_body_rv`, all single-orbit propagation functions return `(period_s, position)`, where `position.cartesian_velocity` is a CZML-style flat sequence `[t, x, y, z, vx, vy, vz, ...]`.

## Complete example

The script below propagates once from each of three different inputs and prints the first sample.

```python
import astrox
from astrox import orbits, propagator

astrox.configure(base_url="http://astrox.cn:8765")


def print_first_sample(label, period_s, position):
    samples = position.cartesian_velocity
    t = samples[0]
    x, y, z, vx, vy, vz = samples[1:7]
    print(f"\n{label}")
    print(f"  Orbital period: {period_s:.3f} s")
    print(f"  Reference frame: {position.reference_frame}")
    print(f"  First sample t={t:.3f} s")
    print(f"  Position (m): x={x:.3f}, y={y:.3f}, z={z:.3f}")
    print(f"  Velocity (m/s): vx={vx:.6f}, vy={vy:.6f}, vz={vz:.6f}")


# 1. Keplerian elements + J2 model
orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=0.0,
    true_anomaly_deg=0.0,
)

period_s, position = propagator.j2(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T01:00:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    step_s=300.0,
)
print_first_sample("J2 propagation", period_s, position)


# 2. Two-line element set (TLE) + SGP4 model
ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

period_s, position = propagator.sgp4(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    step_s=300.0,
    tle=orbits.tle(
        line1=ISS_TLE[0],
        line2=ISS_TLE[1],
        catalog_number="25544",
    ),
)
print_first_sample("SGP4 propagation", period_s, position)


# 3. Keplerian elements + HPOP force model config
config = propagator.hpop_config(
    central_body="Earth",
    gravity=propagator.hpop_two_body_gravity(),
)

period_s, position = propagator.hpop(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    coord_system="Inertial",
    config=config,
)
print_first_sample("HPOP propagation", period_s, position)
```

## Run

```bash
python propagate_an_orbit.py
```

Actual output:

```text
J2 propagation
  Orbital period: 5553.624 s
  Reference frame: INERTIAL
  First sample t=0.000 s
  Position (m): x=6771358.863, y=0.000, z=0.000
  Velocity (m/s): vx=-0.000000, vy=6746.002785, vz=3662.780662

SGP4 propagation
  Orbital period: 5578.082 s
  Reference frame: INERTIAL
  First sample t=0.000 s
  Position (m): x=6367734.323, y=-2380661.222, z=-13622.073
  Velocity (m/s): vx=1669.577611, vy=4453.974636, vz=6005.161261

HPOP propagation
  Orbital period: 6000.000 s
  Reference frame: INERTIAL
  First sample t=0.000 s
  Position (m): x=6771358.863, y=0.000, z=0.000
  Velocity (m/s): vx=0.000000, vy=6746.002785, vz=3662.780662
```

## Return value description

`period_s` is the orbital period returned by ASTROX, in seconds. `position` is a `PropagatorPosition` object containing the following fields:

- `central_body`: central body.
- `epoch`: start epoch of the position samples.
- `reference_frame`: reference frame, e.g. `INERTIAL`, `FIXED`.
- `interpolation_algorithm`: interpolation algorithm.
- `interpolation_degree`: interpolation degree.
- `cartesian_velocity`: CZML-style `[t, x, y, z, vx, vy, vz, ...]` sample sequence.

Every 7 numbers in `cartesian_velocity` form one frame: time offset (seconds), position X/Y/Z (meters), velocity X/Y/Z (meters per second). When `reference_frame` is `INERTIAL` it corresponds to an inertial reference frame; the `INERTIAL` frame returned by SGP4 corresponds to a GCRF/GCRS-style inertial coordinate frame.

## Which propagator to choose

| Your input | Recommended propagator | Notes |
| --- | --- | --- |
| Keplerian elements | `propagator.j2` | Includes J2 perturbation; suitable for most LEO missions. |
| Keplerian elements, pure two-body | `propagator.two_body` | Only central-body gravity; fastest computation. |
| Cartesian position/velocity state | `propagator.two_body_rv` | Fixed-step numerical two-body integration; returns a flat ephemeris sequence `[t, x, y, z, vx, vy, vz, ...]`. |
| Two-line element set (TLE) | `propagator.sgp4` | Propagates directly from TLE; no need to build elements manually. |
| Need to configure a force model | `propagator.hpop` | Supports gravity field, atmosphere, solar radiation pressure, third-body perturbations, and more. |

For batch propagation, use `propagator.multi_j2`, `propagator.multi_two_body`, and `propagator.multi_sgp4`; they bring multiple states to a common target epoch.

## Learn more

- For full parameters, units, and return values of each propagator, see the [propagator manual](../manual/propagator/README.md).
- For orbit constructors and conversion functions, see the [orbits manual](../manual/orbits/README.md).
- For verification status and cross-validation evidence for each branch, see the [propagator validation page](../../../validation/propagator.md).
