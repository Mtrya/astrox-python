# CAT Validation Evidence

This page records the cross-validation and live-snapshot evidence for `astrox.cat` (TLE generation, orbital lifetime estimation, and debris breakup simulation). It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/cat/README.md`](../manual/cat/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`. The live snapshots prove maintained response shape and value compatibility for the public SDK inputs they exercise; they are not semantic proof.

## TLE generation

Status of `cat.generate_tle`:

- Instantaneous-elements branch (`is_mean_elements` omitted or `False`): `verified` against an independent TEME Keplerian state oracle for two element cases.
- TLE identifiers, epoch, and TEME state: `verified` for the false-element branch.
- Mean-elements branch (`is_mean_elements=True`): `unresolved`, retained as a strict calibration xfail. An independent mean-to-osculating SGP4 conversion oracle would be required; the naive comparison with the input osculating elements remains mismatched after the bounded probe.

Comparison path: Skyfield 1.54 raw SGP4 TEME state at epoch, checked against a local Keplerian state derived from the input elements (Brahe `state_koe_to_eci` with a true-to-mean anomaly conversion).

Key constants and tolerances from [`tests/validation/cross_validation/cat/test_cat_skyfield.py`](../../tests/validation/cross_validation/cat/test_cat_skyfield.py):

- `MU_M3_S2 = 398600441500000.0`.
- Generated-state tolerances: `GENERATED_STATE_ABS_M = 10.0` and `GENERATED_VELOCITY_ABS_M_S = 0.02`.

Known residuals and conventions: the false-element output matches the independent input osculating state in raw SGP4 TEME coordinates after one direct comparison; the residual is a few meters and is covered by the stated numerical precision bound.

## Lifetime estimation

Status of `cat.estimate_tle_lifetime`:

- `life_years`: `partial`. The monotonic direction of the response is verified for three increasing numeric parameter-ratio cases (`(1.0, 1000.0)`, `(10.0, 10.0)`, `(100.0, 1.0)`); the observed lifetimes decrease strictly across the ratios.
- Absolute lifetime semantics: unknown. The live endpoint returns a documented fallback value for some cases, so the script checks only the observed monotonic direction for non-fallback cases and does not promote an absolute lifetime oracle.

## Debris breakup

Status of `cat.simulate_debris_breakup_simple`, `cat.simulate_debris_breakup`, and `cat.simulate_debris_breakup_nasa`:

- Returned debris TLEs, `periods_min`, `altitude_of_perigee_km`, and `altitude_of_apogee_km`: `verified` as internally consistent orbital quantities.
- Comparison: each returned debris TLE is propagated with Skyfield 1.54 raw SGP4, and period / perigee / apogee are derived from the state's two-body energy and angular momentum.
- Parameter coverage: simple bounded-angle input (count 2, azimuth 40°–180°, elevation 0°–2°), explicit two-impulse input, and NASA mass/length input.
- Impulse semantics: outside this comparison. The impulse values are only wire-shape verified by behavior and live snapshot tests; no physical impulse convention is asserted here.

Key constants and tolerances:

- `MU_M3_S2 = 398600441500000.0`.
- Calibrated server Earth radius: `EARTH_RADIUS_M = 6378140.0`.
- Altitude tolerance: `DEBRIS_ALTITUDE_ABS_KM = 0.001`.
- Period tolerance: `DEBRIS_PERIOD_ABS_MIN = 1.0e-5`.

Known residuals and conventions: debris periods match the two-body period derived from the returned TLE state. Altitudes match when the local derivation uses the server's apparent 6378.140 km Earth radius; the radius constant was changed once from the common 6378.1363 km candidate after the stable residual showed a 3.9 m offset.

Scope boundary: the verification covers internal consistency of the returned orbital quantities with independent SGP4 states. This page does not claim that the debris breakup model (debris counts, velocity distribution, mass distribution), collision probability, or lifetime prediction is scientifically correct.

## Live snapshot coverage

The CAT functions are exercised in [`tests/validation/live_snapshot/cat/test_cat.py`](../../tests/validation/live_snapshot/cat/test_cat.py), with sidecar [`tests/validation/live_snapshot/cat/cat.snap.json`](../../tests/validation/live_snapshot/cat/cat.snap.json) covering `generate_tle`, `estimate_tle_lifetime`, `debris_breakup_simple`, `debris_breakup`, and `debris_breakup_nasa`. These live snapshots are drift detectors for the response shape and values of maintained public inputs; they do not prove physical or semantic correctness.

Cross-validation script: [`tests/validation/cross_validation/cat/test_cat_skyfield.py`](../../tests/validation/cross_validation/cat/test_cat_skyfield.py).
Live snapshot script: [`tests/validation/live_snapshot/cat/test_cat.py`](../../tests/validation/live_snapshot/cat/test_cat.py).
