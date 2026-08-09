# Terrain Validation Evidence

This page records the cross-validation and live-snapshot evidence for `astrox.terrain` (`TerrainMaskConfig`, `azimuth_elevation_mask`, and `azimuth_elevation_mask_simple`). It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/terrain/README.md`](../manual/terrain/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`. The live snapshots prove maintained response shape for the public SDK inputs they exercise; they are not semantic proof.

## Terrain masks

Status of the full and simple terrain-mask routes: `verified` for response structure and cross-endpoint pair consistency on the maintained explicit Moon polar DEM configuration; terrain elevation semantics are `unverified`.

- Maintained case: a Moon site at latitude −89° (`components.site_position` with `longitude_deg=0.0`, `latitude_deg=-89.0`, `height_m=0.0`, `central_body="Moon"`) and an explicit `TerrainMaskConfig` with `terrain_server_url=""` (an explicit empty string is required by the maintained server route), `flag_pole=1`, `polar_dem_file_name="Moon_LDEM_80s_20m"`, `terrain_zoom_level=-1`, `step_size_m=30.0`, and `max_search_range_km=15.0`.
- Cross-route invariants: `verified` through [`tests/validation/cross_validation/terrain/test_terrain_mask_invariants.py`](../../tests/validation/cross_validation/terrain/test_terrain_mask_invariants.py), within `ABS_TOL = 1e-12`:
  - `azimuth_elevation_mask` returns 361 `AzElMaskData` entries and `azimuth_elevation_mask_simple` returns 722 numeric values (361 pairs).
  - The first full entry has `Azimuth` 0 and the last has `Azimuth` 2π; azimuth is monotonically non-decreasing across entries.
  - Every full entry has a non-empty `Items` collection.
  - The simple route's alternating pairs match the full route's `Azimuth`/`Elevation` values pair-for-pair.
- Response structure: `verified` through live snapshots for both routes — envelope (`IsSuccess`, `Message`, `sitePosition`, `AzElMaskData`), `sitePosition` keys (`CentralBody`, `HeightAboveGround`, `cartographicDegrees`, `clampToGround`), full entries with keys `Azimuth`, `Elevation`, `Items`, and the simple flat numeric list.

Scope boundary: the verification covers response structure and the two-route pair invariant. Terrain elevation physics (the meaning of the returned elevation angles against an independent terrain model) is not independently verified. The server-default configuration path (`TerrainMaskPara` omitted, server uses its appsettings.json defaults) is `unverified`: the maintained evidence uses the explicit polar DEM configuration, and the default metadata path may fail on the deployed server, so it is not promoted.

## Live snapshot coverage

The terrain functions are exercised in [`tests/validation/live_snapshot/terrain/test_terrain.py`](../../tests/validation/live_snapshot/terrain/test_terrain.py), with sidecar [`tests/validation/live_snapshot/terrain/terrain.snap.json`](../../tests/validation/live_snapshot/terrain/terrain.snap.json) covering both `azimuth_elevation_mask` and `azimuth_elevation_mask_simple` with the documented Moon polar DEM configuration. These live snapshots are drift detectors for the response shape of maintained public inputs.

Cross-validation script: [`tests/validation/cross_validation/terrain/test_terrain_mask_invariants.py`](../../tests/validation/cross_validation/terrain/test_terrain_mask_invariants.py).
