# Rocket Validation Evidence

This page records the cross-validation status of the `astrox.rocket` surface. It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/rocket/README.md`](../manual/rocket/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) are taken directly from the coverage checklist in the cross-validation script listed below.

| Family | Cross-validation script | Live snapshot sidecar |
| --- | --- | --- |
| Landing zone | [`tests/validation/cross_validation/rocket/test_landing_zone_geographiclib.py`](../../tests/validation/cross_validation/rocket/test_landing_zone_geographiclib.py) | [`tests/validation/live_snapshot/rocket/landing_zone.snap.json`](../../tests/validation/live_snapshot/rocket/landing_zone.snap.json) |

## Landing Zone

Coverage status from [`test_landing_zone_geographiclib.py`](../../tests/validation/cross_validation/rocket/test_landing_zone_geographiclib.py):

### Branches

| Branch | Status | Comparison path |
| --- | --- | --- |
| North-south launch-to-impact track | verified | GeographicLib WGS-84 direct geodesic |
| East-west launch-to-impact track (eastward) | verified | GeographicLib WGS-84 direct geodesic |
| East-west launch-to-impact track (westward) | verified | GeographicLib WGS-84 direct geodesic |
| Diagonal north-east track | verified | GeographicLib WGS-84 direct geodesic |
| Diagonal north-west track | verified | GeographicLib WGS-84 direct geodesic |
| Diagonal south-east track | verified | GeographicLib WGS-84 direct geodesic |
| Diagonal south-west track | verified | GeographicLib WGS-84 direct geodesic |
| Southern-hemisphere north-east track | verified | GeographicLib WGS-84 direct geodesic |

### Fields and Conventions

| Item | Status | Notes |
| --- | --- | --- |
| `ZoneXYs` pairing convention | verified | Flat `[+X1, +Y1, +X2, +Y2, ...]` sequence produces one geodetic vertex per pair. |
| `+X`/`+Y` local-frame convention | verified | Calibrated right-handed frame at the impact point; see convention details below. |
| Output geodetic ordering | verified | `cartographicDegrees` is ordered `[Longitude, Latitude, Height, ...]`. |
| Height units/behavior | verified | Output height equals the impact height for every vertex; units are metres. |
| Boundary vertex count and order | verified | Reconstructed vertex sequence matches ASTROX output position-by-position. |

The script also exercises two additional cases that are not listed as separate branches in the coverage checklist: a large-offset variant of the diagonal north-east track (`zone_xys_km` magnitudes of 2 km and 1 km) and a single zero-offset vertex. Both pass the same cross-validation comparison and are covered by the `zone_xys_km` offset parameter status.

### Parameters

| Parameter | Status |
| --- | --- |
| Launch point geodetic coordinates | verified |
| Impact point geodetic coordinates | verified |
| `zone_xys_km` offsets (varied magnitudes and sign patterns) | verified |

### Comparison Path

The independent comparison is built from [GeographicLib](https://geographiclib.sourceforge.io/) WGS-84 direct geodesic calculations.

For each case the script:

1. Computes the launch-to-impact WGS-84 inverse geodesic and reads the impact-point azimuth `azi2`.
2. Selects the `+X` azimuth as the southward-facing member of `{azi2, 180 - azi2}` (or `azi2` when both are horizontal).
3. Rotates `+X` 90 degrees clockwise to obtain the `+Y` azimuth.
4. For each `[X, Y]` pair in `zone_xys_km`, applies a WGS-84 direct geodesic offset of distance `hypot(X, Y)` km at azimuth `plus_x_az + atan2(Y, X)` from the impact point.
5. Compares the resulting geodetic vertex against ASTROX's `cartographicDegrees` triple.

### Constants and Tolerances

- Ellipsoid: WGS-84 (`Geodesic.WGS84`).
- Position tolerance: `POSITION_ABS_M = 5.0` m.
- Height tolerance: `HEIGHT_ABS_M = 1.0` m.

### Known Residuals and Calibrated Convention

No systematic residual remains after calibration. The ASTROX convention that reproduces the response is:

- The local frame is right-handed and anchored at the impact point.
- `+X` is chosen from the launch-to-impact geodesic azimuth at the impact point (`azi2`) and its supplement (`180 - azi2`) so that `+X` has a non-positive north component; in other words, `+X` points southward or horizontally.
- `+Y` is `+X` rotated 90 degrees clockwise.
- Each `[X, Y]` offset pair is interpreted as a WGS-84 direct geodesic displacement of `sqrt(X² + Y²)` km at azimuth `plus_x_az + atan2(Y, X)`.

This means the OpenAPI "forward is +X, right is +Y" description matches cardinal tracks literally, but for diagonal tracks `+X` is the southward-facing member of the geodesic azimuth pair and `+Y` follows clockwise from it.

### Live Snapshot Coverage

The live snapshot script [`tests/validation/live_snapshot/rocket/test_landing_zone.py`](../../tests/validation/live_snapshot/rocket/test_landing_zone.py) maintains three cases in [`landing_zone.snap.json`](../../tests/validation/live_snapshot/rocket/landing_zone.snap.json):

- `diagonal_launch_to_impact` — a diagonal launch-to-impact track with four offset vertices.
- `north_south_launch_to_impact` — a pure north-south track with four offset vertices.
- `small_offset_single_vertex` — a single `[0.0, 0.0]` offset vertex at the impact point.

Live snapshots verify shape and drift only; they do not prove physical correctness.

## Dropped Material

The following content from the former `docs/sdk/rocket.md` (removed when the documentation was reorganized into Manual/How-To/Validation layers) was intentionally omitted from this validation page because it belongs in the Manual or How-To layers:

- Import style and usage tutorial (`from astrox import rocket`).
- Function signature and argument/unit reference table.
- Runnable example code and expected printed output.
- Error-handling guidance for `AstroxAPIError`.
- The deferred `/Rocket/*` trajectory, landing, and guidance endpoint note, which is planning information rather than validation evidence.
