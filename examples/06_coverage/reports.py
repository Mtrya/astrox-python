# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Coverage report routes for percent coverage and per-asset coverage."""

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

    percent = coverage.percent_coverage(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        grid=grid,
        assets=[relay],
        minimum_assets=1,
        step_s=60.0,
    )
    by_asset = coverage.coverage_by_asset(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        grid=grid,
        assets=[relay],
        minimum_assets=1,
        step_s=60.0,
    )

    print(f"Percent coverage samples: {len(percent['PercentCoverageDatas'])}")
    print(f"Per-asset rows: {len(by_asset['CoverageByAssetDatas'])}")


if __name__ == "__main__":
    main()
