# Components

This page documents the reusable ASTROX Python component and entity vocabulary. The intended import style is:

```python
from astrox import components
```

ASTROX uses object-like schemas for spacecraft, sites, sensors, and other analysis objects. The Python SDK keeps the reusable parts of that vocabulary in `astrox.components`.

## Position Sources

Most spatial workflows start from a position source. A position source describes where an object is over time, without adding a name or object metadata.

Create a fixed geodetic site:

```python
site = components.site_position(
    longitude_deg=-155.468,
    latitude_deg=19.821,
    height_m=4205.0,
)
```

Create an SGP4 position source from two-line element data:

```python
iss = components.sgp4_position(
    tle_lines=(
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
        "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    ),
)
```

Create J2 or two-body position sources from Classical Keplerian elements:

```python
from astrox import orbits

orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=15.0,
    true_anomaly_deg=45.0,
)

j2_position = components.j2_position(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
)

two_body_position = components.two_body_position(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
)
```

Create a CZML-like sampled position source when you already have sampled position or position-velocity data:

```python
sampled_position = components.czml_position(
    epoch="2024-01-01T00:00:00.000Z",
    reference_frame="INERTIAL",
    cartesian_velocity=[
        0.0, 6114454.0, 2870352.0, 3308542.0, -3548.0, 6463.0, 1830.0,
        900.0, 1200000.0, 6500000.0, 2500000.0, -7200.0, 1500.0, 1200.0,
    ],
)
```

Create a composite CZML-like position source when ASTROX expects a sequence of sampled position blocks:

```python
track = components.czml_positions([sampled_position])
```

Create propagated or special position sources for workflows that need reusable position components:

```python
central_body = components.central_body_position("Sun")

hpop_position = components.hpop_position(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
)

ascent_position = components.simple_ascent_position(
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

ballistic_position = components.ballistic_position(
    start="2024-01-01T00:00:00.000Z",
    ballistic_type="DeltaV",
    ballistic_type_value=5000.0,
)
```

Optional ASTROX defaults are omitted unless you supply them. For example, `site_position(...)` does not send `CentralBody` unless `central_body` is provided.

## Attitude Axes

Use entity attitude axes when an ASTROX workflow needs an object's body frame or a named coordinate frame. The access validation matrix calibrates these axes through sensor-constrained access intervals against an independent two-body, WGS84 obstruction, and field-of-view oracle.

The recommended built-in axes are:

```python
body_vvlh = components.vvlh_axes()
body_lvlh = components.lvlh_axes()
body_vnc = components.vnc_axes()
```

Current cross-validation establishes the following ASTROX conventions for generic axes and the `relative_to="Earth"` / `relative_to="CBF"` variants:

| Constructor | Calibrated axis convention |
| --- | --- |
| `components.vvlh_axes(...)` | `+Z` points nadir, `+X` is along-track velocity projected into the local horizontal plane, and `+Y` completes the right-side frame |
| `components.lvlh_axes(...)` | `+X` is radial outward, `+Z` is orbit angular momentum, and `+Y` is the in-track axis from `Z x X` |
| `components.vnc_axes(...)` | `+X` follows inertial velocity, `+Y` follows orbit angular momentum, and `+Z` completes the right-handed triad |

`relative_to="Moon"`, `"Mars"`, and `"Sun"` remain calibrated only as unresolved validation cases. The live calls and Skyfield body-vector probes are recorded under `tests/validation/cross_validation/access/`, but the SDK documentation does not recommend those variants as understood semantics yet.

Use `fixed_axes(...)` to rotate a body frame relative to a calibrated reference frame:

```python
camera_axes = components.fixed_axes(
    reference_axes="VVLH",
    rotation=components.euler_rotation(
        sequence="321",
        a_deg=0.0,
        b_deg=-20.0,
        c_deg=0.0,
    ),
)
```

`fixed_axes(...)` is cross-validated for built-in `VVLH`, `LVLH`, and `VNC` references with Euler and quaternion rotations. `fixed_at_epoch_axes(...)` is cross-validated for freezing `VVLH` and `LVLH` source axes into `ICRF` at multiple epochs, and `composite_axes(...)` is cross-validated for piecewise interval composition:

```python
frozen = components.fixed_at_epoch_axes(
    source_axes=components.vvlh_axes(),
    reference_axes="ICRF",
    epoch="2024-01-01T00:00:00.000Z",
)

piecewise = components.composite_axes(
    intervals=[
        components.vvlh_axes(start="2024-01-01T00:00:00.000Z", stop="2024-01-01T00:00:20.000Z"),
        camera_axes,
    ],
)
```

Do not treat every ASTROX reference-name spelling as calibrated. Fixed axes relative to `ICRF` / `J2000` / inertial and fixed-name variants are still strict unresolved validation cases: live intervals do not match the bounded inertial or Earth-fixed frame candidates, and some names fail before semantic output.

`czml_axes(...)` is available for ASTROX CZML-like sampled attitude input:

```python
identity_axes = components.czml_axes(
    epoch="2024-01-01T00:00:00.000Z",
    unit_quaternion_xyzw=[
        0.0, 0.0, 0.0, 0.0, 1.0,
        60.0, 0.0, 0.0, 0.0, 1.0,
    ],
    central_body="Earth",
    interpolation_algorithm="LINEAR",
    interpolation_degree=1,
)
```

Current validation only recommends short-span sampled identity quaternions as calibrated. Constant arrays, long-span sampled identity, non-identity sampled quaternions, component order/sign behavior, and fixed-coordinate interpretation remain unresolved after bounded probes. Keep CZML attitude use close to server examples or treat it as an advanced raw-surface escape hatch until upstream conventions are clarified.

## Sensor Pointing and Sensors

Create basic sensor metadata with conic or rectangular sensor constructors:

```python
camera = components.conic_sensor(
    outer_half_angle_deg=30.0,
)

rectangular_sensor = components.rectangular_sensor(
    x_half_angle_deg=5.0,
    y_half_angle_deg=10.0,
)
```

Conic `outer_half_angle_deg` is calibrated as the half-angle around the sensor boresight. Rectangular `x_half_angle_deg` and `y_half_angle_deg` are calibrated as independent X/Z and Y/Z angular limits in the sensor camera axes.

Attach sensor pointing with `fixed_sensor_pointing(...)`:

```python
nadir_camera = components.entity(
    name="Observer",
    position=two_body_position,
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
```

Quaternion and Euler fixed sensor pointing are calibrated as active rotations of the local `+Z` boresight. The SDK uses scalar-first Python arguments for quaternions and lowers them to ASTROX `QS`, `QX`, `QY`, `QZ` fields. Euler sequences `321`, `123`, and `213` are cross-validated for representative single-axis rotations.

`az_el_rotation(...)` has a different calibrated meaning from quaternion or Euler fragments. For sensor pointing, ASTROX treats Az/El as a direct boresight vector in the parent axes: azimuth rotates from `+X` toward `+Y`, and elevation raises toward `+Z`. It is not equivalent to applying a quaternion or Euler rotation to the `+Z` boresight.

```python
along_track_camera = components.fixed_sensor_pointing(
    rotation=components.az_el_rotation(
        azimuth_deg=0.0,
        elevation_deg=0.0,
    ),
)
```

## VGT Orientation Helpers

VGT definitions are advanced ASTROX name-reference objects attached to an entity through `components.vgt(...)`. The calibrated public path is `vgt_fixed_vector(...)` plus `aligned_and_constrained_axes(...)`, validated against a local TRIAD-style vector-alignment derivation:

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
    principal=boresight,
    principal_axis="+Z",
    reference=clock,
    reference_axis="+X",
)

observer = components.entity(
    name="Observer",
    position=two_body_position,
    vgt=components.vgt(
        axes=[body_axes],
        vectors=[boresight, clock],
    ),
    orientation=sensor_axes,
)
```

No-space custom VGT axes names and string references are calibrated for the validated cases. Names containing spaces remain unresolved because the live service reports that the named axes cannot be found. Empty `Axes`, `Vectors`, `Angles`, `Planes`, `Points`, and `Systems` provider collections are pass-through containers in the calibrated VGT access cases, but non-empty `Points` and `Systems` currently return server errors before semantic output; keep them out of recommended examples until upstream behavior is clarified.

## Named Entities

Use `components.entity(...)` when an ASTROX workflow asks for a named analysis object:

```python
satellite = components.entity(
    name="ISS",
    position=iss,
    sensor=camera,
    description="Representative spacecraft",
)
```

An entity is a position source plus object metadata such as name, description, and sensor. Some ASTROX routes accept only a position source rather than a full named object. For example, lighting functions consume position sources directly because the server schema asks for `Position` or `sitePosition`.

## Constraints

Attach shared ASTROX constraints to an entity through the `constraints` argument of `components.entity(...)`:

```python
ground = components.entity(
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
```

The supported constraint constructors are:

- `components.elevation_constraint(minimum_deg=..., maximum_deg=..., maximum_enabled=..., text=...)` lowers to an ASTROX `ElevationAngle` constraint. Values are in degrees. `maximum_deg` is only forwarded when `maximum_enabled=True` is also supplied.
- `components.range_constraint(minimum_km=..., maximum_km=..., maximum_enabled=..., text=...)` lowers to an ASTROX `Range` constraint. Values are in kilometers. `maximum_km` is only forwarded when `maximum_enabled=True` is also supplied.
- `components.az_el_mask_constraint(az_el_mask_rad=..., max_range_km=..., text=...)` lowers to an ASTROX `AzElMask` constraint. `az_el_mask_rad` is a flat sequence of alternating azimuth and elevation samples in radians.

Omitted optional fields are left out of the request so that ASTROX server defaults remain owned by the server. Raw constraint dictionaries are rejected at the public boundary; pass SDK-owned constraint values instead.

```python
components.entity(
    name="Ground",
    position=components.site_position(longitude_deg=0.0, latitude_deg=0.0, height_m=0.0),
    constraints=[
        # AzEl masks are only meaningful for SitePosition participants.
        components.az_el_mask_constraint(
            az_el_mask_rad=[
                0.0, 0.17453292519943295,
                1.5707963267948966, 0.17453292519943295,
                3.141592653589793, 0.17453292519943295,
                4.71238898038469, 0.17453292519943295,
            ],
        ),
    ],
)
```

Access workflows carry entity constraints through `FromObjectPath` and `ToObjectPath` automatically. The SDK does not add a separate `constraints=` argument to `access.compute(...)` because constraints are participant metadata on `Entity`.

Current cross-validation in `tests/validation/cross_validation/access/test_compute_constraints_skyfield.py` calibrates these constraints against independent Skyfield/WGS84 topocentric geometry. Verified behavior for representative fixed-site to SGP4 and SGP4-to-fixed-site cases includes elevation and range limits in the participant's local topocentric frame, geometric range evaluation even with light-time delay enabled, intersection semantics for multiple constraints and both-participant constraints, evaluation of satellite-side elevation and range constraints in the satellite's Earth-fixed geodetic local frame, piecewise-linear AzEl mask interpolation in azimuth with 0/360 closure, and the site-only validity of AzEl masks. `AzElMask.MaxRange` is forwarded but not enforced by ASTROX. Supplying `minimum > maximum` while `maximum_enabled=True` raises a server validation error; ordered but impossible thresholds return empty passes.

## Entity Groups

Use `components.entity_group(...)` when an ASTROX workflow accepts a named group of entities:

```python
targets = components.entity_group(
    name="Targets",
    members=[satellite],
    to_restriction="AnyOf",
)
```

`EntityGroup` is an SDK-owned value object for composing grouped entities. The SDK lowers it to ASTROX `EntityPathGroup` wire shape, but server behavior for a given endpoint still belongs to that endpoint and its validation evidence.

Use `to_wire()` only when you need to inspect the ASTROX request fragment. Ordinary SDK calls accept the SDK value objects directly.
