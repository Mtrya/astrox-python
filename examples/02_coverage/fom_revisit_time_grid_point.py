# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Revisit Time FOM - Grid Point Output

Demonstrates fom_revisit_time() with output="grid_point" to get
the average revisit time (gap between passes) for each grid point.

API: POST /Coverage/FOM/ValueByGridPoint/RevisitTime
"""

from astrox.coverage import fom_revisit_time
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create a 6-satellite Walker constellation
    satellites = []
    altitude = 600000.0
    sma = 6378137.0 + altitude
    inclination = 55.0

    # Walker 3/2/1 configuration
    for plane in range(3):
        raan = plane * 120.0
        for sat in range(2):
            ta = sat * 180.0
            satellite = EntityPath(
                Name=f"Walker-{plane}-{sat}",
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
                        inclination,
                        0.0,
                        raan,
                        ta,
                    ],
                ),
            )
            satellites.append(satellite)

    # Define coverage grid
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-50.0,
        MaxLatitude=50.0,
        Resolution=15.0,
        Height=0.0,
    )

    # Execute: Get per-grid-point revisit times
    result = fom_revisit_time(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",  # 24 hours for meaningful revisit stats
        grid=grid,
        assets=satellites,
        output="grid_point",
        step=120.0,
    )

    # Output: Display revisit time analysis
    print(f"Success: {result['IsSuccess']}")
    print(f"Grid points: {len(result['FOMValues'])}")

    # Analyze revisit times
    times = result["FOMValues"]

    # Filter out points that were never revisited (infinite/very large values)
    valid_times = [t for t in times if t < 86400]  # Less than 24 hours

    print(f"\nRevisit Time Analysis (24-hour period):")
    print(f"  Points with valid revisit data: {len(valid_times)}")
    print(f"  Shortest revisit: {min(valid_times) / 60:.1f} minutes")
    print(f"  Longest revisit: {max(valid_times) / 3600:.2f} hours")
    print(f"  Mean revisit time: {sum(valid_times) / len(valid_times) / 60:.1f} minutes")


if __name__ == "__main__":
    main()
