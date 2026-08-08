# Astrogator Mission Sequence (RunMCS)

`astrox.astrogator` provides the public API for the ASTROX Astrogator mission control sequence (RunMCS). You can combine segments such as initial state, propagation, impulsive maneuver, finite maneuver, nested sequence, target sequence, and stop into one ordered main sequence that ASTROX executes in a single call, and receive the initial state, final state, duration, and scalar results for segments that actually execute and produce output. The recommended import style is:

```python
from astrox import astrogator, propagator
```

This page is organized by concept, verification status, top-level call, segment constructors, initial state, stopping conditions, propagator registration, maneuvers and engines, scalar results, differential correction, result tree, and explicit limitations. All parameters use `snake_case`; parameters that carry units use explicit suffixes such as `_m`, `_m_s`, `_deg`, `_s`, `_kg`, `_m3_s2`. Optional parameters are not sent to ASTROX when omitted; the server retains its defaults. For full control over the request payload, use `astrox.raw`.

## Concept

A RunMCS call describes a spacecraft mission: the main sequence (`main_sequence`) is a list of segments in execution order, each segment performs one operation, and each segment continues from the final state of the previous one. Segment results are returned in main-sequence order, and segment results of nested segments (`sequence`, `target_sequence`) are expanded recursively.

Segment types and their uses:

| Segment | Constructor | Use |
| --- | --- | --- |
| Initial state | `initial_state(...)` | Defines the mission start: epoch, state elements, mass and area parameters |
| Propagation | `propagate(...)` | Advances with the specified propagator until a stopping condition triggers |
| Impulsive maneuver | `impulsive_maneuver(...)` | Instantaneous velocity increment |
| Finite maneuver | `finite_maneuver(...)` | Engine burn over a duration |
| Nested sequence | `sequence(...)` | Wraps a group of segments into a subsequence |
| Target sequence | `target_sequence(...)` | Runs a subsequence, optionally with differential-corrector operators adjusting variables |
| Stop | `stop(...)` | Terminates mission execution when enabled |
| Follow | `follow(...)` | Follows the motion of another entity (currently unavailable; see Limitations) |

`run_mcs(...)` accepts the main sequence and can register propagators and engines explicitly through `propagators` and `engine_models`. Propagation segments reference the registered propagators by name.

## Verification status

This document writes verified behavior as deterministic recommendations; branches marked "partially verified" can construct requests, but the SDK provides no guarantee for the physical semantics of those branches; branches marked "unverified" or "unavailable" should not be used in a mission. For example, propagation, stopping conditions, and impulsive velocity increments along the velocity direction have been independently checked and can be used with confidence; the Follow segment cannot be executed successfully by the server, so this document explicitly marks it as unavailable.

## Top-level call `run_mcs`

```python
astrogator.run_mcs(
    main_sequence: Sequence[MCSSegment],
    *,
    central_body: str = "Earth",
    out_czml_frame_name: str = "INERTIAL",
    compute_czml_positions: bool | None = None,
    entities: Sequence[EntityPath] | None = None,
    propagators: Sequence[HpopConfig] | None = None,
    engine_models: Sequence[EngineConstant] | None = None,
    text: str | None = None,
) -> RunMCSResult
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `main_sequence` | `Sequence[MCSSegment]` | — | Main-sequence segment list, executed in order |
| `central_body` | `str` | `"Earth"` | Central body. All verified paths use `Earth`; behavior for other bodies is partially verified |
| `out_czml_frame_name` | `str` | `"INERTIAL"` | CZML output reference-frame name. The `INERTIAL` frame is verified; conventions for frames such as `FIXED`, `J2000`, and `MEANECLPJ2000` are partially verified |
| `compute_czml_positions` | `bool | None` | `None` | Whether to compute CZML-style position samples (see the CZML positions section below). When omitted, the SDK does not send this field to ASTROX and the server retains its default |
| `entities` | `Sequence[EntityPath] | None` | Entity definitions. Currently relevant only to the unverified Follow segment; see Limitations |
| `propagators` | `Sequence[HpopConfig] | None` | Registered custom propagators; segments reference them through `propagator_name` |
| `engine_models` | `Sequence[EngineConstant] | None` | Registered engines; maneuver segments reference them through `propulsion_method_value` |
| `text` | `str | None` | Mission remark text. Partially verified: the server accepts this input, but its semantics beyond input annotation are not verified |

Every item in `main_sequence` must be an SDK value object returned by a segment constructor; raw dictionaries are not accepted. Once the request is constructed, it is sent via `raw.post("/Astrogator/RunMCS", ...)`.

### Why propagators must be registered explicitly

RunMCS does not look up propagators from a built-in library by name: default names such as `TwoBody`, `J2`, and `HPOP` cannot be referenced directly by a propagation segment, and omitting `propagator_name` also fails. You must therefore register custom propagators explicitly in `propagators` and reference the registered name in the propagation segment:

```python
config = propagator.hpop_config(
    name="Earth_TwoBody_Example",
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
        gravitational_parameter_m3_s2=398600441500000.0,
    ),
)

result = astrogator.run_mcs(
    [
        astrogator.initial_state("Initial State", initial_orbit, epoch=START),
        astrogator.propagate(
            "Coast",
            propagator_name="Earth_TwoBody_Example",
            stop_conditions=[astrogator.duration_stop("One Second", 1.0)],
        ),
    ],
    propagators=[config],
)
```

The `gravitational_parameter_m3_s2` of the two-body gravity model (`hpop_two_body_gravity`) is optional: when supplied, it is written into the `Mu` field of the gravity model in the request. The calibrated RunMCS two-body propagation path must supply it explicitly — when omitted, the server uses the central body's default gravitational constant and the propagation result degenerates toward near-constant-velocity drift, inconsistent with two-body motion, so the omission cannot be claimed to carry the same two-body physical semantics; with an explicit gravitational parameter, the propagated state agrees with independent two-body propagation. This parameter also determines the gravitational constant used by the periapsis/apoapsis stopping conditions and the Keplerian element conversions, so it should match the `gravitational_parameter_m3_s2` in the initial-state elements.

The remaining `propagator.hpop_config` fields in RunMCS (atmosphere, solar radiation pressure, third-body perturbations, and so on) can be passed through, but only the two-body gravity branch has been independently calibrated; the numerical behavior of the other force models is partially verified and is not a semantic guarantee.

## Initial-state elements

The `initial_state` segment defines the mission start through state-element constructors. All four element forms are verified: Keplerian elements, Cartesian state, spherical state, and the hyperbolic outgoing asymptote (TargetVecOut).

### `keplerian_state`

```python
astrogator.keplerian_state(
    *,
    semi_major_axis_m: float,
    eccentricity: float,
    inclination_deg: float,
    raan_deg: float,
    argument_of_periapsis_deg: float,
    gravitational_parameter_m3_s2: float,
    anomaly_type: str = "True",
    true_anomaly_deg: float | None = None,
    mean_anomaly_deg: float | None = None,
    element_type: str = "Osculating",
) -> KeplerianState
```

| Parameter | Unit | Description |
| --- | --- | --- |
| `semi_major_axis_m` | m | Semi-major axis |
| `eccentricity` | — | Eccentricity |
| `inclination_deg` | deg | Orbit inclination |
| `raan_deg` | deg | Right ascension of the ascending node |
| `argument_of_periapsis_deg` | deg | Argument of periapsis |
| `gravitational_parameter_m3_s2` | m³/s² | Gravitational parameter; must be provided explicitly |
| `anomaly_type` | — | Anomaly type: `True` or `Mean` |
| `true_anomaly_deg` | deg | True anomaly; choose either this or `mean_anomaly_deg` |
| `mean_anomaly_deg` | deg | Mean anomaly |
| `element_type` | — | Element type: `Osculating` or another string |

The Keplerian-element form must provide `gravitational_parameter_m3_s2` explicitly: without a gravitational parameter the server cannot represent the orbit and rejects the request. The interpretation of the default `anomaly_type="True"` (true anomaly) is verified; the `"Mean"` (mean anomaly) branch is partially verified.

### `cartesian_state`

```python
astrogator.cartesian_state(
    *,
    x_m: float,
    y_m: float,
    z_m: float,
    vx_m_s: float,
    vy_m_s: float,
    vz_m_s: float,
) -> CartesianState
```

Position is in m and velocity in m/s, matching the `cartesian` representation in the returned states.

### `spherical_state`

```python
astrogator.spherical_state(
    *,
    right_ascension_deg: float,
    declination_deg: float,
    radius_m: float,
    horizontal_fpa_deg: float,
    velocity_azimuth_deg: float,
    velocity_magnitude_m_s: float,
) -> SphericalState
```

Spherical state elements: right ascension/declination/radius, horizontal flight-path angle, velocity azimuth, and velocity magnitude. The conversion between this form and the Cartesian form is verified.

### `target_vector_out_state`

```python
astrogator.target_vector_out_state(
    *,
    radius_of_periapsis_km: float,
    c3_km2_s2: float,
    asymptote_ra_deg: float,
    asymptote_dec_deg: float,
    gravitational_parameter_m3_s2: float,
    velocity_azimuth_at_periapsis_deg: float = 0.0,
    true_anomaly_deg: float = 0.0,
) -> TargetVectorOutState
```

Hyperbolic outgoing-asymptote elements. Note that this form follows the ASTROX convention: `radius_of_periapsis_km` is in km, `c3_km2_s2` is in km²/s², and the remaining angles are in deg. The SDK performs no unit conversion before sending; supply values directly in km and km²/s².

### The `initial_state` segment

```python
astrogator.initial_state(
    name: str,
    state: InitialStateElement,
    *,
    epoch: str,
    coord_system_name: str = "Earth Inertial",
    dry_mass_kg: float = 500.0,
    fuel_mass_kg: float = 500.0,
    coefficient_of_drag: float | None = None,
    coefficient_of_srp: float | None = None,
    drag_area_m2: float | None = None,
    srp_area_m2: float | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> InitialStateSegment
```

| Parameter | Unit | Description |
| --- | --- | --- |
| `name` | — | Segment name, echoed as-is in the result |
| `state` | — | One of the four state element forms above |
| `epoch` | — | Start epoch, a UTC ISO 8601 string such as `2026-01-01T00:00:00Z` |
| `coord_system_name` | — | Coordinate-system name, default `Earth Inertial`. Verified paths use this default; other coordinate systems are partially verified |
| `dry_mass_kg` | kg | Dry mass, default 500 |
| `fuel_mass_kg` | kg | Fuel mass, default 500 |
| `coefficient_of_drag` | — | Drag coefficient. Partially verified: request and return echo can be constructed; the physical effect has not been independently calibrated |
| `coefficient_of_srp` | — | Solar-radiation-pressure coefficient. Partially verified |
| `drag_area_m2` | m² | Drag area. Partially verified |
| `srp_area_m2` | m² | SRP area. Partially verified |
| `results` | — | Scalar result definition list; see the Scalar results section |

The mass parameters are verified: the initial/final dry mass and fuel mass in the segment results echo the requested values, and fuel consumption during maneuver segments is deducted from the fuel mass. `description`, `user_comment`, and `results` are common to all segments; see the Common segment parameters section.

## Propagation segments and stopping conditions

### `propagate`

```python
astrogator.propagate(
    name: str,
    *,
    propagator_name: str,
    stop_conditions: Sequence[StoppingCondition],
    variable_names: str | None = None,
    max_propagation_time_s: float | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> PropagateSegment
```

| Parameter | Unit | Description |
| --- | --- | --- |
| `propagator_name` | — | Must match a propagator name registered in `run_mcs(propagators=...)` |
| `stop_conditions` | — | Stopping-condition list; propagation stops when any one triggers (event order is verified) |
| `variable_names` | — | Variable-path declaration. Partially verified: only the differential-correction usage has verified behavior, see the Differential correction section |
| `max_propagation_time_s` | s | Maximum propagation duration. Partially verified: when exceeded, propagation terminates and sets `stopped_on_maximum_duration`; the triggering semantics of this flag are partially verified |

The propagation result returns a `PropagateResult`, where `stopping_condition_name` is the name of the stopping condition that actually triggered and `duration_s` is the propagation duration. When multiple stopping conditions are enabled at once, the server returns the name of the one that triggers first.

### Stopping-condition constructors

```python
astrogator.duration_stop(name: str, trip_s: float, *, tolerance_s: float = 1.0e-6, active: bool = True) -> DurationStop
astrogator.epoch_stop(name: str, trip_utc: str, *, active: bool = True) -> EpochStop
astrogator.periapsis_stop(
    name: str,
    *,
    gravitational_parameter_m3_s2: float,
    central_body_name: str = "Earth",
    repeat_count: int = 1,
    tolerance: float = 1.0e-6,
    active: bool = True,
) -> PeriapsisStop
astrogator.apoapsis_stop(
    name: str,
    *,
    gravitational_parameter_m3_s2: float,
    central_body_name: str = "Earth",
    repeat_count: int = 1,
    tolerance: float = 1.0e-6,
    active: bool = True,
) -> ApoapsisStop
```

| Constructor | Parameter | Unit | Description |
| --- | --- | --- | --- |
| `duration_stop` | `trip_s` | s | Propagation duration relative to the segment start; the verified usage is a positive duration |
| `duration_stop` | `tolerance_s` | s | Stop tolerance |
| `epoch_stop` | `trip_utc` | — | Target epoch, a UTC ISO 8601 string; stops when the target epoch is reached |
| `periapsis_stop` | `gravitational_parameter_m3_s2` | m³/s² | Gravitational parameter used to compute the periapsis event; must be provided explicitly |
| `periapsis_stop` | `central_body_name` | — | Central-body name, default `Earth` |
| `periapsis_stop` | `repeat_count` | — | Event repeat count; 1 means the next occurrence |
| `apoapsis_stop` | same as above | — | Apoapsis event; parameters are the same as periapsis |
| all | `active` | — | Whether the stopping condition is enabled |

All four stopping conditions are verified: `duration_stop` stops at the requested duration and returns the exact boundary epoch; `epoch_stop` stops at the target epoch; `periapsis_stop` stops at periapsis (true anomaly approximately 0°), and `apoapsis_stop` stops at apoapsis (true anomaly approximately 180°). Waiting for the Nth event with `repeat_count` greater than 1 is partially verified.

## Maneuver segments and engines

### `impulsive_maneuver`

```python
astrogator.impulsive_maneuver(
    name: str,
    *,
    attitude_control: ImpulsiveAttitudeControl,
    propulsion_method_value: str,
    update_mass: bool = False,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> ImpulsiveManeuverSegment
```

An impulsive maneuver applies a velocity increment instantly. `propulsion_method_value` is the propulsion-method name: with `update_mass=False` (the default) no fuel is consumed, `FuelUsed == 0`, and no engine needs to be registered (the verified path uses `"Constant_Thrust_Isp"`); with `update_mass=True` the server looks up the propulsion method by name, so an engine with a matching name must be registered in `run_mcs(engine_models=...)`, and the actual fuel consumption matches the estimate (rocket equation).

### `finite_maneuver`

```python
astrogator.finite_maneuver(
    name: str,
    *,
    attitude_control: FiniteAttitudeControl,
    propagator_name: str,
    stop_conditions: Sequence[StoppingCondition],
    propulsion_method_value: str,
    thrust_efficiency: float = 1.0,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> FiniteManeuverSegment
```

A finite maneuver lasts for a physical duration and requires a propagator and stopping conditions: during the burn, the propagator referenced by `propagator_name` advances until `stop_conditions` trigger. The verified path is a constant-thrust engine (`constant_engine`) plus a custom two-body propagator (fixed-step RKF) plus a duration stopping condition, with a short burn duration. A finite maneuver always consumes fuel; the engine name is referenced through `propulsion_method_value`. The `thrust_efficiency` parameter can be passed, but its effect on results has not been independently verified and it is not recommended as a tuning item.

Finite-maneuver integrator settings affect stability: long burns under adaptive step size may time out, and the verified usage uses a fixed small step (such as 0.1 s) with a short duration (such as 1 s).

### Attitude-control constructors

Attitude control for impulsive maneuvers (`ImpulsiveAttitudeControl`):

```python
astrogator.impulsive_velocity_vector(delta_v_m_s: float) -> ImpulsiveVelocityVector
astrogator.impulsive_anti_velocity_vector(delta_v_m_s: float) -> ImpulsiveAntiVelocityVector
```

These two constructors are verified: `impulsive_velocity_vector` applies a `delta_v_m_s` velocity increment along the velocity direction, and `impulsive_anti_velocity_vector` applies it opposite to the velocity direction; the returned inertial/VNC velocity-increment arrays match an independent vector reconstruction.

```python
astrogator.impulsive_thrust_vector_cartesian(x_m_s: float, y_m_s: float, z_m_s: float, *, thrust_axes_name: str = "VNC(Earth)") -> ImpulsiveThrustVectorCartesian
astrogator.impulsive_thrust_vector_spherical(azimuth_deg: float, elevation_deg: float, magnitude_m_s: float, *, thrust_axes_name: str = "VNC(Earth)") -> ImpulsiveThrustVectorSpherical
astrogator.impulsive_attitude_quaternion(delta_v_m_s: float, *, qx: float = 0.0, qy: float = 0.0, qz: float = 0.0, qs: float = 1.0, reference_axes_name: str = "VNC(Earth)") -> ImpulsiveAttitudeQuaternion
astrogator.impulsive_attitude_euler(delta_v_m_s: float, a_deg: float, b_deg: float, c_deg: float, *, sequence: str = "313", reference_axes_name: str = "VNC(Earth)") -> ImpulsiveAttitudeEuler
```

The thrust-vector (Cartesian/spherical) and attitude (quaternion/Euler angle) branches are partially verified: requests execute successfully and return results, but the reference-frame semantics of direction and attitude have not been independently calibrated and are not a semantic guarantee.

Attitude control for finite maneuvers (`FiniteAttitudeControl`):

```python
astrogator.finite_velocity_vector(*, attitude_update: str = "DuringBurn") -> FiniteVelocityVector
astrogator.finite_anti_velocity_vector(*, attitude_update: str = "DuringBurn") -> FiniteAntiVelocityVector
astrogator.finite_thrust_vector_cartesian(x: float, y: float, z: float, *, thrust_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteThrustVectorCartesian
astrogator.finite_thrust_vector_spherical(azimuth_deg: float, elevation_deg: float, magnitude: float, *, thrust_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteThrustVectorSpherical
astrogator.finite_attitude_quaternion(*, qx: float = 0.0, qy: float = 0.0, qz: float = 0.0, qs: float = 1.0, reference_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteAttitudeQuaternion
astrogator.finite_attitude_euler(a_deg: float, b_deg: float, c_deg: float, *, sequence: str = "313", reference_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteAttitudeEuler
```

`finite_velocity_vector` has been checked by independent integration (burning along the current velocity direction); the remaining finite attitude branches are partially verified.

Impulsive thrust-vector components and magnitudes are in m/s (the parameter names carry the `_m_s` suffix). The finite-maneuver thrust-vector components and magnitude (`x`/`y`/`z`, `magnitude`) are not calibrated and the SDK makes no unit claim for them; the finite-maneuver thrust magnitude is supplied by the registered engine model's `thrust_n`. Angles in the spherical forms are in deg.

### `constant_engine`

```python
astrogator.constant_engine(
    *,
    name: str,
    thrust_n: float,
    isp_s: float,
    gravitational_acceleration_m_s2: float = 9.80665,
) -> EngineConstant
```

| Parameter | Unit | Description |
| --- | --- | --- |
| `name` | — | Engine name; maneuver segments reference it through `propulsion_method_value` |
| `thrust_n` | N | Constant thrust |
| `isp_s` | s | Specific impulse |
| `gravitational_acceleration_m_s2` | m/s² | Standard gravitational acceleration used for the Isp conversion, default 9.80665 |

The constant-thrust engine is verified: finite-maneuver fuel consumption satisfies `FuelUsed = thrust_n / (isp_s * gravitational_acceleration_m_s2) * duration_s`, the fuel-mass boundaries are consistent with `FuelUsed`, and the finite-maneuver `delta_v_magnitude_m_s` satisfies the Tsiolkovsky equation; when an impulsive maneuver enables mass update, the actual fuel consumption matches the estimate. The constant-acceleration engine branch is not implemented on the server, and the SDK provides no constructor.

## Nested and target sequences

### `sequence`

```python
astrogator.sequence(name: str, segments: Sequence[MCSSegment], *, description: str | None = None, user_comment: str | None = None, results: Sequence[CalcScalar] | None = None) -> SequenceSegment
```

Wraps a group of segments into a subsequence. The nesting behavior is verified: it returns a `SequenceResult` whose `segment_results` recursively contain the child segment results, the child order matches the request, and boundary states propagate along the subsequence.

### `target_sequence` and differential correction

```python
astrogator.target_sequence(
    name: str,
    segments: Sequence[MCSSegment],
    *,
    action: str = "RunNominalSequence",
    profiles: Sequence[Profile] | None = None,
    continue_on_failure: str | None = None,
    when_profiles_finish: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> TargetSequenceSegment
```

With `action="RunNominalSequence"` (the default) and no `profiles` supplied, the target sequence runs as an ordinary subsequence, returning a `TargetSequenceResult` with recursive child segment results and an empty `operator_results`; this mode is verified. Other `action` values, `continue_on_failure`, and `when_profiles_finish` are partially verified.

The verified usage of differential-corrector operators (`profiles`) declares a propagation segment as the variable carrier, then uses a differential corrector to adjust the variable so that the constraint is satisfied:

```python
coast = astrogator.propagate(
    "Coast",
    propagator_name="Earth_HPOP_Example",
    stop_conditions=[astrogator.duration_stop("Duration", 60.0)],
    variable_names="StopConditions.Duration",
    results=[
        astrogator.keplerian_scalar(
            "FinalTA",
            "TrueAnomaly",
            gravitational_parameter_m3_s2=MU,
            coord_system_name="Earth Inertial",
        )
    ],
)
profile = astrogator.differential_corrector(
    "DC1",
    controls=[
        astrogator.differential_corrector_control(
            "StopConditions.Duration",
            10.0,
            parent_name="Coast",
            perturbation=1.0,
            max_step=600.0,
            tolerance=0.0001,
        )
    ],
    results=[
        astrogator.differential_corrector_constraint(
            "FinalTA", 36.0, parent_name="Coast", tolerance=0.1
        )
    ],
)
result = astrogator.run_mcs(
    [
        astrogator.initial_state("Init", initial_orbit, epoch=START),
        astrogator.target_sequence(
            "Target", [coast], action="RunActiveOperators", profiles=[profile]
        ),
    ],
    propagators=[config],
)
```

The differential-corrector constructors:

```python
astrogator.differential_corrector_control(
    name: str,
    initial_value: float | str,
    *,
    parent_name: str,
    perturbation: float = 1.0,
    max_step: float = 600.0,
    tolerance: float = 1.0e-4,
    enable: bool = True,
) -> DifferentialCorrectorControl

astrogator.differential_corrector_constraint(
    name: str,
    desired_value: float | str,
    *,
    parent_name: str,
    tolerance: float = 0.1,
    enable: bool = True,
) -> DifferentialCorrectorConstraint

astrogator.differential_corrector(
    name: str,
    *,
    controls: Sequence[DifferentialCorrectorControl],
    results: Sequence[DifferentialCorrectorConstraint],
    maximum_iterations: int = 50,
    active: bool = True,
) -> DifferentialCorrector
```

The verified conventions: the control variable's `name` must point to a propagation-segment stopping-condition path and start with `StopConditions.` (such as `StopConditions.Duration`), not `StoppingConditions.`; `parent_name` is the name of the segment containing that stopping condition; the adjusted propagation segment must declare the same variable path with `variable_names`. The constraint's `name` references a scalar-result name registered on the segment. The returned `DifferentialCorrectorResult` provides `converged`, `total_iterations`, the control-variable trace, and the constraint residuals; under the verified usage the corrector converges, `converged` is `True`, and the control variable's final value and the constraint's current value satisfy the constraint within tolerance. Operator configurations beyond this are partially verified.

### `stop`

```python
astrogator.stop(name: str, *, enable: bool = True, description: str | None = None, user_comment: str | None = None, results: Sequence[CalcScalar] | None = None) -> StopSegment
```

An enabled (default) `stop` segment terminates mission execution when reached: the segment itself and the segments after it produce no segment results. With `enable=False` the segment is transparent and later segments execute normally. Both behaviors are verified.

## Common segment parameters

All segment constructors share the following parameters:

| Parameter | Description |
| --- | --- |
| `name` | Segment name; required, echoed as-is in the segment result |
| `description` | Description text. Partially verified: echoed as metadata |
| `user_comment` | User comment. Partially verified: echoed as metadata |
| `results` | Scalar-result definition list; see the next section |

## Scalar results

Segments can request scalar results through the `results` parameter. Verified scalar constructors:

```python
astrogator.duration_scalar(name: str) -> DurationScalar
astrogator.epoch_scalar(name: str) -> EpochScalar
astrogator.keplerian_scalar(
    name: str, component_name: str, *, gravitational_parameter_m3_s2: float, coord_system_name: str, element_type: str = "Osculating",
) -> KeplerianScalar
astrogator.modified_keplerian_scalar(
    name: str, component_name: str, *, gravitational_parameter_m3_s2: float, coord_system_name: str,
) -> ModifiedKeplerianScalar
astrogator.spherical_scalar(name: str, component_name: str, *, coord_system_name: str) -> SphericalScalar
astrogator.point_scalar(name: str, component_name: str, *, coord_system_name: str) -> PointScalar
```

- `duration_scalar`: the segment's elapsed time, in seconds.
- `epoch_scalar`: the segment's current epoch, a UTC string.
- `keplerian_scalar` / `modified_keplerian_scalar`: Keplerian-element components (such as `TrueAnomaly`, `SemiMajorAxis`); `component_name` selects the component, `gravitational_parameter_m3_s2` selects the conversion gravitational parameter, and `coord_system_name` selects the coordinate system. Verified component values (such as true anomaly) agree with an independent conversion of the final state.
- `spherical_scalar`: spherical-state components (such as `RightAscension`).
- `point_scalar`: position components (such as `X`); `coord_system_name` selects the coordinate system.

Other scalar constructors:

```python
astrogator.cartographic_scalar(name: str, component_name: str, *, central_body_name: str) -> CartographicScalar
astrogator.delta_spherical_scalar(name: str, component_name: str, *, central_body_name: str, parent_central_body_name: str) -> DeltaSphericalScalar
astrogator.relative_scalar(name: str, calc_object: CalcScalar, *, reference_name: str | None = None) -> RelativeScalar
astrogator.b_plane_scalar(name: str, component_name: str, *, gravitational_parameter_m3_s2: float, central_body_name: str) -> BPlaneScalar
```

`cartographic_scalar` is partially verified: the server returns values, but the reference-frame rotation convention for geodetic coordinates is not yet fully explained and is not a semantic guarantee. `delta_spherical_scalar`, `relative_scalar`, and `b_plane_scalar` are unverified: the constructors can generate requests, but the semantics of their results have no independent evidence and should not be relied on in a mission.

Scalar results appear in the segment result's `scalar_results` dictionary by name. The value form varies by type: numeric scalars are plain `float`, and `epoch_scalar` is a UTC string.

## Result tree

`run_mcs` returns `astrogator.RunMCSResult`:

| Field | Type | Description |
| --- | --- | --- |
| `is_success` | `bool` | Whether the call succeeded. When the server returns a failure, the transport layer raises `AstroxAPIError`, so this field is `True` whenever a parsed result is available |
| `message` | `str` | Message text returned by the server. Partially verified: it is only an echo of the returned value |
| `main_sequence_results` | `tuple[SegmentResultValue, ...]` | Segment results in execution order for the segments that actually execute and produce output. With an enabled Stop, the Stop segment itself and the segments after it produce no results (see the `stop` section) |
| `positions` | `components.CzmlPositions | None` | CZML position samples; parsed as `CzmlPositions` when the response contains the field, otherwise `None`. When `compute_czml_positions` is not explicitly passed, whether samples are returned is decided by the server default (the baseline OpenAPI declares a default of `true`) |
| `unknown_fields` | `Mapping` | Response fields not consumed by the parser, preserved as-is |

### Segment results

Every segment result shares the following fields:

| Field | Type | Description |
| --- | --- | --- |
| `type_name` | `str` | Segment type name, such as `InitialState`, `Propagate` |
| `wire_type` | `str | None` | The `$type` discriminator value in the response (some segment results do not have this field) |
| `name` | `str` | Segment name from the request, echoed as-is |
| `description` | `str | None` | Description echo. Partially verified |
| `user_comment` | `str | None` | Comment echo. Partially verified |
| `initial_state` | `SegmentState` | Segment initial state |
| `final_state` | `SegmentState` | Segment final state |
| `duration_s` | `float` | Segment duration, in seconds |
| `scalar_results` | `Mapping` | Scalar-results dictionary keyed by the requested scalar names |
| `unknown_fields` | `Mapping` | Unconsumed fields |

Parsed subclasses returned by segment type:

| Subclass | Additional fields | Description |
| --- | --- | --- |
| `InitialStateResult` | — | Initial-state segment result; `duration_s == 0` and the initial and final states are identical |
| `PropagateResult` | `stopped_on_maximum_duration`, `stopping_condition_name` | Propagation segment result; `stopping_condition_name` is the triggered stopping-condition name, and `stopped_on_maximum_duration` is partially verified |
| `ManeuverImpulsiveResult` | `maneuver_information` | Impulsive maneuver result |
| `ManeuverFiniteResult` | `maneuver_information` | Finite maneuver result |
| `SequenceResult` | `segment_results` | Nested-sequence result; child segment results are expanded recursively |
| `TargetSequenceResult` | `operator_results`, `segment_results` | Target-sequence result; operator trace and child segment results |
| `FollowResult` | — | Follow segment result type. The server currently cannot produce this result; see Limitations |
| `SegmentResult` | — | Fallback base class |

### Segment state `SegmentState`

`initial_state` and `final_state` are `SegmentState` values that contain multiple representations at once:

| Field | Type | Description |
| --- | --- | --- |
| `epoch` | `str` | Boundary epoch, a UTC string |
| `coord_system_name` | `str` | Coordinate-system name. Partially verified: the specific reference-frame meaning it represents is not fully calibrated |
| `cartesian` | `orbits.CartesianState` | Cartesian position/velocity, in m and m/s |
| `keplerian` | `ReturnedKeplerianState` | Keplerian-element representation, including `period_s` (orbital period, in seconds) and `gravitational_parameter_m3_s2` |
| `spherical` | `ReturnedSphericalState` | Spherical representation |
| `dry_mass_kg` | `float` | Dry mass |
| `fuel_mass_kg` | `float` | Fuel mass |
| `coefficient_of_drag` | `float` | Drag coefficient. Partially verified: it is a return echo |
| `coefficient_of_srp` | `float` | Solar-radiation-pressure coefficient. Partially verified |
| `drag_area_m2` | `float` | Drag area. Partially verified |
| `srp_area_m2` | `float` | SRP area. Partially verified |
| `geodetic_latitude_deg` | `float` | Geodetic latitude. Partially verified |
| `geodetic_longitude_deg` | `float` | Geodetic longitude. Partially verified |
| `geodetic_altitude_m` | `float` | Geodetic altitude. Partially verified |
| `geocentric_latitude_deg` | `float` | Geocentric latitude. Partially verified |
| `geocentric_longitude_deg` | `float` | Geocentric longitude. Partially verified |
| `unknown_fields` | `Mapping` | Unconsumed fields |

The Cartesian, Keplerian, and spherical representations have been verified against independent conversions and can cross-check each other. The server always returns the geodetic/geocentric latitude and longitude fields, but the reference-frame conventions are partially verified.

### Maneuver information `ManeuverInformation`

The `maneuver_information` field of impulsive and finite maneuver results:

| Field | Type | Description |
| --- | --- | --- |
| `start` / `stop` | `str` | Maneuver boundary epochs |
| `duration_s` | `float` | Maneuver duration. 0 for impulsive maneuvers |
| `fuel_used_kg` | `float` | Actual fuel consumption. 0 for impulsive maneuvers with `update_mass=False` |
| `estimated_fuel_used_kg` | `float | None` | Estimated fuel consumption, consistent with the rocket equation |
| `delta_v_magnitude_m_s` | `float` | Scalar velocity-increment magnitude. For finite maneuvers it equals the rocket-equation exhaust velocity |
| `delta_v_inertial` | `tuple[float, ...]` | Inertial-frame velocity increment, a six-value array |
| `delta_v_vnc` | `tuple[float, ...]` | VNC-frame velocity increment, a six-value array |
| `maneuver_attitude_name` | `str` | Attitude implementation name |
| `update_mass` | `bool | None` | Whether mass is updated (finite maneuvers do not return this field) |
| `delta_v_body` | `tuple[float, ...] | None` | Body-frame velocity increment. The server currently does not return this field |
| `quaternion` | `tuple[float, ...] | None` | Attitude quaternion. The server currently does not return this field |
| `unknown_fields` | `Mapping` | Unconsumed fields |

The six-value array convention is verified: the first three values are the boundary velocity difference (in the inertial or VNC frame, including gravity acting during the maneuver), and the last three values are the azimuth, elevation, and magnitude of the first three values. `delta_v_magnitude_m_s` contains only the thrust contribution; do not confuse it with the norm of the first three array values.

### CZML positions

When `compute_czml_positions` is omitted, the SDK does not send the field to ASTROX and whether samples are computed is decided by the server default (the baseline OpenAPI declares a default of `true`); explicit `compute_czml_positions=True` requests samples, and explicit `False` disables them. When the response contains no position data, `result.positions` is `None`. CZML samples are used for trajectory visualization (for example in Cesium); the verified `INERTIAL`-frame samples agree point by point with independent two-body propagation.

`components.CzmlPositions` contains `central_body` and `positions` (`tuple[components.CzmlPosition, ...]`). Fields of each `CzmlPosition`:

| Field | Description |
| --- | --- |
| `epoch` | Sample start epoch |
| `interval` | Sample time interval |
| `reference_frame` | Reference frame; defaults to the request's `out_czml_frame_name` |
| `interpolation_algorithm` | Interpolation algorithm. Partially verified: it is a server-returned value |
| `interpolation_degree` | Interpolation degree. Partially verified |
| `cartesian` | Position sequence; currently `None` |
| `cartesian_velocity` | CZML-style `[t, x, y, z, vx, vy, vz, ...]` sample sequence, one frame per 7 values: time offset (s), position X/Y/Z (m), velocity X/Y/Z (m/s) |

The sample-sequence layout matches the `PropagatorPosition.cartesian_velocity` returned by `astrox.propagator`; see the [propagator manual](../propagator/README.md) for details.

## Explicit limitations

- **The Follow segment is unavailable**: the `follow(...)` constructor and `entities`, `mission_position`, and `entity_path` can construct requests, but the ASTROX server currently cannot execute a Follow segment (the required position data is missing), and the mission fails when the Follow segment is created. Do not put a Follow segment into a mission.
- **Scalar stopping conditions are not supported**: stopping conditions based on a scalar threshold (such as a duration scalar) are not implemented on the server, and the SDK provides no corresponding constructor.
- **The constant-acceleration engine is not supported**: this branch is not implemented on the server, and the SDK provides no constructor.
- **Default propagator names are not available**: propagation segments must reference explicitly registered custom propagators; built-in names cannot be referenced.
- **The calibrated two-body path requires an explicit gravitational parameter**: the `gravitational_parameter_m3_s2` in both the propagator gravity model and the Keplerian initial state must be provided explicitly; otherwise results are unreliable or the request is rejected. The `hpop_two_body_gravity` constructor itself allows omitting the parameter, but an omission is not calibrated two-body semantics.
- **Partially verified branches**: the thrust-vector and attitude branches of impulsive/finite maneuvers, the finite anti-velocity-direction branch, `thrust_efficiency`, non-`Earth` central bodies, non-`INERTIAL` CZML output frames, `cartographic_scalar`, `delta_spherical_scalar`, `relative_scalar`, `b_plane_scalar`, and the geodetic/geocentric coordinate fields are all partially verified or unverified; the SDK provides no guarantee for the semantics of these branches.

## Error handling

All ASTROX errors inherit from `astrox.exceptions.AstroxError`. When the server responds with `IsSuccess=false`, `run_mcs` raises `AstroxAPIError`; HTTP 4xx/5xx responses raise `AstroxHTTPError`; request timeouts raise `AstroxTimeoutError`; connection failures raise `AstroxConnectionError`. These four exceptions are sibling subclasses of `AstroxError`; there is no subclass relationship between them. The SDK does not hide or rewrite server error messages. When the parser encounters a missing required field it raises `KeyError`; a field of the wrong type raises `TypeError`. When the full raw response is needed, use `astrox.raw.post` directly.

## Full example

A runnable full example is in `examples/07_astrogator/run_mcs.py`; the task guide is [How to run an Astrogator mission sequence](../../how_to/run_an_astrogator_mcs.md).
