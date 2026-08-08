# Astrogator validation

This page registers the cross-validation and live-snapshot evidence for `astrox.astrogator` (the `run_mcs` endpoint). It does not teach normal usage or reproduce API signatures; see [`docs/manual/astrogator/README.md`](../manual/astrogator/README.md) for that. Claims are written in the evidence register voice: each branch is marked with the same status used by its coverage checklist, and semantic statements use the form "cross-validated against X within tolerance Y" rather than "proven" or "correct".

Two evidence layers back this page. The live snapshots in `tests/validation/live_snapshot/astrogator/` are drift detectors for maintained response shape: they detect upstream response-shape drift for the supported public cases and do not prove physical or semantic correctness. The cross-validation scripts in `tests/validation/cross_validation/astrogator/` are the semantic evidence: each compares live ASTROX behavior with an external library, a physical invariant, or an independent local derivation.

## Live snapshot coverage

Live snapshot script: [`tests/validation/live_snapshot/astrogator/test_run_mcs.py`](../../tests/validation/live_snapshot/astrogator/test_run_mcs.py).
Sidecar snapshot: [`tests/validation/live_snapshot/astrogator/run_mcs.snap.json`](../../tests/validation/live_snapshot/astrogator/run_mcs.snap.json).

The snapshot covers nine cases: `initial_state`, `propagate`, `propagate_czml`, `impulsive`, `finite`, `all_force_models`, `sequence`, `scalar_results`, and `target_sequence`. These snapshots establish response-shape drift detection, not physics correctness; the semantic claims below come from the cross-validation suites.

## Initial-state representations

Status of the four `initial_state` element forms:

- Cartesian initial state: `verified`.
- Keplerian initial state: `verified`.
- Spherical initial state: `verified`.
- TargetVecOut hyperbolic initial state: `verified`.

Comparison path: local Cartesian/spherical basis equations and hyperbolic conic equations. The external side interprets TargetVecOut `C3` in km²/s² and `RadiusOfPeriapsis` in km before converting to SI; the reconstructed conic matches the relations `a = -Mu/C3` and `e = 1 + rp*C3/Mu` after unit conversion.

Key constants and tolerances from [`tests/validation/cross_validation/astrogator/test_initial_state_conversions.py`](../../tests/validation/cross_validation/astrogator/test_initial_state_conversions.py):

- `MU = 398600441500000.0` m³/s².
- State tolerance: `STATE_EPS = 1.0e-6` (m or m/s).
- Conic scalar tolerance: `SCALAR_EPS = 1.0e-9` relative.

Known residuals and conventions: no unexplained residual remains for the four exercised forms. Cartesian identity, Keplerian element echo, spherical-to-Cartesian conversion, and the hyperbolic periapsis radius / eccentricity / semi-major axis are each compared in one representative case.

Cross-validation script: [`tests/validation/cross_validation/astrogator/test_initial_state_conversions.py`](../../tests/validation/cross_validation/astrogator/test_initial_state_conversions.py).

## Two-body propagation with explicit gravitational parameter

Status of `propagate` with a registered custom two-body propagator:

- Keplerian `InitialState` plus registered `TwoBody` `Propagate`: `verified`.
- Three orbit regimes (eccentric LEO, high-inclination LEO, near-circular orbit-scale) and three durations (1 s, 10 s, 60 s): `verified`.
- Final Cartesian state and final osculating Keplerian elements: `verified`.
- `DurationSec`: `verified`.

Comparison path: the Brahe `KeplerianPropagator` with the same Earth GM and true-to-mean anomaly conversion, using the same fixed 0.1 s RKF step on both sides.

Key constants and tolerances from [`tests/validation/cross_validation/astrogator/test_run_mcs_two_body_brahe.py`](../../tests/validation/cross_validation/astrogator/test_run_mcs_two_body_brahe.py):

- `MU = 398600441500000.0` m³/s².
- Position tolerance: `POSITION_ABS_M = 0.05` (m).
- Velocity tolerance: `VELOCITY_ABS_M_S = 5.0e-5`.
- Element tolerance: `ELEMENT_ABS = 1.0e-5` in native units.

Calibration evidence for the explicit-`Mu` requirement: a custom two-body gravity model without an explicit `Mu` made live ASTROX degenerate toward near-constant-velocity drift, with a maximum Brahe position residual of approximately `11.021737797094943` m; with the explicit `Mu` the residual fell to approximately `1.30385160446167e-08` m. This is calibration evidence for why the explicit gravitational parameter is required, not a general correctness claim. No frame adjustment was needed: both paths are Earth-centered inertial.

Cross-validation script: [`tests/validation/cross_validation/astrogator/test_run_mcs_two_body_brahe.py`](../../tests/validation/cross_validation/astrogator/test_run_mcs_two_body_brahe.py).

## Stopping conditions

Status of the four stopping conditions:

- `Duration`: `verified` (stops at the requested duration and returns the exact boundary epoch; the `DurationSec` field is Brahe cross-validated in the two-body suite above).
- `Epoch`: `verified` (a target 600 s after the start returned `DurationSec == 600` and the exact target epoch, checked with independent UTC epoch arithmetic; the `StoppingConditionName` echo is also checked).
- `Apoapsis`: `verified` (starting at periapsis on a two-body orbit stopped at approximately half the orbital period and returned a true anomaly of approximately 180 degrees).
- `Periapsis`: `verified` (starting at apoapsis stopped at the next periapsis and returned a true anomaly of approximately 0 degrees).
- Scalar-threshold stopping conditions: `unresolved` / upstream-blocked (see the unresolved section below).

Comparison path: the periapsis and apoapsis checks use the conic half-period solution from the exact apsides; the epoch check uses independent UTC epoch arithmetic; the duration branch is additionally Brahe cross-validated in the two-body suite above.

Key constants and tolerances from [`tests/validation/cross_validation/astrogator/test_branch_semantics.py`](../../tests/validation/cross_validation/astrogator/test_branch_semantics.py):

- `MU = 398600441500000.0` m³/s²; `a = 7_000_000` m; `e = 0.3`.
- Duration tolerance: `DURATION_EPS_S = 1.0e-4` (s); true anomaly tolerance: `TRUE_ANOMALY_EPS_DEG = 1.0e-4` (deg).
- Mass tolerance: `MASS_EPS_KG = 1.0e-9` (kg); delta-v tolerance: `DELTA_V_EPS_M_S = 1.0e-6` (m/s).

The same script also covers the enabled-Stop, nominal `RunNominalSequence`, and impulsive `UpdateMass=true` cases below.

Cross-validation script: [`tests/validation/cross_validation/astrogator/test_branch_semantics.py`](../../tests/validation/cross_validation/astrogator/test_branch_semantics.py).

## Enabled Stop termination

Status of the enabled `stop` segment:

- Enabled Stop after the initial segment: `verified` (the Stop segment itself and every later segment produce no result object; the returned `main_sequence_results` contains only the `InitialState` result and the final state is the unpropagated mission-start state).

Comparison path: sequence-termination semantics — with the Stop enabled, propagation may not run after the stop and later segments must be absent from the results.

Cross-validation script: [`tests/validation/cross_validation/astrogator/test_branch_semantics.py`](../../tests/validation/cross_validation/astrogator/test_branch_semantics.py).

## Nested sequence and INERTIAL CZML samples

Status of nested `sequence` and `compute_czml_positions=True` with `out_czml_frame_name="INERTIAL"`:

- Nested `Sequence` containing `InitialState` and `Propagate`: `verified`.
- Recursive `SegmentResults` order and boundary-state continuity: `verified`.
- Sequence aggregate `DurationSec`: `verified`.
- CZML epoch / interval / reference frame / sample ordering: `verified`.
- All sampled Cartesian position and velocity values: `verified` against Brahe.

Comparison path: the Brahe `KeplerianPropagator` sampled at every ASTROX CZML time offset, for a one-second duration with a 0.1 s fixed step.

Key constants and tolerances from [`tests/validation/cross_validation/astrogator/test_sequence_czml_brahe.py`](../../tests/validation/cross_validation/astrogator/test_sequence_czml_brahe.py):

- `DURATION_S = 1.0`, `STEP_S = 0.1`.
- Position tolerance: `POSITION_ABS_M = 0.05` (m).
- Velocity tolerance: `VELOCITY_ABS_M_S = 5.0e-5`.

Known residuals and conventions: only the `INERTIAL` output frame is calibrated. Other `out_czml_frame_name` values (`FIXED`, `J2000`, `MEANECLPJ2000`) remain `partial`.

Cross-validation script: [`tests/validation/cross_validation/astrogator/test_sequence_czml_brahe.py`](../../tests/validation/cross_validation/astrogator/test_sequence_czml_brahe.py).

## Scalar results

Status of the calibrated scalar-result subset:

- `Duration`: `verified` (equals the propagation duration).
- `Epoch`: `verified` (equals the final-state epoch).
- `KeplerianElement(TrueAnomaly)`: `verified` against an independent conversion of the final state.
- `ModifiedKeplerianElement(TrueAnomaly)`: `verified` for the exercised case (matches the osculating true anomaly there).
- `PointElement(X)`: `verified`.
- `SphericalElement(RightAscension)`: `verified`.
- `Cartographic(Latitude)`: `unresolved` (strict calibration xfail; the naive geocentric-latitude oracle `asin(z/|r|)` on the final Cartesian state has a stable residual of approximately `0.170666` deg against the server value, which follows a fixed-frame/geodetic-style convention the naive inertial oracle does not model).
- `DeltaSpherical` (`Delta_Right_Asc` / `Delta_RMag`): `unresolved` (strict calibration xfail; the server currently returns an empty result dict, recorded as a result-missing mismatch against the independent RA/radius-difference oracle rather than a `KeyError`/`TypeError`).
- `Relative` (TrueAnomaly vs Init): `unresolved` (strict calibration xfail; the server currently returns an empty result dict, recorded as a result-missing mismatch against the independent osculating element-difference oracle rather than a `KeyError`/`TypeError`).
- `BPlane` (`BDotR`/`BDotT`): `unresolved` (strict calibration xfail; `BDotR` matches the outgoing-asymptote +Z-reference candidate, but the equally plausible incoming-asymptote / flipped-T conventions are rejected and `BDotT` ~ 0 cannot pin the T/R handedness for the exercised geometry).

These four branches are represented by strict calibration xfails in the script below; they are recorded as `unresolved`, not promoted as working scalars.

Comparison path: Brahe two-body propagation plus an independent Cartesian-to-spherical conversion, with an explicit Earth `Mu` and a 0.1 s fixed integration step.

Key constants and tolerances from [`tests/validation/cross_validation/astrogator/test_scalar_invariants.py`](../../tests/validation/cross_validation/astrogator/test_scalar_invariants.py):

- `MU = 398600441500000.0` m³/s².
- Verified scalar tolerance: `SCALAR_EPS = 1.0e-7` in native units.
- B-plane candidate comparison tolerance: `BPLANE_REL_EPS = 1.0e-9` relative.

Cross-validation script: [`tests/validation/cross_validation/astrogator/test_scalar_invariants.py`](../../tests/validation/cross_validation/astrogator/test_scalar_invariants.py).

## Maneuver invariants and the constant engine

Status of maneuver branches:

- Impulsive `VelocityVector`: `verified`.
- Impulsive `VelocityVector` with `UpdateMass=true` and a registered constant engine: `verified` (the boundary fuel-mass difference equals `FuelUsed`; final fuel mass and `FuelUsed` match the Tsiolkovsky equation `m1 = m0 * exp(-dv/(Isp*g))`; `EstimatedFuelUsed` equals `FuelUsed`; `DeltaV_Mag` equals the commanded 100 m/s) — [`test_branch_semantics.py`](../../tests/validation/cross_validation/astrogator/test_branch_semantics.py).
- Impulsive `AntiVelocityVector`: `verified`.
- Finite `VelocityVector` with a constant engine and a two-body propagator: `verified`.
- Impulsive velocity jump and VNC direction: `verified`.
- Finite total inertial/VNC delta-v arrays: `verified`.
- Finite thrust-only `DeltaV_Mag`: `verified` against the rocket equation.
- `FuelUsed` and final fuel mass: `verified` against the constant mass-flow equation.
- Other impulsive attitude branches (thrust-vector Cartesian/spherical, attitude quaternion/Euler): `partial`.
- Other finite attitude branches (anti-velocity direction, thrust-vector Cartesian/spherical, attitude quaternion/Euler): `partial`.
- `ThrustEfficiency` effect: `partial` (the field is preserved in the request shape; a bounded comparison at 0.98 and 1.02 produced identical primary results, so the effect is unverified and must not be treated as active).

Comparison path: independent local vectors, a VNC basis, spherical conversion, and the Tsiolkovsky equation.

Calibration note for `UpdateMass=true`: the engine collection is searched by the name in `PropulsionMethodValue`; the literal name `Constant_Thrust_Isp` is not found unless an engine with that exact name is registered, so the registered `EngineConstant` must be referenced by its own name (the exercised case registers and references `EngineA`).

Key constants and tolerances from [`tests/validation/cross_validation/astrogator/test_maneuver_invariants.py`](../../tests/validation/cross_validation/astrogator/test_maneuver_invariants.py):

- Initial dry/fuel mass 500 kg each; `g = 9.80665` m/s².
- 100 m/s impulsive magnitude; 500 N / 600 s / 1 s finite burn.
- Vector tolerance: `VECTOR_EPS = 1.0e-8` (m/s).
- Mass tolerance: `MASS_EPS = 1.0e-10` (kg).
- Scalar tolerance: `SCALAR_EPS = 1.0e-10` (m/s).

Invariant distinction: the finite-maneuver invariants are `FuelUsed = T/(Isp*g)*duration` and `DeltaV_Mag = Isp*g*ln(m0/m1)`. The first three values of the six-value `DeltaV_Inertial` and `DeltaV_VNC` arrays are the total boundary velocity difference, including gravity acting during the burn; they must not be conflated with the thrust-only `DeltaV_Mag`. The last three values of each six-value array are the azimuth, elevation, and magnitude of that array's first three values.

Cross-validation script: [`tests/validation/cross_validation/astrogator/test_maneuver_invariants.py`](../../tests/validation/cross_validation/astrogator/test_maneuver_invariants.py).

## Target sequence and differential corrector

Status of the calibrated `TargetSequence` case:

- `TargetSequence` with `action="RunActiveOperators"`: `verified`.
- Differential-corrector control path `StopConditions.Duration`: `verified`.
- `KeplerianElement(TrueAnomaly)` target result: `verified`.
- `Converged` and `TotalIterations`: `verified`.
- Control `FinalValue` / `Correction` / `Values` trace: `verified`.
- Constraint `CurrentValue` / `Difference` / `Values` trace: `verified`.
- Nested `Propagate` `DurationSec` and `FinalTA`: `verified`.
- Nominal `action="RunNominalSequence"` with no profiles: `verified` (the same inner sequence is executed directly at the top level and inside the target sequence; empty `operator_results`, recursive child results, aggregate duration, and the `FinalTA` scalar agree between the two runs, and `FinalTA` matches an independent Kepler mean-anomaly solve) — [`test_branch_semantics.py`](../../tests/validation/cross_validation/astrogator/test_branch_semantics.py). The empty-`operator_results` shape is also exercised by the live snapshot `target_sequence` and `sequence` cases.
- Other `action` values, `continue_on_failure`, and `when_profiles_finish`: `partial`.

Comparison path: an independent local Keplerian mean-anomaly propagation and a one-step finite-difference Newton solve. The control variable must be named with the `StopConditions.` prefix (not `StoppingConditions.`), matching live behavior.

Key constants and tolerances from [`tests/validation/cross_validation/astrogator/test_target_sequence_local.py`](../../tests/validation/cross_validation/astrogator/test_target_sequence_local.py):

- `a = 7_000_000` m, `e = 0.3`, `Mu = 398600441500000.0` m³/s².
- Initial control 10 s, perturbation 1 s, desired true anomaly 36 deg.
- Solver trace tolerance: `1.0e-7` (s/deg).
- Residual identity tolerance: `1.0e-10`.

Calibrated case values: the independently reconstructed one-step Newton trace for the exercised case produced `DurationSec ≈ 53.37293598506221`, `FinalTA ≈ 35.94823673349805`, `Converged == true`, and `TotalIterations == 1`, with a returned residual of approximately `-0.05176326650195051`. These values are evidence for this calibrated case, not a general correctness claim.

Cross-validation script: [`tests/validation/cross_validation/astrogator/test_target_sequence_local.py`](../../tests/validation/cross_validation/astrogator/test_target_sequence_local.py).

## Partially verified branches

The following branches are structurally reachable and the request/response shapes are exercised, but their numerical semantics are not independently calibrated:

- Non-`INERTIAL` frame conventions: `out_czml_frame_name` values other than `INERTIAL`, and `coord_system_name` values other than the default `Earth Inertial`.
- Cartographic rotation convention: the Earth Inertial to Earth Fixed rotation used by `cartographic_scalar` remains unexplained, which is the reason `Cartographic(Latitude)` stays `unresolved` (see the scalar section above); the geodetic/geocentric state fields remain `partial`.
- Custom atmosphere, solar radiation pressure, and third-body effects on the `propagator.hpop_config` models registered in RunMCS: structurally evidenced through the `all_force_models` live snapshot case, with no independent numerical calibration.
- Other impulsive attitude branches (thrust-vector Cartesian/spherical, attitude quaternion/Euler).
- Other finite attitude branches (anti-velocity direction, thrust-vector Cartesian/spherical, attitude quaternion/Euler).
- `ThrustEfficiency` effect, as noted above.
- Additional partially verified items recorded in the manual: `text`, `max_propagation_time_s` / `stopped_on_maximum_duration`, `anomaly_type="Mean"`, non-`Earth` central bodies, `repeat_count` greater than 1, `description` / `user_comment` echoes, CZML interpolation metadata, and `message`.

## Unresolved and upstream-blocked branches

- **Follow segment**: a leader `EntityPath` whose position is a nested `AstrogatorMCS` is accepted in top-level `Entities`, but a request with a unique leader fails deterministically: the server reports that the maneuver computation result is missing the position data needed to create the Follow segment. Follow semantics therefore remain `unresolved`: joining/separation modes, offsets, role permutations, and relative-state meaning cannot be relied on. The typed request constructor remains callable only through the advanced/raw surface.
- **Scalar stopping condition**: a duration-scalar-threshold stop fails deterministically with `The method or operation is not implemented.`; the server specifically reports failure creating `AgVAScalarStoppingCondition`. This branch is upstream-blocked; the SDK provides no constructor.
- **Constant-acceleration engine**: two targeted requests failed with `The provided value cannot be null. Property name: ScalarDerivative`. This branch is upstream-blocked; the SDK provides no constructor.
- **`Cartographic(Latitude)` scalar semantics**: `unresolved`; the naive geocentric-latitude oracle `asin(z/|r|)` leaves a stable residual of approximately `0.170666` deg against the server value, so the server applies a fixed-frame/geodetic-style convention that is not yet independently calibrated.
- **`DeltaSpherical`, `Relative`, and `BPlane` scalar semantics**: the constructors can generate requests, but the result semantics have no independent evidence and should not be relied on in a mission. The server currently returns an empty result dict for `DeltaSpherical` and `Relative`, and the `BPlane` sign convention cannot be pinned by the exercised geometry. These four scalar branches are represented by strict calibration xfails in `test_scalar_invariants.py`; a snapshot or a successful request must not be read as semantic proof for them.

## Coverage summary

Coverage by branch family, mapping the verified / partial / unresolved status above to its scripts:

| Branch family | Status | Scripts |
| --- | --- | --- |
| Initial-state representations (Cartesian, Keplerian, spherical, TargetVecOut) | verified | `test_initial_state_conversions.py` |
| Two-body propagation with explicit `Mu` | verified | `test_run_mcs_two_body_brahe.py` |
| Duration / epoch / periapsis / apoapsis stops | verified | `test_run_mcs_two_body_brahe.py` (duration); `test_branch_semantics.py` (epoch / periapsis / apoapsis) |
| Enabled Stop termination | verified | `test_branch_semantics.py` |
| Nominal `RunNominalSequence` without profiles (direct-sequence comparison) | verified | `test_branch_semantics.py` |
| Impulsive `UpdateMass=true` with a registered constant engine | verified | `test_branch_semantics.py` |
| Sequence and INERTIAL CZML samples | verified | `test_sequence_czml_brahe.py` |
| Verified scalar subset | verified | `test_scalar_invariants.py` |
| Impulsive velocity/anti-velocity; finite velocity-vector constant-thrust | verified | `test_maneuver_invariants.py` |
| Constant-engine mass flow and rocket equation | verified | `test_maneuver_invariants.py` |
| Differential corrector `StopConditions.Duration` single-step case | verified | `test_target_sequence_local.py` |
| Frames, atmosphere/SRP/third-body, other attitude/finite branches, `ThrustEfficiency` | partial | live snapshots only |
| Follow, scalar stopping condition, constant-acceleration engine | unresolved / upstream-blocked | no cross-validation script; deterministic server error modes |
| `Cartographic(Latitude)`, `DeltaSpherical`, `Relative`, `BPlane` scalars | unresolved | strict calibration xfails in `test_scalar_invariants.py` |

Live snapshots detect response-shape drift and do not prove physics correctness; cross-validation scripts are the semantic evidence.
