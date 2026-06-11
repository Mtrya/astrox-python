# Access Cross-Validation Scope

This folder calibrates ASTROX access behavior against independent geometry, external propagation helpers, and cross-endpoint invariants. It is not a snapshot layer; SDK contract snapshots live under `tests/validation/sdk_contract/access/` and only prove maintained live response shape.

## Current Majority Coverage

The current non-orientation access calibration covers these behavior axes:

| Axis | Status | Evidence |
| --- | --- | --- |
| Fixed ground to SGP4 intervals | covered | Skyfield SGP4 plus WGS84 segment-obstruction oracle |
| ComputeAER field behavior | covered for fixed ground to SGP4 | omitted and `false` return interval-only passes, while `true` preserves intervals and adds AER data fields |
| OutStep AER sample cadence | covered for fixed ground to SGP4 | changing `OutStep` preserves interval boundaries and changes interior `AllDatas` sample cadence, with access start/stop rows preserved |
| Ground-origin SGP4 AER convention | covered with precision caveat | Skyfield topocentric azimuth/elevation/range comparison |
| Strict ground-origin SGP4 AER precision | calibration xfail | same-epoch, light-time-shifted, manual ITRS topocentric, and horizon diagnostics still leave a sub-arcsecond residual |
| SGP4 to ground interval/range role reversal | covered | symmetry against ground to SGP4 live output |
| Satellite-origin SGP4 AER convention | covered for fixed ground target | angles match an Earth-fixed local east/north/up frame at the satellite WGS84 geodetic subpoint; orbital RSW/TNW/VVLH-style frames were rejected by targeted diagnostics |
| Fixed ground to fixed ground obstruction | covered | blocked WGS84 segment case returns no passes |
| No-access response with AER requested | covered for fixed ground to fixed ground | blocked case returns an empty `Passes` list even when `ComputeAER=true` |
| SGP4 to J2 no-access branch | covered for the chosen case | Skyfield SGP4 plus calibrated ASTROX-like secular J2 sampled segment-obstruction oracle |
| Site-paired HPOP/two-body branches | covered for callability | live companion probes verify site to model and model to site calls return successfully |
| Distinct-orbit HPOP/two-body satellite pair | partial | live role-reversal interval symmetry is checked; no independent timing oracle is claimed |
| Coincident-orbit HPOP/two-body satellite pair | calibration xfail | same initial orbit mixed-model pair produces a server worker error in both directions |
| Direct chain site to SGP4 | covered | chain output matches direct compute and the independent line-of-sight oracle |
| Empty connection-list chain | covered | live `Connections: []` matches the direct `Connections: null` two-participant chain and reports the same direct strand |
| Entity-group AnyOf chain | covered | complete access equals the union of member strand intervals |
| Entity-group AtLeastN target chain | covered for the chosen target case | complete access equals the intersection of member strand intervals when the group is used as the end object with `ToAccess_Restriction=AtLeastN` and `ToAccess_Number=2` |
| Explicit ground to relay to ground chain | covered | complete access equals direct-link intersection, with strand/object access consistency checks |
| Explicit connection direction | covered | reversed link directions fail for the forward chain, while the matching reversed start/end chain returns symmetric intervals |
| Serial-chain light-time delay | covered for the chosen route | light-time and non-light-time chain results each match the corresponding direct-link intersection, and the option changes interval boundaries |
| Unused chain participants | covered | adding an unused participant does not change the single explicit route |
| Duplicate explicit link | calibration xfail | duplicating a required link produces a server no-path error even though the unique serial route works |
| Extra branch connection in one request | calibration xfail | a single route still works when the extra participant is unused, but adding an extra connection out of the start object produces a server no-path error |
| Multiple explicit relay routes in one request | calibration xfail | two individual relay routes work when requested separately, but combining both possible routes produces a server no-path error in either connection order |
| Entity-group start chain | calibration xfail | using an EntityGroup as `StartObject` produces a server index error for the chosen case |
| LinkConnection MinUses/MaxUses | calibration xfail | a two-link serial chain returns unchanged complete intervals for `MaxUses=0` and for inconsistent `MinUses=2, MaxUses=1` |
| Light-time delay for ground to SGP4 | covered for the chosen case | interval boundary shifts match range-over-c at millisecond scale and AER samples move measurably |

This is a majority calibration of the current access surface before orientation-sensitive entity behavior: direct role/model branches, core chain compositions, ground-origin AER, light-time, and known edge cases are covered or explicitly marked as calibration xfails.

## Deliberate Non-Claims

These tests do not prove full ASTROX access correctness. They do not yet calibrate:

| Axis | Current status |
| --- | --- |
| Central-body access semantics | live SDK contract only |
| CZML, simple-ascent, and ballistic access semantics | live SDK contract only |
| Broad HPOP force-model access semantics | live SDK contract plus companion callability only |
| One request containing multiple alternative relay routes | partial; the calibrated two-route case currently fails, and an extra branch connection also fails |
| LinkConnection MinUses/MaxUses cardinality semantics beyond the single-route probes | partial |
| EntityGroup as StartObject and intermediate connection node | partial; start-group calibration currently fails |
| Sensor/orientation-aware access behavior | deferred to the future orientation-aware entity/access slice |
| All time windows, all sites, all orbital regimes, or all server options | unverified |

When adding new cross-validation, prefer a passing independent oracle or a strong invariant. If a residual cannot be explained, keep it as a strict calibration xfail with diagnostics that narrow the trigger.
