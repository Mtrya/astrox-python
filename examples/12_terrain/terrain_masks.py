# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""演示显式地形配置下的完整和简化方位角-仰角遮罩查询。"""

from astrox import components, terrain


SITE = components.site_position(
    longitude_deg=0.0,
    latitude_deg=-89.0,
    height_m=0.0,
    central_body="Moon",
)
CONFIG = terrain.TerrainMaskConfig(
    text="terrain example",
    terrain_server_url="",
    flag_pole=1,
    polar_dem_file_name="Moon_LDEM_80s_20m",
    terrain_zoom_level=-1,
    step_size_m=30.0,
    max_search_range_km=15.0,
)


def main() -> None:
    full = terrain.azimuth_elevation_mask(site_position=SITE, config=CONFIG)
    simple = terrain.azimuth_elevation_mask_simple(site_position=SITE, config=CONFIG)
    print(f"完整遮罩: {len(full['AzElMaskData'])} 个方位条目")
    print(f"简化遮罩: {len(simple['AzElMaskData']) // 2} 个方位-仰角对")
    print(f"首个完整条目: {full['AzElMaskData'][0]}")


if __name__ == "__main__":
    main()
