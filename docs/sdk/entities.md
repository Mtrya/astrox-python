# Entities

This page documents the reusable ASTROX Python entity and position-source vocabulary. The intended import style is:

```python
from astrox import entities
```

ASTROX uses object-like schemas for spacecraft, sites, sensors, and other analysis objects. The Python SDK keeps the reusable parts of that vocabulary in `astrox.entities`.

## Position Sources

Most spatial workflows start from a position source. A position source describes where an object is over time, without adding a name or object metadata.

Create a fixed geodetic site:

```python
site = entities.site_position(
    longitude_deg=-155.468,
    latitude_deg=19.821,
    height_m=4205.0,
)
```

Create an SGP4 position source from two-line element data:

```python
iss = entities.sgp4_position(
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

j2_position = entities.j2_position(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
)

two_body_position = entities.two_body_position(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
)
```

Create a CZML-like sampled position source when you already have sampled position or position-velocity data:

```python
sampled_position = entities.czml_position(
    epoch="2024-01-01T00:00:00.000Z",
    reference_frame="INERTIAL",
    cartesian_velocity=[
        0.0, 6114454.0, 2870352.0, 3308542.0, -3548.0, 6463.0, 1830.0,
        900.0, 1200000.0, 6500000.0, 2500000.0, -7200.0, 1500.0, 1200.0,
    ],
)
```

Optional ASTROX defaults are omitted unless you supply them. For example, `site_position(...)` does not send `CentralBody` unless `central_body` is provided.

## Sensors

Create basic sensor metadata with conic or rectangular sensor constructors:

```python
camera = entities.conic_sensor(
    outer_half_angle_deg=30.0,
)

rectangular_sensor = entities.rectangular_sensor(
    x_half_angle_deg=5.0,
    y_half_angle_deg=10.0,
)
```

These values are metadata fragments. They are useful when an ASTROX workflow accepts a named object with an attached sensor.

## Named Entities

Use `entities.entity(...)` when an ASTROX workflow asks for a named analysis object:

```python
satellite = entities.entity(
    name="ISS",
    position=iss,
    sensor=camera,
    description="Representative spacecraft",
)
```

An entity is a position source plus object metadata such as name, description, and sensor. Some ASTROX routes accept only a position source rather than a full named object. For example, lighting functions consume position sources directly because the server schema asks for `Position` or `sitePosition`.

Use `to_wire()` only when you need to inspect the ASTROX request fragment. Ordinary SDK calls accept the SDK value objects directly.
