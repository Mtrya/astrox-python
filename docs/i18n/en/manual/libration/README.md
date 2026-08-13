# Libration points and CRTBP dynamics

`astrox.libration` provides libration points, unit systems, trajectory integration, Earth-Moon periodic-orbit families, and fixed-x differential correction for the circular restricted three-body problem (CRTBP). The recommended import is:

```python
from astrox import libration
```

> CRTBP positions, velocities, times, and periods in this module are nondimensional. Only the gravitational parameters and unit scales in `LibrationUnitSystem` carry explicit SI units.

This page is organized by coordinate and unit conventions, return-value objects, function reference, and complete examples. Optional parameters that are not supplied are omitted from the ASTROX request so the server retains its defaults.

## Coordinates, mass ratio, and units

The CRTBP mass ratio is:

```text
mass_ratio = m2 / (m1 + m2)
```

Here, `m1` is the primary-body mass and `m2` is the secondary-body mass. `positions` returns libration points in the barycentric rotating frame. `crtbp_trajectory` and `correct_periodic_orbit_fixed_x` support both barycentric and primary-centered rotating frames. For the same state, the two origin conventions are related by:

```text
x_barycentric = x_primary_centered - mass_ratio
```

The `y`, `z`, and three velocity components are unchanged. In the primary-centered rotating frame, the primary is at `x=0` and the secondary is at `x=1`.

`libration.units()` converts the primary and secondary gravitational parameters and mean separation into CRTBP length, time, and velocity scales. Convert between nondimensional and SI values with:

```text
position_m = position * length_unit_m
time_s = time * time_unit_s
velocity_m_s = velocity * velocity_unit_m_s
```

The default gravitational parameters used by `libration.units()` produce a different `mass_ratio` from the value `0.01215058560962404` used by the Earth-Moon periodic-orbit families. When connecting unit systems, libration points, trajectory integration, and Earth-Moon families, explicitly reuse one `mass_ratio`. Do not mix the default `libration.units()` mass ratio with states from `earth_moon_l1_halo`, `earth_moon_l2_halo`, or `earth_moon_dro`.

## Return values and state objects

### `libration.CrtbpState` / `libration.crtbp_state(...)`

```python
libration.crtbp_state(
    *,
    x: float,
    y: float,
    z: float,
    vx: float,
    vy: float,
    vz: float,
) -> CrtbpState
```

`crtbp_state(...)` creates an immutable `CrtbpState`. The field order is position `x, y, z` followed by rotating-frame velocity `vx, vy, vz`; all fields are nondimensional.

```python
state = libration.crtbp_state(
    x=1.189017399646985,
    y=0.0,
    z=0.06060558718057466,
    vx=0.0,
    vy=-0.17403902743307584,
    vz=0.0,
)

print(state.x, state.y, state.z)
print(state.vx, state.vy, state.vz)
```

### Other return types

| Type | Main fields | Description |
| --- | --- | --- |
| `LibrationPoint` | `x`, `y` | One nondimensional libration-point coordinate |
| `LibrationPoints` | `l1`–`l5`, `l1_distance_to_secondary`, `l2_distance_to_secondary`, `l3_distance_to_primary` | Five libration points and the nondimensional distances from the three collinear points to their nearby body |
| `LibrationUnitSystem` | `primary_gravitational_parameter_m3_s2`, `secondary_gravitational_parameter_m3_s2`, `mass_ratio`, `length_unit_m`, `time_unit_s`, `velocity_unit_m_s` | Dimensional scales for one CRTBP system |
| `CrtbpSample` | `time`, `state` | A CRTBP state at one nondimensional time |
| `CrtbpTrajectory` | `mass_ratio`, `is_barycentric`, `samples` | An integrated trajectory; `samples` is a tuple of `CrtbpSample` values |
| `PeriodicOrbit` | `is_barycentric`, `period`, `initial_state`, `corrected_state`, `samples` | The original guess, corrected initial state, and one sampled period of a periodic orbit |

`PeriodicOrbit.initial_state` is the initial guess used for family generation or correction. `corrected_state` is the corrected initial state used for integration. `period` and each sample's `time` are nondimensional.

## Libration points

### `libration.positions`

```python
libration.positions(*, mass_ratio: float) -> LibrationPoints
```

Computes L1-L5 for a supplied mass ratio and returns nondimensional barycentric rotating-frame coordinates.

| Parameter | Unit | Description |
| --- | --- | --- |
| `mass_ratio` | — | Required, `m2 / (m1 + m2)` |

```python
EARTH_MOON_MASS_RATIO = 0.01215058560962404

points = libration.positions(mass_ratio=EARTH_MOON_MASS_RATIO)
print(points.l1.x, points.l1.y)
print(points.l4.x, points.l4.y)
```

`l1_distance_to_secondary` and `l2_distance_to_secondary` are the distances from L1 and L2 to the secondary. `l3_distance_to_primary` is the distance from L3 to the primary.

## Unit systems

### `libration.units`

```python
libration.units(
    *,
    primary_gravitational_parameter_m3_s2: float | None = None,
    secondary_gravitational_parameter_m3_s2: float | None = None,
    mean_separation_m: float | None = None,
) -> LibrationUnitSystem
```

Computes the mass ratio and nondimensionalization scales for a primary-secondary system.

| Parameter | Unit | Description |
| --- | --- | --- |
| `primary_gravitational_parameter_m3_s2` | m³/s² | Optional primary-body gravitational parameter |
| `secondary_gravitational_parameter_m3_s2` | m³/s² | Optional secondary-body gravitational parameter |
| `mean_separation_m` | m | Optional mean separation of the two bodies |

```python
unit_system = libration.units(
    primary_gravitational_parameter_m3_s2=398600441800000.0,
    secondary_gravitational_parameter_m3_s2=4904869500000.0,
    mean_separation_m=384400000.0,
)

print(unit_system.mass_ratio)
print(unit_system.length_unit_m)
print(unit_system.time_unit_s)
print(unit_system.velocity_unit_m_s)
```

All three parameters may be omitted, in which case the server uses its defaults. For a custom primary-secondary system, pass `unit_system.mass_ratio` to subsequent `positions` and `crtbp_trajectory` calls.

## CRTBP trajectory integration

### `libration.crtbp_trajectory`

```python
libration.crtbp_trajectory(
    *,
    initial_state: CrtbpState,
    mass_ratio: float,
    start_time: float | None = None,
    end_time: float | None = None,
    barycentric: bool | None = None,
    output_step: float | None = None,
) -> CrtbpTrajectory
```

Numerically integrates a nondimensional initial state in a CRTBP rotating frame.

| Parameter | Unit | Description |
| --- | --- | --- |
| `initial_state` | nondimensional | Required `CrtbpState` |
| `mass_ratio` | — | Required; must match the primary-secondary system of the state |
| `start_time` | nondimensional | Optional integration start time |
| `end_time` | nondimensional | Optional integration end time; may be less than `start_time` for reverse integration |
| `barycentric` | — | `True` selects a barycentric origin; `False` selects a primary-centered origin |
| `output_step` | nondimensional | Output step; `0.0` returns adaptive integration nodes, while other values request that step |

```python
trajectory = libration.crtbp_trajectory(
    initial_state=state,
    mass_ratio=0.01215058560962404,
    start_time=0.0,
    end_time=0.2,
    barycentric=False,
    output_step=0.05,
)

for sample in trajectory.samples:
    print(sample.time, sample.state.x, sample.state.y, sample.state.z)
```

`trajectory.mass_ratio` and `trajectory.is_barycentric` record the mass ratio and origin convention used for the returned trajectory.

## Earth-Moon periodic-orbit families

### `libration.earth_moon_l1_halo`

```python
libration.earth_moon_l1_halo(
    *,
    z_amplitude: float | None = None,
    southern: bool | None = None,
) -> PeriodicOrbit
```

Returns an Earth-Moon L1 Halo periodic orbit. `z_amplitude` is the nondimensional z amplitude of the corrected initial state; its recommended range is `0.022`-`0.199`. `southern=False` selects the northern Halo and `southern=True` selects the southern Halo.

### `libration.earth_moon_l2_halo`

```python
libration.earth_moon_l2_halo(
    *,
    x_amplitude: float | None = None,
    southern: bool | None = None,
) -> PeriodicOrbit
```

Returns an Earth-Moon L2 Halo periodic orbit. `x_amplitude` is the nondimensional `corrected_state.x - 1.0` in the primary-centered rotating frame. Use a value slightly above `0.026` and no greater than `0.1928`. The server rejects the exactly rounded lower bound `0.026`; `0.0261` is a practical starting value. `southern` selects the northern or southern Halo branch.

### `libration.earth_moon_dro`

```python
libration.earth_moon_dro(*, x_amplitude: float | None = None) -> PeriodicOrbit
```

Returns a planar Earth-Moon distant retrograde orbit (DRO). `x_amplitude` is the nondimensional amplitude on the far side of the Moon and is also defined as `corrected_state.x - 1.0`. Use a value slightly above `0.078` and no greater than `0.520`. The server rejects the exactly rounded lower bound `0.078`; `0.0781` is a practical starting value.

```python
l1 = libration.earth_moon_l1_halo(z_amplitude=0.05, southern=False)
l2 = libration.earth_moon_l2_halo(x_amplitude=0.10, southern=True)
dro = libration.earth_moon_dro(x_amplitude=0.1801)

print(l1.period, l1.corrected_state)
print(l2.period, l2.corrected_state)
print(dro.period, dro.corrected_state)
```

All three functions return a `PeriodicOrbit` in the primary-centered rotating frame, so `is_barycentric` is `False`. The L1 Halo `z_amplitude` and the L2 Halo/DRO `x_amplitude` are different family parameters and retain their separate definitions.

## Fixed-x periodic-orbit correction

### `libration.correct_periodic_orbit_fixed_x`

```python
libration.correct_periodic_orbit_fixed_x(
    *,
    initial_state: CrtbpState,
    period_guess: float,
    mass_ratio: float,
    barycentric: bool | None = None,
    output_step: float | None = None,
) -> PeriodicOrbit
```

Holds the initial x coordinate fixed while correcting z position, y velocity, and period to generate a CRTBP periodic orbit symmetric about the XZ plane. `initial_state` should be an XZ-plane-crossing state, with `y`, `vx`, and `vz` near zero.

| Parameter | Unit | Description |
| --- | --- | --- |
| `initial_state` | nondimensional | Required XZ-plane-crossing state to correct |
| `period_guess` | nondimensional | Required full-period guess; do not pass a half period |
| `mass_ratio` | — | Required; must match the system of the initial state |
| `barycentric` | — | `True` uses a barycentric origin for both input and output; `False` uses a primary-centered origin |
| `output_step` | nondimensional | Output step for the returned orbit; `0.0` returns adaptive integration nodes |

```python
EARTH_MOON_MASS_RATIO = 0.01215058560962404

family_member = libration.earth_moon_l1_halo(
    z_amplitude=0.05,
    southern=False,
)

corrected = libration.correct_periodic_orbit_fixed_x(
    initial_state=family_member.corrected_state,
    period_guess=family_member.period,
    mass_ratio=EARTH_MOON_MASS_RATIO,
    barycentric=False,
    output_step=0.05,
)

print(corrected.period)
print(corrected.corrected_state)
```

In the correction result, `initial_state` preserves the caller's guess and `corrected_state.x` equals the guess's x coordinate. ASTROX rejects a result that does not converge because the state is too far from a target orbit or the period guess is unsuitable.

## Changing the coordinate origin

To convert a primary-centered state to a barycentric state, subtract the mass ratio from x:

```python
mass_ratio = 0.01215058560962404
primary_centered = l1.corrected_state

barycentric = libration.crtbp_state(
    x=primary_centered.x - mass_ratio,
    y=primary_centered.y,
    z=primary_centered.z,
    vx=primary_centered.vx,
    vy=primary_centered.vy,
    vz=primary_centered.vz,
)
```

Pass `barycentric=True` to `crtbp_trajectory` or `correct_periodic_orbit_fixed_x` so the coordinate values and declared origin remain consistent.

## Errors and related material

`crtbp_trajectory` and `correct_periodic_orbit_fixed_x` accept only `CrtbpState` state inputs. A type mismatch raises `TypeError`; an `IsSuccess=false` response raises `astrox.exceptions.AstroxAPIError`; HTTP errors, request timeouts, and connection failures raise `AstroxHTTPError`, `AstroxTimeoutError`, and `AstroxConnectionError`, respectively. The SDK does not impose additional physical plausibility checks on amplitudes, guesses, or mass ratios.

- See [Generate and inspect a CRTBP periodic orbit](../../how_to/generate_a_crtbp_periodic_orbit.md) for a task-oriented walkthrough.
- See `examples/13_libration/libration_dynamics.py` for a runnable example.
- See the [libration validation page](../../../../validation/libration.md) for validation scope and known limitations.
