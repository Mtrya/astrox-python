# Access Cross-Validation Scope

This folder calibrates ASTROX access behavior against independent geometry, external propagation helpers, and cross-endpoint invariants. It is not a snapshot layer; live snapshot files live under `tests/validation/live_snapshot/access/` and only prove maintained live response shape.

## Current Majority Coverage

The current non-orientation access calibration covers these behavior axes:

| Axis | Status | Evidence |
| --- | --- | --- |
| Fixed ground to SGP4 intervals | covered | Skyfield SGP4 plus WGS84 segment-obstruction oracle |
| Ground-origin SGP4 AER convention | covered with precision caveat | Skyfield topocentric azimuth/elevation/range comparison for coarse boundary rows and dense `OutStep=60s` interior rows |
| Strict ground-origin SGP4 AER precision | calibration xfail | same-epoch, light-time-shifted, manual ITRS topocentric, horizon, and simple site/time offset diagnostics still leave an arcsecond-scale dense-row residual |
| SGP4 to ground interval/range role reversal | covered | symmetry against ground to SGP4 live output |
| Satellite-origin SGP4 AER convention | covered for fixed ground target | angles match an Earth-fixed local east/north/up frame at the satellite WGS84 geodetic subpoint; orbital RSW/TNW/VVLH-style frames were rejected by targeted diagnostics |
| Fixed ground to fixed ground obstruction | covered | blocked WGS84 segment case returns no passes |
| SGP4 to J2 no-access branch | covered for the chosen case | Skyfield SGP4 plus calibrated ASTROX-like secular J2 sampled segment-obstruction oracle |
| Site-paired HPOP/two-body branches | covered for callability | live companion probes verify site to model and model to site calls return successfully |
| Distinct-orbit HPOP/two-body satellite pair | partial | live role-reversal interval symmetry is checked; no independent timing oracle is claimed |
| Near-coincident HPOP/two-body satellite pair | partial | a tiny true-anomaly offset is callable and role-reversal symmetric; no independent timing oracle is claimed |
| Coincident satellite orbit pairs | calibration xfail | exact same initial orbit produces a server worker error for same-model and mixed HPOP/two-body satellite pairs |
| Direct chain site to SGP4 | covered | chain output matches direct compute and the independent Skyfield/WGS84 line-of-sight oracle |
| Explicit ground to relay to ground chain | covered | each link matches the independent Skyfield/WGS84 oracle, and complete access matches the intersection of those oracle intervals with strand/object access consistency checks |
| Light-time delay for ground to SGP4 | covered for the chosen case | interval boundary shifts match range-over-c at millisecond scale and AER samples move measurably |

Endpoint option behavior and chain topology edge cases that compare ASTROX only with ASTROX now live under `tests/validation/live_snapshot/access/`.

This is a majority calibration of the current access surface before orientation-sensitive entity behavior: direct role/model branches, Skyfield-backed chain compositions, ground-origin AER, light-time, and known model-pair edge cases are covered or explicitly marked as calibration xfails.

## Deliberate Non-Claims

These tests do not prove full ASTROX access correctness. They do not yet calibrate:

| Axis | Current status |
| --- | --- |
| Central-body access semantics | live snapshot only |
| CZML, simple-ascent, and ballistic access semantics | live snapshot only |
| Broad HPOP force-model access semantics | live snapshot plus companion callability only |
| ComputeAER field toggles and OutStep cadence semantics | live snapshot only |
| Chain topology variants such as empty connections, entity groups, multiple possible relay paths, and LinkConnection cardinality | live snapshot only |
| Sensor/orientation-aware access behavior | deferred to the future orientation-aware entity/access slice |
| All time windows, all sites, all orbital regimes, or all server options | unverified |

When adding new cross-validation, prefer a passing independent oracle or a strong invariant. If a residual cannot be explained, keep it as a strict calibration xfail with diagnostics that narrow the trigger.
