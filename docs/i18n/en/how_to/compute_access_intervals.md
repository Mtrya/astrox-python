# Compute access intervals between a ground station and a satellite

This page completes a specific task: compute the access intervals during which a fixed ground station can see a satellite within a given time window.

## Two decisions you need to make

1. **Choose suitable position sources for both ends**: the ground station uses `components.site_position(...)`, and the satellite uses `components.sgp4_position(...)` to pass a two-line element set (TLE). Then wrap each in a `components.entity(...)` named object.
2. **Whether to add constraints**: keep the main path unconstrained to get the geometric visibility intervals first; if you need to filter low-elevation passes, attach `constraints` to the ground-station named object, as shown in “Next step: add an elevation constraint” below.

## Complete example

Save the following code as `access_intervals.py` and run it:

```python
import astrox
from astrox import access, components

astrox.configure(base_url="http://astrox.cn:8765")

ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)

ground = components.entity(
    name="Ground",
    position=components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
)

iss = components.entity(
    name="ISS",
    position=components.sgp4_position(tle_lines=ISS_TLE),
)

result = access.compute(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-02T00:00:00.000Z",
    from_entity=ground,
    to_entity=iss,
    step_s=600.0,
    compute_aer=True,
)

print(f"访问区间数量: {len(result['Passes'])}")
for i, interval in enumerate(result["Passes"][:5], start=1):
    print(
        f"  区间 {i}: {interval['AccessStart']} 至 {interval['AccessStop']} "
        f"(持续 {interval['Duration']:.1f} s)"
    )
```

Run:

```bash
python access_intervals.py
```

You will see output similar to this:

```text
访问区间数量: 6
  区间 1: 2024-01-01T01:33:10.636Z 至 2024-01-01T01:38:07.276Z (持续 296.6 s)
  区间 2: 2024-01-01T03:06:00.213Z 至 2024-01-01T03:17:55.654Z (持续 715.4 s)
  区间 3: 2024-01-01T04:44:17.416Z 至 2024-01-01T04:53:38.665Z (持续 561.2 s)
  区间 4: 2024-01-01T11:21:40.718Z 至 2024-01-01T11:30:20.788Z (持续 520.1 s)
  区间 5: 2024-01-01T12:57:07.455Z 至 2024-01-01T13:09:06.964Z (持续 719.5 s)
```

## What just happened

`access.compute` initiates a direct access computation with ASTROX. `from_entity` and `to_entity` must be named objects built with `components.entity(...)`:

- For the ground station, use `site_position` to give longitude, latitude, and altitude;
- For the satellite, use `sgp4_position` to pass the two TLE lines; the server computes the satellite position with the SGP4 model.

`step_s=600.0` controls the sampling step of the AER output, and `compute_aer=True` requests that each access interval include azimuth, elevation, and range data. If you only need the interval start and stop times, you can omit `compute_aer` or set it to `False`.

The returned `result` is the raw ASTROX response dict. `result["Passes"]` is the list of access intervals; each interval contains `AccessStart`, `AccessStop`, and `Duration` (in seconds).

## Next step: add an elevation constraint

Real tasks usually require the satellite to reach at least a certain elevation. Attach the constraint to the ground-station named object; the rest of the main code stays unchanged:

```python
constrained_ground = components.entity(
    name="Ground",
    position=components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    ),
    constraints=[
        components.elevation_constraint(minimum_deg=10.0),
    ],
)
```

The snippet above cannot run on its own; replace the `ground` object in the complete example before running it.

## Further reading and validation

- For full parameters, return-value fields, and chain usage of access computation, see the [access manual](../manual/access/README.md).
- For details on constructing named objects, position sources, and constraints, see the [components manual](../manual/components/README.md).
- Validation evidence for access intervals and AER output, plus constraint calibration status, is in the [Access validation page](../../../validation/access.md).
