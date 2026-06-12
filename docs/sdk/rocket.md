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

`zone_xys_km` must contain an even number of numeric values. Each pair defines one boundary vertex relative to the impact point. The OpenAPI description states that `+X` points forward along the launch-to-impact direction and `+Y` points to the right.

The function returns the raw ASTROX JSON-like response dictionary, including `IsSuccess`, `Message`, and `cartographicDegrees`. `cartographicDegrees` is a flat array of `[Longitude, Latitude, Height, ...]` values in `[deg, deg, m]`.

Cross-validation shows that for cardinal launch-to-impact tracks the ASTROX frame matches a WGS-84 geodesic forward/right convention, but for diagonal tracks the frame rotation is currently unresolved. See `tests/validation/cross_validation/rocket/test_landing_zone_geographiclib.py` for the calibration details.

## Rocket Trajectory Endpoints

The `/Rocket/*` trajectory, landing, and guidance endpoints are deferred to PR-18 because of an upstream server-side initialization failure (`AeroSpace.Rocket.ScRocketStatic`). They are not exposed by this SDK surface yet.
