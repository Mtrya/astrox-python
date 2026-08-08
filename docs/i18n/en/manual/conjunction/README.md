# Conjunction Analysis

`astrox.conjunction` screens close approaches between a primary vehicle and a set of space objects within a time window, returning the time of closest approach, minimum range, relative speed, orbital-plane angle, and collision probability for each close approach. The recommended import style is:

```python
from astrox import components, conjunction, orbits, propagator
```

The primary vehicle has two possible sources, which determine which function to use:

- The primary vehicle is a two-line element set (TLE) → `conjunction.find_tle_close_approaches`.
- The primary vehicle is a CZML sampled trajectory (for objects without a TLE, such as rockets) → `conjunction.find_czml_close_approaches`.

The target list is a sequence of `orbits.Tle` under both entries. Both functions return the same `CloseApproachesResult` structure; only the result-item type differs.

## Parameters and tolerances

Both functions share the same parameter set:

| Parameter | Unit | Description |
| --- | --- | --- |
| `start` | — | Analysis start time string (UTC, `yyyy-MM-ddTHH:mm:ss.fffZ` format) |
| `stop` | — | Analysis stop time string (UTC) |
| `tle` / `position` | — | Primary vehicle: an `orbits.Tle` instance or a `components.CzmlPosition` instance |
| `targets` | — | Target list, a sequence of `orbits.Tle`; when omitted, nothing is sent to ASTROX |
| `tol_max_distance_km` | km | Maximum distance for reporting a close approach, server default 5 km |
| `tol_cross_dt_s` | s | Time-error tolerance for the crossing-time screening, server default 10 s |
| `tol_theta_deg` | deg | Orbital-plane angle threshold, server default 1°; below this value the server does not apply plane-angle screening |
| `tol_dh_km` | km | Perigee/apogee altitude screening tolerance, server default 30 km |

Optional parameters are not sent to ASTROX when omitted; the server retains its default values, and those default filters may exclude a target before the distance search. `tol_max_distance_km` sets the distance threshold; when the target count is large, tightening it can markedly reduce the number of candidates. The examples explicitly set the other three screening tolerances to reproduce the verified result.

## `conjunction.find_tle_close_approaches`

```python
conjunction.find_tle_close_approaches(
    *,
    start: str,
    stop: str,
    tle: Tle,
    tol_max_distance_km: float | None = None,
    tol_cross_dt_s: float | None = None,
    tol_theta_deg: float | None = None,
    tol_dh_km: float | None = None,
    targets: Sequence[Tle] | None = None,
) -> CloseApproachesResult
```

The primary vehicle and the targets are both TLEs. The result items are `TleCloseApproach`, which include the TLEs of both the primary vehicle and the target.

```python
ISS_TLE = orbits.tle(
    line1="1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    line2="2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    name="ISS",
    catalog_number="25544",
)
probe_tle = orbits.tle(
    line1="1 25545U 99999A   24001.00000000  .00000000  00000-0  00000-0 0  9993",
    line2="2 25545  51.6264 339.8059 0009386 217.1816 140.0000 15.52489080    03",
    name="probe",
    catalog_number="25545",
)

result = conjunction.find_tle_close_approaches(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    tle=ISS_TLE,
    targets=[probe_tle],
    tol_max_distance_km=1000.0,
    tol_cross_dt_s=1000.0,
    tol_theta_deg=180.0,
    tol_dh_km=1000.0,
)

for approach in result.results:
    print(approach.min_range_time, approach.min_range_km, approach.relative_speed_km_s)
```

## `conjunction.find_czml_close_approaches`

```python
conjunction.find_czml_close_approaches(
    *,
    start: str,
    stop: str,
    position: components.CzmlPosition,
    tol_max_distance_km: float | None = None,
    tol_cross_dt_s: float | None = None,
    tol_theta_deg: float | None = None,
    tol_dh_km: float | None = None,
    targets: Sequence[Tle] | None = None,
) -> CloseApproachesResult
```

The primary vehicle is a CZML sampled trajectory; the targets remain TLEs. The result items are `CzmlCloseApproach`, which contain only the target TLE, not the primary-vehicle information. A sampled trajectory can be produced by propagating with `propagator.sgp4` and constructing the position directly:

```python
period_s, position = propagator.sgp4(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    step_s=60.0,
    tle=ISS_TLE,
)

czml = components.czml_position(
    epoch=position.epoch,
    central_body=position.central_body,
    interpolation_algorithm=position.interpolation_algorithm,
    interpolation_degree=position.interpolation_degree,
    reference_frame=position.reference_frame,
    cartesian_velocity=position.cartesian_velocity,
)

result = conjunction.find_czml_close_approaches(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    position=czml,
    targets=[probe_tle],
    tol_max_distance_km=1000.0,
    tol_cross_dt_s=1000.0,
    tol_theta_deg=180.0,
    tol_dh_km=1000.0,
)
```

## Return Values

`CloseApproachesResult` is a parsed frozen dataclass:

| Field | Type | Description |
| --- | --- | --- |
| `is_success` | `bool` | Whether the call succeeded |
| `message` | `str` | Server message |
| `total_number` | `int` | Total number of targets |
| `after_apo_peri_filter_number` | `int` | Number of targets remaining after the perigee/apogee altitude filter |
| `after_cross_plane_number` | `int` | Number of targets remaining after the orbital-plane angle filter |
| `results` | `tuple[TleCloseApproach, ...]` or `tuple[CzmlCloseApproach, ...]` | List of close-approach results |

`TleCloseApproach` and `CzmlCloseApproach` have the following fields:

| Field | Type | Description |
| --- | --- | --- |
| `primary` | `orbits.Tle` | Primary-vehicle TLE (only in `TleCloseApproach`) |
| `target` | `orbits.Tle` | Target TLE |
| `min_range_time` | `str` | Time of closest approach (UTCG string) |
| `min_range_km` | `float` | Minimum range, in km |
| `orbital_plane_angle_deg` | `float` | Orbital-plane angle, in deg |
| `relative_speed_km_s` | `float` | Relative speed, in km/s |
| `collision_probability` | `float` | A server-returned scalar observed as 0.0; unchanged across four probe rounds (repeated V3/V4, changing target distance, orbital-plane angle, relative speed, and filter thresholds), stable but unexplained, kept unresolved without statistical collision-probability semantics |

## Verified scope

- TLE entry: the time of closest approach matches the nearest sampled time of an independent SGP4 propagation at 60-second sampling; the minimum range matches the 3-D geometric distance; the relative speed matches the geometric relative speed; the orbital-plane angle matches the inclination difference of the two TLEs (returned at the server's decimal precision). Samples at both the start and stop times participate in reporting.
- CZML entry: minimum range, relative speed, and orbital-plane angle were verified using a public SGP4 trajectory sampled at 60 seconds; the closest-approach time reported by the server usually falls on the sample point before Stop, and the sample at Stop does not participate in reporting.
- Collision probability (`collision_probability`) remains unresolved: four probe rounds of repeated V3/V4 calls with changes to target distance, orbital-plane angle, relative speed, and filter thresholds all observed 0.0; the requests expose no covariance, hard-body radius, or equivalent error-model input and there is no independent probability oracle to compare against, so it is described as a stable but unexplained server-owned scalar (opaque scalar) without statistical collision-probability semantics, and neither this page nor the examples treat it as a recommended basis for decisions.

## Convention notes

- The time granularity and sampling pattern of `min_range_time` are determined by the server; under the CZML entry they are related to the sampling interval of the input trajectory.
- A close approach is constrained by the four tolerances together: candidate targets are first screened by perigee/apogee altitude and orbital-plane angle, then distance minima are searched within the time window; `total_number` is the total number of targets, and the two screening counts count only targets, not the number of close approaches.
- The units of the orbital-plane angle and relative speed are indicated by the field suffixes (`_deg`, `_km_s`) in the returned object.

A complete runnable example is available at `examples/08_conjunction/close_approaches.py`.

## Error handling

When ASTROX returns an unsuccessful response or the network request fails, the close-approach functions raise `astrox.exceptions.AstroxAPIError`. The SDK does not rewrite server error messages. When you need full control over the request payload or want to handle the raw response, use `astrox.raw.post`.
