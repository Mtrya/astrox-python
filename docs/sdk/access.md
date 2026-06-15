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

`step_s` maps to the server output step. For a representative fixed-site to SGP4 case with `compute_aer=True`, validation shows that changing `step_s` changes the cadence of interior `AllDatas` AER rows without changing access interval boundaries; ASTROX still includes access start and stop rows. `compute_aer=True` asks ASTROX to include AER-like data for access intervals. For the same validated case, omitting `compute_aer` and passing `compute_aer=False` both return interval-only passes, while `compute_aer=True` preserves intervals and adds AER data fields. `use_light_time_delay=True` forwards the server light-time-delay option. Optional fields are omitted unless you supply them.

The return value is the raw ASTROX response dictionary. Successful responses contain `Passes` when ASTROX returns intervals. When `compute_aer=True`, each pass may include `AccessBeginData`, `AccessEndData`, `AllDatas`, `MaxElevationData`, `MinElevationData`, `MaxRangeData`, and `MinRangeData`.

For fixed ground sites, access intervals for representative site-to-SGP4 cases are cross-validated against an independent Skyfield/WGS84 line-segment obstruction check, including the below-local-horizontal geometric horizon effect for elevated sites. Ground-origin access AER follows the same user convention as site AER elsewhere in ASTROX: azimuth is in the local horizontal plane with north as `0 deg` and positive eastward; elevation is the angle from the local horizontal plane, positive toward zenith. Cross-validation against Skyfield confirms the sign, units, and topocentric convention for representative fixed-site to SGP4 access samples, including dense `OutStep=60s` rows. An arcsecond-scale residual remains visible in validation after same-epoch, light-time, manual ITRS, horizon-threshold, and simple site/time-offset diagnostics, so do not treat access AER as independently calibrated to `1e-4 deg` precision yet.

For SGP4-to-ground role reversal, current cross-validation confirms interval symmetry and range symmetry with the ground-to-SGP4 case. Satellite-origin AER for the representative SGP4-to-fixed-site case is not an orbital LVLH/VVLH-style frame. The angles match an Earth-fixed local east/north/up frame at the satellite WGS84 geodetic subpoint, using the vector from the satellite to the target site; azimuth is measured from local north toward local east, and elevation is measured from that local horizontal plane.

`use_light_time_delay=True` is exercised for the representative ground-to-SGP4 case. The observed access-boundary shifts are consistent with a simple range-over-speed-of-light estimate at millisecond scale for that case; this validates the option is wired and produces physically plausible timing shifts, not that every model pair has been calibrated.

## Entity Constraints

Attach shared ASTROX constraints to the `from_entity` or `to_entity` participant through the entity `constraints` list:

```python
ground = entities.entity(
    name="Ground",
    position=entities.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
    constraints=[
        entities.elevation_constraint(minimum_deg=10.0),
        entities.range_constraint(maximum_km=2500.0, maximum_enabled=True),
    ],
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

`access.compute(...)` does not accept a separate `constraints=` argument. Constraints are participant metadata, so they travel with the entity through `FromObjectPath` and `ToObjectPath`. The SDK rejects raw constraint dictionaries at the entity boundary; use `entities.elevation_constraint(...)`, `entities.range_constraint(...)`, or `entities.az_el_mask_constraint(...)`.

The supported constraint types are elevation-angle limits in degrees, range limits in kilometers, and azimuth/elevation mask samples in radians. Cross-validation in `tests/validation/cross_validation/access/test_compute_constraints_skyfield.py` establishes the following for representative fixed-site to SGP4 and SGP4-to-fixed-site cases:

- `ElevationAngle.MinimumValue` is a lower bound in degrees at the constrained participant, evaluated in the participant's local topocentric frame. The boundary is inclusive within the calibration tolerance.
- `ElevationAngle.MaximumValue` is active only when `IsMaximumEnabled=True` and uses the same frame and units as the minimum.
- `Range.MinimumValue` and `Range.MaximumValue` are evaluated in kilometers on the geometric range between the two participants. `MinimumValue` is active whenever supplied; `MaximumValue` is active only when `IsMaximumEnabled=True`.
- `use_light_time_delay=True` shifts access interval boundaries but the range constraint threshold is still evaluated on geometric range.
- Multiple constraints on the same participant produce the intersection of their predicates. When both participants have elevation minima, the result is the intersection of the two independent local-frame predicates.
- Constraints attached to the satellite participant are evaluated in the satellite's Earth-fixed geodetic local frame (the same convention used for satellite-origin AER rows), not in a spacecraft body frame and not ignored.
- `compute_aer=True` returns AER rows that satisfy the active elevation constraint.

AzEl mask interpolation for non-flat sector masks, `AzElMask.MaxRange` semantics, AzEl masks attached to a satellite participant, and server error behavior for some contradictory combinations remain unresolved. Consult the cross-validation matrix for the current evidence state of each branch.

## Sensor-Constrained Access

Attach `orientation`, `sensor`, and optional `sensor_pointing` metadata to the `from_entity` when an access computation should be constrained by a spacecraft sensor:

```python
observer = entities.entity(
    name="Observer",
    position=entities.two_body_position(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T02:00:00.000Z",
        step_s=120.0,
    ),
    orientation=entities.vvlh_axes(),
    sensor=entities.conic_sensor(outer_half_angle_deg=8.0),
    sensor_pointing=entities.fixed_sensor_pointing(
        rotation=entities.quaternion_rotation(
            scalar=1.0,
            x=0.0,
            y=0.0,
            z=0.0,
        ),
    ),
)
```

Current cross-validation covers conic and rectangular sensor fields of view; quaternion, Euler, and Az/El fixed sensor pointing; VVLH/LVLH/VNC axes; Fixed, FixedAtEpoch, Composite, short-span sampled-identity CZML axes; and VGT aligned-and-constrained axes built from fixed vectors. These cases compare `Passes.AccessStart` and `Passes.AccessStop` against an independent local geometry oracle that samples two-body state, WGS84 obstruction, calibrated body frames, and sensor field-of-view predicates.

The calibrated body-frame summary is:

| Frame | Validated convention |
| --- | --- |
| `VVLH` | `+Z` nadir, `+X` along-track projected into the local horizontal plane, `+Y` completes the right-side frame |
| `LVLH` | `+X` radial outward, `+Z` orbit angular momentum, `+Y = Z x X` |
| `VNC` | `+X` inertial velocity, `+Y` orbit angular momentum, `+Z` completes the right-handed frame |

Quaternion and Euler sensor rotations act on the local `+Z` boresight. Az/El sensor pointing is not equivalent to those rotations: validation shows ASTROX treats Az/El as a direct boresight vector in the parent axes, with azimuth from `+X` toward `+Y` and elevation toward `+Z`.

Unresolved orientation branches are deliberately not hidden. Moon/Mars/Sun-relative axes, Fixed axes relative to inertial-name variants such as `ICRF` and `J2000`, CZML constant and non-identity quaternion behavior, VGT names containing spaces, and non-empty VGT Points/Systems remain strict calibration xfails under `tests/validation/cross_validation/access/`. The SDK forwards those request fragments when you build them, but this documentation does not present them as semantically understood.

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

When `connections` is omitted, the SDK sends ASTROX the direct-chain form. To define an explicit sequence of allowed directional links, pass `access.Connection` values:

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

`connections=[]` is preserved as an empty connection list. It is not rewritten to the direct-chain form. Live validation shows that, for a simple two-participant chain, ASTROX currently treats `Connections: []` like the direct `Connections: null` chain and reports the same direct strand.

The return value is the raw ASTROX response dictionary. Successful chain responses include fields such as `ComputedStrands`, `CompleteChainAccess`, `IndividualStrandAccess`, and `IndividualObjectAccess`. Current validation covers direct site-to-SGP4 chains, target entity-group chains, and one explicit serial multi-hop route. Direct site-to-SGP4 chain access is cross-checked against `access.compute(...)` and the independent line-of-sight oracle. For an `EntityGroup` used as the end object, cross-validation checks that `to_restriction="AnyOf"` complete access is the union of member strand intervals and that `to_restriction="AtLeastN", to_number=2` complete access is the intersection of the two member strand intervals for representative fixed-site to SGP4 group cases. For a representative `ground -> relay SGP4 -> ground` route, cross-validation checks that `CompleteChainAccess` is the intersection of the two direct link intervals and that `ComputedStrands`, `IndividualStrandAccess`, and `IndividualObjectAccess` are consistent with that composition. Reversing the link directions fails for that forward route; using the matching reversed start/end route returns symmetric intervals. For the same serial route, `use_light_time_delay=True` changes interval boundaries and matches the intersection of direct-link access computed with light-time delay enabled.

Do not assume that one ChainCompute request can describe several possible relay paths at once. Current calibration probes first verify that `ground -> relay_a -> target` and `ground -> relay_b -> target` each work when requested separately. The same probes then combine both sets of allowed links in one request, and ASTROX returns a server no-path error in either connection order. The failure is not caused merely by listing an unused participant: a single explicit route still works with an unused extra relay object present, but adding an additional connection from the same start object to that extra relay also triggers the no-path error. Duplicating a required link also produces the same no-path error. A group used as `StartObject` fails with a server index error for the calibrated case. `MinUses` and `MaxUses` are forwarded when supplied, but current validation does not establish useful cardinality semantics: a two-link serial chain returns unchanged intervals for both `MaxUses=0` and inconsistent `MinUses=2, MaxUses=1`. The SDK forwards these options; it does not reinterpret them or compute chain access locally.

## Position Sources

Access workflows accept named `entities.Entity` values. The maintained direct-access contract cases cover fixed sites, SGP4 TLE positions, central bodies, HPOP positions, CZML-like sampled positions, simple ascent positions, and ballistic positions. Semantic cross-validation currently covers fixed-site to SGP4, SGP4 to fixed-site, blocked ground-to-ground, SGP4 to J2, and HPOP/two-body mixed-model cases.

For fixed ground-to-ground pairs, validation includes a blocked Hawaii-to-Madrid style case and checks that ASTROX returns no passes when the independent WGS84 line segment intersects Earth. The blocked case also returns an empty `Passes` list when `compute_aer=True`. For SGP4-to-J2, validation compares the no-access result against sampled segment-vs-Earth obstruction using Skyfield for SGP4 and the calibrated ASTROX-like secular J2 helper. For HPOP and two-body position sources, current validation shows site-paired HPOP and site-paired two-body access branches are callable, and distinct-orbit and tiny-offset HPOP/two-body satellite pairs are callable and interval-symmetric under role reversal. The remaining server-worker-error edge case is narrower and not specific to mixed models: exact same initial orbit produces a server worker error for same-model and mixed HPOP/two-body satellite pairs, while changing only the second satellite's true anomaly by `1e-6 deg` makes the mixed HPOP/two-body pair callable.

Access functions return ASTROX JSON-like response dictionaries. The SDK owns Pythonic request lowering and wiring; ASTROX owns support policy, physical feasibility, and server-side validation.
