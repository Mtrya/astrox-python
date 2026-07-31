# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""根据经纬度网格定义生成覆盖网格点。"""

from astrox import coverage


def main() -> None:
    grid = coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=35.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-100.0,
        resolution_deg=5.0,
    )

    result = coverage.grid_points(
        grid=grid,
        text="Western US grid",
    )

    points = result["Points"]["GridPoints"]
    print(f"生成的网格点数: {len(points)}")
    if points:
        print(f"第一个网格点: {points[0]['Position']}")


if __name__ == "__main__":
    main()
