# Access

This page documents the curated ASTROX Python access interface. The intended import style is:

```python
from astrox import access, entities
```

Access functions compute line-of-sight style access between named ASTROX analysis objects. The SDK assembles the Python request payload from `entities.Entity`, `entities.EntityGroup`, and `access.Connection` values, then returns the ASTROX JSON-like response dictionary unchanged.

## Direct Access

`access.compute(...)` computes direct access from one concrete entity to another concrete entity:

```python
ground = entities.entity(
    name="Ground",
    position=entities.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
)

iss = entities.entity(
    name="ISS",
    position=entities.sgp4_position(
        tle_lines=(
            "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
            "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
        ),
    ),
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    from_entity=ground,
    to_entity=iss,
    step_s=600.0,
    compute_aer=True,
)
```

`from_entity` and `to_entity` accept `entities.Entity` values. Name strings and entity groups are chain concepts and are not accepted by `compute(...)`.

`step_s` maps to the server output step. `compute_aer=True` asks ASTROX to include AER-like data for access intervals. `use_light_time_delay=True` forwards the server light-time-delay option. Optional fields are omitted unless you supply them.

The return value is the raw ASTROX response dictionary. Successful responses contain `Passes` when ASTROX returns intervals. When `compute_aer=True`, each pass may include `AccessBeginData`, `AccessEndData`, `AllDatas`, `MaxElevationData`, `MinElevationData`, `MaxRangeData`, and `MinRangeData`.

For fixed ground sites, access intervals for representative site-to-SGP4 cases are cross-validated against an independent Skyfield/WGS84 line-segment obstruction check, including the below-local-horizontal geometric horizon effect for elevated sites. Ground-origin access AER follows the same user convention as site AER elsewhere in ASTROX: azimuth is in the local horizontal plane with north as `0 deg` and positive eastward; elevation is the angle from the local horizontal plane, positive toward zenith. Cross-validation against Skyfield confirms the sign, units, and topocentric convention for representative fixed-site to SGP4 access samples. A stricter sub-arcsecond residual remains visible in validation after same-epoch, light-time, frame/constant, and horizon-threshold diagnostics, so do not treat access AER as independently calibrated to `1e-4 deg` precision yet.

For SGP4-to-ground role reversal, current cross-validation confirms interval symmetry and range symmetry with the ground-to-SGP4 case. Satellite-origin AER angles are still `unverified`: validation compares several candidate spacecraft frames, but none currently explains the ASTROX angles closely enough to document a frame convention.

`use_light_time_delay=True` is exercised for the representative ground-to-SGP4 case. The observed access-boundary shifts are consistent with a simple range-over-speed-of-light estimate at millisecond scale for that case; this validates the option is wired and produces physically plausible timing shifts, not that every model pair has been calibrated.

## Chain Access

`access.chain(...)` computes access through named chain participants. `participants` defines the objects that may appear in the chain. `start_participant`, `end_participant`, and optional `connections` refer to those participants by name; you can pass the participant value itself and the SDK lowers it to its name.

```python
targets = entities.entity_group(
    name="Targets",
    members=[iss],
    to_restriction="AnyOf",
)

chain_result = access.chain(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    participants=[ground, targets],
    start_participant=ground,
    end_participant=targets,
)
```

`participants` accepts `entities.Entity` and `entities.EntityGroup` values. `start_participant`, `end_participant`, and `access.connection(...)` endpoints accept an `Entity`, an `EntityGroup`, or a string name. String names are forwarded as references; the SDK does not locally check that a string appears in `participants`.

When `connections` is omitted, the SDK sends ASTROX the direct-chain form. To define an explicit topology, pass `access.Connection` values:

```python
chain_result = access.chain(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    participants=[ground, relay, iss],
    start_participant=ground,
    end_participant=iss,
    connections=[
        access.connection(ground, relay),
        access.connection(relay, iss),
    ],
)
```

`connections=[]` is preserved as an empty connection list. It is not rewritten to the direct-chain form.

The return value is the raw ASTROX response dictionary. Successful chain responses include fields such as `ComputedStrands`, `CompleteChainAccess`, `IndividualStrandAccess`, and `IndividualObjectAccess`. Current validation covers direct site-to-SGP4 chains, site-to-entity-group chains, and explicit multi-hop topology. Direct site-to-SGP4 chain access is cross-checked against `access.compute(...)` and the independent line-of-sight oracle. For an `EntityGroup` with `to_restriction="AnyOf"`, cross-validation checks that complete chain access is the union of the member strand intervals for a representative fixed-site to SGP4 group case. For a representative `ground -> relay SGP4 -> ground` topology, cross-validation checks that `CompleteChainAccess` is the intersection of the two direct link intervals and that `ComputedStrands`, `IndividualStrandAccess`, and `IndividualObjectAccess` are consistent with that composition.

## Position Sources

Access workflows accept named `entities.Entity` values. The maintained direct-access contract cases cover fixed sites, SGP4 TLE positions, central bodies, HPOP positions, CZML-like sampled positions, simple ascent positions, and ballistic positions. Semantic cross-validation currently covers fixed-site to SGP4, SGP4 to fixed-site, blocked ground-to-ground, SGP4 to J2, and HPOP/two-body mixed-model cases.

For fixed ground-to-ground pairs, validation includes a blocked Hawaii-to-Madrid style case and checks that ASTROX returns no passes when the independent WGS84 line segment intersects Earth. For SGP4-to-J2, validation compares the no-access result against sampled segment-vs-Earth obstruction using Skyfield for SGP4 and the calibrated ASTROX-like secular J2 helper. For HPOP and two-body position sources, current validation shows site-paired HPOP and site-paired two-body access branches are callable, and a distinct-orbit HPOP/two-body satellite pair is callable and interval-symmetric under role reversal. The remaining server-worker-error edge case is narrower: it appears when the mixed HPOP and two-body satellite pair is seeded from coincident initial orbits in both directions.

Access functions return ASTROX JSON-like response dictionaries. The SDK owns Pythonic request lowering and wiring; ASTROX owns support policy, physical feasibility, and server-side validation.
