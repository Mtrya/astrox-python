# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""演示城市、设施和卫星目录查询。"""

from astrox import catalog


def main() -> None:
    cities = catalog.query_cities(city_name="Beijing")
    city_rows = cities.get("Cities") or []
    print(f"城市查询: {len(city_rows)} 条结果")

    facilities = catalog.query_facilities(facility_name="Goldstone")
    facility_rows = facilities.get("Facilities") or []
    print(f"设施查询: {len(facility_rows)} 条结果")

    satellites = catalog.query_satellites(name="FENGYUN", active=True)
    rows = satellites.get("TLEs", [])
    print(f"活动卫星查询: TotalCount={satellites.get('TotalCount')}")
    if rows:
        print(f"第一条记录: {rows[0].get('CommonName', '<unnamed>')}")


if __name__ == "__main__":
    main()
