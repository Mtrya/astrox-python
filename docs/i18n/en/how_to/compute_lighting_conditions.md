# Compute lighting conditions

This page solves a specific task: within a given time window, compute sunlight/penumbra/umbra intervals, solar intensity samples, and solar azimuth-elevation-range (AER) samples for a position source.

## Two decisions to make

1. **Choose the position source**: are you looking at a satellite or a ground station?
   - Ground station → use `components.site_position(...)` to give longitude, latitude, and altitude.
   - Satellite → use `components.sgp4_position(...)` to pass a two-line element set (TLE), or a propagated position source such as `j2_position` or `two_body_position`.
2. **Choose the output type**:
   - For sunlight/penumbra/umbra intervals → use `lighting.lighting_times(...)`.
   - For time-sampled solar intensity → use `lighting.solar_intensity(...)`.
   - For solar AER samples → use `lighting.solar_aer(...)`.

These three functions accept an `astrox.components` position source directly as the `position` argument; you do not need to wrap it in a `components.entity(...)` named object first.

## Complete example

The script below demonstrates satellite lighting intervals together with ground-station solar intensity and solar AER. Save it as `compute_lighting_conditions.py`:

```python
import astrox
from astrox import components, lighting

astrox.configure(base_url="http://astrox.cn:8765")

ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

site = components.site_position(
    longitude_deg=-155.468,
    latitude_deg=19.821,
    height_m=4205.0,
)

iss = components.sgp4_position(tle_lines=ISS_TLE)

intervals = lighting.lighting_times(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T06:00:00.000Z",
    position=iss,
    occultation_bodies=["Earth", "Moon"],
)

intensity = lighting.solar_intensity(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T06:00:00.000Z",
    position=site,
    step_s=900.0,
)

aer = lighting.solar_aer(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T06:00:00.000Z",
    position=site,
    step_s=900,
)

print("=== ISS 光照区间 ===")
for name in ("SunLight", "Penumbra", "Umbra"):
    data = intervals[name]
    print(f"{name}: {len(data['Intervals'])} 段，总时长 {data['TotalDuration']:.1f} s")

print("\n=== 地面站太阳辐射强度（前 3 个采样） ===")
for sample in intensity["Datas"][:3]:
    print(
        f"  {sample['Time']}: Intensity={sample['Intensity']:.3f}, "
        f"PercentShadow={sample['PercentShadow']:.3f}"
    )

print("\n=== 地面站太阳 AER（前 3 个采样） ===")
for sample in aer["Datas"][:3]:
    print(
        f"  {sample['Time']}: "
        f"Azimuth={sample['Azimuth']:.3f} deg, "
        f"Elevation={sample['Elevation']:.3f} deg, "
        f"Range={sample['Range']:.1f} km"
    )
```

## Run

```bash
python compute_lighting_conditions.py
```

## Actual output

```text
=== ISS 光照区间 ===
SunLight: 5 段，总时长 13131.7 s
Penumbra: 8 段，总时长 73.0 s
Umbra: 4 段，总时长 8395.3 s

=== 地面站太阳辐射强度（前 3 个采样） ===
  2024-01-01T00:00:00.000Z: Intensity=1.000, PercentShadow=0.000
  2024-01-01T00:15:00.000Z: Intensity=1.000, PercentShadow=0.000
  2024-01-01T00:30:00.000Z: Intensity=1.000, PercentShadow=0.000

=== 地面站太阳 AER（前 3 个采样） ===
  2024-01-01T00:00:00.000Z: Azimuth=209.548 deg, Elevation=41.253 deg, Range=147098121.7 km
  2024-01-01T00:15:00.000Z: Azimuth=213.376 deg, Elevation=39.412 deg, Range=147098260.4 km
  2024-01-01T00:30:00.000Z: Azimuth=216.934 deg, Elevation=37.381 deg, Range=147098420.2 km
```

## What just happened

`lighting.lighting_times` sends a request to `/Lighting/LightingTimes` and returns the raw ASTROX response dict, containing the keys `SunLight`, `Penumbra`, and `Umbra`. Under each key there is an `Intervals` list plus statistics such as `TotalDuration` and `MeanDuration`. `occultation_bodies=["Earth", "Moon"]` tells the computation to account for Earth and Moon occlusion; this parameter is usually not needed for ground-station lighting calculations.

`lighting.solar_intensity` returns a `Datas` list sampled at `step_s`; each element contains `Time`, `Intensity` (fraction of the solar disk visible, where `1` means fully visible), `PercentShadow` (occluded fraction), and other fields. `step_s` is in seconds.

`lighting.solar_aer` also returns a `Datas` list sampled at `step_s`; each element contains `Time`, `Azimuth` (azimuth angle, degrees), `Elevation` (elevation angle, degrees), and `Range` (distance, kilometers).

None of these three functions parse or wrap the response structure inside the SDK; they return the raw ASTROX response dict directly.

## Next steps

- If you only need the enter/exit eclipse times for a particular satellite, replace the `position` in the example with `sgp4_position(...)` or `j2_position(...)`; the rest of the call stays the same.
- For full parameters of the lighting functions, optional azimuth-elevation mask data (`az_el_mask_data`), occultation body lists, and more, see the [lighting manual](../manual/lighting/README.md).
- For the full list of position-source constructors, see the [components manual](../manual/components/README.md).
- For verification status, known residuals, and cross-validation evidence for each branch, see the [Lighting validation page](../../../validation/lighting.md).
