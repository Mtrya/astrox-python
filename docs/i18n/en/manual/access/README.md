# Access

`astrox.access` computes access intervals between two named entities, and can also chain multiple named entities and entity groups into multi-hop chains to solve end-to-end access. Recommended import:

```python
from astrox import access, components
```

All access functions accept named objects constructed by `components` and return the raw ASTROX response dictionary. The SDK only assembles Python parameters into ASTROX request fragments and forwards server results; it does not perform secondary parsing on the response.

## Direct Access

### `access.compute`

```python
access.compute(
    *,
    start: str,
    stop: str,
    from_entity: components.Entity,
    to_entity: components.Entity,
    step_s: float | None = None,
    compute_aer: bool | None = None,
    use_light_time_delay: bool | None = None,
) -> dict[str, Any]
```

Computes direct access from `from_entity` to `to_entity`. Both arguments must be named objects constructed by `components.entity(...)`; strings, raw dicts, or entity groups will be rejected by the SDK.

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Start time string in ISO 8601 format |
| `stop` | — | Stop time string in ISO 8601 format |
| `from_entity` | — | Source named object, a `components.Entity` value |
| `to_entity` | — | Target named object, a `components.Entity` value |
| `step_s` | s | Output sampling step, corresponding to ASTROX `OutStep` |
| `compute_aer` | — | Whether to request AER output; when `True` each access interval includes AER data |
| `use_light_time_delay` | — | Whether to enable the light-time option |

The returned dict contains the three fields `IsSuccess`, `Message`, and `Passes`. `Passes` is a list of access intervals; the fields of each interval are as follows:

| Field | Type | Description |
| --- | --- | --- |
| `AccessStart` | `str` | Interval start time |
| `AccessStop` | `str` | Interval stop time |
| `Duration` | `float` | Interval duration, unit s |
| `AccessBeginData` | `dict` | AER data at interval start (only present when `compute_aer=True`) |
| `AccessEndData` | `dict` | AER data at interval stop (only present when `compute_aer=True`) |
| `AllDatas` | `list[dict]` | AER data sampled inside the interval according to `step_s` (only present when `compute_aer=True`) |
| `MaxElevationData` | `dict` | Maximum elevation sample (only present when `compute_aer=True`) |
| `MinElevationData` | `dict` | Minimum elevation sample (only present when `compute_aer=True`) |
| `MaxRangeData` | `dict` | Maximum range sample (only present when `compute_aer=True`) |
| `MinRangeData` | `dict` | Minimum range sample (only present when `compute_aer=True`) |

In AER data rows, the units of `Azimuth` and `Elevation` are deg, the unit of `Range` is m, and `Time` is an ISO 8601 string; when `compute_aer` is omitted or `False`, the above AER fields will not appear.

```python
ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

ground = components.entity(
    name="Ground",
    position=components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
)
iss = components.entity(
    name="ISS",
    position=components.sgp4_position(tle_lines=ISS_TLE),
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    from_entity=ground,
    to_entity=iss,
    step_s=600.0,
    compute_aer=True,
)

print(f"Direct access intervals: {len(result['Passes'])}")
```

A complete runnable example can be found at `examples/04_access/compute.py`.

## Constraints and Sensors

`access.compute(...)` has no standalone `constraints=` parameter; constraints are passed through the named object's `constraints` list and sent to ASTROX along with the object. Available constraints include elevation constraint, range constraint, azimuth-elevation mask constraint, sun exclusion angle constraint, and moon exclusion angle constraint; see the [components manual](../components/README.md) for details.

```python
constrained_ground = components.entity(
    name="Ground",
    position=components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
    constraints=[
        components.elevation_constraint(minimum_deg=10.0),
        components.range_constraint(maximum_km=2500.0, maximum_enabled=True),
    ],
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T03:00:00.000Z",
    from_entity=constrained_ground,
    to_entity=iss,
    step_s=60.0,
    compute_aer=True,
)
```

A complete runnable example can be found at `examples/04_access/constraints.py`.

If the access should be determined by a spacecraft sensor's field of view, you can attach `orientation`, `sensor`, and `sensor_pointing` to the starting named object:

```python
observer = components.entity(
    name="ObserverSat",
    position=components.two_body_position(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T02:00:00.000Z",
        step_s=120.0,
    ),
    orientation=components.vvlh_axes(),
    sensor=components.conic_sensor(outer_half_angle_deg=8.0),
    sensor_pointing=components.fixed_sensor_pointing(
        rotation=components.quaternion_rotation(
            scalar=1.0,
            x=0.0,
            y=0.0,
            z=0.0,
        ),
    ),
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T02:00:00.000Z",
    from_entity=observer,
    to_entity=target_site,
    step_s=120.0,
    compute_aer=True,
)
```

A complete runnable example can be found at `examples/04_access/sensor_pointing.py` and `examples/04_access/custom_axes.py`.

## Access Chain

### `access.chain`

```python
access.chain(
    *,
    start: str,
    stop: str,
    participants: Sequence[components.Entity | components.EntityGroup],
    start_participant: components.Entity | components.EntityGroup | str,
    end_participant: components.Entity | components.EntityGroup | str,
    connections: Sequence[Connection] | None = None,
    use_light_time_delay: bool | None = None,
) -> dict[str, Any]
```

Computes multi-hop access chains among explicitly provided participants. `participants` lists all available objects and may be named objects or entity groups; `start_participant` and `end_participant` may be the objects themselves or their name strings.

| Parameter | Description |
| --- | --- |
| `start` | Start time string |
| `stop` | Stop time string |
| `participants` | All participating objects, elements are `Entity` or `EntityGroup` |
| `start_participant` | Chain start, may be an object, an entity group, or a name string |
| `end_participant` | Chain end, may be an object, an entity group, or a name string |
| `connections` | Explicit connection list; when omitted a direct-chain form is sent |
| `use_light_time_delay` | Whether to enable the light-time option |

The returned dict contains the following fields:

| Field | Description |
| --- | --- |
| `IsSuccess` | Whether successful |
| `Message` | Server message |
| `ComputedStrands` | List of actually computed chains, each a sequence of names |
| `CompleteChainAccess` | Access interval list for the entire chain |
| `IndividualStrandAccess` | Access interval for each chain segment, keyed by strings of the form `"A>B"` or `"A>B>C"` |
| `IndividualObjectAccess` | Access interval for each individual object, keyed by object name |

### Entity Groups and Restriction Semantics

Entity groups are constructed via `components.entity_group(...)` and allow multiple objects to be treated as one endpoint in a chain. The optional values for `from_restriction` and `to_restriction` are `"AnyOf"` or `"AtLeastN"`:

- `"AnyOf"`: as long as any member in the group satisfies the access condition.
- `"AtLeastN"`: at least `from_number` or `to_number` members must satisfy the condition simultaneously; when using this value the corresponding count parameter must be provided at the same time.

```python
targets = components.entity_group(
    name="Targets",
    members=[iss, hubble],
    to_restriction="AnyOf",
)

group_chain = access.chain(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    participants=[ground, targets],
    start_participant=ground,
    end_participant=targets,
)
```

### Explicit Connections

When you need to specify which directional connections the chain must pass through, use `access.connection(...)` to construct a `Connection` list:

```python
access.connection(
    from_participant: Entity | EntityGroup | str,
    to_participant: Entity | EntityGroup | str,
    *,
    min_uses: int | None = None,
    max_uses: int | None = None,
) -> Connection
```

`from_participant` and `to_participant` may be objects, entity groups, or name strings; `min_uses` and `max_uses` are forwarded to ASTROX as-is. `connections=[]` is preserved as an empty list rather than rewritten into direct-chain form.

```python
explicit_chain = access.chain(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    participants=[ground, iss, hubble],
    start_participant=ground,
    end_participant=hubble,
    connections=[
        access.connection(ground, iss),
        access.connection(iss, hubble),
    ],
)
```

A complete runnable example can be found at `examples/04_access/chain.py`.

## Composable Position Sources

Access computation itself imposes no restriction on position source types; any position source supported by `components` can be embedded in a named object: ground sites, SGP4 two-line elements, J2/two-body/HPOP propagated positions, CZML sampled positions, simple ascent, ballistic trajectories, central bodies, etc. For construction and units of each position source, see the [components manual](../components/README.md).

## Error Handling

When ASTROX returns an unsuccessful response or the network request fails, the access functions raise `astrox.exceptions.AstroxAPIError`. The SDK does not rewrite server error messages. Use `astrox.raw.post` when you need full control over the request payload or to handle the raw response.

## Conventions

- Optional parameters are not sent to ASTROX when not provided; the server keeps its defaults.
- AER data is produced in each access interval only when `compute_aer=True`; when omitted or explicitly set to `False`, only interval start and stop times are returned.
- Constraints must be passed as fields of a named object; `access.compute(...)` does not accept a standalone constraint parameter.
- Name references in a chain are forwarded to ASTROX as-is; the SDK does not check whether a string name appears among `participants`.
