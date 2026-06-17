# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Coverage figure-of-merit routes grouped by metric namespace."""

from astrox import coverage, components


ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def main() -> None:
    grid = coverage.lat_lon_grid(
        min_latitude_deg=20.0,
        max_latitude_deg=25.0,
        min_longitude_deg=-120.0,
        max_longitude_deg=-110.0,
        resolution_deg=5.0,
    )
    relay = components.entity(
        name="Relay",
        position=components.sgp4_position(tle_lines=ISS_TLE),
    )
    common = {
        "start": "2024-01-01T00:00:00.000Z",
        "stop": "2024-01-01T00:30:00.000Z",
        "grid": grid,
        "assets": [relay],
        "minimum_assets": 1,
        "step_s": 300.0,
    }

    simple = coverage.simple_coverage.by_grid_point(**common)
    at_time = coverage.number_of_assets.by_grid_point_at_time(
        time="2024-01-01T00:10:00.000Z",
        **common,
    )
    duration_stats = coverage.coverage_time.grid_stats(
        compute_type="TotalTimeAbove",
        **common,
    )
    response_stats = coverage.response_time.grid_stats(
        compute_type="Maximum",
        **common,
    )
    revisit_stats = coverage.revisit_time.grid_stats(
        compute_type="Average",
        **common,
    )

    print(f"Simple coverage rows: {len(simple['Datas'])}")
    print(f"Number-of-assets rows at time: {len(at_time['Datas'])}")
    print(f"Coverage-time average: {duration_stats['Average']:.6f} s")
    print(f"Response-time maximum: {response_stats['Maximum']:.6f} s")
    print(f"Revisit-time maximum: {revisit_stats['Maximum']:.6f} s")


if __name__ == "__main__":
    main()
