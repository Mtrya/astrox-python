# Generate and inspect a CRTBP periodic orbit

This page solves one specific task: generate a periodic orbit from the Earth-Moon L1 Halo family, reconstruct it with fixed-x differential correction, and integrate one full period to inspect the first and last states. All CRTBP states, times, periods, and steps are nondimensional.

## Complete example

```python
import astrox
from astrox import libration


EARTH_MOON_MASS_RATIO = 0.01215058560962404

astrox.configure(base_url="http://astrox.cn:8765")

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

print(f"Period: {orbit.period:.12f}")
print(f"Corrected initial state: {state_values(orbit.corrected_state)}")
print(f"Sample count: {len(trajectory.samples)}")
print(f"Maximum absolute first/last state difference: {closure:.3e}")
```

Run the saved script from the repository root:

```bash
uv run python generate_a_crtbp_periodic_orbit.py
```

## Two decisions to make

### 1. Choose the family and amplitude definition

The three Earth-Moon periodic-orbit families use different parameter definitions:

| Family | Function | Amplitude definition |
| --- | --- | --- |
| L1 Halo | `earth_moon_l1_halo(z_amplitude=..., southern=...)` | `z_amplitude` is the z amplitude of the corrected initial state |
| L2 Halo | `earth_moon_l2_halo(x_amplitude=..., southern=...)` | `x_amplitude = corrected_state.x - 1.0` |
| DRO | `earth_moon_dro(x_amplitude=...)` | `x_amplitude = corrected_state.x - 1.0`, the x amplitude on the far side of the Moon |

L1 Halo does not use `x_amplitude`, and L2 Halo and DRO do not use `z_amplitude`. Do not combine them into one ambiguous generic amplitude.

For L2 Halo, do not pass the exactly rounded lower bound `0.026`; start at `0.0261`. For DRO, do not pass exactly `0.078`; start at `0.0781`.

### 2. Keep the origin and mass ratio consistent

`earth_moon_l1_halo`, `earth_moon_l2_halo`, and `earth_moon_dro` return primary-centered rotating-frame states, so the example explicitly passes `barycentric=False` for both correction and integration. The Earth-Moon family mass ratio is `0.01215058560962404`, and the same constant is reused by both subsequent functions.

The default gravitational parameters in `libration.units()` produce another mass ratio, which must not be mixed with Earth-Moon family states. For a custom primary-secondary system, call `libration.units(...)` with explicit gravitational parameters and mean separation, then reuse `unit_system.mass_ratio` in `positions(...)`, `crtbp_trajectory(...)`, and `correct_periodic_orbit_fixed_x(...)`.

If an initial guess is already in the barycentric rotating frame, pass `barycentric=True` to subsequent calls. The primary-centered and barycentric origins differ only in x:

```text
x_barycentric = x_primary_centered - mass_ratio
```

Velocity is unchanged.

## Correcting an initial guess

`correct_periodic_orbit_fixed_x` expects `initial_state` at an XZ-plane crossing, with `y`, `vx`, and `vz` near zero. It holds x fixed while correcting the other state components and the period.

`period_guess` must be a full-period guess, not a half period. When correcting a family result again, `family_member.period` is the clearest starting point. A custom guess that is too far from the target orbit may not converge, in which case ASTROX raises `AstroxAPIError`.

## Reading the result

`orbit` is a `PeriodicOrbit`:

- `initial_state` is the guess supplied for correction.
- `corrected_state` is the corrected periodic-orbit initial state.
- `period` is the nondimensional full period.
- `samples` contains one full period of `CrtbpSample` values.
- `is_barycentric` records whether the result uses a barycentric origin.

The example also calls `crtbp_trajectory` for one complete period and calculates the maximum absolute difference across the six first and last state components. This is a direct inspection of the returned orbit's closure and should not be treated as a universal acceptance threshold for other orbits.

## Learn more

- See the [libration points and CRTBP dynamics manual](../manual/libration/README.md) for all functions, parameters, return values, and coordinate conventions.
- See `examples/13_libration/libration_dynamics.py` for the repository's runnable version.
- See the [libration validation page](../../../validation/libration.md) for validation status across families, coordinate branches, and numerical ranges.
