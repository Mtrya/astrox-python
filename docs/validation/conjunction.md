# Conjunction Validation Evidence

This page records the cross-validation and live-snapshot evidence for `astrox.conjunction`. It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/conjunction/README.md`](../manual/conjunction/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`. The live snapshots prove maintained response shape and value compatibility for the public SDK inputs they exercise; they are not semantic proof.

## TLE entry (V3)

Status of `conjunction.find_tle_close_approaches`:

- TLE primary plus TLE targets branch: `verified` for four target mean-anomaly cases (135°, 137.7421°, 140°, 145°) at 60-second sampling over a 10-minute window.
- `min_range_time`: `verified` as the nearest sampled epoch on the server's 60-second grid.
- `min_range_km`: `verified` against the GCRS 3-D separation, rounded to 0.001 km.
- `relative_speed_km_s`: `verified` against the GCRS relative speed, rounded to 1e-6 km/s.
- `orbital_plane_angle_deg`: `verified` as the absolute TLE inclination difference, rounded to 0.01 deg.
- Stop-time coverage: `verified` at 5, 8, and 10 minutes; the sample at Stop participates in reporting.
- No-result filter boundary: the 130° mean-anomaly case is retained as a filtered-empty case (`total_number = 1` with an empty `results` list).

Comparison path: Skyfield 1.54 `EarthSatellite` GCRS state propagation on checked-in TLEs with UTC epochs and a 60-second sample interval.

Key constants and tolerances from [`tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py`](../../tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py):

- `START = "2024-01-01T00:00:00.000Z"`.
- `SAMPLE_STEP_S = 60`.
- Range tolerance: `RANGE_ABS_KM = 0.001`.
- Relative-speed tolerance: `RELATIVE_SPEED_ABS_KM_S = 5.0e-7`.
- V3 plane-angle tolerance: `V3_ANGLE_ABS_DEG = 0.0051`.
- V4 plane-angle tolerance: `V4_ANGLE_ABS_DEG = 0.00051`.

Known residuals and conventions: the naive continuous-time interpretation is not used as the maintained oracle. ASTROX reports the nearest one-minute sampled epoch for these requests, and a 1-second Skyfield scan confirmed that the reported samples are the nearest values on the server's 60-second grid. The V3 plane angle matches the absolute TLE inclination difference instead of the instantaneous GCRS angular-momentum angle.

## CZML entry (V4)

Status of `conjunction.find_czml_close_approaches`:

- CZML primary plus TLE targets branch: `verified` for three stop-time cases (5, 8, and 10 minutes) using a 60-second public SGP4 position.
- `min_range_km` and `relative_speed_km_s`: `verified` against the same GCRS geometry as the TLE entry.
- `orbital_plane_angle_deg`: `verified` against the instantaneous GCRS angular-momentum angle, rounded to 0.001 deg.
- Interval convention: the final CZML sample at Stop is excluded by the observed server interval convention, so the reported closest-approach time falls on the sample one step before Stop.

The CZML primary is produced with the public `propagator.sgp4` at 60-second sampling and converted to `components.czml_position`, so this branch also exercises the public propagation surface.

Comparison path and tolerances: the same Skyfield GCRS oracle and the constants listed for the TLE entry, with `V4_ANGLE_ABS_DEG = 0.00051`.

## Collision probability

Status of `collision_probability`:

- `unresolved`: four live probe rounds — repeated V3/V4 calls; target-distance changes via target mean anomalies 135° and 140°; a plane-angle change via target inclination +5°; a relative-speed change via target mean motion 16.52489080 rev/day; and filter thresholds from 1000 km to 10000 km — all observed `collision_probability = 0.0`. The promoted requests expose no covariance, hard-body radius, or equivalent error model, and there is no independent probability oracle, so the field is classified as a stable server-owned opaque scalar rather than a verified statistical collision probability. The case is retained as a strict calibration xfail in the cross-validation script.

## Live snapshot coverage

Both close-approach functions are exercised in [`tests/validation/live_snapshot/conjunction/test_close_approaches.py`](../../tests/validation/live_snapshot/conjunction/test_close_approaches.py), with sidecar [`tests/validation/live_snapshot/conjunction/close_approaches.snap.json`](../../tests/validation/live_snapshot/conjunction/close_approaches.snap.json) covering the `tle_v3` and `czml_v4` cases. These live snapshots are drift detectors for the response shape and values of maintained public inputs; they do not prove physical or semantic correctness.

Cross-validation script: [`tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py`](../../tests/validation/cross_validation/conjunction/test_close_approaches_skyfield.py).
Live snapshot script: [`tests/validation/live_snapshot/conjunction/test_close_approaches.py`](../../tests/validation/live_snapshot/conjunction/test_close_approaches.py).
