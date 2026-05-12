# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Coverage Time FOM - Grid Point Output

Demonstrates fom_coverage_time() with output="grid_point" to get
total coverage time (in seconds) for each individual grid point.

API: POST /Coverage/FOM/ValueByGridPoint/CoverageTime
"""

from astrox.coverage import fom_coverage_time
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create a 3-satellite constellation
    satellites = []
    altitude = 700000.0  # 700 km
    sma = 6378137.0 + altitude

    for i in range(3):
        satellite = EntityPath(
            Name=f"Sat-{i+1}",
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
                    60.0,           # Inclination
                    0.0,            # Argument of periapsis
                    i * 120.0,      # RAAN: 0, 120, 240 degrees
                    0.0,            # True anomaly
                ],
            ),
        )
        satellites.append(satellite)

    # Define regional grid
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-30.0,
        MaxLatitude=30.0,
        Resolution=12.0,
        Height=0.0,
    )

    # Execute: Get per-grid-point coverage times
    result = fom_coverage_time(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T12:00:00.000Z",
        grid=grid,
        assets=satellites,
        output="grid_point",
        step=120.0,
    )

    # Output: Display coverage times
    print(f"Success: {result['IsSuccess']}")
    print(f"Analysis period: 12 hours ({12 * 3600} seconds)")
    print(f"Grid points: {len(result['FOMValues'])}")

    # Find min and max coverage times
    times = result["FOMValues"]
    max_time = max(times)
    min_time = min(times)

    print(f"\nMaximum coverage time: {max_time:.1f} s ({max_time / 3600:.2f} hrs)")
    print(f"Minimum coverage time: {min_time:.1f} s ({min_time / 3600:.2f} hrs)")
    print(f"Mean coverage time: {sum(times) / len(times):.1f} s")


if __name__ == "__main__":
    main()
