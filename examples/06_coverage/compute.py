# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Compute coverage for a satellite asset over a bounded grid."""

from astrox import coverage, entities


ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def main() -> None:
    grid = coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=35.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-100.0,
        resolution_deg=5.0,
    )
    relay = entities.entity(
        name="Relay",
        position=entities.sgp4_position(tle_lines=ISS_TLE),
    )

    result = coverage.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        grid=grid,
        assets=[relay],
        minimum_assets=1,
        include_asset_access_results=True,
        include_coverage_points=True,
        step_s=60.0,
    )

    intervals_by_point = result["SatisfactionIntervalsWithNumberOfAssets"]
    asset_intervals_by_point = result["AssetAccessResults"]
    points = result["CoverageOutput"]["Points"]["GridPoints"]
    print(f"Grid points with interval lists: {len(intervals_by_point)}")
    if intervals_by_point:
        covering_intervals = [
            interval
            for point_intervals in intervals_by_point
            for interval in point_intervals
            if interval["NumberOfAssets"] > 0
        ]
        print(f"Grid points echoed in response: {len(points)}")
        print(f"Per-point asset interval lists: {len(asset_intervals_by_point)}")
        print(f"Intervals for first point: {len(intervals_by_point[0])}")
        print(f"Intervals with at least one asset: {len(covering_intervals)}")


if __name__ == "__main__":
    main()
