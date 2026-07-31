# Lighting

`astrox.lighting` computes lighting times, solar intensity samples, and solar azimuth-elevation-range (AER) samples for a position source. Import it as follows:

```python
from astrox import components, lighting
```

The lighting functions themselves do not define orbits or positions; they consume position sources from `astrox.components`. Position sources that can be used for lighting calculations include fixed ground sites, SGP4 two-line element set (TLE) positions, J2/two-body Keplerian positions, and CZML sampled positions. For how to construct position sources, see the [components manual](../components/README.md).

## Return values

All three functions in `astrox.lighting` return the raw ASTROX response dict directly, without parsing or wrapping. Callers read results by field name:

- `lighting_times(...)` returns a dict containing keys such as `SunLight`, `Penumbra`, and `Umbra`.
- `solar_intensity(...)` returns a dict containing a `Datas` list whose elements are sample points.
- `solar_aer(...)` returns a dict containing a `Datas` list whose elements are `Time`, `Azimuth`, `Elevation`, and `Range`.

For full control over the request or response, use `astrox.raw.post` directly.

## Lighting times

### `lighting.lighting_times`

```python
lighting.lighting_times(
    *,
    start: str,
    stop: str,
    position: components.EntityPosition,
    description: str | None = None,
    az_el_mask_data: Sequence[float] | None = None,
    occultation_bodies: Sequence[str] | None = None,
) -> dict[str, Any]
```

Computes the sunlight, penumbra, and umbra intervals for the specified position source between `start` and `stop`.

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Start time string |
| `stop` | — | Stop time string |
| `position` | — | `astrox.components` position source |
| `description` | — | Description text |
| `az_el_mask_data` | rad | Azimuth-elevation mask data, interleaved |
| `occultation_bodies` | — | List of occulting body names, e.g. `["Earth", "Moon"]` |

Main fields in the returned dict:

| Field | Description |
| --- | --- |
| `SunLight` | Sunlight intervals, including `Intervals`, `TotalDuration`, `MeanDuration`, `MinDuration`, `MaxDuration` |
| `Penumbra` | Penumbra intervals and statistics |
| `Umbra` | Umbra intervals and statistics |

```python
iss = components.sgp4_position(
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

print(f"ISS sunlight intervals: {len(intervals['SunLight']['Intervals'])}")
```

A complete runnable example is in `examples/03_lighting/lighting.py`.

## Solar intensity

### `lighting.solar_intensity`

```python
lighting.solar_intensity(
    *,
    start: str,
    stop: str,
    position: components.EntityPosition,
    description: str | None = None,
    az_el_mask_data: Sequence[float] | None = None,
    step_s: float | None = None,
    occultation_bodies: Sequence[str] | None = None,
) -> dict[str, Any]
```

Computes solar intensity samples for the specified position source between `start` and `stop`. Each sample point contains fields such as `Intensity` (fraction of the solar disk visible, `1` for fully visible and `0` for fully occluded) and `PercentShadow` (occluded fraction).

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Start time string |
| `stop` | — | Stop time string |
| `position` | — | `astrox.components` position source |
| `description` | — | Description text |
| `az_el_mask_data` | rad | Azimuth-elevation mask data, interleaved |
| `step_s` | s | Sample step size |
| `occultation_bodies` | — | List of occulting body names |

Elements of the returned dict's `Datas` list typically contain fields such as `Time`, `Intensity`, `PercentShadow`, `CurrentCondition`, `Obstruction`, and `ApparentSolarRange`.

```python
site = components.site_position(
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

first = intensity["Datas"][0]
print(
    f"First site intensity sample: "
    f"{first['Intensity']:.3f} visible, "
    f"{first['PercentShadow']:.3f} shadow"
)
```

A complete runnable example is in `examples/03_lighting/lighting.py`.

## Solar AER

### `lighting.solar_aer`

```python
lighting.solar_aer(
    *,
    start: str,
    stop: str,
    position: components.EntityPosition,
    text: str | None = None,
    step_s: int | None = None,
) -> dict[str, Any]
```

Computes solar azimuth-elevation-range (AER) samples for the specified position source between `start` and `stop`.

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Start time string |
| `stop` | — | Stop time string |
| `position` | — | `astrox.components` position source |
| `text` | — | Text label |
| `step_s` | s | Sample step size |

Elements of the returned dict's `Datas` list contain `Time`, `Azimuth`, `Elevation`, and `Range` fields, with units of time string, degrees, degrees, and kilometers, respectively.

```python
aer = lighting.solar_aer(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:30:00.000Z",
    position=site,
    step_s=900,
)

first = aer["Datas"][0]
print(
    f"First site solar AER sample: "
    f"az={first['Azimuth']:.3f} deg, "
    f"el={first['Elevation']:.3f} deg, "
    f"range={first['Range']:.1f} km"
)
```

A complete runnable example is in `examples/03_lighting/lighting.py`.

## Input type notes

All three functions accept an `astrox.components` position source as the `position` argument. They do not accept raw dicts or full `components.entity(...)` named objects. Optional parameters such as `az_el_mask_data` and `occultation_bodies` are only sent to ASTROX when provided.

## Conventions

- Time strings use ISO 8601 format, e.g. `2024-01-01T00:00:00.000Z`.
- `az_el_mask_data` is in radians and interleaved as `[az1, el1, az2, el2, ...]`.
- The `Azimuth` and `Elevation` returned by `solar_aer` are in degrees, and `Range` is in kilometers.
