# Terrain Masks

`astrox.terrain` provides site terrain-mask (azimuth-elevation mask) query APIs: it requests the server-computed terrain mask data around a site over 360 degrees of azimuth. The server describes this data as the maximum elevation angle occluded by terrain at each azimuth and distance; the SDK only constructs requests and returns raw responses, and does not perform physical-semantic validation of these values. The recommended import style is:

```python
from astrox import components, terrain
```

This page is organized by concepts, the configuration object, the full mask, and the simple mask. Both query functions send HTTP POST requests through `astrox.raw.post` and return ASTROX raw JSON response dictionaries without typed response parsing. Server terrain data supports Earth, Moon, Mars, and the lunar south pole (server documentation); when the mask input does not provide a `TerrainMaskConfig`, the server uses its default configuration (appsettings.json), which depends on the server deployment and may fail, so passing an explicit configuration is recommended (see the example below).

## Concepts

A terrain-mask response describes azimuth-elevation data around a fixed ground site. The SDK provides two routes with the same request and different response structures:

- `terrain.azimuth_elevation_mask`: full response, one record per azimuth with per-distance detail entries.
- `terrain.azimuth_elevation_mask_simple`: simplified response, a flat numeric array with alternating azimuth and elevation values.

The site position uses `components.site_position` from the [components manual](../components/README.md); the server performs mask computation for lunar polar sites with a polar DEM file (e.g. `Moon_LDEM_80s_20m`).

## Mask configuration

### `terrain.TerrainMaskConfig`

```python
terrain.TerrainMaskConfig(
    *,
    text: str | None = None,
    terrain_server_url: str | None = None,
    flag_pole: int | None = None,
    polar_dem_file_name: str | None = None,
    terrain_zoom_level: int | None = None,
    step_size_m: float | None = None,
    max_search_range_km: float | None = None,
) -> TerrainMaskConfig
```

Server terrain-source and sampling configuration, an immutable (frozen) named dataclass. `to_wire()` returns the ASTROX `TerrainMaskConfig` request fragment; fields that are not supplied do not appear in the fragment.

| Field | Wire key | Unit | Description |
| --- | --- | --- | --- |
| `text` | `Text` | — | Configuration description |
| `terrain_server_url` | `TerrainServerUrl` | — | Terrain service URL (full stkTerrainServer path, up to before layer.json) |
| `flag_pole` | `FlagPole` | — | Terrain projection type: `0` for 4326, `1` for the south pole, `-1` for the north pole; the server documentation notes this parameter is currently ineffective |
| `polar_dem_file_name` | `PolarDemFileName` | — | Polar DEM file name; when non-empty it takes precedence over `terrain_server_url`, currently supports only lunar polar DEMs, typical name `Moon_LDEM_80s_20m` |
| `terrain_zoom_level` | `TerrainZoomLevel` | — | Maximum terrain level, `-1` for automatic; ineffective when lunar polar tif data is used directly |
| `step_size_m` | `StepSize` | m | Step size for computation in a direction, server default 30 m |
| `max_search_range_km` | `MaxSearchRange` | km | Maximum search distance in a direction, server default 15 km |

```python
config = terrain.TerrainMaskConfig(
    text="terrain example",
    terrain_server_url="",
    flag_pole=1,
    polar_dem_file_name="Moon_LDEM_80s_20m",
    terrain_zoom_level=-1,
    step_size_m=30.0,
    max_search_range_km=15.0,
)
```

## Full mask

### `terrain.azimuth_elevation_mask`

```python
terrain.azimuth_elevation_mask(
    *,
    site_position: components.SitePosition,
    config: TerrainMaskConfig | None = None,
    text: str | None = None,
) -> dict[str, Any]
```

Requests the full terrain mask for a site and returns a raw JSON response dictionary.

| Parameter | Wire key | Description |
| --- | --- | --- |
| `site_position` | `sitePosition` | Mask computation point, a `SitePosition` value built with `components.site_position` |
| `config` | `TerrainMaskPara` | Mask computation parameters; when omitted, the server uses its default configuration |
| `text` | `Text` | Request description |

The response contains `IsSuccess`, `Message`, `sitePosition` (echo of the request position) and `AzElMaskData`. `AzElMaskData` is an array of records with keys `Azimuth` (azimuth, rad), `Elevation` (elevation value, rad), and `Items` (per-distance detail array); each `Items` entry contains `Distance` (distance from the center point, m) and `Elevation` (elevation value at that distance, rad). The server documentation describes these elevation values as the maximum elevation angle occluded by terrain at the corresponding azimuth/distance. With the lunar polar configuration shown in this page's example, the server returns 361 azimuth entries and azimuth increases monotonically from 0 to 2π.

```python
site = components.site_position(
    longitude_deg=0.0,
    latitude_deg=-89.0,
    height_m=0.0,
    central_body="Moon",
)

full = terrain.azimuth_elevation_mask(site_position=site, config=config)

print(f"Full mask: {full['IsSuccess']}, {len(full['AzElMaskData'])} azimuth entries")
print(f"First full entry: {full['AzElMaskData'][0]}")
```

## Simple mask

### `terrain.azimuth_elevation_mask_simple`

```python
terrain.azimuth_elevation_mask_simple(
    *,
    site_position: components.SitePosition,
    config: TerrainMaskConfig | None = None,
    text: str | None = None,
) -> dict[str, Any]
```

Requests the simplified terrain mask for a site and returns a raw JSON response dictionary. The request parameters are the same as `azimuth_elevation_mask`; the request is sent to the `/Terrain/AzElMaskSimple` route.

```python
simple = terrain.azimuth_elevation_mask_simple(site_position=site, config=config)

print(f"Simple mask: {simple['IsSuccess']}, {len(simple['AzElMaskData']) // 2} azimuth-elevation pairs")
```

The `AzElMaskData` field of the response is a flat numeric array alternating as `[azimuth1, elevation1, azimuth2, elevation2, ...]`, all in rad. With the lunar polar configuration shown in this page's example, the server returns 722 values, i.e. 361 azimuth-elevation pairs; the simple response and the full response carry the same azimuth-elevation values.

## Convention notes

- The example on this page passes an explicit lunar polar configuration with `terrain_server_url=""` (empty string) and `polar_dem_file_name="Moon_LDEM_80s_20m"`.
- `Azimuth`, `Elevation`, and the simple-array values are in rad; `Items[].Distance` is in m.
- When `TerrainMaskPara` is omitted, the server uses its default configuration (appsettings.json), which depends on the server deployment and may fail.
- Validation evidence is recorded on the [terrain validation page](../../../../validation/terrain.md).

A complete runnable example is available at `examples/12_terrain/terrain_masks.py`.

## Error handling

When an ASTROX call fails, the functions in this module raise the corresponding exception from `astrox.exceptions`:

- `astrox.exceptions.AstroxAPIError`: ASTROX returns an unsuccessful response (e.g. `IsSuccess` is false).
- `astrox.exceptions.AstroxHTTPError`: ASTROX returns an unsuccessful HTTP status code.
- `astrox.exceptions.AstroxTimeoutError`: the request times out.
- `astrox.exceptions.AstroxConnectionError`: connecting to ASTROX fails.

The SDK does not rewrite server error messages. When you need full control over the request payload or want to handle the raw response, use `astrox.raw.post`.
