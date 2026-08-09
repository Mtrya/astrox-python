# Celestial Validation Evidence

This page records the cross-validation and live-snapshot evidence for `astrox.celestial` (`ephemeris`, `cb_axes_rotation`, and `mpc_ephemeris`). It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/celestial/README.md`](../manual/celestial/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`. The live snapshots prove maintained response shape and value compatibility for the public SDK inputs they exercise; they are not semantic proof.

## Ephemeris

Status of `celestial.ephemeris`: `partial` — response, wire-declared frame, epoch, and sample-layout fields are `verified`; the numeric geometric state semantics are `unresolved`.

- Response structure: `verified` through live snapshots for an explicit Moon window — envelope (`IsSuccess`, `Message`, `Position`, `Period`) and the `Position` keys (`CentralBody`, `referenceFrame`, `epoch`, `interval`, `interpolationAlgorithm`, `interpolationDegree`, `cartesianVelocity`), with `cartesianVelocity` as a 7-value-per-sample list `[Time, X, Y, Z, dX, dY, dZ]` where positions are m and velocities are m/s.
- Wire-declared frame and central body: `verified` for the maintained cases. `Position.CentralBody` is `Earth` and `Position.referenceFrame` matches the requested `observer_frame` for `J2000` and `MeanEclpJ2000` at the requested epoch.
- Geometric state semantics: `unresolved`. The maintained executable comparison uses Skyfield 1.54 with the DE421 ephemeris as the independent target-minus-Earth geometric state at the same epoch; `MeanEclpJ2000` is obtained by applying the standard J2000 mean-obliquity rotation (23.439291111 deg) to the same geometric state. The comparison intentionally does not use Skyfield `observe()`, which would apply light-time and compare a retarded apparent state with ASTROX's sampled same-epoch state. DE430t is only probe history (its kernel contains a Mars barycenter segment rather than a Mars center segment) and is not part of the maintained comparison. ASTROX's internal planetary kernel is not known to be identical to Skyfield's, so the comparison stays a calibration probe: the residual is not explained and no passing tolerance is derived.

Key constants and probes from [`tests/validation/cross_validation/celestial/test_ephemeris_skyfield.py`](../../tests/validation/cross_validation/celestial/test_ephemeris_skyfield.py):

- `START = "2026-01-01T00:00:00.000Z"`, `STOP = "2026-01-02T00:00:00.000Z"`, sample step 43200 s, sample offsets 0, 43200, and 86400 s.
- Diagnostic resolution thresholds only: position 1e-6 km, velocity 1e-12 km/s. These are not passing tolerances; the numeric comparisons are retained as strict calibration xfails.
- Coverage: Moon and Mars × `J2000`/`MeanEclpJ2000` × three sample offsets (12 comparisons).

Known residuals and probe history: at the maintained 2026-01 window the Moon residuals are approximately 0.056 km / 2.37e-7 km/s and the Mars barycenter residuals are approximately 33.6 km / 1.26e-5 km/s; DE421 is similar. Applying an ERFA frame-bias rotation in either direction does not explain both position and velocity residuals. A second 2026-06 window changes the Mars position residual to about 69.8 km, and a 3600 s sample step leaves the 2026-01 residual essentially unchanged. The numeric geometric semantics therefore remain `unresolved`: the comparisons stay visible as strict calibration xfails with the probe notes preserved in the script, and no tolerance is derived from these observations.

## Central-body axes rotation

Status of `celestial.cb_axes_rotation`: `partial` — the same-body identity invariant, the Earth INERTIAL→FIXED transformation, and the Earth→Moon order=1 angular velocity are `verified`; the Earth→Moon quaternion remains `unresolved`.

- Response structure: `verified` through live snapshots for `order=0` (Rotation length 4) and `order=1` (Rotation length 7), with numeric items, on the default Earth→Moon request.
- Same-body identity invariant: `verified` through [`tests/validation/cross_validation/celestial/test_cb_axes_rotation_invariants.py`](../../tests/validation/cross_validation/celestial/test_cb_axes_rotation_invariants.py). With the same central body on both sides (`Earth` and `Moon`) and `INERTIAL` frames on both sides, the returned Rotation is the identity quaternion `(0, 0, 0, 1)` and the angular-velocity suffix is zero for `order=1`, within `ABS_TOL = 1e-12`, at two maintained epochs (`2026-01-01T00:00:00.000Z` and `2026-06-01T00:00:00.000Z`), for 8 checks total.
- Earth INERTIAL→FIXED transformation: `verified` for `order=0` and `order=1` against an independent ERFA construction (`c2i06a` plus the Earth rotation angle evaluated with UTC, matching the service's observed UTC rotation convention), at the two maintained epochs, within `MATRIX_ABS_TOL = 1e-8` and `ANGULAR_VELOCITY_ABS_TOL = 1e-10` rad/s.
- Earth→Moon INERTIAL→FIXED angular velocity (`order=1`): `verified` against an independent SPICE J2000→IAU_MOON orientation derivative (`xf2rav` on the maintained public PCK/DE440 data), at the two maintained epochs; the residual is about 4.7e-11 rad/s, within `ANGULAR_VELOCITY_ABS_TOL = 1e-10` rad/s.
- Earth→Moon INERTIAL→FIXED quaternion (`order=0`): `unresolved`. The independent SPICE DE440 IAU_MOON orientation differs by 0.001–0.003 degrees across the maintained epochs; the comparison is retained as a strict calibration xfail (`QUATERNION_RESOLUTION_DEG = 1e-6` is a diagnostic resolution, not a passing tolerance) until the ASTROX Moon frame/model convention is identified.
- Scope boundary: the maintained evidence covers the identity invariant, the Earth INERTIAL→FIXED branch, and the Earth→Moon order=1 angular velocity; the Earth→Moon quaternion and frame combinations beyond these remain `unverified`.

## MPC ephemeris

Status of `celestial.mpc_ephemeris`: structure `verified`, numeric values external-data-owned.

- Response structure: `verified` through the live snapshot for `target_name="Ceres"` with the server-owned default window (fixed `Start`/`Stop` omitted) — envelope (`IsSuccess`, `Message`, `OrbitElements`, `Position`), `OrbitElements` keys (`EpochMjdTdt`, `PeriTimeMjdTdt`, `Q`, `SemimajorAxis`, `Eccentricity`, `Inclination`, `Raan`, `ArgOfPeriapsis`, `MeanAnomaly`), and a `Position` CZML-like structure with the same keys as `ephemeris`.
- Numeric values: `unverified` as ASTROX semantics. The route fetches orbital elements from the external MPC API (`https://data.minorplanetcenter.net/api/get-orb`, element epoch in MJD TDT) and propagates them heliocentrically with a fixed 1-day step; the numeric orbital values are external-data-owned and may change with MPC updates. No independent oracle is maintained, so no semantic cross-validation is claimed. The maintained case omits `Start`/`Stop` so the server applies its orbital-epoch default window, avoiding fixed windows that could fall before a future MPC orbital epoch and be rejected.

## Live snapshot coverage

The celestial functions are exercised in [`tests/validation/live_snapshot/celestial/test_celestial.py`](../../tests/validation/live_snapshot/celestial/test_celestial.py), with sidecar [`tests/validation/live_snapshot/celestial/celestial.snap.json`](../../tests/validation/live_snapshot/celestial/celestial.snap.json) covering `ephemeris` (Moon, explicit window), `cb_axes_rotation` (order 0 and 1), and `mpc_ephemeris` (Ceres, server-owned default window). The snapshots freeze recursive nested type/layout descriptors: per-field value kinds, the CZML `cartesianVelocity` 7-value grouping, and the order-dependent `Rotation` lengths (4 for `order=0`, 7 for `order=1`); volatile numeric values are not frozen, and the MPC numeric values remain external-data-owned. These live snapshots are drift detectors for the response shape of maintained public inputs.

Cross-validation scripts:
- [`tests/validation/cross_validation/celestial/test_ephemeris_skyfield.py`](../../tests/validation/cross_validation/celestial/test_ephemeris_skyfield.py)
- [`tests/validation/cross_validation/celestial/test_cb_axes_rotation_invariants.py`](../../tests/validation/cross_validation/celestial/test_cb_axes_rotation_invariants.py)
