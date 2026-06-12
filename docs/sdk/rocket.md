# Rocket

This page documents the curated ASTROX Python rocket interface. The intended import style is:

```python
from astrox import rocket
```

## Landing Zone

`rocket.landing_zone(...)` computes the geodetic boundary of a rocket landing zone from a launch point, an impact point, and local downrange/crossrange offsets.

```python
result = rocket.landing_zone(
    launch_longitude_deg=100.0,
    launch_latitude_deg=30.0,
    launch_height_m=0.0,
    impact_longitude_deg=101.0,
    impact_latitude_deg=30.5,
    impact_height_m=100.0,
    zone_xys_km=[
        1.0, 0.5,
        -1.0, 0.5,
        -1.0, -0.5,
        1.0, -0.5,
    ],
)
```

Arguments use explicit unit suffixes:

| Argument | Unit | Meaning |
|----------|------|---------|
| `launch_longitude_deg` | degrees | Launch geodetic longitude |
| `launch_latitude_deg` | degrees | Launch geodetic latitude |
| `launch_height_m` | metres | Launch geodetic height |
| `impact_longitude_deg` | degrees | Impact (落点) geodetic longitude |
| `impact_latitude_deg` | degrees | Impact (落点) geodetic latitude |
| `impact_height_m` | metres | Impact geodetic height |
| `zone_xys_km` | kilometres | Flat `[+X1, +Y1, +X2, +Y2, ...]` offset pairs |

`zone_xys_km` must contain an even number of numeric values. Each pair defines one boundary vertex relative to the impact point. Cross-validation against WGS-84 geodesy shows that ASTROX builds a local right-handed frame at the impact point:

- `+X` is chosen from the launch-to-impact geodesic azimuth at the impact point and its supplement so that `+X` points southward (or horizontally at the equator).
- `+Y` is `+X` rotated 90° clockwise.

This means the OpenAPI description "forward is +X, right is +Y" matches cardinal tracks (north-south and east-west) literally, but for diagonal tracks `+X` is the southward-facing member of the geodesic azimuth pair and `+Y` follows clockwise from it.

The function returns the raw ASTROX JSON-like response dictionary, including `IsSuccess`, `Message`, and `cartographicDegrees`. `cartographicDegrees` is a flat array of `[Longitude, Latitude, Height, ...]` values in `[deg, deg, m]`.

See `tests/validation/cross_validation/rocket/test_landing_zone_geographiclib.py` for the calibration details and coverage checklist.

## Rocket Trajectory Endpoints

The `/Rocket/*` trajectory, landing, and guidance endpoints are deferred to PR-18 because of an upstream server-side initialization failure (`AeroSpace.Rocket.ScRocketStatic`). They are not exposed by this SDK surface yet.
