# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Revisit Time FOM - Grid Stats Over Time Output

Demonstrates fom_revisit_time() with output="grid_stats_over_time" to get
revisit time statistics that evolve throughout the analysis period.

API: POST /Coverage/FOM/GridStatsOverTime/RevisitTime
"""

from astrox.coverage import fom_revisit_time
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create an 8-satellite constellation
    satellites = []
    altitude = 750000.0
    sma = 6378137.0 + altitude

    # 4 planes, 2 satellites per plane
    for plane in range(4):
        raan = plane * 90.0
        for sat in range(2):
            ta = sat * 180.0
            satellite = EntityPath(
                Name=f"Const-P{plane}S{sat}",
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
                        60.0,
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

    # Execute: Get revisit statistics over time
    result = fom_revisit_time(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",  # Full day
        grid=grid,
        assets=satellites,
        output="grid_stats_over_time",
        step=300.0,
    )

    # Output: Display statistics evolution
    print(f"Success: {result['IsSuccess']}")
    print(f"Number of time samples: {len(result['StatsArray'])}")

    # Show stats at key intervals
    stats = result["StatsArray"]
    sample_indices = [
        0,                      # Start
        len(stats) // 4,        # 6 hours
        len(stats) // 2,        # 12 hours
        3 * len(stats) // 4,    # 18 hours
        len(stats) - 1,         # End
    ]

    print(f"\nRevisit Time Statistics Evolution:")
    for idx in sample_indices:
        s = stats[idx]
        mean_min = s["Mean"] / 60
        print(f"  {s['Time']}: Min={s['Minimum'] / 60:.1f}min, "
              f"Max={s['Maximum'] / 3600:.2f}hrs, Mean={mean_min:.1f}min")


if __name__ == "__main__":
    main()
