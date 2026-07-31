# Orbits Validation Evidence

This page records the cross-validation status of the `astrox.orbits` surface. It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/orbits/README.md`](../manual/orbits/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) are taken directly from the coverage checklists in the cross-validation scripts listed under each family.

| Family | Cross-validation script | Live snapshot sidecar |
| --- | --- | --- |
| Orbit conversions | [`tests/validation/cross_validation/orbits/test_kozai_izsak_mean_elements_invariants.py`](../../tests/validation/cross_validation/orbits/test_kozai_izsak_mean_elements_invariants.py) | [`tests/validation/live_snapshot/orbits/conversions.snap.json`](../../tests/validation/live_snapshot/orbits/conversions.snap.json) |
| Internal conversion consistency | [`tests/validation/live_snapshot/orbits/test_conversion_roundtrip.py`](../../tests/validation/live_snapshot/orbits/test_conversion_roundtrip.py) | none (runtime consistency check) |
| Orbit wizards | [`tests/validation/cross_validation/orbits/test_wizards_local_derivation.py`](../../tests/validation/cross_validation/orbits/test_wizards_local_derivation.py) | [`tests/validation/live_snapshot/orbits/wizards.snap.json`](../../tests/validation/live_snapshot/orbits/wizards.snap.json) |
| Walker constellations | [`tests/validation/cross_validation/orbits/test_walker_constellation_equations.py`](../../tests/validation/cross_validation/orbits/test_walker_constellation_equations.py) | [`tests/validation/live_snapshot/orbits/wizards.snap.json`](../../tests/validation/live_snapshot/orbits/wizards.snap.json) |
| Lambert transfers | [`tests/validation/cross_validation/orbits/test_lambert_lamberthub.py`](../../tests/validation/cross_validation/orbits/test_lambert_lamberthub.py) | [`tests/validation/live_snapshot/orbits/conversions.snap.json`](../../tests/validation/live_snapshot/orbits/conversions.snap.json) |
| Frame / libration transforms | [`tests/validation/cross_validation/orbit_system/test_convert_czml_position.py`](../../tests/validation/cross_validation/orbit_system/test_convert_czml_position.py), [`tests/validation/cross_validation/orbit_system/test_earth_moon_libration.py`](../../tests/validation/cross_validation/orbit_system/test_earth_moon_libration.py) | [`tests/validation/live_snapshot/orbits/orbit_system.snap.json`](../../tests/validation/live_snapshot/orbits/orbit_system.snap.json) |

## Orbit Conversions

### Keplerian / Cartesian

`keplerian_to_cartesian` and `cartesian_to_keplerian` are covered by a live internal-consistency check, not by an independent external comparison.

| Branch | Status | Comparison path |
| --- | --- | --- |
| `keplerian_to_cartesian` | Internal roundtrip verified; independent physical cross-validation unverified | ASTROX-internal roundtrip through `cartesian_to_keplerian` |
| `cartesian_to_keplerian` | Internal roundtrip verified; independent physical cross-validation unverified | ASTROX-internal roundtrip through `keplerian_to_cartesian` |

The roundtrip script exercises four Keplerian inputs (LEO, inclined, GEO-like, eccentric) and one Cartesian sample. Tolerances are `SEMI_MAJOR_AXIS_ABS_M = 0.1`, `ECCENTRICITY_ABS = 2.0e-9`, `ANGLE_ABS_DEG = 1.0e-6`, `ARGUMENT_OF_LATITUDE_ABS_DEG = 1.0e-9`, `POSITION_ABS_M = 1.0e-4`, and `VELOCITY_ABS_M_S = 5.0e-6`. For near-circular orbits the comparison uses argument of latitude; for eccentric orbits it compares `argument_of_periapsis_deg` and `true_anomaly_deg` separately.

Live snapshot sidecars: `conversions.snap.json` records `keplerian_to_cartesian` and `cartesian_to_keplerian` response shapes.

### `lla_at_ascending_node`

| Branch | Status | Comparison path |
| --- | --- | --- |
| `lla_at_ascending_node` | unverified | none |

No independent cross-validation script exists for the ascending-node longitude/latitude/height output. The function is exercised only as a live snapshot shape check in `conversions.snap.json`.

### `kozai_izsak_mean_elements`

Coverage status from [`test_kozai_izsak_mean_elements_invariants.py`](../../tests/validation/cross_validation/orbits/test_kozai_izsak_mean_elements_invariants.py):

| Branch / Field | Status |
| --- | --- |
| `kozai_izsak_mean_elements` | partial |
| `semi_major_axis_m`, `eccentricity`, `inclination_deg` | partial (bounded near the osculating input for one representative LEO) |
| `raan_deg`, `argument_of_perigee_deg`, `mean_anomaly_deg` | partial (finite angular values checked) |
| `longitude_of_perigee_deg` | verified against `raan_deg + argument_of_perigee_deg` modulo 360 |
| `mean_longitude_deg` | verified against `longitude_of_perigee_deg + mean_anomaly_deg` modulo 360 |
| `argument_of_latitude_deg` | partial (finite angular value checked; ASTROX convention not fully calibrated) |
| Input osculating `KeplerianElements` | partial (one representative LEO case) |

Comparison path: local angular identities for Keplerian mean elements and bounded near-orbit physical invariants. Constants and tolerances: `NEAR_SEMI_MAJOR_AXIS_ABS_M = 2500.0`, `NEAR_ECCENTRICITY_ABS = 5.0e-4`, `NEAR_INCLINATION_ABS_DEG = 1.0e-2`, plus `ANGLE_ABS_DEG = 1.0e-9` for wrapped-angle identities.

Unresolved: full Kozai-Izsak short-period removal has not yet been compared with a Vallado-style independent implementation.

Live snapshot sidecar: `conversions.snap.json` includes `kozai_izsak_mean_elements`.

## Orbit Wizards

### GEO, Molniya, SSO

Coverage status from [`test_wizards_local_derivation.py`](../../tests/validation/cross_validation/orbits/test_wizards_local_derivation.py):

| Wizard | Status |
| --- | --- |
| GEO | partial |
| Molniya | partial |
| SSO | partial |

Verified items per wizard:

- GEO: `semi_major_axis_m`, `eccentricity`, `inclination_deg`, TOD RAAN longitude convention, `argument_of_periapsis_deg`, `true_anomaly_deg`.
- Molniya: perigee altitude, calibrated 12-hour resonant period, `eccentricity`, critical inclination, TOD RAAN longitude convention, `argument_of_periapsis_deg`, `true_anomaly_deg`.
- SSO: altitude-derived `semi_major_axis_m`, `eccentricity`, J2 nodal-precession inclination, `argument_of_periapsis_deg`, `true_anomaly_deg`.

Partial items:

- The TOD-to-inertial element pair is only checked for finite near-TOD geometry and matching `semi_major_axis_m`/`eccentricity`.
- GEO/Molniya resonant periods use calibrated ASTROX wizard constants rather than a separately published server constant.
- SSO local-time-to-RAAN mapping and the inertial pair remain partial.
- Each wizard is exercised for one representative parameter case.

Comparison path: local two-body geometry, Skyfield GMST for TOD longitude-to-RAAN conversion, and the J2 nodal-precession equation for SSO inclination. Constants: `EARTH_MU = 398600441500000.0`, `EARTH_RADIUS_M = 6378137.0`, `J2_UNNORMALIZED = 0.00108262668`, `SUN_MEAN_MOTION_DEG_PER_DAY = 0.98564736`, `ASTROX_GEO_PERIOD_S = 86170.49417017814`, `ASTROX_MOLNIYA_PERIOD_S = 43064.70571005682`. Tolerances: `LENGTH_ABS_M = 1.0e-3`, `ECC_ABS = 1.0e-12`, `ANGLE_ABS_DEG = 5.0e-5`, `TOD_RAAN_ABS_DEG = 1.0e-4`, and `INERTIAL_ANGLE_NEAR_TOD_DEG = 2.0` for the inertial-pair sanity bound.

Live snapshot sidecar: `wizards.snap.json` covers `geo`, `molniya`, and `sso`.

### Walker Delta, Star, Custom

Coverage status from [`test_walker_constellation_equations.py`](../../tests/validation/cross_validation/orbits/test_walker_constellation_equations.py):

| Branch | Status |
| --- | --- |
| Walker Delta | verified |
| Walker Star | verified |
| Walker Custom | verified |

Verified items:

- Nested plane/satellite shape.
- `semi_major_axis_m`, `eccentricity`, `inclination_deg`, and `argument_of_periapsis_deg` inherited unchanged from the seed orbit.
- `raan_deg` spacing against standard Walker equations.
- `true_anomaly_deg` against in-plane spacing plus branch phasing equations.

Partial items:

- The seed orbit is a single representative LEO case.

Parameter coverage: `num_planes = 3` and `num_sats_per_plane = 2` shape; `inter_plane_phase_increment = 1` for Delta and Star; `inter_plane_true_anomaly_increment_deg = 30.0` and `raan_increment_deg = 60.0` for Custom.

Comparison path: local derivation from standard Walker Delta, Star, and custom phasing equations. No tuned physical constants are used. Tolerances: `ANGLE_ABS_DEG = 1.0e-9` for wrapped angular fields and `SCALAR_ABS = 1.0e-9` for inherited scalar elements.

Live snapshot sidecar: `wizards.snap.json` covers `walker_delta`, `walker_star`, and `walker_custom`.

## Lambert Transfers

Coverage status from [`test_lambert_lamberthub.py`](../../tests/validation/cross_validation/orbits/test_lambert_lamberthub.py):

| Branch | Status |
| --- | --- |
| `lambert_delta_v` (Cartesian endpoints) | verified |
| `geo_ym_lambert_delta_v` (Keplerian platform/target) | verified with calibrated ASTROX target convention |

Verified fields: both departure and arrival delta-v vectors.

Parameter coverage:

- `time_of_flight_s` and `gravitational_parameter_m3_s2` are verified for `TIME_OF_FLIGHT_S = 3600.0` and `EARTH_MU = 398600441500000.0`.
- Platform/target orbits and Cartesian endpoint states are each partial (one representative GEO-like pair and one Cartesian transfer, respectively).

Comparison path: `lamberthub` `izzo2015` zero-revolution prograde Lambert solver. Tolerances: `STRICT_RESIDUAL_M_S = 1.0e-3` for the verified comparison; `CONVENTION_DIAGNOSTIC_RESIDUAL_M_S = 1.0e-2` guards the GEO-YM target-timing convention.

Known convention for `geo_ym_lambert_delta_v`: ASTROX advances the target orbit's `true_anomaly_deg` linearly by `mean_motion * time_of_flight_s` before solving the Lambert transfer. This is different from propagating the target mean anomaly through Kepler's equation; the diagnostic threshold intentionally fails if the mean-anomaly path starts to match, so that a convention change is not silently absorbed.

Live snapshot sidecar: `conversions.snap.json` covers `lambert_delta_v_cartesian`, `lambert_delta_v_with_platform_mu`, and `lambert_delta_v_server_default_mu`.

## OrbitSystem Frame Work

### `convert_czml_position`

Cross-validation is organized by target central body and target reference frame in [`test_convert_czml_position.py`](../../tests/validation/cross_validation/orbit_system/test_convert_czml_position.py) with helpers in [`tests/validation/cross_validation/orbit_system/_support.py`](../../tests/validation/cross_validation/orbit_system/_support.py). Static samples at `SAMPLE_RADIUS_M = 7_000_000.0` are used for all cases; planetary bodies use `PLANETARY_EPOCH = 2026-06-12T00:00:00Z` and Earth/Moon cases use `EPOCH = 2024-01-01T00:00:00Z`.

| Branch | Status | Comparison path |
| --- | --- | --- |
| Earth `INERTIAL` → `FIXED` | verified | IAU 2000 Earth Rotation Angle (ERA) |
| Earth `FIXED` → `INERTIAL` | verified | IAU 2000 Earth Rotation Angle (ERA) |
| Earth `INERTIAL` → `J2000` | verified | FK5 mean equator/equinox of J2000.0 via ERFA `bp06` frame-bias matrix |
| Earth `INERTIAL` → `ICRF` | verified | ICRS via ERFA `bp06` frame-bias matrix |
| Moon `INERTIAL` | verified | Moon Mean Equator/Equinox J2000 (MMEJ2000) + JPL DE440 translation |
| Moon `INERTIAL` origin | verified | Earth center → Moon center in MMEJ2000 |
| Moon `FIXED` | verified | High-precision NAIF `MOON_ME` frame (DE440) |
| Mars `INERTIAL` | verified | SPICE `MARSIAU` frame |
| Mars `FIXED` | verified for orientation only | SPICE `IAU_MARS` orientation |
| Sun `INERTIAL` | verified | Common J2000 inertial axes |
| Sun `FIXED` | verified | SPICE `IAU_SUN` frame |
| All other `to_central_body` / `target_reference_frame` combinations | unverified | none |

Tolerances from `_support.py`:

- Earth radius check: `EARTH_RADIUS_ABS_M = 1.0`
- Earth `FIXED` ↔ `INERTIAL` radius check: `EARTH_FIXED_TO_INERTIAL_RADIUS_ABS_M = 1.0`
- Earth longitude check: `EARTH_LONGITUDE_ABS_DEG = 0.001`
- Earth `J2000`: `EARTH_J2000_ABS_M = 5.0`
- Earth `ICRF`: `EARTH_ICRF_ABS_M = 5.0`
- Moon `INERTIAL`: `MOON_INERTIAL_ABS_M = 200.0`
- Moon `FIXED`: `MOON_FIXED_ABS_M = 1000.0`, `MOON_FIXED_ANGLE_ARCSEC = 1.0`
- Mars `INERTIAL`: `MARS_INERTIAL_ABS_M = 200_000.0`, `MARS_INERTIAL_ANGLE_ARCSEC = 0.2`
- Mars `FIXED`: `MARS_FIXED_ANGLE_ARCSEC = 10.0` (angular only; absolute residual is dominated by the Mars-barycenter approximation)
- Sun `INERTIAL`: `SUN_INERTIAL_ABS_M = 500.0`
- Sun `FIXED`: `SUN_FIXED_ABS_M = 1000.0`, `SUN_FIXED_ANGLE_ARCSEC = 0.002`

Known residuals and convention notes:

- Earth `INERTIAL` matches a GCRS-style inertial frame.
- Mars predictions use the Mars barycenter (NAIF ID 4) because `de440.bsp` does not provide Mars body-centre state relative to Earth directly. The barycenter-to-centre offset is much smaller than the observed residuals.
- Mars `FIXED` is calibrated on orientation only because the barycenter approximation produces a large absolute offset at planetary distance.

Live snapshot sidecar: `orbit_system.snap.json` covers an Earth `INERTIAL` → `FIXED` case.

### `earth_moon_libration`

Coverage status from [`test_earth_moon_libration.py`](../../tests/validation/cross_validation/orbit_system/test_earth_moon_libration.py):

| Field | Status |
| --- | --- |
| `cartesian` samples | verified |
| `unit_quaternion` | unresolved |
| `cartesian_translation` | unresolved (not populated in exercised responses) |

Comparison path for `cartesian`: the input state expressed in a Moon-centered libration frame whose x-axis points Earth-to-Moon and whose z-axis is aligned with the Earth-Moon orbital angular momentum, derived from JPL DE440 via Skyfield. Tolerance: `LIBRATION_POSITION_ABS_M = 1.0`.

Unresolved for `unit_quaternion`: the field does not match any of the standard quaternion conventions tested (scalar-first/last, with/without conjugation, for either libration-to-inertial or inertial-to-libration). The best residual is approximately `24.56°`, well above `QUATERNION_MATCH_DEG = 1.0` and above `QUATERNION_CALIBRATION_MIN_DEG = 1.0`. Treat this field as an unvalidated auxiliary orientation.

Unresolved for `cartesian_translation`: live probes across epochs (`2024-01-01T00:00:00Z` and `2024-06-01T00:00:00Z`), reference frames (`INERTIAL`, `FIXED`, `J2000`, `ICRF`), central bodies (`Earth`, `Moon`), sample counts (`8`), interpolation degrees (`1`, `7`), and velocity flags (`False`, `True`) did not populate `cartesian_translation` in the response. The field absence is recorded, but its intended semantics remain unresolved.

Live snapshot sidecar: `orbit_system.snap.json` covers `earth_moon_libration`.
