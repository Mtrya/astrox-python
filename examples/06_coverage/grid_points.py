# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Generate coverage grid points from a latitude/longitude grid definition."""

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
    print(f"Generated grid points: {len(points)}")
    if points:
        print(f"First point: {points[0]['Position']}")


if __name__ == "__main__":
    main()
