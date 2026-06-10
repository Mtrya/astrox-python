# Lighting

This page documents the curated ASTROX Python lighting interface. The intended import style is:

```python
from astrox import entities, lighting
```

The lighting functions compute sunlight intervals, solar intensity samples, and solar azimuth/elevation/range samples. They use the position-source values from `astrox.entities`.

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

`lighting.solar_intensity(...)` computes sampled solar visibility for a position source. Each sample includes `Intensity`, where `1` means the solar disk is fully visible and `0` means fully blocked, and `PercentShadow`, the blocked fraction of the solar disk.

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

Site-position samples include the Sun azimuth/elevation/range fields returned by ASTROX. Those site angles are the light-delay-only solar direction used by the intensity calculation. For direct apparent topocentric Sun angles at a site, use `solar_aer(...)`.

## Solar AER

`lighting.solar_aer(...)` computes solar azimuth, elevation, and range samples for a position source. For fixed sites, azimuth is in the local horizontal plane with north as `0 deg` and positive eastward; elevation is the angle to the local horizontal plane, positive toward zenith. For spacecraft positions, azimuth is in VVLH front/right/down axes with forward as `0 deg` and positive toward right; elevation is the angle to the VVLH `xy` plane, positive toward zenith.

```python
aer = lighting.solar_aer(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    position=site,
    step_s=900,
)
```

`solar_aer(...)` accepts the promoted position-source values from `astrox.entities`, not a full named entity. The route now requires the same typed `Position` envelope used by `lighting_times(...)` and `solar_intensity(...)`.

## Position Sources

`lighting_times(...)`, `solar_intensity(...)`, and `solar_aer(...)` accept the promoted position-source values from `astrox.entities`: fixed sites, SGP4 TLE positions, J2 and two-body Keplerian positions, and CZML-like sampled positions.

Lighting functions currently return ASTROX JSON-like response dictionaries. The SDK assembles the Pythonic request shape and leaves the response envelope visible.
