# Access Validation Evidence

This page records the cross-validation status of the `astrox.access` surface and the `astrox.components` evidence that is exercised through access calls. It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/access/README.md`](../manual/access/README.md) and [`docs/manual/components/README.md`](../manual/components/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) are taken directly from the coverage checklists in the cross-validation scripts listed under each family.

| Family | Cross-validation script | Live snapshot sidecar / runner |
| --- | --- | --- |
| Fixed site ↔ SGP4 | [`tests/validation/cross_validation/access/test_compute_ground_sgp4_skyfield.py`](../../tests/validation/cross_validation/access/test_compute_ground_sgp4_skyfield.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| Site ↔ J2 | [`tests/validation/cross_validation/access/test_compute_site_j2_geometry.py`](../../tests/validation/cross_validation/access/test_compute_site_j2_geometry.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| Site ↔ two_body | [`tests/validation/cross_validation/access/test_compute_site_two_body_geometry.py`](../../tests/validation/cross_validation/access/test_compute_site_two_body_geometry.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| Site ↔ HPOP | [`tests/validation/cross_validation/access/test_compute_site_hpop_geometry.py`](../../tests/validation/cross_validation/access/test_compute_site_hpop_geometry.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| J2 ↔ two_body | [`tests/validation/cross_validation/access/test_compute_j2_two_body_geometry.py`](../../tests/validation/cross_validation/access/test_compute_j2_two_body_geometry.py) | [`tests/validation/live_snapshot/access/test_compute_model_pairs.py`](../../tests/validation/live_snapshot/access/test_compute_model_pairs.py) |
| SGP4 ↔ J2 | [`tests/validation/cross_validation/access/test_compute_sgp4_j2_geometry.py`](../../tests/validation/cross_validation/access/test_compute_sgp4_j2_geometry.py) | [`tests/validation/live_snapshot/access/test_compute_model_pairs.py`](../../tests/validation/live_snapshot/access/test_compute_model_pairs.py) |
| Constraints | [`tests/validation/cross_validation/access/test_compute_constraints_skyfield.py`](../../tests/validation/cross_validation/access/test_compute_constraints_skyfield.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| Sun/Moon exclusion | [`tests/validation/cross_validation/access/test_compute_exclusion_constraints_invariants.py`](../../tests/validation/cross_validation/access/test_compute_exclusion_constraints_invariants.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| Chain topology | [`tests/validation/cross_validation/access/test_chain_sgp4_skyfield.py`](../../tests/validation/cross_validation/access/test_chain_sgp4_skyfield.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json), [`tests/validation/live_snapshot/access/test_chain_topology.py`](../../tests/validation/live_snapshot/access/test_chain_topology.py) |
| Orbital axes | [`tests/validation/cross_validation/access/test_axes_orientation_geometry.py`](../../tests/validation/cross_validation/access/test_axes_orientation_geometry.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| Fixed/frozen/composite/CZML axes | [`tests/validation/cross_validation/access/test_composite_czml_axes_geometry.py`](../../tests/validation/cross_validation/access/test_composite_czml_axes_geometry.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| VGT orientation | [`tests/validation/cross_validation/access/test_vgt_orientation_resolution.py`](../../tests/validation/cross_validation/access/test_vgt_orientation_resolution.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| Sensor pointing / FOV | [`tests/validation/cross_validation/access/test_sensor_pointing_geometry.py`](../../tests/validation/cross_validation/access/test_sensor_pointing_geometry.py) | [`tests/validation/live_snapshot/access/access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json) |
| Compute options | none (cross-validation above covers the calibrated option branches) | [`tests/validation/live_snapshot/access/test_compute_options.py`](../../tests/validation/live_snapshot/access/test_compute_options.py) |
| Model-pair callability | none | [`tests/validation/live_snapshot/access/test_compute_model_pairs.py`](../../tests/validation/live_snapshot/access/test_compute_model_pairs.py) |

Helpers: [`_aer.py`](../../tests/validation/cross_validation/access/_aer.py), [`_cases.py`](../../tests/validation/cross_validation/access/_cases.py), [`_constraints.py`](../../tests/validation/cross_validation/access/_constraints.py), [`_exclusion.py`](../../tests/validation/cross_validation/access/_exclusion.py), [`_geometry.py`](../../tests/validation/cross_validation/access/_geometry.py), [`_mixed_model.py`](../../tests/validation/cross_validation/access/_mixed_model.py), [`_orientation.py`](../../tests/validation/cross_validation/access/_orientation.py).

## Direct Access

### Fixed site ↔ SGP4

Coverage status from [`test_compute_ground_sgp4_skyfield.py`](../../tests/validation/cross_validation/access/test_compute_ground_sgp4_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| ground site → SGP4 satellite | verified for intervals, AER convention, and light-time shift |
| SGP4 satellite → ground site | verified for interval/range symmetry and satellite-origin AER convention |
| ground site → ground site | verified for a blocked WGS84 segment case |
| `Passes.AccessStart` / `AccessStop` | verified |
| `AllDatas.Azimuth` / `Elevation` / `Range` | partial (ground-origin and satellite-origin conventions calibrated; strict dense residual unresolved) |
| no-access `Passes` | verified |
| `compute_aer=True` | verified for AER comparisons; false/omitted field-shape behavior lives in live snapshot tests |
| `step_s` | partial (60 s dense AER sample compared) |
| `use_light_time_delay` | verified for ground → SGP4 range-over-c shift |

Comparison path: Skyfield SGP4 topocentric geometry, WGS84 segment obstruction, range-over-c light-time derivation, and a geodetic local satellite frame for the reverse role. Constants: TLE_A, WGS84 ellipsoid via Skyfield, `SPEED_OF_LIGHT_M_S = 299792458.0`. Tolerances from [`_cases.py`](../../tests/validation/cross_validation/access/_cases.py): `INTERVAL_ABS_S = 0.25`, `CHAIN_INTERVAL_ABS_S = 5.0e-3`, `AER_CONVENTION_AZIMUTH_ABS_DEG = 5.0e-4`, `AER_CONVENTION_ELEVATION_ABS_DEG = 2.0e-4`, `AER_DENSE_AZIMUTH_ABS_DEG = 3.0e-3`, `AER_DENSE_ELEVATION_ABS_DEG = 1.5e-3`, `AER_CONVENTION_RANGE_ABS_M = 25.0`, `SATELLITE_LOCAL_AER_ABS_DEG = 5.0e-3`, `LIGHT_TIME_SHIFT_ABS_S = 3.0e-3`, `LIGHT_TIME_AER_ABS_DEG = 1.0e-6`, `LIGHT_TIME_RANGE_ABS_M = 1.0e-3`, `RANGE_SYMMETRY_ABS_M = 1.0e-6`.

Known residuals and convention notes:

- Ground-origin AER follows the Skyfield topocentric convention: azimuth measured from north toward east, elevation from the local horizontal plane positive toward zenith.
- A strict dense-row residual remains unresolved after same-epoch, range-over-c light-time, manual ITRS topocentric, ellipsoid-horizon, and simple site/time-offset diagnostics; the case is kept as a strict calibration xfail with `AER_STRICT_ABS_DEG = 1.0e-4`.
- Satellite-origin AER for SGP4 → ground matches an Earth-fixed local east/north/up frame at the satellite WGS84 geodetic subpoint; orbital RSW/TNW/VVLH-style frames were rejected by targeted diagnostics.
- `use_light_time_delay=True` shifts interval boundaries by approximately `-range / c` at millisecond scale and produces measurable AER sample shifts.

Live snapshot sidecar: `access.snap.json` covers `access_compute_site_sgp4`, `access_compute_site_sgp4_elevation_range_constraints`, `access_compute_site_sgp4_az_el_mask_constraint`, and `access_compute_site_sgp4_az_el_mask_constraint_with_max_range`.

### Site ↔ J2

Coverage status from [`test_compute_site_j2_geometry.py`](../../tests/validation/cross_validation/access/test_compute_site_j2_geometry.py):

| Branch / Field | Status |
| --- | --- |
| ground site → J2 satellite | partial |
| `Passes.AccessStart` / `AccessStop` | verified against local J2 state plus WGS84 obstruction |
| `AllDatas.Azimuth` / `Elevation` / `Range` | partial (checked for first returned pass when access exists) |
| `from_entity` site coordinates | verified for the shared Hawaii site |
| `to_entity` J2 orbit/constants | verified for the calibrated ASTROX-like J2 secular helper |
| `compute_aer` / `step_s` | partial for `compute_aer=True` and 300 s cadence |

Comparison path: local calibrated J2 secular state and WGS84 segment-obstruction/topocentric geometry. Constants: shared Hawaii site coordinates, `EARTH_MU = 398600441500000.0`, `EARTH_RADIUS_M = 6378136.3`, `ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE = 0.000484166956667088`. Tolerances: `INTERVAL_ABS_S` and mixed-model AER tolerances (`MIXED_MODEL_AZIMUTH_ABS_DEG = 2.0e-2`, `MIXED_MODEL_ELEVATION_ABS_DEG = 2.0e-2`, `AER_CONVENTION_RANGE_ABS_M = 25.0`).

### Site ↔ two_body

Coverage status from [`test_compute_site_two_body_geometry.py`](../../tests/validation/cross_validation/access/test_compute_site_two_body_geometry.py):

| Branch / Field | Status |
| --- | --- |
| ground site → two_body satellite | partial |
| `Passes.AccessStart` / `AccessStop` | verified against local Keplerian two-body state plus WGS84 obstruction |
| `AllDatas.Azimuth` / `Elevation` / `Range` | partial (checked for first returned pass when access exists) |
| `to_entity` two-body orbit and Earth mu | verified for the shared access orbit |
| `compute_aer` / `step_s` | partial for `compute_aer=True` and 300 s cadence |

Comparison path: local Keplerian two-body propagation and WGS84 segment-obstruction/topocentric geometry. Constants: shared access orbit, `EARTH_MU`. Tolerances: `INTERVAL_ABS_S` and mixed-model AER tolerances.

### Site ↔ HPOP

Coverage status from [`test_compute_site_hpop_geometry.py`](../../tests/validation/cross_validation/access/test_compute_site_hpop_geometry.py):

| Branch / Field | Status |
| --- | --- |
| ground site → HPOP satellite with two-body HPOP gravity config | partial |
| `Passes.AccessStart` / `AccessStop` | verified against local two-body state plus WGS84 obstruction |
| `AllDatas.Azimuth` / `Elevation` / `Range` | partial (checked for first returned pass when access exists) |
| `to_entity` HPOP two-body orbit/config | partial (validated against the matching local Keplerian state) |
| `compute_aer` / `step_s` | partial for `compute_aer=True` and 300 s cadence |

Comparison path: local Keplerian two-body propagation and WGS84 segment-obstruction/topocentric geometry; the HPOP fixture uses `propagator.hpop_two_body_gravity()`. Constants: shared access orbit, `EARTH_MU`. Tolerances: `INTERVAL_ABS_S` and mixed-model AER tolerances.

### J2 ↔ two_body

Coverage status from [`test_compute_j2_two_body_geometry.py`](../../tests/validation/cross_validation/access/test_compute_j2_two_body_geometry.py):

| Branch / Field | Status |
| --- | --- |
| J2 satellite → two_body satellite | partial |
| `Passes.AccessStart` / `AccessStop` | verified against local J2/two-body states plus WGS84 obstruction |
| `AllDatas` | partial (satellite-origin AER convention not asserted in this script) |
| `from_entity` J2 orbit/constants | verified for the calibrated ASTROX-like J2 secular helper |
| `to_entity` two-body orbit and Earth mu | verified for the shared access orbit |
| `compute_aer` / `step_s` | partial for `compute_aer=True` and 300 s cadence |

Comparison path: local calibrated J2 secular state, local two-body propagation, and WGS84 segment obstruction. Constants: `EARTH_MU`, `EARTH_RADIUS_M`, `ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE`. Tolerance: `INTERVAL_ABS_S`.

### SGP4 ↔ J2

Coverage status from [`test_compute_sgp4_j2_geometry.py`](../../tests/validation/cross_validation/access/test_compute_sgp4_j2_geometry.py):

| Branch / Field | Status |
| --- | --- |
| SGP4 satellite → J2 satellite | verified for the no-access sample window |
| `Passes.AccessStart` / `AccessStop` | verified (empty interval set matches independent segment-obstruction oracle) |
| `AllDatas` | partial (checked to exist if ASTROX ever returns a pass, but the covered case has no access) |
| `from_entity` SGP4 TLEs | verified for TLE_A |
| `to_entity` J2 Keplerian orbit and J2 constants | verified for the calibrated ASTROX-like secular J2 helper |
| `compute_aer` | partial (requested; no AER rows exist because the verified case has no pass) |

Comparison path: Skyfield SGP4 state plus local calibrated J2 secular state, both tested with WGS84 segment obstruction. Constants: TLE_A, `EARTH_MU`, `EARTH_RADIUS_M`, `ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE`. Tolerance: `INTERVAL_ABS_S`.

## AER Conventions and Light-Time Effects

The AER evidence is split by origin frame:

| Origin | Status | Comparison path |
| --- | --- | --- |
| Ground-origin AER (fixed site to satellite) | verified for representative SGP4 cases; partial for dense interior rows; strict dense residual unresolved | Skyfield topocentric azimuth/elevation/range |
| Satellite-origin AER (satellite to fixed site) | verified for representative SGP4 cases | Earth-fixed local east/north/up frame at the satellite WGS84 geodetic subpoint |
| Light-time-delayed AER boundary shift | verified for ground → SGP4 | `range / c` estimate at millisecond scale |

Ground-origin AER uses the standard topocentric convention (north-zero, positive east, elevation above the local horizontal). The unresolved strict dense-row residual is kept as a calibration xfail in [`test_compute_ground_sgp4_skyfield.py`](../../tests/validation/cross_validation/access/test_compute_ground_sgp4_skyfield.py); it survives same-epoch Skyfield comparison, light-time shift, manual ITRS construction, ellipsoid-horizon checks, and small site/time offsets.

Satellite-origin AER does not match an orbital LVLH/VVLH/RSW/TNW body frame for the covered SGP4-to-ground case. It matches a geodetic local east/north/up frame erected at the satellite subpoint, with the vector pointing from the satellite to the target site.

`use_light_time_delay=True` for ground → SGP4 shifts access start and stop by approximately `-range / c` and produces measurable AER sample differences; the option is wired and physically plausible for the covered case, but not every model pair has been calibrated.

## Constraints Calibration

### Elevation, Range, and AzElMask

Coverage status from [`test_compute_constraints_skyfield.py`](../../tests/validation/cross_validation/access/test_compute_constraints_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| `ElevationAngle` on `from_entity` (ground site) | verified |
| `ElevationAngle` on `to_entity` (satellite) | verified |
| `ElevationAngle.maximum_enabled` True/False | verified |
| `Range` on `from_entity` (ground site) | verified |
| `Range` on `to_entity` (satellite) | verified |
| `Range` minimum_only/maximum_only/minimum_and_maximum | verified |
| `AzElMask` on `from_entity` (ground site) | verified |
| `AzElMask` on `to_entity` (satellite) | verified site-only (server rejects) |
| Combined elevation + range constraints | verified |
| Both participants constrained | verified for elevation minima |
| ground-to-SGP4 access role | verified for constraints on `from_entity` |
| SGP4-to-ground access role | verified for constraints on `to_entity` |
| `compute_aer=True` output with elevation constraint | verified |
| `use_light_time_delay=True` with range constraint | verified |
| Sharp boundary cases | verified |
| Contradictory/no-access cases | verified |
| Server error behavior for `min > max` when maximum enabled | verified |
| `Passes.AccessStart` / `AccessStop` under elevation/range/AzElMask constraints | verified |
| `AllDatas.Azimuth` / `Elevation` / `Range` with elevation constraint | verified |

Comparison path: Skyfield SGP4 topocentric geometry. Constants: TLE_A, WGS84 ellipsoid via Skyfield. Tolerances: `CONSTRAINT_TOLERANCE_S = 0.25` s, `AER_DENSE_AZIMUTH_ABS_DEG = 3.0e-3` deg, `AER_DENSE_ELEVATION_ABS_DEG = 1.5e-3` deg, `AER_CONVENTION_RANGE_ABS_M = 25.0` m.

Known findings:

- Elevation and range constraints are evaluated in the constrained participant's local topocentric frame. For a satellite participant this is the same Earth-fixed geodetic local-frame convention used for satellite-origin AER rows, not a spacecraft body frame.
- `Range.MaximumValue` and `ElevationAngle.MaximumValue` are active only when `maximum_enabled=True` is supplied.
- `Range.MinimumValue` is active whenever it is supplied, even without a maximum.
- `AzElMask.AzElMaskData` is a flat sequence of alternating azimuth and elevation samples in radians, interpolated piecewise-linearly in azimuth using the north-zero/east-positive convention; the first sample is duplicated across the 0/360 boundary.
- `AzElMask.MaxRange` is forwarded by the SDK but not enforced by ASTROX.
- Multiple constraints on the same participant produce the intersection of predicates; elevation minima on both participants also produce the intersection.
- `use_light_time_delay=True` shifts interval boundaries, but the range constraint threshold is still evaluated on geometric range.

### Sun and Moon Exclusion Angles

Coverage status from [`test_compute_exclusion_constraints_invariants.py`](../../tests/validation/cross_validation/access/test_compute_exclusion_constraints_invariants.py):

| Branch / Field | Status |
| --- | --- |
| `SunExclusionAngle` on fixed site `from_entity` | verified |
| `MoonExclusionAngle` on fixed site `from_entity` | verified |
| `SunExclusionAngle` on fixed site `to_entity` | verified |
| `MoonExclusionAngle` on fixed site `to_entity` | verified |
| `SunExclusionAngle` on SGP4 `from_entity` | verified |
| `MoonExclusionAngle` on SGP4 `from_entity` | verified |
| `SunExclusionAngle` on SGP4 `to_entity` | verified |
| `MoonExclusionAngle` on SGP4 `to_entity` | verified |
| `ChainCompute` direct fixed-site and SGP4 Sun/Moon exclusion routes | verified against `AccessCompute` and Skyfield body-separation geometry |
| `Passes.AccessStart` / `AccessStop` under fixed-site and SGP4 exclusion constraints | verified |
| `CompleteChainAccess.Start` / `Stop` under direct-chain exclusion constraints | verified |

Comparison path: Skyfield SGP4, DE421 Sun/Moon ephemerides, apparent topocentric body altitude gate, astrometric topocentric/satellite-observer body-separation angle, satellite body Earth-occultation, and WGS84 segment-obstruction visibility. Constants: TLE_A, a no-drag SGP4 TLE for the `to_entity` SGP4 fixture, Hawaii/Madrid WGS84 site coordinates. Tolerance: `EXCLUSION_INTERVAL_ABS_S = 0.35` s.

Known findings:

- For a fixed-site observer, the constraint is satisfied when the apparent Sun/Moon is below the site's local horizon, or when the target line of sight is separated from the topocentric astrometric Sun/Moon vector by at least `MinimumValue` degrees.
- For a satellite observer, the constraint is satisfied when Earth occults the Sun/Moon from the satellite, or when the target line of sight is separated from the satellite-observer astrometric Sun/Moon vector by at least `MinimumValue` degrees.
- Larger thresholds split or narrow intervals; validation compares the full derived interval set rather than pass count.
- Drag-bearing TLE fixtures can surface live SGP4 propagation errors before intervals are returned; the stable no-drag fixture is used as semantic evidence.

## Chain Behavior

Coverage status from [`test_chain_sgp4_skyfield.py`](../../tests/validation/cross_validation/access/test_chain_sgp4_skyfield.py) and the live snapshot runner [`test_chain_topology.py`](../../tests/validation/live_snapshot/access/test_chain_topology.py):

| Branch / Field | Status |
| --- | --- |
| Direct site → SGP4 chain with `Connections` omitted | verified |
| Explicit site → SGP4 → SGP4 chain with two satellite participants | verified against independent Skyfield/WGS84 link-visibility intersection |
| Serial site → SGP4 relay → site chain with explicit connections | unresolved (relay-to-ground interval residual against Skyfield/WGS84 oracle for later passes) |
| Explicit site → SGP4 → SGP4 → site full two-relay route | unresolved server no-path calibration |
| `CompleteChainAccess.Start` / `Stop` | partial (direct and two-satellite routes verified; serial relay and full two-relay unresolved) |
| `ComputedStrands` | partial (checked for direct/two-satellite/serial route topology) |
| `IndividualStrandAccess` and `IndividualObjectAccess` | partial (two-satellite route verified; serial route consistency remains behind calibration xfail) |
| `use_light_time_delay` in two-satellite chain | partial (delay matches range-over-c on the limiting ground-to-satellite link) |
| Empty `connections=[]` matches direct chain semantics | verified (live snapshot) |
| `AnyOf` entity group complete access is union of member strands | verified (live snapshot) |
| `AtLeastN` entity group complete access is intersection of member strands | verified for `to_number=2` (live snapshot) |
| Single explicit route tolerates unused participants | verified (live snapshot) |
| Explicit connections are directional | verified (live snapshot) |
| Serial chain light-time delay matches direct-link composition | verified (live snapshot) |
| Multiple explicit relay routes in one request | unresolved (server no-path despite each route working separately) |
| Duplicate explicit link | unresolved (server no-path despite unique route working) |
| Extra branch connection | unresolved (server no-path despite original route still present) |
| EntityGroup used as chain start object | unresolved (server index error) |
| `min_uses` / `max_uses` cardinality semantics | unresolved (`MaxUses=0` and inconsistent `MinUses/MaxUses` return unchanged intervals) |

Comparison path: Skyfield SGP4 states plus WGS84 segment-obstruction line-of-sight oracle; for serial routes the expected complete access is the intersection of per-link oracle intervals. Tolerances: `INTERVAL_ABS_S` for external oracle intervals, `CHAIN_INTERVAL_ABS_S` for exact ASTROX chain object consistency.

Known findings:

- Direct chains match `access.compute(...)` and the independent line-of-sight oracle.
- Two-satellite chains match the intersection of direct-link intervals and the independent Skyfield/WGS84 oracle.
- Serial ground → relay → ground chains show an unresolved relay-to-ground interval residual of about 15–20 s for later passes against the undirected Skyfield/WGS84 oracle.
- The full GroundA → RelayA → RelayB → GroundB route returns a server no-path error even though all direct links, both two-link subroutes, and the direct-link intersection are non-empty.
- `connections=[]` is preserved as an empty list and behaves like omitted `Connections` for the tested two-participant case.
- `AnyOf` and `AtLeastN` group restrictions compose as union and intersection of member strands, respectively, for the calibrated cases.
- `min_uses` / `max_uses` are forwarded, but current validation does not establish useful cardinality semantics.

## Orientation and Axes Evidence

### Orbital Axes (VVLH, LVLH, VNC)

Coverage status from [`test_axes_orientation_geometry.py`](../../tests/validation/cross_validation/access/test_axes_orientation_geometry.py):

| Branch | Status |
| --- | --- |
| VVLH, VVLH(Earth), VVLH(CBF) | verified against local front/right/down frame for nadir, along-track, and cross-track targets |
| VNC, VNC(Earth), VNC(CBF) | verified against local velocity/normal/co-normal frame for along-track, radial-out, and cross-track targets |
| LVLH, LVLH(Earth), LVLH(CBF) | verified against local radial/along-track/angular-momentum frame for radial-out, along-track, and cross-track targets |
| VVLH/LVLH/VNC Moon and Mars variants | unresolved after live central-body target probes and Skyfield body-vector candidate comparison |
| VVLH/LVLH/VNC Sun variants | unresolved (live central-body target fails before semantic output; DE421-sampled CZML Sun target probes do not calibrate all axes) |
| `relative_to` generic, Earth, CBF | verified where live variants match the corresponding generic branch |
| `relative_to` Moon/Mars/Sun | unresolved |
| sensor orientation with quaternion identity, AzEl(0,0), AzEl(90,0), AzEl(0,90) | verified |

Comparison path: independent two-body state sampling, local orbital-frame derivations, WGS84 obstruction, and conic FOV predicates. Constants: controlled two-body orbit in [`_orientation.py`](../../tests/validation/cross_validation/access/_orientation.py), `EARTH_MU`. Tolerance: `ORIENTATION_INTERVAL_ABS_S = 0.5` s.

Calibrated conventions:

- `VVLH`: `+Z` nadir, `+X` along-track velocity projected into the local horizontal plane, `+Y` completes the right-side frame.
- `LVLH`: `+X` radial outward, `+Z` orbit angular momentum, `+Y = Z × X`.
- `VNC`: `+X` inertial velocity, `+Y` orbit angular momentum, `+Z` completes the right-handed triad.

Moon/Mars/Sun-relative axes remain strict calibration xfails; Skyfield DE421 body-vector candidates produced residuals or empty-only agreement.

### Fixed, Frozen, Composite, and CZML Axes

Coverage status from [`test_composite_czml_axes_geometry.py`](../../tests/validation/cross_validation/access/test_composite_czml_axes_geometry.py):

| Branch | Status |
| --- | --- |
| Fixed axes relative to built-in VVLH, LVLH, VNC | verified with Euler and quaternion rotations |
| Fixed axes relative to ICRF/J2000 and inertial/fixed name variants | unresolved after inertial and Earth-fixed local frame candidates plus live reference-name probes |
| FixedAtEpoch axes from VVLH/LVLH into ICRF at start epoch and +60 s | verified against frozen-at-epoch local frame derivations |
| Composite axes with identity/off-nadir two-interval and identity/off-nadir/identity three-interval layouts | verified for multiple switch points |
| CZML sampled-identity quaternions over short spans | verified against inertial-frame oracle for 30 s and 60 s spans, with and without `CentralBody`, and with LINEAR/LAGRANGE/HERMITE interpolation |
| CZML constant, long-span sampled, and non-identity sampled quaternions | unresolved after server failures and unexplained interval/component/sign residuals |

Comparison path: independent VVLH frame, Euler rotation, frozen source/reference transform, and piecewise composite interval derivation. Constants: controlled two-body orbit in [`_orientation.py`](../../tests/validation/cross_validation/access/_orientation.py), `COMPOSITE_SWITCH_S = 20.0` s. Tolerance: `ORIENTATION_INTERVAL_ABS_S = 0.5` s.

Known findings:

- Fixed axes are calibrated only when referencing the built-in VVLH/LVLH/VNC names.
- `fixed_at_epoch_axes(...)` correctly freezes the source frame into the reference frame at the requested epoch.
- `composite_axes(...)` switches at the interval boundaries as expected for the tested layouts.
- CZML axes with short-span sampled identity quaternions behave like a fixed inertial frame for the tested span; constant arrays, long spans, and non-identity sampled quaternions remain unresolved.

### VGT Orientation and Name Resolution

Coverage status from [`test_vgt_orientation_resolution.py`](../../tests/validation/cross_validation/access/test_vgt_orientation_resolution.py):

| Branch / Field | Status |
| --- | --- |
| `vgt_fixed_vector` with built-in VVLH reference axes | verified |
| `aligned_and_constrained_axes` using built-in VVLH fixed vectors | verified against local TRIAD-style alignment for orthogonal, permuted-axis, and non-orthogonal-reference cases |
| `Vgt.Axes`, `Vgt.Vectors`, `Vgt.Angles`, `Vgt.Planes`, and empty `Vgt.Points`/`Vgt.Systems` | verified as pass-through containers that do not alter calibrated VVLH sensor access |
| custom fixed-axes name resolution inside `aligned_and_constrained_axes` | verified for no-space object and string reference styles |
| custom fixed-axes names containing spaces | unresolved (object and string reference styles both report the named axes cannot be found) |
| non-empty `Vgt.Points` and `Vgt.Systems` provider collections | unresolved after SDK-callable and raw-wire probes return HTTP 500 before semantic output |

Comparison path: local TRIAD-style axes construction plus independent VVLH/FOV interval oracle. Tolerance: `ORIENTATION_INTERVAL_ABS_S = 0.5` s.

### Sensor Pointing and FOV

Coverage status from [`test_sensor_pointing_geometry.py`](../../tests/validation/cross_validation/access/test_sensor_pointing_geometry.py):

| Branch | Status |
| --- | --- |
| `fixed_sensor_pointing` quaternion identity with conic FOV | verified |
| `fixed_sensor_pointing` quaternion off-nadir and single-axis rotations with conic FOV | verified |
| `fixed_sensor_pointing` Euler 321/123/213 off-nadir equivalents to quaternion | verified |
| `fixed_sensor_pointing` AzEl along-track, cross-track, positive-elevation, and negative-elevation cases with conic FOV | verified |
| `fixed_sensor_pointing` AzEl off-target no-access case | verified |
| rectangular sensor FOV with identity/off-nadir rotations and two width pairs | verified |
| no-sensor line-of-sight positive and WGS84 blocked target controls | verified |
| `Passes.AccessStart` / `AccessStop` | verified |
| `Passes.AccessBeginData` / `AccessEndData` AER | partial (AER convention covered in access AER tests) |

Comparison path: independent two-body geometry, VVLH frame derivation, WGS84 obstruction, and local conic/rectangular FOV predicates. Constants: controlled two-body orbit in [`_orientation.py`](../../tests/validation/cross_validation/access/_orientation.py), `EARTH_MU`, WGS84 from Skyfield. Tolerance: `ORIENTATION_INTERVAL_ABS_S = 0.5` s.

Known findings:

- Quaternion and Euler sensor rotations act as active rotations of the local `+Z` boresight.
- Az/El sensor pointing is calibrated as a direct boresight vector in the parent axes (azimuth from `+X` toward `+Y`, elevation toward `+Z`); it is not equivalent to applying a quaternion or Euler rotation to `+Z`.
- Conic `outer_half_angle_deg` is the half-angle around the boresight.
- Rectangular `x_half_angle_deg` and `y_half_angle_deg` are independent X/Z and Y/Z angular limits in the sensor camera axes.

## Live Snapshot Coverage

The live snapshot layer proves maintained response shape, not semantic correctness. Coverage from [`tests/validation/live_snapshot/access/`](../../tests/validation/live_snapshot/access/):

- [`test_access.py`](../../tests/validation/live_snapshot/access/test_access.py) / [`access.snap.json`](../../tests/validation/live_snapshot/access/access.snap.json): direct site-to-SGP4 access with AER; elevation/range constraints; AzElMask constraint with and without `max_range_km`; site-to-central-body (Moon); site-to-HPOP; site-to-composite CZML positions; site-to-simple-ascent; site-to-ballistic; sensor-pointing two-body-to-site; custom fixed axes relative to VVLH; VGT container with named VVLH axes; direct site-to-SGP4 chain; chain to `AnyOf` entity group; explicit multi-hop chain through a relay.
- [`test_compute_options.py`](../../tests/validation/live_snapshot/access/test_compute_options.py): `compute_aer=False` matches omitted and `compute_aer=True` preserves intervals; `step_s` controls AER sample cadence but not interval boundaries; no-access with `compute_aer=True` returns empty `Passes`.
- [`test_compute_model_pairs.py`](../../tests/validation/live_snapshot/access/test_compute_model_pairs.py): HPOP and two-body site-companion branches are callable; distinct-orbit and near-coincident HPOP/two-body satellite pairs are callable and symmetric; coincident initial orbits produce an isolated server worker error (unresolved).
- [`test_chain_topology.py`](../../tests/validation/live_snapshot/access/test_chain_topology.py): empty `connections=[]` matches direct chain semantics; `AnyOf` union and `AtLeastN` intersection; single explicit route tolerates unused participants; explicit connections are directional; serial chain light-time delay matches direct-link composition. Unresolved topology cases include multiple explicit relay routes, duplicate links, extra branch connections, entity group as start object, and unenforced `min_uses`/`max_uses` cardinality.

## Dropped Material

The following narratives from the former `docs/sdk/access.md` and `docs/sdk/components.md` (removed when the documentation was reorganized into Manual/How-To/Validation layers) were intentionally omitted because this page is an evidence register, not a usage guide or API reference: function signatures and argument tables for `access.compute`, `access.chain`, `access.connection`, and every `components` constructor; example code blocks; installation and import guidance; entity-group and connection cardinality usage explanations; and recommendations for which constructor to use. Convention statements that are already covered in [`docs/manual/access/README.md`](../manual/access/README.md) and [`docs/manual/components/README.md`](../manual/components/README.md) are not repeated here.
