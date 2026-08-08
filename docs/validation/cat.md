# CAT Validation Evidence

This page records the cross-validation and live-snapshot evidence for `astrox.cat` (TLE generation, orbital lifetime estimation, and debris breakup simulation). It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/cat/README.md`](../manual/cat/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`. The live snapshots prove maintained response shape and value compatibility for the public SDK inputs they exercise; they are not semantic proof.

## TLE generation

Status of `cat.generate_tle`:

- Instantaneous-elements branch: `verified`. Both request forms — `is_mean_elements=False` and `is_mean_elements` omitted — are exercised live against an independent TEME Keplerian state oracle, with two element cases for each form.
- TLE identifiers, epoch, and TEME state: `verified` for the false/omitted branch. The generated TLE epoch is compared explicitly with `START` within `EPOCH_ABS_S = 0.01` s before the state comparison.
- Mean-elements branch (`is_mean_elements=True`): `partial`. For moderate/high eccentricity (e = 0.01, 0.05), the input true anomaly is converted to mean anomaly and the output argument-of-perigee plus mean-anomaly preserves the corresponding input mean longitude within 0.1 deg, read from independent Skyfield TLE mean fields (eccentricity within 0.0012, inclination and RAAN within 0.02 deg). The near-circular branch (e ≈ 0.0001882) redistributes argument of perigee and mean anomaly and retains an unexplained kilometre-scale state residual; it remains a strict calibration xfail, so the full true-to-mean conversion is not claimed verified.

Comparison path: Skyfield 1.54 raw SGP4 TEME state at epoch, checked against a local Keplerian state derived from the input elements (Brahe `state_koe_to_eci` with a true-to-mean anomaly conversion); Skyfield TLE mean fields (`ecco`, `inclo`, `argpo`, `nodeo`, `mo`) as the independent mean-element readout for the mean-elements branch.

Key constants and tolerances from [`tests/validation/cross_validation/cat/test_cat_skyfield.py`](../../tests/validation/cross_validation/cat/test_cat_skyfield.py):

- `START = "2024-01-01T00:00:00.000Z"`.
- `MU_M3_S2 = 398600441500000.0`.
- TLE epoch tolerance: `EPOCH_ABS_S = 0.01`.
- Generated-state tolerances: `GENERATED_STATE_ABS_M = 10.0` and `GENERATED_VELOCITY_ABS_M_S = 0.02`.
- Mean-element longitude tolerance: 0.1 deg, with eccentricity within 0.0012 and inclination / RAAN within 0.02 deg.

Known residuals and conventions: the explicit-false and omitted-`is_mean_elements` outputs both match the independent input osculating state in raw SGP4 TEME coordinates at the requested epoch; the residual is a few meters and is covered by the stated numerical precision bounds.

## Lifetime estimation

Status of `cat.estimate_tle_lifetime`: `partial`.

- `life_years`: `partial` as a relative estimator. The response depends on the `sm`/`mass` ratio: matched-ratio cases (`(0.1, 100)` vs `(1, 1000)`, `(1, 100)` vs `(10, 1000)`, `(10, 100)` vs `(1, 10)`) agree value-for-value within 1e-12, and the three-ratio sweep (`(1.0, 1000.0)`, `(10.0, 10.0)`, `(100.0, 1.0)`) decreases strictly. Low ratios return the 25-year cap.
- Breakup A2M equivalence: debris `life_years` from `simulate_debris_breakup` with `area_to_mass_ratio_m2_kg = ratio` agree value-for-value with `estimate_tle_lifetime(sm=ratio, mass=1.0)` for ratios 0.001, 0.002, and 0.01 within 1e-12.
- Absolute lifetime semantics: unknown. `life_years` is not promoted as an absolute physical lifetime prediction; the 25-year cap and the documented fallback values are server-owned. The branch as a whole stays `partial` while absolute lifetime semantics remain unverified.

## Debris breakup

Status of `cat.simulate_debris_breakup_simple`, `cat.simulate_debris_breakup`, and `cat.simulate_debris_breakup_nasa`:

- Returned debris TLEs, `periods_min`, `altitude_of_perigee_km`, and `altitude_of_apogee_km`: `verified` as internally consistent orbital quantities.
- Response arrays are synchronized positional fields: `debris_tles`, `impulses`, `life_years`, `altitude_of_perigee_km`, `altitude_of_apogee_km`, and `periods_min` correspond by return position. The cross-validation asserts the orbital arrays have equal lengths, and the SDK parser raises `TypeError` when the synchronized lengths do not match.
- Comparison: each returned debris TLE is propagated with Skyfield 1.54 raw SGP4, and period / perigee / apogee are derived from the state's two-body energy and angular momentum.
- Parameter coverage: simple bounded-angle input (count 2, azimuth 40°–180°, elevation 0°–2°), explicit two-impulse input, and NASA mass/length input.
- AzElVel (`impulses` in the response): `verified` for explicit breakup as an input echo whose delta-v norm matches m/s. At the epoch, the direction follows an RTN convention — azimuth 0° → +along-track, 90° → −cross-track, 180° → −along-track, and positive elevation → +radial — within 0.02 m/s across five azimuth/elevation cases.
- A2M sweep: `area_to_mass_ratio_m2_kg` over 0.0002, 0.002, and 0.02 does not change the generated orbit (period, perigee, and apogee within the stated tolerances) but changes the returned lifetime monotonically.

Key constants and tolerances:

- `MU_M3_S2 = 398600441500000.0`.
- Calibrated server Earth radius: `EARTH_RADIUS_M = 6378140.0`.
- Altitude tolerance: `DEBRIS_ALTITUDE_ABS_KM = 0.001`.
- Period tolerance: `DEBRIS_PERIOD_ABS_MIN = 1.0e-5`.
- RTN delta-v tolerance: 0.02 m/s.

Known residuals and conventions: debris periods match the two-body period derived from the returned TLE state. Altitudes match when the local derivation uses the server's apparent 6378.140 km Earth radius; the radius constant was changed once from the common 6378.1363 km candidate after the stable residual showed a 3.9 m offset.

Scope boundary: the verification covers internal consistency of the returned orbital quantities with independent SGP4 states. This page does not claim that the debris breakup model (debris counts, velocity distribution, mass distribution), collision probability, or lifetime prediction is scientifically correct.

## Live snapshot coverage

The CAT functions are exercised in [`tests/validation/live_snapshot/cat/test_cat.py`](../../tests/validation/live_snapshot/cat/test_cat.py), with sidecar [`tests/validation/live_snapshot/cat/cat.snap.json`](../../tests/validation/live_snapshot/cat/cat.snap.json) covering `generate_tle`, `estimate_tle_lifetime`, `debris_breakup_simple`, `debris_breakup`, and `debris_breakup_nasa`. These live snapshots are drift detectors for the response shape and values of maintained public inputs; they do not prove physical or semantic correctness.

Cross-validation script: [`tests/validation/cross_validation/cat/test_cat_skyfield.py`](../../tests/validation/cross_validation/cat/test_cat_skyfield.py).
Live snapshot script: [`tests/validation/live_snapshot/cat/test_cat.py`](../../tests/validation/live_snapshot/cat/test_cat.py).
