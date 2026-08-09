# Catalog Validation Evidence

This page records the live-snapshot evidence for `astrox.catalog` (city, facility, and satellite catalog queries). It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/catalog/README.md`](../manual/catalog/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`. The live snapshots prove maintained response shape for the public SDK inputs they exercise; they are not semantic proof.

## Catalog queries

Status of `catalog.query_cities`, `catalog.query_facilities`, and `catalog.query_satellites`:

- Request lowering: `verified` through the deterministic behavior tests in [`tests/sdk/catalog/test_catalog.py`](../../tests/sdk/catalog/test_catalog.py). The maintained wire contract includes the server's `minmumApogee` spelling for `minimum_apogee_m`, the boolean `active` lowered to the strings `"true"`/`"false"`, meter/degree unit suffixes for the perigee/apogee and inclination filters, and omission of unsupplied optional filters.
- Response envelope and record keys: `verified` for the maintained query cases through live snapshots. `query_cities` returns `IsSuccess`/`Message`/`Cities` with record keys `CityName`, `TypeOfCity`, `ProvinceName`, `CountryName`, `ProvinceRank`, `Population`, `Latitude`, `Longitude`, `CentralBodyName`; `query_facilities` returns `IsSuccess`/`Message`/`Facilities` with record keys `FacilityName`, `NetworkName`, `Latitude`, `Longitude`, `Altitude`, `CentralBodyName`; `query_satellites` returns `IsSuccess`/`Message`/`TLEs`/`TotalCount` with the 21 record keys recorded in the sidecar snapshot.
- Units confirmed by live probe: city and facility `Latitude`/`Longitude` are radians, and facility `Altitude` is meters. Satellite response field units (e.g. `Mass` kg, `Apogee`/`Perigee` m, `Period` s, `Inclination` rad) follow the server's OpenAPI documentation and are not independently re-verified.
- Database rows and cardinality: `unverified` by design. Satellite catalog rows are volatile and intentionally not frozen in the snapshot (the `query_satellites_by_name_active` case records shape and keys only). No database-semantic cross-validation is maintained for any catalog query.

## Live snapshot coverage

The catalog functions are exercised in [`tests/validation/live_snapshot/catalog/test_catalog.py`](../../tests/validation/live_snapshot/catalog/test_catalog.py), with sidecar [`tests/validation/live_snapshot/catalog/catalog.snap.json`](../../tests/validation/live_snapshot/catalog/catalog.snap.json) covering `query_cities(city_name="Beijing")`, `query_facilities(facility_name="Goldstone")`, and `query_satellites(name="FENGYUN", active=True)`. These live snapshots are drift detectors for the response envelope and record keys of maintained public inputs; database row content is expected to change and is outside the snapshot contract.

There is no cross-validation script under `tests/validation/cross_validation/` for the catalog domain; catalog data is server-owned and volatile, so only wire shape and response keys are maintained evidence.
