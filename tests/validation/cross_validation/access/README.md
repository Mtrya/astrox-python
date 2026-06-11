# Access Cross-Validation Scope

This folder calibrates ASTROX access behavior against independent geometry, external propagation helpers, and cross-endpoint invariants. It is not a snapshot layer; SDK contract snapshots live under `tests/validation/sdk_contract/access/` and only prove maintained live response shape.

## Current Majority Coverage

The current non-orientation access calibration covers these behavior axes:

| Axis | Status | Evidence |
| --- | --- | --- |
| Fixed ground to SGP4 intervals | covered | Skyfield SGP4 plus WGS84 segment-obstruction oracle |
| Ground-origin SGP4 AER convention | covered with precision caveat | Skyfield topocentric azimuth/elevation/range comparison |
| Strict ground-origin SGP4 AER precision | calibration xfail | same-epoch, light-time-shifted, manual ITRS topocentric, and horizon diagnostics still leave a sub-arcsecond residual |
| SGP4 to ground interval/range role reversal | covered | symmetry against ground to SGP4 live output |
| Satellite-origin SGP4 AER frame | calibration xfail | range is symmetric, but tested RSW/TNW/VVLH/LVLH/nadir-velocity frames do not explain angles |
| Fixed ground to fixed ground obstruction | covered | blocked WGS84 segment case returns no passes |
| SGP4 to J2 no-access branch | covered for the chosen case | Skyfield SGP4 plus calibrated ASTROX-like secular J2 sampled segment-obstruction oracle |
| Site-paired HPOP/two-body branches | covered for callability | live companion probes verify site to model and model to site calls return successfully |
| Distinct-orbit HPOP/two-body satellite pair | partial | live role-reversal interval symmetry is checked; no independent timing oracle is claimed |
| Coincident-orbit HPOP/two-body satellite pair | calibration xfail | same initial orbit mixed-model pair produces a server worker error in both directions |
| Direct chain site to SGP4 | covered | chain output matches direct compute and the independent line-of-sight oracle |
| Entity-group AnyOf chain | covered | complete access equals the union of member strand intervals |
| Explicit ground to relay to ground chain | covered | complete access equals direct-link intersection, with strand/object access consistency checks |
| Light-time delay for ground to SGP4 | covered for the chosen case | interval boundary shifts match range-over-c at millisecond scale and AER samples move measurably |

This is a majority calibration of the current access surface before orientation-sensitive entity behavior: direct role/model branches, core chain compositions, ground-origin AER, light-time, and known edge cases are covered or explicitly marked as calibration xfails.

## Deliberate Non-Claims

These tests do not prove full ASTROX access correctness. They do not yet calibrate:

| Axis | Current status |
| --- | --- |
| Central-body access semantics | live SDK contract only |
| CZML, simple-ascent, and ballistic access semantics | live SDK contract only |
| Broad HPOP force-model access semantics | live SDK contract plus companion callability only |
| Satellite-origin AER frame convention | calibration xfail |
| Sensor/orientation-aware access behavior | deferred to the future orientation-aware entity/access slice |
| All time windows, all sites, all orbital regimes, or all server options | unverified |

When adding new cross-validation, prefer a passing independent oracle or a strong invariant. If a residual cannot be explained, keep it as a strict calibration xfail with diagnostics that narrow the trigger.
