# How to screen close approaches between a satellite and space objects

This page solves a specific task: given the primary satellite's two-line element set (TLE) and a batch of target TLEs, find the close approaches that may occur within the analysis window, and read out the time of closest approach, minimum range, relative speed, and orbital-plane angle.

## Complete example

The script below runs one close-approach screen with a primary satellite and one target TLE, and prints the result of each close approach.

```python
import astrox
from astrox import conjunction, orbits

astrox.configure(base_url="http://astrox.cn:8765")

primary = orbits.tle(
    line1="1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    line2="2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    name="ISS",
    catalog_number="25544",
)

target = orbits.tle(
    line1="1 25545U 99999A   24001.00000000  .00000000  00000-0  00000-0 0  9993",
    line2="2 25545  51.6264 339.8059 0009386 217.1816 140.0000 15.52489080    03",
    name="probe",
    catalog_number="25545",
)

result = conjunction.find_tle_close_approaches(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    tle=primary,
    targets=[target],
    tol_max_distance_km=1000.0,
    tol_cross_dt_s=1000.0,
    tol_theta_deg=180.0,
    tol_dh_km=1000.0,
)

print(f"Total targets: {result.total_number}")
print(f"After altitude filter: {result.after_apo_peri_filter_number}")
print(f"After plane-angle filter: {result.after_cross_plane_number}")
print(f"Reported close approaches: {len(result.results)}")

for approach in result.results:
    print(f"\nTime of closest approach: {approach.min_range_time}")
    print(f"Minimum range: {approach.min_range_km:.3f} km")
    print(f"Relative speed: {approach.relative_speed_km_s:.4f} km/s")
    print(f"Orbital-plane angle: {approach.orbital_plane_angle_deg:.4f} deg")
```

## Two decisions to make

1. **The primary vehicle's form**: when the primary vehicle has a TLE, use `conjunction.find_tle_close_approaches`, and the result includes the TLEs of both the primary vehicle and the target; when the primary vehicle is a CZML sampled trajectory (for example an object without a TLE, such as a rocket), use `conjunction.find_czml_close_approaches`, and the result contains only the targets. For the latter, you can first propagate with `propagator.sgp4` and construct `components.czml_position` directly from the returned sample sequence.
2. **Close-approach tolerances**: `tol_max_distance_km` determines how close counts as a close approach; the remaining tolerances (crossing time, orbital-plane angle, perigee/apogee altitude) can use the server defaults, but the default filters may exclude a target before the distance search. This example explicitly widens the other three screening tolerances to reproduce the verified result. When the target count is large, tightening `tol_max_distance_km` can markedly reduce the computation.

## Reading the results

`total_number` is the total number of targets, `after_apo_peri_filter_number` and `after_cross_plane_number` are the numbers of targets remaining after the altitude and plane-angle filters, and `results` is the list of actually reported close approaches. The meaning and units of each result field are in the [conjunction analysis manual](../manual/conjunction/README.md).

The `collision_probability` field remains unresolved: repeated calls with changes to target distance, orbital-plane angle, relative speed, and filter thresholds always observed 0.0; it is only a stable but unexplained scalar (opaque scalar) returned by the server without statistical collision-probability semantics, so do not use it as a basis for decisions. Base your screening decisions on the minimum range and the relative speed.

## Learn more

- For all parameters, tolerance semantics, and the verified scope of the close-approach functions, see the [conjunction analysis manual](../manual/conjunction/README.md).
- For TLE construction and field descriptions, see the [orbits manual](../manual/orbits/README.md).
- When using a CZML sampled trajectory as the primary vehicle, read the [propagator manual](../manual/propagator/README.md) first to see how sampled positions are generated.
