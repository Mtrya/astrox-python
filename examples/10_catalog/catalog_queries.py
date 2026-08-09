# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""演示城市、设施和卫星目录查询。"""

from astrox import catalog


def main() -> None:
    cities = catalog.query_cities(city_name="Beijing")
    print(f"城市查询: {cities['IsSuccess']}, {len(cities.get('Cities', []))} 条结果")

    facilities = catalog.query_facilities(facility_name="Goldstone")
    print(
        f"设施查询: {facilities['IsSuccess']}, "
        f"{len(facilities.get('Facilities', []))} 条结果"
    )

    satellites = catalog.query_satellites(name="FENGYUN", active=True)
    rows = satellites.get("TLEs", [])
    print(f"活动卫星查询: {satellites['IsSuccess']}, TotalCount={satellites.get('TotalCount')}")
    if rows:
        print(f"第一条记录: {rows[0].get('CommonName', '<unnamed>')}")


if __name__ == "__main__":
    main()
