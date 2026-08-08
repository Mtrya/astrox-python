# Conjunction Validation Evidence

This page records the cross-validation and live-snapshot evidence for `astrox.conjunction`. It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/conjunction/README.md`](../manual/conjunction/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`. The live snapshots prove maintained response shape and value compatibility for the public SDK inputs they exercise; they are not semantic proof.

## TLE entry (V3)

Status of `conjunction.find_tle_close_approaches`: `unresolved` overall, because the complete result includes `CA_Probability`, which remains an unresolved server-owned scalar. The remaining fields are calibrated as follows:

- TLE primary plus TLE targets branch: `unresolved` overall; range, relative speed, continuous TCA, and the TLE-defined plane angle are calibrated across target mean-anomaly, RAAN, inclination, and stop-time cases, while `collision_probability` remains unresolved.
- `min_range_km`: `verified` against the GCRS 3-D separation within `RANGE_ABS_KM = 0.001` km.
- `relative_speed_km_s`: `verified` against the GCRS relative speed within `RELATIVE_SPEED_ABS_KM_S = 5.0e-7` km/s.
- `min_range_time` (TCA): compared with an independent continuous local minimum of the Skyfield GCRS range (1-second coarse scan plus golden-section local refinement). The interior off-grid case (target mean anomaly 142.85°, TCA ≈ 534.305 s) lands inside the window but off the 60-second grid and matches the independent continuous minimum within one second, so V3 is not described as a sampled-grid convention; boundary-only cases cannot distinguish sampled-time from continuous-time behavior.
- `orbital_plane_angle_deg`: compared with the full plane angle derived from both TLE inclinations and RAANs within `V3_ANGLE_ABS_DEG = 0.01` deg. Independent RAAN-only and inclination-only probes distinguish the result from the absolute TLE inclination difference.
- Stop-time coverage: `verified` at 5, 8, and 10 minutes; the sample at Stop participates in reporting.
- Target mean-anomaly cases: 135°, 137.7421°, 140°, and 145°; the 130° case is retained as a no-result filter boundary (`total_number = 1` with an empty `results` list).
- `collision_probability`: `unresolved`; see the dedicated section below.

Comparison path: Skyfield 1.54 `EarthSatellite` GCRS state propagation on checked-in TLEs with UTC epochs, a 1-second coarse scan plus golden-section local refinement for the continuous TCA minimum, and the TLE inclination/RAAN plane-angle derivation for the V3 plane angle.

Key constants and tolerances from [`tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py`](../../tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py):

- `START = "2024-01-01T00:00:00.000Z"`.
- `SAMPLE_STEP_S = 60`.
- TCA tolerance: 1 second.
- Range tolerance: `RANGE_ABS_KM = 0.001`.
- Relative-speed tolerance: `RELATIVE_SPEED_ABS_KM_S = 5.0e-7`.
- V3 plane-angle tolerance: `V3_ANGLE_ABS_DEG = 0.01`.
- V4 plane-angle tolerance: `V4_ANGLE_ABS_DEG = 0.00051`.

Known residuals and conventions: the V3 TCA matches the independent continuous minimum within one second, including the interior off-grid case, so the 60-second grid is a property of the tested input sampling, not a claimed server convention. The V3 plane angle follows the full angle derived from the two TLE inclinations and RAANs instead of the absolute inclination difference or the instantaneous GCRS angular-momentum angle.

## CZML entry (V4)

Status of `conjunction.find_czml_close_approaches`: `unresolved` overall, for the same reason as the TLE entry: the complete result includes `CA_Probability`, which remains an unresolved server-owned scalar. The remaining fields are calibrated as follows:

- CZML primary plus TLE targets branch: `unresolved` overall; range, relative speed, the supplied-sample boundary behavior, and the GCRS plane angle are calibrated across three stop-time cases (5, 8, and 10 minutes) using a 60-second public SGP4 position, while `collision_probability` remains unresolved.
- `min_range_km` and `relative_speed_km_s`: `verified` against the same GCRS geometry as the TLE entry within the same tolerances.
- `orbital_plane_angle_deg`: `verified` against the instantaneous GCRS angular-momentum angle within `V4_ANGLE_ABS_DEG = 0.00051` deg.
- `min_range_time`: compared with the supplied 60-second CZML sample boundary convention. The final CZML sample at Stop is excluded by the observed server interval convention, so the reported closest-approach time falls on the supplied sample one step before Stop.
- `collision_probability`: `unresolved`; see the dedicated section below.

The CZML primary is produced with the public `propagator.sgp4` at 60-second sampling and converted to `components.czml_position`, so this branch also exercises the public propagation surface.

Comparison path and tolerances: the same Skyfield GCRS oracle and the constants listed for the TLE entry, with `V4_ANGLE_ABS_DEG = 0.00051`.

## Collision probability

Status of `collision_probability`: `unresolved`.

Eight live probe rounds observed a stable wire zero:

- Rounds 1–4 (earlier): repeated V3/V4 calls; target-distance changes via target mean anomalies 135° and 140°; a plane-angle change via target inclination +5°; a relative-speed change via target mean motion 16.52489080 rev/day; and filter thresholds from 1000 km to 10000 km.
- Rounds 5–8 (new): independent geometry axes — eccentricity 0.02, inclination 40°, RAAN 90°, and mean anomaly 135°/142.8°; a threshold matrix (broad, distance, cross-dt, and plane values); V3/V4 cadence parity at 30 s, 60 s, and 120 s CZML sampling; and a sub-kilometre encounter (eccentricity 0.0018) plus a repeated and a multi-target response.

Every returned wire value was exactly integer zero, including the repeated calls and the multi-target response. The OpenAPI request and live response expose no covariance, hard-body radius, uncertainty, or equivalent probability-model input, and there is no independent probability oracle, so the field is classified as a stable server-owned opaque scalar rather than a verified statistical collision probability. The case is retained as a strict calibration xfail in [`tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py`](../../tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py), and the field is not assigned statistical collision-probability semantics.

## Live snapshot coverage

Both close-approach functions are exercised in [`tests/validation/live_snapshot/conjunction/test_close_approaches.py`](../../tests/validation/live_snapshot/conjunction/test_close_approaches.py), with sidecar [`tests/validation/live_snapshot/conjunction/close_approaches.snap.json`](../../tests/validation/live_snapshot/conjunction/close_approaches.snap.json) covering the `tle_v3` and `czml_v4` cases. These live snapshots are drift detectors for the response shape and values of maintained public inputs; they do not prove physical or semantic correctness.

Cross-validation script: [`tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py`](../../tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py).
Live snapshot script: [`tests/validation/live_snapshot/conjunction/test_close_approaches.py`](../../tests/validation/live_snapshot/conjunction/test_close_approaches.py).
