# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Simple Coverage FOM - Grid Stats Over Time Output

Demonstrates fom_simple_coverage() with output="grid_stats_over_time" to get
coverage statistics (min, max, mean) that evolve throughout the analysis period.

API: POST /Coverage/FOM/GridStatsOverTime/SimpleCoverage
"""

from astrox.coverage import fom_simple_coverage
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create a Walker constellation with 4 satellites
    satellites = []
    altitude = 600000.0  # 600 km
    sma = 6378137.0 + altitude

    for plane in range(2):
        raan = plane * 90.0
        for sat in range(2):
            ta = sat * 180.0
            satellite = EntityPath(
                Name=f"Sat-P{plane}S{sat}",
                Position=J2Position(
                    **{"$type": "J2"},
                    CentralBody="Earth",
                    J2NormalizedValue=0.000484165143790815,
                    RefDistance=6378137.0,
                    OrbitEpoch="2024-01-01T00:00:00.000Z",
                    CoordSystem="Inertial",
                    CoordType="Classical",
                    OrbitalElements=[
                        sma,
                        0.001,
                        55.0,
                        0.0,
                        raan,
                        ta,
                    ],
                ),
            )
            satellites.append(satellite)

    # Define coverage grid
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-40.0,
        MaxLatitude=40.0,
        Resolution=15.0,
        Height=0.0,
    )

    # Execute: Get coverage statistics over time
    result = fom_simple_coverage(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T12:00:00.000Z",
        grid=grid,
        assets=satellites,
        output="grid_stats_over_time",
        step=300.0,
    )

    # Output: Display statistics evolution
    print(f"Success: {result['IsSuccess']}")
    print(f"Number of time samples: {len(result['StatsArray'])}")

    # Show stats at beginning, middle, and end
    stats = result["StatsArray"]
    indices = [0, len(stats) // 2, len(stats) - 1]

    for idx in indices:
        s = stats[idx]
        print(f"\nTime: {s['Time']}")
        print(f"  Min: {s['Minimum']:.4f}, Max: {s['Maximum']:.4f}")
        print(f"  Mean: {s['Mean']:.4f}, StdDev: {s['StdDev']:.4f}")


if __name__ == "__main__":
    main()
