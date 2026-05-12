# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Number of Assets FOM - Grid Stats Output

Demonstrates fom_number_of_assets() with output="grid_stats" to get
summary statistics (min, max, mean) of asset coverage across all grid points.

API: POST /Coverage/FOM/GridStats/NumberOfAssets
"""

from astrox.coverage import fom_number_of_assets
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create a 4-satellite constellation
    satellites = []
    altitude = 800000.0  # 800 km
    sma = 6378137.0 + altitude

    for i in range(4):
        satellite = EntityPath(
            Name=f"Constellation-Sat-{i+1}",
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
                    65.0,           # Inclination
                    0.0,            # Argument of periapsis
                    i * 90.0,       # RAAN: 0, 90, 180, 270
                    i * 45.0,       # Phased true anomaly
                ],
            ),
        )
        satellites.append(satellite)

    # Define coverage grid
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-60.0,
        MaxLatitude=60.0,
        Resolution=12.0,
        Height=0.0,
    )

    # Execute: Get summary statistics
    result = fom_number_of_assets(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T08:00:00.000Z",
        grid=grid,
        assets=satellites,
        output="grid_stats",
        step=120.0,
    )

    # Output: Display statistics
    print(f"Success: {result['IsSuccess']}")
    print(f"\nCoverage Depth Statistics:")
    print(f"  Minimum assets covering any point: {result['Minimum']:.1f}")
    print(f"  Maximum assets covering any point: {result['Maximum']:.1f}")
    print(f"  Mean assets per point: {result['Mean']:.2f}")
    print(f"  Standard deviation: {result['StdDev']:.2f}")


if __name__ == "__main__":
    main()
