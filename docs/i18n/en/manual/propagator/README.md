# Propagator

`astrox.propagator` provides the public API for orbit propagation and ballistic trajectory computation, including two-body, J2, SGP4, simple ascent, HPOP, and ballistic models. The recommended import style is:

```python
from astrox import orbits, propagator
```

This page is organized by concept, return-value conventions, function-family reference, and examples. All parameters use `snake_case`; parameters that carry units use explicit suffixes such as `_m`, `_deg`, and `_s`. Optional parameters are not sent to ASTROX when omitted; the server retains its defaults. For full control over the request payload, use `astrox.raw`.

## Orbit Input

Propagation functions accept `orbits.KeplerianElements` or `orbits.CartesianState` as the orbit description; `propagator.sgp4` accepts `orbits.Tle` two-line element data. `orbits.keplerian(...)` constructs an orbit from six Keplerian elements, `orbits.cartesian_state(...)` constructs a Cartesian state from position/velocity, and `orbits.tle(...)` constructs a TLE from two-line element data. The epoch `orbit_epoch` applies only to `KeplerianElements` or `CartesianState` orbit input; it is separate from the elements or state and is received by the propagation function on its own. `propagator.sgp4` does not accept `orbit_epoch`; its propagation epoch comes from the epoch encoded in the TLE.

```python
orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=0.0,
    true_anomaly_deg=0.0,
)
```

For details on orbit constructors, see the [orbits manual](../orbits/README.md).

## Return Values

Single-orbit propagation functions return a `(period_s, position)` tuple:

- `period_s`: `float`, the orbital period returned by ASTROX, in seconds.
- `position`: `propagator.PropagatorPosition` frozen dataclass with the following fields:

| Field | Type | Description |
| --- | --- | --- |
| `central_body` | `str` | Central body |
| `epoch` | `str` | Start epoch of the position samples |
| `reference_frame` | `str` | Reference frame, e.g. `INERTIAL`, `FIXED` |
| `interpolation_algorithm` | `str` | Interpolation algorithm |
| `interpolation_degree` | `int` | Interpolation degree |
| `cartesian_velocity` | `tuple[float, ...]` | CZML-style `[t, x, y, z, vx, vy, vz, ...]` sample sequence |

The coordinates and velocities in `cartesian_velocity` use the units consistent with `reference_frame`; `INERTIAL` corresponds to an inertial reference frame, and `FIXED` corresponds to an Earth-fixed reference frame. The `INERTIAL` frame returned by SGP4 corresponds to a GCRF/GCRS-style inertial coordinate frame.

Batch propagation functions `multi_j2`, `multi_two_body`, and `multi_sgp4` return `tuple[orbits.KeplerianElements, ...]`, i.e. a tuple of Keplerian elements at the target epoch. Each element in the raw ASTROX response also contains a `GravitationalParameter` field, which is omitted from the SDK-parsed return value; for the full raw response, use `astrox.raw`.

## J2 and Two-Body Propagation

### `propagator.j2`

```python
propagator.j2(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
    j2_normalized_value: float | None = None,
    ref_distance_m: float | None = None,
) -> tuple[float, PropagatorPosition]
```

Propagates Keplerian elements starting from `orbit_epoch` using the J2 model. `j2_normalized_value` is the normalized J2 coefficient, and `ref_distance_m` is the reference distance; both override server defaults.

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Propagation start time string |
| `stop` | — | Propagation stop time string |
| `orbit_epoch` | — | Orbit elements epoch string |
| `orbit` | — | `orbits.KeplerianElements` instance |
| `step_s` | s | Sampling step size |
| `central_body` | — | Central body name |
| `gravitational_parameter_m3_s2` | m³/s² | Gravitational parameter |
| `coord_system` | — | Coordinate system, e.g. `Inertial` |
| `j2_normalized_value` | — | Normalized J2 value |
| `ref_distance_m` | m | J2 reference distance |

```python
period_s, position = propagator.j2(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    step_s=300.0,
    coord_system="Inertial",
    gravitational_parameter_m3_s2=398600441500000.0,
    j2_normalized_value=0.000484165143790815,
    ref_distance_m=6378137.0,
)
```

A complete runnable example is available at `examples/01_propagation/j2_classical.py`.

### `propagator.two_body`

```python
propagator.two_body(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
) -> tuple[float, PropagatorPosition]
```

Propagates Keplerian elements using the two-body model. Parameters are the same as for `j2`, except `j2_normalized_value` and `ref_distance_m` are not accepted.

```python
period_s, position = propagator.two_body(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    gravitational_parameter_m3_s2=398600441500000.0,
)
```

A complete runnable example is available at `examples/01_propagation/two_body_classical.py`.

## Batch Propagation

Batch propagation brings multiple states or TLEs to a common target epoch `epoch`.

### `propagator.multi_j2`

```python
propagator.multi_j2(
    *,
    epoch: str,
    states: Sequence[tuple[str, KeplerianElements]],
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[KeplerianElements, ...]
```

Propagates multiple Keplerian-element sets to `epoch` using the J2 model. Each item in `states` is `(orbit_epoch, orbit)`, where `orbit_epoch` is the epoch string for that state and `orbit` is a `KeplerianElements` instance.

### `propagator.multi_two_body`

```python
propagator.multi_two_body(
    *,
    epoch: str,
    states: Sequence[tuple[str, KeplerianElements]],
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[KeplerianElements, ...]
```

Batch propagation using the two-body model. If `gravitational_parameter_m3_s2` is provided, it is written into each input state.

### `propagator.multi_sgp4`

```python
propagator.multi_sgp4(
    *,
    epoch: str,
    tle_sets: Sequence[tuple[str, str]],
) -> tuple[KeplerianElements, ...]
```

Propagates multiple two-line element sets (TLEs) to `epoch` using SGP4. Each item in `tle_sets` is a pair containing the first and second TLE lines.

```python
leo = orbits.keplerian(...)
inclined = orbits.keplerian(...)

states = [
    ("2024-01-01T00:00:00.000Z", leo),
    ("2024-01-01T00:03:00.000Z", inclined),
]

elements = propagator.multi_two_body(
    epoch="2024-01-01T00:10:00.000Z",
    states=states,
    gravitational_parameter_m3_s2=398600441500000.0,
)
```

A complete runnable example is available at `examples/01_propagation/batch_propagators.py`.

## SGP4 Propagation

### `propagator.sgp4`

```python
propagator.sgp4(
    *,
    start: str,
    stop: str,
    tle: Tle,
    step_s: float | None = None,
) -> tuple[float, PropagatorPosition]
```

Propagates a satellite orbit from a two-line element set (TLE) using the SGP4 model. `tle` must be an `orbits.Tle` instance constructed with `orbits.tle(...)`; when the TLE provides a `catalog_number`, the SDK sends it to ASTROX as the satellite number, and when it is not provided nothing is sent.

| Parameter | Description |
| --- | --- |
| `start` | Propagation start time string |
| `stop` | Propagation stop time string |
| `tle` | `orbits.Tle` instance containing the first and second TLE lines |
| `step_s` | Sampling step size |

```python
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
```

For the field descriptions of `orbits.tle(...)`, see the [orbits manual](../orbits/README.md). A complete runnable example is available at `examples/01_propagation/sgp4_tle.py`.

## Simple Ascent

### `propagator.simple_ascent`

```python
propagator.simple_ascent(
    *,
    start: str,
    stop: str,
    launch_latitude_deg: float,
    launch_longitude_deg: float,
    launch_altitude_m: float,
    burnout_velocity_m_s: float,
    burnout_latitude_deg: float,
    burnout_longitude_deg: float,
    burnout_altitude_m: float,
    step_s: float | None = None,
    central_body: str | None = None,
) -> tuple[float, PropagatorPosition]
```

Generates a simple ascent trajectory from launch-point and burnout-point parameters.

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Start time string |
| `stop` | — | Stop time string |
| `launch_latitude_deg` | deg | Launch-point latitude |
| `launch_longitude_deg` | deg | Launch-point longitude |
| `launch_altitude_m` | m | Launch-point altitude |
| `burnout_velocity_m_s` | m/s | Burnout velocity |
| `burnout_latitude_deg` | deg | Burnout-point latitude |
| `burnout_longitude_deg` | deg | Burnout-point longitude |
| `burnout_altitude_m` | m | Burnout-point altitude |
| `step_s` | s | Sampling step size |
| `central_body` | — | Central body |

```python
period_s, position = propagator.simple_ascent(
    start="2024-01-01T03:00:00.000Z",
    stop="2024-01-01T03:02:00.000Z",
    step_s=30.0,
    central_body="Earth",
    launch_latitude_deg=40.9575,
    launch_longitude_deg=100.2912,
    launch_altitude_m=1000.0,
    burnout_velocity_m_s=7800.0,
    burnout_latitude_deg=41.3,
    burnout_longitude_deg=101.0,
    burnout_altitude_m=200000.0,
)
```

A complete runnable example is available at `examples/01_propagation/simple_ascent.py`.

## HPOP High-Precision Propagation

HPOP supports high-precision numerical propagation from either Keplerian elements or a Cartesian state, using a force-model configuration.

### `propagator.hpop`

```python
propagator.hpop(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements | None = None,
    state: CartesianState | None = None,
    config: HpopConfig | Mapping[str, Any] | None = None,
    coord_system: str | None = None,
    coord_epoch: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coefficient_of_drag: float | None = None,
    area_mass_ratio_drag_m2_kg: float | None = None,
    coefficient_of_srp: float | None = None,
    area_mass_ratio_srp_m2_kg: float | None = None,
) -> tuple[float, PropagatorPosition]
```

Exactly one of `orbit` or `state` must be provided. `config` may be an `HpopConfig` object or a raw dict matching the known ASTROX structure.

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Propagation start time string |
| `stop` | — | Propagation stop time string |
| `orbit_epoch` | — | Orbit epoch string |
| `orbit` | — | Keplerian-elements input |
| `state` | — | Cartesian-state input |
| `config` | — | HPOP configuration object or mapping |
| `coord_system` | — | Coordinate system |
| `coord_epoch` | — | Coordinate epoch |
| `gravitational_parameter_m3_s2` | m³/s² | Gravitational parameter |
| `coefficient_of_drag` | — | Drag coefficient |
| `area_mass_ratio_drag_m2_kg` | m²/kg | Drag area-to-mass ratio |
| `coefficient_of_srp` | — | Solar-radiation-pressure coefficient |
| `area_mass_ratio_srp_m2_kg` | m²/kg | Solar-radiation-pressure area-to-mass ratio |

### HPOP Configuration Constructors

These constructors return frozen SDK value objects and send only the fields explicitly provided by the caller.

#### `propagator.hpop_config`

```python
propagator.hpop_config(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    central_body: str | None = None,
    integrator: HpopIntegrator | None = None,
    gravity: HpopGravity | None = None,
    atmosphere: HpopAtmosphere | None = None,
    srp: HpopSrp | None = None,
    third_bodies: Sequence[HpopThirdBody] | None = None,
) -> HpopConfig
```

#### `propagator.hpop_rkf78`

```python
propagator.hpop_rkf78(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    use_fixed_step: bool | None = None,
    initial_step_s: float | None = None,
    max_step_s: float | None = None,
    min_step_s: float | None = None,
    max_abs_error: float | None = None,
    max_rel_error: float | None = None,
    max_iterations: int | None = None,
) -> HpopIntegrator
```

Configures the RKF7(8) numerical integrator.

#### `propagator.hpop_two_body_gravity`

```python
propagator.hpop_two_body_gravity(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
) -> HpopGravity
```

Uses the two-body gravity model. When `gravitational_parameter_m3_s2` is supplied, it is written into the `Mu` field of the gravity model in the request, overriding the central body's default gravitational parameter (units m³/s²); when omitted, the field is not sent to ASTROX and the server uses the central body default. Explicit `Mu` is the value used by the validated RunMCS two-body propagation scenario; in that scenario an omission cannot be claimed to carry the same two-body physical semantics.

#### `propagator.hpop_gravity_field`

```python
propagator.hpop_gravity_field(
    *,
    gravity_file_name: str,
    degree: int,
    order: int,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    use_secular_variations: bool | None = None,
    solid_tide_type: str | None = None,
    eop_file_path: str | None = None,
) -> HpopGravity
```

Configures the gravity-field model. `gravity_file_name` is the gravity-field file; `degree` and `order` are the model degree and order.

#### `propagator.hpop_jacchia_roberts`

```python
propagator.hpop_jacchia_roberts(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    drag_model_type: str | None = None,
    atmos_data_source: str | None = None,
    f10p7: float | None = None,
    f10p7_avg: float | None = None,
    kp: float | None = None,
) -> HpopAtmosphere
```

Configures the Jacchia-Roberts atmosphere model.

#### `propagator.hpop_srp_spherical`

```python
propagator.hpop_srp_spherical(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    shadow_model: str | None = None,
    sun_position: str | None = None,
    eclipsing_bodies: Sequence[str] | None = None,
) -> HpopSrp
```

Configures the spherical solar-radiation-pressure model.

#### `propagator.hpop_third_body`

```python
propagator.hpop_third_body(
    third_body_name: str,
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    mode_type: str | None = None,
    ephem_source: str | None = None,
    grav_source: str | None = None,
    mu_m3_s2: float | None = None,
) -> HpopThirdBody
```

Configures third-body perturbation. `third_body_name` is the name of the body.

```python
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
)

period_s, position = propagator.hpop(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    coord_system="Inertial",
    gravitational_parameter_m3_s2=398600441500000.0,
    config=config,
)
```

Cartesian-state input:

```python
state = orbits.cartesian_state(
    x_m=7000000.0,
    y_m=1000.0,
    z_m=2000.0,
    vx_m_s=-1.0,
    vy_m_s=7500.0,
    vz_m_s=10.0,
)

period_s, position = propagator.hpop(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    state=state,
    config=propagator.hpop_config(
        central_body="Earth",
        gravity=propagator.hpop_two_body_gravity(),
    ),
)
```

A complete runnable example is available at `examples/01_propagation/hpop.py`.

## Ballistic Propagation

Ballistic propagation computes the suborbital trajectory from a launch point to an impact point. There are five functions: one nominal function and four that solve under different constraints. All functions return `(period_s, position)`.

| Function | Additional Required Parameters | Constraint Type |
| --- | --- | --- |
| `propagator.ballistic` | None | Nominal ballistic trajectory |
| `propagator.ballistic_delta_v` | `delta_v_m_s` | Delta-v |
| `propagator.ballistic_delta_v_min_ecc` | `delta_v_m_s` | Minimum-eccentricity delta-v |
| `propagator.ballistic_apogee_altitude` | `apogee_altitude_m` | Apogee altitude |
| `propagator.ballistic_time_of_flight` | `time_of_flight_s` | Time of flight |

Common parameters:

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Start time string |
| `impact_latitude_deg` | deg | Impact-point latitude |
| `impact_longitude_deg` | deg | Impact-point longitude |
| `stop` | — | Stop time string |
| `step_s` | s | Sampling step size |
| `central_body` | — | Central body |
| `gravitational_parameter_m3_s2` | m³/s² | Gravitational parameter |
| `launch_latitude_deg` | deg | Launch-point latitude |
| `launch_longitude_deg` | deg | Launch-point longitude |
| `launch_altitude_m` | m | Launch-point altitude |
| `impact_altitude_m` | m | Impact-point altitude |

### `propagator.ballistic`

```python
propagator.ballistic(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]
```

### `propagator.ballistic_delta_v`

```python
propagator.ballistic_delta_v(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    delta_v_m_s: float,
    ...
) -> tuple[float, PropagatorPosition]
```

### `propagator.ballistic_delta_v_min_ecc`

```python
propagator.ballistic_delta_v_min_ecc(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    delta_v_m_s: float,
    ...
) -> tuple[float, PropagatorPosition]
```

### `propagator.ballistic_apogee_altitude`

```python
propagator.ballistic_apogee_altitude(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    apogee_altitude_m: float,
    ...
) -> tuple[float, PropagatorPosition]
```

### `propagator.ballistic_time_of_flight`

```python
propagator.ballistic_time_of_flight(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    time_of_flight_s: float,
    ...
) -> tuple[float, PropagatorPosition]
```

```python
period_s, position = propagator.ballistic_delta_v(
    start="2024-01-01T12:00:00.000Z",
    impact_latitude_deg=30.0,
    impact_longitude_deg=-70.0,
    launch_latitude_deg=28.5721,
    launch_longitude_deg=-80.648,
    launch_altitude_m=10.0,
    impact_altitude_m=0.0,
    delta_v_m_s=3000.0,
    step_s=30.0,
)
```

Complete runnable examples are available at `examples/01_propagation/ballistic_delta_v.py`, `ballistic_min_ecc.py`, `ballistic_apogee_alt.py`, and `ballistic_time_of_flight.py`.

## Correspondence with `astrox.components` Position Sources

`astrox.components` provides position-source objects that correspond to propagator parameters, such as `J2Position`, `TwoBodyPosition`, `Sgp4Position`, `HpopPosition`, `SimpleAscentPosition`, and `BallisticPosition`, for assembling position sources as named objects. Their parameters correspond one-to-one with the functions in `propagator`, but they belong to the component-layer value objects. For details, see the [components manual](../components/README.md).

## Error Handling

When ASTROX returns an unsuccessful response or a network request fails, all propagation functions raise an exception from `astrox.exceptions`: an `IsSuccess=false` response raises `AstroxAPIError`, an HTTP 4xx/5xx response raises `AstroxHTTPError`, a request timeout raises `AstroxTimeoutError`, and a connection failure raises `AstroxConnectionError`. They are all sibling subclasses of `AstroxError`. The SDK does not hide or rewrite server error messages. For the full raw response, use `astrox.raw.post` directly.
