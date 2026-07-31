# Components

`astrox.components` provides the public vocabulary for ASTROX analysis objects: named entities, position sources, sensors, constraints, attitude axes, rotations, and Vector Geometry Tool (VGT) utilities. These value objects do not initiate network requests themselves; they only assemble Python parameters into request fragments that ASTROX recognizes. The recommended import is:

```python
from astrox import components
```

Components are typically embedded in requests for `astrox.access` access computations, coverage computations, and so on. This page introduces each public constructor and its parameters grouped by concept; for how each endpoint uses these values, see the [access manual](../access/README.md) and [propagator manual](../propagator/README.md).

All constructors use `snake_case` parameter names, and parameters with units use explicit suffixes such as `_m`, `_deg`, `_s`, `_km`, etc. Optional parameters that are not provided are not sent to ASTROX, and the server retains its default values. Every value object has a `to_wire()` method that can be used to inspect the generated request fragment when needed; ordinary SDK calls simply pass the value object in directly.

## Named Entities

### `components.entity`

```python
components.entity(
    *,
    name: str,
    position: EntityPosition,
    description: str | None = None,
    vgt: VgtProvider | None = None,
    orientation: EntityAxes | None = None,
    sensor: EntitySensor | None = None,
    sensor_pointing: SensorPointing | None = None,
    constraints: Sequence[Constraint] | None = None,
) -> Entity
```

`entity` constructs a named entity (Entity), which is a combination of a position source and metadata. `Entity` is a frozen dataclass with the following fields:

| Field | Type | Description |
| --- | --- | --- |
| `name` | `str` | Entity name, used in access chains to identify this object |
| `position` | `EntityPosition` | Position source, required |
| `description` | `str \| None` | Description |
| `vgt` | `VgtProvider \| None` | Attached VGT named geometry definitions |
| `orientation` | `EntityAxes \| None` | Attitude axes of the named entity |
| `sensor` | `EntitySensor \| None` | Sensor shape |
| `sensor_pointing` | `SensorPointing \| None` | Sensor pointing |
| `constraints` | `tuple[Constraint, ...] \| None` | Constraints |

```python
satellite = components.entity(
    name="ISS",
    position=components.sgp4_position(
        tle_lines=(
            "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
            "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
        )
    ),
    description="Representative spacecraft",
)
```

### `components.entity_group`

```python
components.entity_group(
    *,
    name: str,
    members: Sequence[Entity],
    from_restriction: str | None = None,
    from_number: int | None = None,
    to_restriction: str | None = None,
    to_number: int | None = None,
) -> EntityGroup
```

`entity_group` combines multiple named entities into a named entity group (EntityGroup), used in scenarios such as access chains that require grouped participants. The optional values for `from_restriction` and `to_restriction` are `"AnyOf"` or `"AtLeastN"`; when the value is `"AtLeastN"`, the corresponding `from_number` or `to_number` must also be provided.

```python
targets = components.entity_group(
    name="Targets",
    members=[satellite],
    to_restriction="AnyOf",
)
```

### `astrox.access.connection`

The explicit connection fragment for an access chain is constructed by `astrox.access.connection`, and its corresponding type is `astrox.access.Connection`. It is not exported from `astrox.components`, but it is used together with named entity groups:

```python
from astrox import access, components

link = access.connection(ground, satellite)
```

The full signature and usage of `connection` are in the [access manual](../access/README.md).

## Position Sources

Position sources describe the spatial position of an object as a function of time and are the `position` field of a named entity. The position sources in `astrox.components` correspond one-to-one with the propagation functions in `astrox.propagator`, but they belong to the component-layer value objects used for embedding in requests such as access.

### Ground Site Position

```python
components.site_position(
    *,
    longitude_deg: float,
    latitude_deg: float,
    height_m: float,
    central_body: str | None = None,
    clamp_to_ground: bool | None = None,
    height_above_ground_m: float | None = None,
) -> SitePosition
```

`site_position` describes a fixed ground site using geodetic longitude, latitude, and height. `longitude_deg` and `latitude_deg` are in degrees, and `height_m` is altitude above the reference ellipsoid in meters.

```python
site = components.site_position(
    longitude_deg=-155.468,
    latitude_deg=19.821,
    height_m=4205.0,
)
```

### CZML Sampled Position

```python
components.czml_position(
    *,
    epoch: str,
    central_body: str | None = None,
    interpolation_algorithm: str | None = None,
    interpolation_degree: int | None = None,
    reference_frame: str | None = None,
    interval: str | None = None,
    cartesian: Sequence[float] | None = None,
    cartesian_velocity: Sequence[float] | None = None,
) -> CzmlPosition
```

`czml_position` describes a position using a CZML-style sampled sequence. `cartesian` has the form `[t, x, y, z, ...]`, and `cartesian_velocity` has the form `[t, x, y, z, vx, vy, vz, ...]`.

```python
sampled = components.czml_position(
    epoch="2024-01-01T00:00:00.000Z",
    reference_frame="INERTIAL",
    cartesian_velocity=[
        0.0, 7000000.0, 0.0, 0.0, 0.0, 7500.0, 0.0,
    ],
)
```

### Composite CZML Position

```python
components.czml_positions(
    positions: Sequence[CzmlPosition],
    *,
    central_body: str | None = None,
) -> CzmlPositions
```

`czml_positions` combines multiple `CzmlPosition` objects into a composite position source.

```python
track = components.czml_positions([sampled], central_body="Earth")
```

### Central Body Position

```python
components.central_body_position(name: str) -> CentralBodyPosition
```

`central_body_position` constructs a value that uses the specified central body itself as the position source.

```python
sun = components.central_body_position("Sun")
```

### Propagation Position Sources

The parameters of the following constructors are consistent with the propagation functions of the same name in `astrox.propagator`; the difference is that they return component value objects instead of initiating propagation requests directly. For the full meaning of parameters and their units, see the [propagator manual](../propagator/README.md).

```python
components.j2_position(
    *,
    orbit_epoch: str,
    orbit: KeplerianElements,
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
    j2_normalized_value: float | None = None,
    ref_distance_m: float | None = None,
) -> J2Position

components.two_body_position(
    *,
    orbit_epoch: str,
    orbit: KeplerianElements,
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
) -> TwoBodyPosition

components.sgp4_position(
    *,
    tle_lines: tuple[str, str] | list[str],
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    satellite_number: str | None = None,
) -> Sgp4Position
```

```python
j2 = components.j2_position(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    step_s=300.0,
)

iss = components.sgp4_position(
    tle_lines=(
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
        "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    ),
)
```

### HPOP, Simple Ascent, and Ballistic Position Sources

```python
components.hpop_position(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements | None = None,
    state: CartesianState | None = None,
    config: HpopConfig | Mapping[str, Any] | None = None,
    coord_epoch: str | None = None,
    coord_system: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coefficient_of_drag: float | None = None,
    area_mass_ratio_drag_m2_kg: float | None = None,
    coefficient_of_srp: float | None = None,
    area_mass_ratio_srp_m2_kg: float | None = None,
) -> HpopPosition

components.simple_ascent_position(
    *,
    start: str,
    stop: str,
    launch_latitude_deg: float,
    launch_longitude_deg: float,
    launch_altitude_m: float,
    burnout_velocity_m_s: float,
    burnout_latitude_deg: float,
    burnout_longitude_deg: float,
    burnout_altitude_m: float,
    step_s: float | None = None,
    central_body: str | None = None,
) -> SimpleAscentPosition

components.ballistic_position(
    *,
    start: str,
    ballistic_type: str,
    ballistic_type_value: float,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_latitude_deg: float | None = None,
    impact_longitude_deg: float | None = None,
    impact_altitude_m: float | None = None,
) -> BallisticPosition
```

For `hpop_position`, exactly one of `orbit` or `state` must be provided; `config` can be an object returned by `propagator.hpop_config(...)` or a raw dictionary mapping with a known ASTROX structure. `ballistic_position`'s `ballistic_type` and `ballistic_type_value` correspond to different ballistic solution branches in propagator:

| `ballistic_type` | Meaning of `ballistic_type_value` |
| --- | --- |
| `"DeltaV"` | Velocity increment `delta_v_m_s` |
| `"MinEccentricity"` | Velocity increment `delta_v_m_s` |
| `"ApogeeAltitude"` | Apogee altitude `apogee_altitude_m` |
| `"TimeOfFlight"` | Time of flight `time_of_flight_s` |

The full branch description for ballistic propagation is in the [propagator manual](../propagator/README.md).

```python
ascent = components.simple_ascent_position(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    launch_latitude_deg=40.0,
    launch_longitude_deg=100.0,
    launch_altitude_m=1000.0,
    burnout_velocity_m_s=7800.0,
    burnout_latitude_deg=41.0,
    burnout_longitude_deg=101.0,
    burnout_altitude_m=200000.0,
)

ballistic = components.ballistic_position(
    start="2024-01-01T00:00:00.000Z",
    ballistic_type="DeltaV",
    ballistic_type_value=5000.0,
)
```

## Sensors and Sensor Pointing

### Conic and Rectangular Sensors

```python
components.conic_sensor(
    *,
    inner_half_angle_deg: float | None = None,
    outer_half_angle_deg: float | None = None,
    minimum_clock_angle_deg: float | None = None,
    maximum_clock_angle_deg: float | None = None,
    text: str | None = None,
) -> ConicSensor

components.rectangular_sensor(
    *,
    x_half_angle_deg: float | None = None,
    y_half_angle_deg: float | None = None,
    text: str | None = None,
) -> RectangularSensor
```

Angle parameters are in degrees. `outer_half_angle_deg` is the most commonly used half-angle for conic sensors; rectangular sensors use `x_half_angle_deg` and `y_half_angle_deg` to describe the half-angles in the two directions.

```python
camera = components.conic_sensor(outer_half_angle_deg=30.0)
rect_camera = components.rectangular_sensor(
    x_half_angle_deg=5.0,
    y_half_angle_deg=10.0,
)
```

### Fixed Sensor Pointing

```python
components.fixed_sensor_pointing(
    *,
    rotation: Rotation,
    text: str | None = None,
) -> FixedSensorPointing
```

`fixed_sensor_pointing` defines a fixed sensor pointing relative to the host body axes using a rotation fragment. `Rotation` can be `az_el_rotation`, `quaternion_rotation`, or `euler_rotation`.

```python
sensor_pointing = components.fixed_sensor_pointing(
    rotation=components.quaternion_rotation(
        scalar=1.0,
        x=0.0,
        y=0.0,
        z=0.0,
    ),
)
```

### Pointing Directions

```python
components.ra_dec_direction(
    *,
    ra_deg: float,
    dec_deg: float,
    magnitude: float | None = None,
) -> RaDecDirection

components.xyz_direction(
    *,
    x: float,
    y: float,
    z: float,
) -> XyzDirection
```

`ra_dec_direction` and `xyz_direction` are used to construct directions for VGT fixed vectors, described below in [Vector Geometry Tool VGT](#vector-geometry-tool-vgt).

## Constraints

Constraints are embedded in a named entity as the `Entity.constraints` list and are used by access and other computations.

### Elevation Constraint

```python
components.elevation_constraint(
    *,
    minimum_deg: float | None = None,
    maximum_deg: float | None = None,
    maximum_enabled: bool | None = None,
    text: str | None = None,
) -> ElevationConstraint
```

Angles are in degrees. `maximum_deg` only takes effect when `maximum_enabled=True` is also provided.

### Range Constraint

```python
components.range_constraint(
    *,
    minimum_km: float | None = None,
    maximum_km: float | None = None,
    maximum_enabled: bool | None = None,
    text: str | None = None,
) -> RangeConstraint
```

Distance is in kilometers. `maximum_km` only takes effect when `maximum_enabled=True` is also provided.

### Azimuth-Elevation Mask Constraint

```python
components.az_el_mask_constraint(
    *,
    az_el_mask_rad: Sequence[float],
    max_range_km: float | None = None,
    text: str | None = None,
) -> AzElMaskConstraint
```

`az_el_mask_rad` is an alternating sequence of azimuth and elevation samples in radians. This constraint is only valid for `SitePosition` position sources.

### Sun/Moon Exclusion Angle Constraints

```python
components.sun_exclusion_angle_constraint(
    *,
    minimum_deg: float | None = None,
    text: str | None = None,
) -> SunExclusionAngleConstraint

components.moon_exclusion_angle_constraint(
    *,
    minimum_deg: float | None = None,
    text: str | None = None,
) -> MoonExclusionAngleConstraint
```

Angles are in degrees and represent the minimum allowed angular separation between the constrained object and the Sun/Moon direction.

```python
constraints = [
    components.elevation_constraint(minimum_deg=10.0),
    components.range_constraint(maximum_km=2500.0, maximum_enabled=True),
    components.az_el_mask_constraint(az_el_mask_rad=[0.0, 0.1]),
    components.sun_exclusion_angle_constraint(minimum_deg=25.0),
    components.moon_exclusion_angle_constraint(minimum_deg=15.0),
]
```

## Attitude Axes

Entity-level attitude axes describe the body axes or reference frame of a named entity. `astrox.components` uses `Axes` at this layer, distinguished from the rotation fragments `Rotation` described below.

### Orbit-Related Axes

```python
components.vvlh_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> VvlhAxes

components.lvlh_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> LvlhAxes

components.vnc_axes(
    *,
    relative_to: str | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> VncAxes
```

The optional values for `relative_to` are `"Earth"`, `"Moon"`, `"Mars"`, `"Sun"`, `"CBF"`. If referenced by other axes or VGT vectors, it must be named via the `name` parameter.

```python
body_axes = components.vvlh_axes(name="BodyVVLH")
lvlh = components.lvlh_axes()
vnc = components.vnc_axes(relative_to="Earth")
```

### Fixed Axes and Fixed-at-Epoch Axes

```python
components.fixed_axes(
    *,
    reference_axes: EntityAxes | str,
    rotation: Rotation,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> FixedAxes

components.fixed_at_epoch_axes(
    *,
    source_axes: EntityAxes | str,
    reference_axes: EntityAxes | str,
    epoch: str,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> FixedAtEpochAxes
```

`fixed_axes` fixes a reference axes by the given rotation. `fixed_at_epoch_axes` freezes the source axes onto the reference axes at the specified epoch. Referenced `EntityAxes` objects must already be named.

```python
camera_axes = components.fixed_axes(
    reference_axes=body_axes,
    rotation=components.euler_rotation(
        sequence="321",
        a_deg=0.0,
        b_deg=-20.0,
        c_deg=0.0,
    ),
    name="CameraAxes",
)

frozen = components.fixed_at_epoch_axes(
    source_axes=camera_axes,
    reference_axes="ICRF",
    epoch="2024-01-01T00:00:00.000Z",
)
```

### Aligned and Constrained Axes

```python
components.aligned_and_constrained_axes(
    *,
    principal: VgtVector | str,
    principal_axis: str,
    reference: VgtVector | str,
    reference_axis: str,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> AlignedAndConstrainedAxes
```

The optional values for `principal_axis` and `reference_axis` are `"+X"`, `"-X"`, `"+Y"`, `"-Y"`, `"+Z"`, `"-Z"`. This axes system aligns `principal_axis` with the `principal` vector direction while keeping `reference_axis` pointing as close as possible to the `reference` vector direction.

### CZML Axes and Composite Axes

```python
components.czml_axes(
    *,
    epoch: str,
    unit_quaternion_xyzw: Sequence[float],
    central_body: str | None = None,
    interpolation_algorithm: str | None = None,
    interpolation_degree: int | None = None,
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> CzmlAxes

components.composite_axes(
    *,
    intervals: Sequence[EntityAxes],
    name: str | None = None,
    description: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> CompositeAxes
```

`czml_axes` describes attitude using a CZML-style unit quaternion sampled sequence, with quaternion order `xyzw`. `composite_axes` concatenates multiple axes by time interval.

```python
czml_attitude = components.czml_axes(
    epoch="2024-01-01T00:00:00.000Z",
    unit_quaternion_xyzw=[0.0, 0.0, 0.0, 1.0],
    central_body="Earth",
)

piecewise = components.composite_axes(
    intervals=[
        components.vvlh_axes(
            start="2024-01-01T00:00:00.000Z",
            stop="2024-01-01T00:00:20.000Z",
        ),
        camera_axes,
    ],
)
```

## Rotations

Rotation fragments are used for the `rotation` parameter of `fixed_axes`, sensor pointing, and other places that require a small attitude offset.

### Azimuth-Elevation Rotation

```python
components.az_el_rotation(
    *,
    azimuth_deg: float,
    elevation_deg: float,
) -> AzElRotation
```

### Quaternion Rotation

```python
components.quaternion_rotation(
    *,
    scalar: float,
    x: float,
    y: float,
    z: float,
) -> QuaternionRotation
```

Parameters are in scalar-first, vector-last order; the SDK translates them into ASTROX's `QS/QX/QY/QZ` fields.

### Euler Rotation

```python
components.euler_rotation(
    *,
    sequence: str,
    a_deg: float,
    b_deg: float,
    c_deg: float,
) -> EulerRotation
```

`sequence` is a rotation order string, such as `"321"`, `"123"`.

```python
az_el = components.az_el_rotation(azimuth_deg=0.0, elevation_deg=-20.0)
quat = components.quaternion_rotation(scalar=1.0, x=0.0, y=0.0, z=0.0)
euler = components.euler_rotation(sequence="321", a_deg=0.0, b_deg=-20.0, c_deg=0.0)
```

## Vector Geometry Tool VGT

VGT (Vector Geometry Tool) is a collection of named geometry definitions attached to a named entity, used via `entity(..., vgt=...)`. `VgtProvider` is the value object returned by the `vgt(...)` constructor.

```python
components.vgt(
    *,
    axes: Sequence[EntityAxes],
    vectors: Sequence[VgtVector] | None = None,
    points: Sequence[VgtPoint] | None = None,
    systems: Sequence[VgtSystem] | None = None,
    angles: Sequence[VgtAngle] | None = None,
    planes: Sequence[VgtPlane] | None = None,
) -> VgtProvider
```

`axes` is required; the remaining collections are optional. Elements in the collections must provide a `name` so they can be referenced in axis definitions.

### Fixed Vector

```python
components.vgt_fixed_vector(
    *,
    name: str,
    reference_axes: EntityAxes | str,
    direction: VgtDirection,
    description: str | None = None,
) -> VgtFixedVector
```

`direction` is `xyz_direction(...)` or `ra_dec_direction(...)`.

### Points, Systems, Angles, and Planes

```python
components.vgt_point(
    *,
    name: str,
    description: str | None = None,
) -> VgtPoint

components.vgt_system(
    *,
    name: str,
    description: str | None = None,
) -> VgtSystem

components.vgt_angle(
    *,
    name: str,
    from_vector: VgtVector | str,
    to_vector: VgtVector | str,
    description: str | None = None,
) -> VgtAngle

components.vgt_plane(
    *,
    name: str,
    plane_type: str | None = None,
    description: str | None = None,
) -> VgtPlane
```

### Complete Example

```python
body_axes = components.vvlh_axes(name="BodyVVLH")

boresight = components.vgt_fixed_vector(
    name="Boresight",
    reference_axes=body_axes,
    direction=components.xyz_direction(x=0.0, y=0.0, z=1.0),
)

clock = components.vgt_fixed_vector(
    name="Clock",
    reference_axes=body_axes,
    direction=components.xyz_direction(x=1.0, y=0.0, z=0.0),
)

sensor_axes = components.aligned_and_constrained_axes(
    name="AlignedCamera",
    principal=boresight,
    principal_axis="+Z",
    reference=clock,
    reference_axis="+X",
)

observer = components.entity(
    name="Observer",
    position=components.two_body_position(
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
    ),
    vgt=components.vgt(
        axes=[body_axes],
        vectors=[boresight, clock],
    ),
    orientation=sensor_axes,
)
```

## Composing into Access Requests

Component value objects are usually passed directly to `astrox.access.compute` or `astrox.access.chain`:

```python
from astrox import access, components

satellite = components.entity(
    name="ISS",
    position=components.sgp4_position(tle_lines=ISS_TLE),
)

ground = components.entity(
    name="Ground",
    position=components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    from_entity=ground,
    to_entity=satellite,
    step_s=600.0,
)
```

Full examples are in `examples/04_access/compute.py`, `constraints.py`, `custom_axes.py`, `sensor_pointing.py`, and `chain.py`. The semantics and return values of access computations are described in the [access manual](../access/README.md).

## Conventions

- Optional parameters are not sent to ASTROX when not provided; the server retains default values.
- `EntityAxes` and `VgtVector` objects referenced by other axes or VGT definitions must provide a `name`.
- `az_el_mask_constraint`'s `az_el_mask_rad` is in radians and is only valid for `SitePosition`.
- `range_constraint` uses kilometers; elevation and exclusion angle constraints use degrees.
- `quaternion_rotation` uses the scalar-first Python parameter order.
