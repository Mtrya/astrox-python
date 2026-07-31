# Rocket

`astrox.rocket` provides public APIs for rocket trajectory and landing analysis. The current module exposes only one function, `landing_zone`, which calculates the geographic coordinates of a landing zone boundary from the launch point, impact point, and local offsets.

Import it as follows:

```python
from astrox import rocket
```

## Landing Zone

### `rocket.landing_zone`

```python
rocket.landing_zone(
    *,
    launch_longitude_deg: float,
    launch_latitude_deg: float,
    launch_height_m: float,
    impact_longitude_deg: float,
    impact_latitude_deg: float,
    impact_height_m: float,
    zone_xys_km: Sequence[float],
) -> dict[str, Any]
```

Calculates the geographic coordinates of landing-zone boundary vertices from the launch point, impact point, and local downrange/crossrange offsets. Downrange is along the launch-to-impact direction; crossrange is perpendicular to it.

| Parameter | Unit | Description |
| --- | --- | --- |
| `launch_longitude_deg` | deg | Launch point longitude |
| `launch_latitude_deg` | deg | Launch point latitude |
| `launch_height_m` | m | Launch point height |
| `impact_longitude_deg` | deg | Impact point longitude |
| `impact_latitude_deg` | deg | Impact point latitude |
| `impact_height_m` | m | Impact point height |
| `zone_xys_km` | km | Flattened sequence of local offsets, given in pairs as `[+X1, +Y1, +X2, +Y2, ...]` |

`zone_xys_km` must contain an even number of values; if odd, `rocket.landing_zone` raises `ValueError`. If a non-numeric sequence is passed, it raises `TypeError`.

## Return Value

`rocket.landing_zone` returns the raw ASTROX response dictionary without parsing or rewriting the response body. A typical response contains the following fields:

| Field | Description |
| --- | --- |
| `IsSuccess` | Boolean indicating whether the request succeeded |
| `Message` | Message string returned by the server |
| `cartographicDegrees` | Flattened boundary-vertex array in `[longitude, latitude, height, ...]` order, with units deg/deg/m |

## Conventions

In `zone_xys_km`, `+X` is along the launch-to-impact direction and `+Y` is perpendicular to it, in pair order `[+X1, +Y1, +X2, +Y2, ...]`. The returned `cartographicDegrees` is flattened in `[longitude, latitude, height, ...]` order.

## Example

The following example matches `examples/05_rocket/landing_zone.py`:

```python
from astrox import rocket


result = rocket.landing_zone(
    launch_longitude_deg=100.0,
    launch_latitude_deg=30.0,
    launch_height_m=0.0,
    impact_longitude_deg=101.0,
    impact_latitude_deg=30.5,
    impact_height_m=100.0,
    zone_xys_km=[
        1.0,
        0.5,
        -1.0,
        0.5,
        -1.0,
        -0.5,
        1.0,
        -0.5,
    ],
)

print(f"Success: {result['IsSuccess']}")
print(f"Message: {result['Message']}")

cartographic = result["cartographicDegrees"]
num_vertices = len(cartographic) // 3
print(f"Boundary vertices: {num_vertices}")
for index in range(num_vertices):
    lon = cartographic[index * 3]
    lat = cartographic[index * 3 + 1]
    height = cartographic[index * 3 + 2]
    print(f"  {index}: lon={lon:.6f} deg, lat={lat:.6f} deg, height={height:.3f} m")
```

Output:

```text
Success: True
Message: Success
Boundary vertices: 4
  0: lon=101.006448 deg, lat=30.491602 deg, height=100.098 m
  1: lon=100.988372 deg, lat=30.500570 deg, height=100.098 m
  2: lon=100.993550 deg, lat=30.508397 deg, height=100.098 m
  3: lon=101.011627 deg, lat=30.499429 deg, height=100.098 m
```

## Error Handling

When ASTROX returns an unsuccessful response or the network request fails, `rocket.landing_zone` raises `astrox.exceptions.AstroxAPIError`. The SDK does not hide or rewrite server error messages.
