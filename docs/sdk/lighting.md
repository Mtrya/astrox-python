# Lighting

This page documents the curated ASTROX Python lighting interface. The intended import style is:

```python
from astrox import entities, lighting
```

The lighting functions compute sunlight intervals, solar intensity samples, and site-based solar azimuth/elevation/range samples. They use the position-source values from `astrox.entities`.

## Lighting Times

`lighting.lighting_times(...)` computes sunlight, penumbra, and umbra intervals for a position source.

```python
iss = entities.sgp4_position(
    tle_lines=(
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
        "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    ),
)

intervals = lighting.lighting_times(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    position=iss,
    occultation_bodies=["Earth", "Moon"],
)
```

The return value is the ASTROX JSON-like response dictionary. `SunLight`, `Penumbra`, and `Umbra` contain interval and duration data when ASTROX returns them.

## Solar Intensity

`lighting.solar_intensity(...)` computes solar intensity samples for a position source.

```python
site = entities.site_position(
    longitude_deg=-155.468,
    latitude_deg=19.821,
    height_m=4205.0,
)

intensity = lighting.solar_intensity(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    position=site,
    step_s=900.0,
)
```

For site positions, `az_el_mask_data` can be supplied as an alternating azimuth/elevation mask array in radians. `occultation_bodies` can be supplied when you want to override the server's occulting-body defaults.

## Solar AER

`lighting.solar_aer(...)` computes solar azimuth, elevation, and range samples for a fixed site.

```python
aer = lighting.solar_aer(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    site_position=site,
    step_s=900,
)
```

`solar_aer(...)` accepts `site_position=entities.site_position(...)`, not a full named entity. The server schema for this route is site-specific.

## Position Sources

`lighting_times(...)` and `solar_intensity(...)` accept the promoted position-source values from `astrox.entities`: fixed sites, SGP4 TLE positions, J2 and two-body Keplerian positions, and CZML-like sampled positions.

Lighting functions currently return ASTROX JSON-like response dictionaries. The SDK assembles the Pythonic request shape and leaves the response envelope visible.
