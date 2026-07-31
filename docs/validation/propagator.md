# Propagator validation

This page registers the cross-validation and live-snapshot evidence for `astrox.propagator`. It does not teach normal usage or reproduce API signatures; see [`docs/manual/propagator/README.md`](../manual/propagator/README.md) for that. Claims are written in the evidence register voice: each branch is marked with the same status used by its coverage checklist, and semantic statements use the form "cross-validated against X within tolerance Y" rather than "proven" or "correct".

## Two-body propagation

Status of `propagator.two_body`:

- Keplerian-element input branch: `verified`.
- Cartesian-state input branch: `verified`.
- `orbit` parameter coverage: `partial` (only LEO and inclined-LEO samples are exercised).
- `start` / `stop` / `step_s` coverage: `partial` (one 10-minute window with 300-second steps).
- `gravitational_parameter_m3_s2` coverage: `verified` for Brahe Earth GM.

Comparison path: Brahe two-body state transition (`bh.KeplerianPropagator`) and element conversion. The external side converts ASTROX true-anomaly input to mean anomaly for Brahe, propagates, and converts back to true anomaly for comparison. Samples are compared at 0 s, 300 s, and 600 s. Final Keplerian elements from the propagated state are also compared.

Key constants and tolerances from [`tests/validation/cross_validation/propagator/test_two_body_brahe.py`](../../tests/validation/cross_validation/propagator/test_two_body_brahe.py):

- `EARTH_MU = bh.GM_EARTH`.
- Position tolerance: `POSITION_ABS_M = 1.0e-5`.
- Velocity tolerance: `VELOCITY_ABS_M_S = 1.0e-8`.
- Semi-major-axis tolerance: `SEMI_MAJOR_AXIS_ABS_M = 1.0e-5`.
- Eccentricity tolerance: `ECCENTRICITY_ABS = 1.0e-12`.
- Angle tolerances: `ANGLE_ABS_DEG = 1.0e-8`.

Known residuals and conventions: no unexplained residual remains after the true-to-mean and mean-to-true conversions. The test covers only near-circular low Earth orbits; higher orbits and longer arcs are not calibrated.

Live snapshot coverage: `propagator.two_body` has a sidecar snapshot at [`tests/validation/live_snapshot/propagator/two_body.snap.json`](../../tests/validation/live_snapshot/propagator/two_body.snap.json).

Cross-validation script: [`tests/validation/cross_validation/propagator/test_two_body_brahe.py`](../../tests/validation/cross_validation/propagator/test_two_body_brahe.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_two_body.py`](../../tests/validation/live_snapshot/propagator/test_two_body.py).

## J2 propagation

Status of `propagator.j2`:

- Single J2 Cartesian propagation branch: `verified`.
- Single J2 Keplerian-element propagation branch: `verified`.
- `j2_normalized_value` parameter: `verified` with a calibrated effective J2 value.
- `ref_distance_m` and `gravitational_parameter_m3_s2`: `verified` for Earth constants.
- `orbit` / `start` / `target` / `step_s` coverage: `partial` (one LEO case over a 10-minute window for single propagation; four regimes are covered for `multi_j2`).

Comparison path: a local analytical secular J2 model with corrected mean motion. The model uses the standard secular equations for RAAN, argument of periapsis, and mean anomaly with a first-order correction to mean motion. Calibration showed that ASTROX behaves as if its secular model uses an effective normalized J2 coefficient that differs slightly from the value supplied in the request.

Key constants and tolerances from [`tests/validation/cross_validation/propagator/test_j2_analytical.py`](../../tests/validation/cross_validation/propagator/test_j2_analytical.py):

- `EARTH_MU = 398600441500000.0`.
- `EARTH_RADIUS_M = 6378136.3`.
- Request J2 value: `J2_NORMALIZED_VALUE = 0.000484165143790815`.
- Calibrated effective J2 value: `ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE = 0.000484166956667088`.
- Position tolerance: `POSITION_ABS_M = 0.05`.
- Velocity tolerance: `VELOCITY_ABS_M_S = 5.0e-5`.
- Semi-major-axis tolerance: `SEMI_MAJOR_AXIS_ABS_M = 1.0e-6`.
- Eccentricity tolerance: `ECCENTRICITY_ABS = 1.0e-12`.
- Inclination tolerance: `INCLINATION_ABS_DEG = 1.0e-10`.
- Secular angle tolerance: `SECULAR_ANGLE_ABS_DEG = 1.0e-8`.

Known residuals and conventions: the residual is explained by using the calibrated effective normalized J2 coefficient. RAAN and argument-of-periapsis rates match the standard secular equations when those rates use corrected mean motion. The mean-anomaly rate matches the first-order correction from Keplerian mean motion. The single-J2 time and parameter envelope is narrow; the `multi_j2` comparison extends the orbit regime coverage but still uses a fixed 600-second propagation interval.

Live snapshot coverage: `propagator.j2` has a sidecar snapshot at [`tests/validation/live_snapshot/propagator/j2.snap.json`](../../tests/validation/live_snapshot/propagator/j2.snap.json).

Cross-validation script: [`tests/validation/cross_validation/propagator/test_j2_analytical.py`](../../tests/validation/cross_validation/propagator/test_j2_analytical.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_j2.py`](../../tests/validation/live_snapshot/propagator/test_j2.py).

## SGP4 propagation

Status of `propagator.sgp4`:

- Single SGP4 propagation from TLE: `verified`.
- `period_s` field: `verified` against Skyfield mean motion.
- `Position.cartesian_velocity` time / position / velocity samples: `verified` against Skyfield GCRS state samples.
- `satellite_number`: `verified` for the ISS sample.
- `tle_lines`: `verified` for the ISS TLE sample.
- `start` / `stop` / `step_s`: `partial` (two samples over one 10-minute window).

Comparison path: Skyfield `EarthSatellite` GCRS state. The script uses Skyfield's built-in frame handling; raw low-level SGP4 TEME coordinates are not the comparison target.

Key constants and tolerances from [`tests/validation/cross_validation/propagator/test_sgp4_skyfield.py`](../../tests/validation/cross_validation/propagator/test_sgp4_skyfield.py):

- `START = "2024-01-01T00:00:00.000Z"`.
- `STOP = "2024-01-01T00:10:00.000Z"`.
- `STEP_S = 300.0`.
- `SAMPLE_OFFSETS_S = (0.0, 300.0)`.
- ISS TLE sample: `TLE_LINES` (satellite 25544).
- Period tolerance: `PERIOD_ABS_S = 1.0e-9`.
- Position tolerance: `POSITION_ABS_M = 0.02`.
- Velocity tolerance: `VELOCITY_ABS_M_S = 2.0e-5`.

Known residuals and conventions: ASTROX reports SGP4 output with `reference_frame == "INERTIAL"`. For the checked ISS sample, that frame matches Skyfield's GCRS/GCRF-style state, not raw TEME output from a low-level SGP4 propagator. If another tool starts from TEME, the state must be transformed to GCRF/GCRS before comparing coordinates. Sample coverage is limited to two points in one 10-minute arc.

Live snapshot coverage: `propagator.sgp4` has a sidecar snapshot at [`tests/validation/live_snapshot/propagator/sgp4.snap.json`](../../tests/validation/live_snapshot/propagator/sgp4.snap.json).

Cross-validation script: [`tests/validation/cross_validation/propagator/test_sgp4_skyfield.py`](../../tests/validation/cross_validation/propagator/test_sgp4_skyfield.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_sgp4.py`](../../tests/validation/live_snapshot/propagator/test_sgp4.py).

## Batch / multi propagators

This section covers `propagator.multi_two_body`, `propagator.multi_j2`, and `propagator.multi_sgp4`.

### `multi_two_body`

Status:

- Batch two-body propagation branch: `verified`.
- Final Keplerian elements returned for each input state: `verified` against Brahe.
- `orbit` coverage: `partial` (LEO and inclined-LEO samples).
- `gravitational_parameter_m3_s2`: `verified` for Brahe Earth GM.

Comparison path and tolerances are the same as for single two-body propagation; see [`tests/validation/cross_validation/propagator/test_two_body_brahe.py`](../../tests/validation/cross_validation/propagator/test_two_body_brahe.py).

Known residuals and conventions: ASTROX raw batch responses include a `GravitationalParameter` field on each returned element. The curated SDK omits that field because live behavior shows it is not a reliable echo of the propagation parameter used for the result. Use `astrox.raw` when the full raw envelope is needed.

Live snapshot coverage: `propagator.multi_two_body` has a sidecar snapshot at [`tests/validation/live_snapshot/propagator/multi_two_body.snap.json`](../../tests/validation/live_snapshot/propagator/multi_two_body.snap.json), including a two-state case and an empty-batch case.

Cross-validation script: [`tests/validation/cross_validation/propagator/test_two_body_brahe.py`](../../tests/validation/cross_validation/propagator/test_two_body_brahe.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_multi_two_body.py`](../../tests/validation/live_snapshot/propagator/test_multi_two_body.py).

### `multi_j2`

Status:

- Batch J2 propagation branch: `verified`.
- Final Keplerian elements returned for each input state: `verified` against the calibrated analytical secular J2 model.
- Regime coverage: `partial` (LEO 28.5°, ISS-like 51.6°, SSO-like 98°, and MEO 55° are exercised, all propagated 600 s to the same target epoch).

Comparison path and tolerances are the same as for single J2 propagation; see [`tests/validation/cross_validation/propagator/test_j2_analytical.py`](../../tests/validation/cross_validation/propagator/test_j2_analytical.py).

Known residuals and conventions: the same calibrated effective normalized J2 coefficient applies. The batch route does not expose `j2_normalized_value` or `ref_distance_m` through the curated SDK; the batch ASTROX route owns those constants.

Live snapshot coverage: `propagator.multi_j2` has a sidecar snapshot at [`tests/validation/live_snapshot/propagator/multi_j2.snap.json`](../../tests/validation/live_snapshot/propagator/multi_j2.snap.json), including a two-state case and an empty-batch case.

Cross-validation script: [`tests/validation/cross_validation/propagator/test_j2_analytical.py`](../../tests/validation/cross_validation/propagator/test_j2_analytical.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_multi_j2.py`](../../tests/validation/live_snapshot/propagator/test_multi_j2.py).

### `multi_sgp4`

Status:

- Multi-SGP4 element query for multiple TLEs: `verified`.
- All six returned Keplerian elements: `verified` (Skyfield state converted to elements with Brahe).
- Target time: `verified` for the single target epoch tested.
- TLE list coverage: `partial` (ISS and Hubble regimes).

Comparison path: Skyfield GCRS states converted to Keplerian elements with Brahe, using mean-to-true anomaly conversion.

Key constants and tolerances from [`tests/validation/cross_validation/propagator/test_multi_sgp4_skyfield.py`](../../tests/validation/cross_validation/propagator/test_multi_sgp4_skyfield.py):

- `TARGET = "2024-01-01T00:10:00.000Z"`.
- ISS TLE and Hubble TLE samples.
- Semi-major-axis tolerance: `SEMI_MAJOR_AXIS_ABS_M = 0.02`.
- Eccentricity tolerance: `ECCENTRICITY_ABS = 2.0e-9`.
- Inclination tolerance: `INCLINATION_ABS_DEG = 1.0e-6`.
- Angle tolerance: `ANGLE_ABS_DEG = 1.0e-4`.

Known residuals and conventions: the same GCRS-frame convention applies as for single SGP4. Only two TLE regimes are compared; other orbital regimes are not calibrated.

Live snapshot coverage: `propagator.multi_sgp4` has a sidecar snapshot at [`tests/validation/live_snapshot/propagator/multi_sgp4.snap.json`](../../tests/validation/live_snapshot/propagator/multi_sgp4.snap.json), including a two-TLE case and an empty-batch case.

Cross-validation script: [`tests/validation/cross_validation/propagator/test_multi_sgp4_skyfield.py`](../../tests/validation/cross_validation/propagator/test_multi_sgp4_skyfield.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_multi_sgp4.py`](../../tests/validation/live_snapshot/propagator/test_multi_sgp4.py).

## Simple ascent

Status of `propagator.simple_ascent`:

- Launch-to-burnout branch: `partial`.
- `Position` metadata fields (`epoch`, `reference_frame`, `interpolation_algorithm`, `interpolation_degree`): `verified` for expected response shape.
- `Position.cartesian_velocity` sample times: `verified` for the start / stop / step_s grid.
- First position sample: `verified` against independent WGS84 launch geodetic conversion.
- Final position sample: `verified` against independent WGS84 burnout geodetic conversion.
- Final velocity magnitude: `verified` against `burnout_velocity_m_s`.
- `start` / `stop` / `step_s`: `verified` for the sample grid.
- Launch latitude / longitude / altitude: `verified` through the first ECEF sample.
- Burnout latitude / longitude / altitude / velocity: `verified` through the final ECEF sample and velocity magnitude.
- `central_body`: `partial` (Earth fixed-frame behavior only).
- `Period` field: `partial` (ASTROX currently reports 6000 s; no independent interpretation is asserted).

Comparison path: local WGS84 geodetic-to-ECEF derivation and Euclidean velocity norm.

Key constants and tolerances from [`tests/validation/cross_validation/propagator/test_simple_ascent_geodetic.py`](../../tests/validation/cross_validation/propagator/test_simple_ascent_geodetic.py):

- `WGS84_A_M = 6378137.0`.
- `WGS84_E2 = 6.6943799901413165e-3`.
- Position tolerance: `POSITION_ABS_M = 2.0e-5`.
- Speed tolerance: `SPEED_ABS_M_S = 1.0e-9`.
- Time tolerance: `TIME_ABS_S = 1.0e-9`.

Known residuals and conventions: only endpoint geometry is verified. The shape of the trajectory between launch and burnout, the physical interpretation of the reported period, and non-Earth central bodies are not cross-validated.

Live snapshot coverage: `propagator.simple_ascent` has a sidecar snapshot at [`tests/validation/live_snapshot/propagator/simple_ascent.snap.json`](../../tests/validation/live_snapshot/propagator/simple_ascent.snap.json).

Cross-validation script: [`tests/validation/cross_validation/propagator/test_simple_ascent_geodetic.py`](../../tests/validation/cross_validation/propagator/test_simple_ascent_geodetic.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_simple_ascent.py`](../../tests/validation/live_snapshot/propagator/test_simple_ascent.py).

## Ballistic branches

Status of the five ballistic functions (`propagator.ballistic`, `propagator.ballistic_delta_v`, `propagator.ballistic_delta_v_min_ecc`, `propagator.ballistic_apogee_altitude`, `propagator.ballistic_time_of_flight`):

- Nominal branch: `partial` (launch / impact endpoint geometry verified).
- `ballistic_delta_v` branch: `partial` (launch / impact endpoint geometry verified).
- `ballistic_delta_v_min_ecc` branch: `partial` (launch / impact endpoint geometry verified).
- `ballistic_apogee_altitude` branch: `partial` (launch / impact endpoint geometry and sampled maximum WGS84 altitude verified).
- `ballistic_time_of_flight` branch: `partial` (launch / impact endpoint geometry and final sample time verified).
- Metadata fields: `verified` for expected response shape.
- First and final position samples: `verified` against WGS84 geodetic conversion.
- Final sample time for `time_of_flight`: `verified`.
- Maximum WGS84 altitude for `apogee_altitude`: `partial` (sampled trajectory peak is bounded near the requested altitude within the step-grid sampling residual).
- Velocity components: `partial` (not solved by the endpoint-geometry oracle).
- Launch / impact latitude / longitude / altitude: `verified` through endpoint ECEF samples.
- `step_s`: `partial` (sample-grid divisibility checked).
- `delta_v_m_s`: `unresolved` for velocity interpretation.
- `apogee_altitude_m`: `partial`.
- `time_of_flight_s`: `verified` through final sample time.
- `Period` field: `unresolved` (ASTROX reports 6000 s for all tested branches; this page does not assert an interpretation).

Comparison path: local WGS84 geodetic-to-ECEF and ECEF-to-height derivations.

Key constants and tolerances from [`tests/validation/cross_validation/propagator/test_ballistic_geodetic.py`](../../tests/validation/cross_validation/propagator/test_ballistic_geodetic.py):

- `WGS84_A_M = 6378137.0`.
- `WGS84_E2 = 6.6943799901413165e-3`.
- Position tolerance: `POSITION_ABS_M = 15.0`.
- Altitude tolerance: `ALTITUDE_ABS_M = 1000.0`.
- Time tolerance: `TIME_ABS_S = 1.0e-9`.

Known residuals and conventions: ASTROX ballistic velocity convention, exact impact surface convention, continuous apogee interpolation, and the meaning of the `Period` field need deeper trajectory-model calibration. The endpoint-geometry oracle is intentionally weak; it confirms launch and impact locations but does not validate the intermediate ballistic arc.

Live snapshot coverage: all five ballistic functions are exercised in [`tests/validation/live_snapshot/propagator/test_ballistic.py`](../../tests/validation/live_snapshot/propagator/test_ballistic.py), with sidecar [`tests/validation/live_snapshot/propagator/ballistic.snap.json`](../../tests/validation/live_snapshot/propagator/ballistic.snap.json). The ballistic live snapshots have shown sub-nanounit numeric drift across live runners; the test keeps exact structure while allowing `abs_tol = 1.0e-9`, and x-fails only when the mismatch signatures exactly match the known older backend baseline. A third baseline, shape drift, case-id drift, missing field, added field, or unrecognized numeric mismatch still fails CI.

Cross-validation script: [`tests/validation/cross_validation/propagator/test_ballistic_geodetic.py`](../../tests/validation/cross_validation/propagator/test_ballistic_geodetic.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_ballistic.py`](../../tests/validation/live_snapshot/propagator/test_ballistic.py).

## HPOP

Status of `propagator.hpop`:

- Gravity degree / order zero branch: `verified`.
- Cartesian input with degree / order zero gravity: `verified`.
- Gravity degree / order zero with Sun / Moon point masses: `verified`.
- Spherical SRP in sunlit geometry: `verified`.
- Spherical SRP near Earth-shadow transition: `unresolved` calibration xfail.
- Jacchia-Roberts constant-values atmosphere with spherical drag: `verified` against GMAT when the GMAT validation image is configured.
- Position / velocity samples: `verified` for representative cases.
- Integrator fixed-step settings: `verified` for the GMAT comparison cases.
- Initial-state coordinate type: `partial` (Classical and Cartesian covered).
- Gravity model and third bodies: `partial` (degree / order zero plus Sun / Moon point masses).
- SRP spacecraft coefficients and area / mass: `partial` (spherical SRP covered; shadow transition unresolved).
- Atmosphere and drag spacecraft coefficients: `partial` (Jacchia-Roberts constant-values branch covered).

Comparison path: GMAT R2026a driver executed through the validation image. ASTROX `CoordSystem = "Inertial"` is mapped to GMAT `EarthMJ2000Eq` for the comparison.

Key constants and tolerances from [`tests/validation/cross_validation/propagator/test_hpop_gmat.py`](../../tests/validation/cross_validation/propagator/test_hpop_gmat.py):

- `START = "2024-01-01T00:00:00.000Z"`.
- `STOP = "2024-01-01T00:10:00.000Z"`.
- `SAMPLE_OFFSETS_S = (0.0, 300.0, 600.0)`.
- `EARTH_MU = 398600441500000.0`.
- `ASTROX_GRAVITY_FILE = "EGM2008.grv"`.
- Default position tolerance: `POSITION_ABS_M = 1.0e-5`.
- Default velocity tolerance: `VELOCITY_ABS_M_S = 1.0e-8`.
- Jacchia-Roberts drag case position tolerance: `5.0e-3` (5 mm).
- Jacchia-Roberts drag case velocity tolerance: `1.0e-5`.

Known residuals and conventions: the Jacchia-Roberts drag tolerances were calibrated after matching constant F10.7 / F10.7A / Kp inputs, because GMAT and ASTROX do not produce bitwise-identical atmosphere accelerations. The SRP Earth-shadow transition residual remains visible as a strict calibration xfail. Other atmosphere data-source branches, higher-degree gravity fields, and other integrator modes are not covered by cross-validation.

Live snapshot coverage: `propagator.hpop` has a sidecar snapshot at [`tests/validation/live_snapshot/propagator/hpop.snap.json`](../../tests/validation/live_snapshot/propagator/hpop.snap.json) covering `classical_two_body`, `cartesian_two_body`, `gravity_field_integrator`, and `full_branch_surface`. These live snapshots are drift detectors for response shape and do not prove physical correctness.

Cross-validation script: [`tests/validation/cross_validation/propagator/test_hpop_gmat.py`](../../tests/validation/cross_validation/propagator/test_hpop_gmat.py).
Live snapshot script: [`tests/validation/live_snapshot/propagator/test_hpop.py`](../../tests/validation/live_snapshot/propagator/test_hpop.py).

GMAT-backed validation requires the `GMAT_VALIDATION_IMAGE` environment variable to be set. In strict external-validation mode (`ASTROX_EXTERNAL_VALIDATION=strict`) the test fails if the image is unavailable; otherwise it skips. The shadow-transition case is marked with `pytest.mark.calibration` and `xfail(strict=True)`.
