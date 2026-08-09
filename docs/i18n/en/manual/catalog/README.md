# Catalog Queries

`astrox.catalog` provides read-only query APIs for server-owned catalog data: cities, facilities (ground stations), and satellites. The recommended import style is:

```python
from astrox import catalog
```

This page is organized by data domain: `catalog.query_cities` queries cities, `catalog.query_facilities` queries ground stations (facilities), and `catalog.query_satellites` queries the satellite catalog. All three functions send HTTP GET requests through `astrox.raw.get` and return ASTROX raw JSON response dictionaries without typed response parsing; every query parameter is an optional filter, and parameters that are not supplied are not sent to the server.

Catalog data is maintained by the server (the server documentation describes it as read from a server folder and updated manually), may change independently of the SDK version, and no promise is made about the number of query results.

## City queries

### `catalog.query_cities`

```python
catalog.query_cities(
    *,
    city_name: str | None = None,
    province_name: str | None = None,
    country_name: str | None = None,
    city_type: str | None = None,
) -> dict[str, Any]
```

Queries the server-owned city catalog and returns a raw JSON response dictionary.

| Parameter | Wire parameter | Description |
| --- | --- | --- |
| `city_name` | `cityName` | City name (English or pinyin) |
| `province_name` | `provinceName` | Province name |
| `country_name` | `countryName` | Country name |
| `city_type` | `typeOfCity` | City type, server enum `PopulatedPlace` / `AdministrationCenter` / `NationalCapital` / `TerritorialCapital` |

```python
cities = catalog.query_cities(city_name="Beijing")
city_rows = cities.get("Cities") or []

print(f"City query: {cities['IsSuccess']}, {len(city_rows)} results")
```

The `Cities` field of the response is an array of records with keys `CityName`, `TypeOfCity`, `ProvinceName`, `CountryName`, `ProvinceRank`, `Population`, `Latitude`, `Longitude`, and `CentralBodyName`. `Latitude` and `Longitude` are in radians (rad), and `ProvinceRank` and `Population` are integers.

## Facility queries

### `catalog.query_facilities`

```python
catalog.query_facilities(
    *,
    facility_name: str | None = None,
    network_name: str | None = None,
) -> dict[str, Any]
```

Queries the server-owned ground station catalog and returns a raw JSON response dictionary.

| Parameter | Wire parameter | Description |
| --- | --- | --- |
| `facility_name` | `facilityName` | Facility name (English or pinyin) |
| `network_name` | `networkName` | Owning network, e.g. `NASA DSN`, `NRO` |

```python
facilities = catalog.query_facilities(facility_name="Goldstone")
facility_rows = facilities.get("Facilities") or []

print(f"Facility query: {facilities['IsSuccess']}, {len(facility_rows)} results")
```

The `Facilities` field of the response is an array of records with keys `FacilityName`, `NetworkName`, `Latitude`, `Longitude`, `Altitude`, and `CentralBodyName`. `Latitude` and `Longitude` are in radians (rad), and `Altitude` is in meters (m).

## Satellite queries

### `catalog.query_satellites`

```python
catalog.query_satellites(
    *,
    name: str | None = None,
    catalog_number: str | None = None,
    mission: str | None = None,
    owner: str | None = None,
    active: bool | None = None,
    minimum_perigee_m: float | None = None,
    maximum_perigee_m: float | None = None,
    minimum_apogee_m: float | None = None,
    maximum_apogee_m: float | None = None,
    minimum_inclination_deg: float | None = None,
    maximum_inclination_deg: float | None = None,
) -> dict[str, Any]
```

Queries the server-owned satellite catalog with filters and returns a raw JSON response dictionary.

| Parameter | Wire parameter | Unit | Description |
| --- | --- | --- | --- |
| `name` | `sscName` | — | Satellite name, e.g. `FENGYUN` |
| `catalog_number` | `sscNumber` | — | SSC number |
| `mission` | `mission` | — | Mission type, e.g. `Astronomy`, `Comm`, `Navigation` |
| `owner` | `owner` | — | Owning country, e.g. `PRC`, `US` |
| `active` | `active` | — | Whether active; a boolean lowered by the SDK to the string `"true"` / `"false"` |
| `minimum_perigee_m` | `minimumPerigee` | m | Minimum perigee altitude; results have perigee altitude above this value |
| `maximum_perigee_m` | `maximumPerigee` | m | Maximum perigee altitude; results have perigee altitude below this value |
| `minimum_apogee_m` | `minmumApogee` | m | Minimum apogee altitude; results have apogee altitude above this value |
| `maximum_apogee_m` | `maximumApogee` | m | Maximum apogee altitude; results have apogee altitude below this value |
| `minimum_inclination_deg` | `minimumInclination` | deg | Minimum orbital inclination |
| `maximum_inclination_deg` | `maximumInclination` | deg | Maximum orbital inclination |

`minimum_apogee_m` is lowered to the server's actual spelling `minmumApogee` (the server parameter name carries its own typo); this is part of the wire contract and the SDK does not correct it.

```python
satellites = catalog.query_satellites(name="FENGYUN", active=True)

rows = satellites.get("TLEs", [])
print(f"Active satellite query: {satellites['IsSuccess']}, TotalCount={satellites.get('TotalCount')}")
if rows:
    print(f"First record: {rows[0].get('CommonName', '<unnamed>')}")
```

The response contains `IsSuccess`, `Message`, `TotalCount` (the total number of satellites found, an integer) and `TLEs` (an array of satellite records). Record keys are `Active`, `CommonName`, `OfficialName`, `SatelliteNumber`, `TleEpoch`, `RevolutionNumber`, `TLE_Line1`, `TLE_Line2`, `InternationalDesignator`, `Owner`, `Mission`, `LaunchSite`, `LaunchDateString`, `OrbitDescription`, `Mass`, `Apogee`, `Perigee`, `Period`, `Inclination`, `LastDatabaseUpdate`, and `WriteUp`. `Active` is a boolean; the server documentation states that `Mass` is in kg, `Apogee`/`Perigee` in m, `Period` in s, and `Inclination` in rad, and the meaning of these values is determined by the server's data source.

Satellite catalog data is volatile: database rows change as the server data updates, and no promise is made about the number of results or the specific row content.

## Convention notes

- All parameters are optional; parameters that are not supplied are not sent to ASTROX and the query is made without that filter.
- `active` is a boolean parameter lowered by the SDK to the string `"true"` / `"false"`, not a number.
- `minimum_apogee_m` maps to the server parameter `minmumApogee` (server spelling).
- Filter values use m for perigee/apogee altitudes and deg for orbital inclination, matching the SDK parameter suffixes.
- Validation evidence is recorded on the [catalog validation page](../../../../validation/catalog.md).

A complete runnable example is available at `examples/10_catalog/catalog_queries.py`.

## Error handling

When ASTROX returns an unsuccessful response or the network request fails, the functions in this module raise `astrox.exceptions.AstroxAPIError`. The SDK does not rewrite server error messages. When you need full control over the request payload or want to handle the raw response, use `astrox.raw.get`.
