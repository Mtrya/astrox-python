# 目录查询

`astrox.catalog` 提供服务端目录数据的只读查询 API：城市、地面站与卫星目录。推荐导入方式：

```python
from astrox import catalog
```

本页按数据域组织：`catalog.query_cities` 查询城市，`catalog.query_facilities` 查询地面站（设施），`catalog.query_satellites` 查询卫星目录。三个函数都通过 `astrox.raw.get` 发出 HTTP GET 请求，并返回 ASTROX 原始 JSON 响应字典，不做 typed response 解析；所有查询参数都是可选过滤条件，未提供的参数不会被发往服务端。

目录数据由服务端维护（服务端文档标注为从服务器文件夹读取、需手动更新），内容可能不随 SDK 版本更新，也不对查询结果条数做任何承诺。

## 城市查询

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

查询服务端城市目录，返回原始 JSON 响应字典。

| 参数 | wire 参数 | 说明 |
| --- | --- | --- |
| `city_name` | `cityName` | 城市名称（英文或汉语拼音） |
| `province_name` | `provinceName` | 省份名称 |
| `country_name` | `countryName` | 国家名称 |
| `city_type` | `typeOfCity` | 城市类型，服务端枚举 `PopulatedPlace` / `AdministrationCenter` / `NationalCapital` / `TerritorialCapital` |

```python
cities = catalog.query_cities(city_name="Beijing")
city_rows = cities.get("Cities") or []

print(f"城市查询: {len(city_rows)} 条结果")
```

响应中的 `Cities` 是记录数组，记录键为 `CityName`、`TypeOfCity`、`ProvinceName`、`CountryName`、`ProvinceRank`、`Population`、`Latitude`、`Longitude`、`CentralBodyName`。其中 `Latitude` 与 `Longitude` 的单位为弧度（rad），`ProvinceRank` 与 `Population` 为整数。

## 设施查询

### `catalog.query_facilities`

```python
catalog.query_facilities(
    *,
    facility_name: str | None = None,
    network_name: str | None = None,
) -> dict[str, Any]
```

查询服务端地面站目录，返回原始 JSON 响应字典。

| 参数 | wire 参数 | 说明 |
| --- | --- | --- |
| `facility_name` | `facilityName` | 地面站名称（英文或汉语拼音） |
| `network_name` | `networkName` | 所属网络，如 `NASA DSN`、`NRO` |

```python
facilities = catalog.query_facilities(facility_name="Goldstone")
facility_rows = facilities.get("Facilities") or []

print(f"设施查询: {len(facility_rows)} 条结果")
```

响应中的 `Facilities` 是记录数组，记录键为 `FacilityName`、`NetworkName`、`Latitude`、`Longitude`、`Altitude`、`CentralBodyName`。`Latitude` 与 `Longitude` 的单位为弧度（rad），`Altitude` 的单位为米（m）。

## 卫星查询

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

按过滤条件查询服务端卫星目录，返回原始 JSON 响应字典。

| 参数 | wire 参数 | 单位 | 说明 |
| --- | --- | --- | --- |
| `name` | `sscName` | — | 卫星名称，如 `FENGYUN` |
| `catalog_number` | `sscNumber` | — | SSC 编号 |
| `mission` | `mission` | — | 任务类型，如 `Astronomy`、`Comm`、`Navigation` |
| `owner` | `owner` | — | 所属国家，如 `PRC`、`US` |
| `active` | `active` | — | 是否有效；布尔值，SDK 会 lower 为字符串 `"true"` / `"false"` |
| `minimum_perigee_m` | `minimumPerigee` | m | 最小近地点高度，结果中近地点高度大于此值 |
| `maximum_perigee_m` | `maximumPerigee` | m | 最大近地点高度，结果中近地点高度小于此值 |
| `minimum_apogee_m` | `minmumApogee` | m | 最小远地点高度，结果中远地点高度大于此值 |
| `maximum_apogee_m` | `maximumApogee` | m | 最大远地点高度，结果中远地点高度小于此值 |
| `minimum_inclination_deg` | `minimumInclination` | deg | 最小轨道倾角 |
| `maximum_inclination_deg` | `maximumInclination` | deg | 最大轨道倾角 |

`minimum_apogee_m` 会按服务端实际拼写 lower 为 `minmumApogee`（服务端参数名自带拼写错误），这是 wire 契约的一部分，SDK 不代为纠正。

```python
satellites = catalog.query_satellites(name="FENGYUN", active=True)

rows = satellites.get("TLEs", [])
print(f"活动卫星查询: TotalCount={satellites.get('TotalCount')}")
if rows:
    print(f"第一条记录: {rows[0].get('CommonName', '<unnamed>')}")
```

响应包含 `TotalCount`（查询到的卫星总数，整数）与 `TLEs`（卫星记录数组）。记录键为 `Active`、`CommonName`、`OfficialName`、`SatelliteNumber`、`TleEpoch`、`RevolutionNumber`、`TLE_Line1`、`TLE_Line2`、`InternationalDesignator`、`Owner`、`Mission`、`LaunchSite`、`LaunchDateString`、`OrbitDescription`、`Mass`、`Apogee`、`Perigee`、`Period`、`Inclination`、`LastDatabaseUpdate`、`WriteUp`。`Active` 为布尔值；服务端文档标注 `Mass` 单位为 kg、`Apogee`/`Perigee` 单位为 m、`Period` 单位为 s、`Inclination` 单位为 rad，这些数值的含义由服务端数据源决定。

卫星目录数据易变：数据库行内容随服务端数据更新而变化，不承诺查询条数与具体行内容。

## 约定说明

- 所有参数可选；未提供的参数不会被发往 ASTROX，查询不带该过滤条件。
- `active` 是布尔参数，SDK lower 为字符串 `"true"` / `"false"`，不是数值。
- `minimum_apogee_m` 对应服务端参数 `minmumApogee`（服务端拼写）。
- 过滤值中的近地点/远地点单位为 m，轨道倾角单位为 deg，与 SDK 参数后缀一致。
- 验证证据见 [catalog 验证页](../../validation/catalog.md)。

完整可运行示例见 `examples/10_catalog/catalog_queries.py`。

## 错误处理

当 ASTROX 返回不成功响应或网络请求失败时，本模块函数会抛出 `astrox.exceptions.AstroxAPIError`。SDK 不会改写服务器错误信息。需要完全控制请求载荷或处理原始响应时，请使用 `astrox.raw.get`。
