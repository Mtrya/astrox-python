# Celestial Validation Evidence

This page records the cross-validation and live-snapshot evidence for `astrox.celestial` (`ephemeris`, `cb_axes_rotation`, and `mpc_ephemeris`). It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/celestial/README.md`](../manual/celestial/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`. The live snapshots prove maintained response shape and value compatibility for the public SDK inputs they exercise; they are not semantic proof.

## Ephemeris

Status of `celestial.ephemeris`: `partial`.

- Response structure: `verified` through live snapshots for an explicit Moon window — envelope (`IsSuccess`, `Message`, `Position`, `Period`) and the `Position` keys (`CentralBody`, `referenceFrame`, `epoch`, `interval`, `interpolationAlgorithm`, `interpolationDegree`, `cartesianVelocity`), with `cartesianVelocity` as a 7-value-per-sample list `[Time, X, Y, Z, dX, dY, dZ]` where positions are m and velocities are m/s.
- Wire-declared frame and central body: `verified` for the maintained cases. `Position.CentralBody` is `Earth` and `Position.referenceFrame` matches the requested `observer_frame` for `J2000` and `MeanEclpJ2000` at the requested epoch.
- Geometric state semantics: `partial`. The comparison uses Skyfield 1.54 with the DE421 ephemeris as an independent target-minus-Earth geometric state at the same epoch; `MeanEclpJ2000` is obtained by applying the standard J2000 mean-obliquity rotation (23.439291111 deg) to the same geometric state. The comparison intentionally does not use Skyfield `observe()`, which would apply light-time and compare a retarded apparent state with ASTROX's sampled same-epoch state. ASTROX's internal planetary kernel is not known to be identical to Skyfield's DE421 kernel, so the comparison calibrates an envelope rather than proving exact equivalence.

Key constants and tolerances from [`tests/validation/cross_validation/celestial/test_ephemeris_skyfield.py`](../../tests/validation/cross_validation/celestial/test_ephemeris_skyfield.py):

- `START = "2026-01-01T00:00:00.000Z"`, `STOP = "2026-01-02T00:00:00.000Z"`, sample step 43200 s, sample offsets 0, 43200, and 86400 s.
- Position tolerance `POSITION_ABS_KM`: Moon 0.1 km, Mars 40 km.
- Velocity tolerance `VELOCITY_ABS_KM_S`: Moon 1e-6 km/s, Mars 2e-5 km/s.
- Coverage: Moon and Mars × `J2000`/`MeanEclpJ2000` × three sample offsets (12 comparisons).

Known residuals: Moon residuals are approximately 0.04–0.06 km and 2.2–2.4e-7 km/s in the maintained 2026 window; Mars residuals are approximately 32.7 km and 1.27e-5 km/s. These stable differences are treated as cross-kernel/model residuals and are not erased by claiming exact ephemeris equivalence; the page does not claim per-point exactness.

## Central-body axes rotation

Status of `celestial.cb_axes_rotation`: `verified` only for the same-body inertial identity invariant; arbitrary transformations remain outside the check.

- Response structure: `verified` through live snapshots for `order=0` (Rotation length 4) and `order=1` (Rotation length 7), with numeric items, on the default Earth→Moon request.
- Same-body identity invariant: `verified` through [`tests/validation/cross_validation/celestial/test_cb_axes_rotation_invariants.py`](../../tests/validation/cross_validation/celestial/test_cb_axes_rotation_invariants.py). With the same central body on both sides (`Earth` and `Moon`) and `INERTIAL` frames on both sides, the returned Rotation is the identity quaternion `(0, 0, 0, 1)` and the angular-velocity suffix is zero for `order=1`, within `ABS_TOL = 1e-12`, at two maintained epochs (`2026-01-01T00:00:00.000Z` and `2026-06-01T00:00:00.000Z`), for 8 checks total.
- Scope boundary: arbitrary central-body/frame transformation values (e.g. FIXED↔INERTIAL or cross-body rotations) are `unverified`; the maintained evidence covers only the identity invariant and the response shape, not the correctness of general axes-rotation semantics.

## MPC ephemeris

Status of `celestial.mpc_ephemeris`: structure `verified`, numeric values external-data-owned.

- Response structure: `verified` through the live snapshot for `target_name="Ceres"` with an explicit window — envelope (`IsSuccess`, `Message`, `OrbitElements`, `Position`), `OrbitElements` keys (`EpochMjdTdt`, `PeriTimeMjdTdt`, `Q`, `SemimajorAxis`, `Eccentricity`, `Inclination`, `Raan`, `ArgOfPeriapsis`, `MeanAnomaly`), and a `Position` CZML-like structure with the same keys as `ephemeris`.
- Numeric values: `unverified` as ASTROX semantics. The route fetches orbital elements from the external MPC API (`https://data.minorplanetcenter.net/api/get-orb`, element epoch in MJD TDT) and propagates them heliocentrically with a fixed 1-day step; the numeric orbital values are external-data-owned and may change with MPC updates. No independent oracle is maintained, so no semantic cross-validation is claimed. Query windows are subject to the external orbital epoch: the maintained cases use a 2026 window after the Ceres orbital epoch.

## Live snapshot coverage

The celestial functions are exercised in [`tests/validation/live_snapshot/celestial/test_celestial.py`](../../tests/validation/live_snapshot/celestial/test_celestial.py), with sidecar [`tests/validation/live_snapshot/celestial/celestial.snap.json`](../../tests/validation/live_snapshot/celestial/celestial.snap.json) covering `ephemeris` (Moon, explicit window), `cb_axes_rotation` (order 0 and 1), and `mpc_ephemeris` (Ceres, explicit window). These live snapshots are drift detectors for the response shape of maintained public inputs.

Cross-validation scripts:
- [`tests/validation/cross_validation/celestial/test_ephemeris_skyfield.py`](../../tests/validation/cross_validation/celestial/test_ephemeris_skyfield.py)
- [`tests/validation/cross_validation/celestial/test_cb_axes_rotation_invariants.py`](../../tests/validation/cross_validation/celestial/test_cb_axes_rotation_invariants.py)
