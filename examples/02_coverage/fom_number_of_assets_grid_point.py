# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Number of Assets FOM - Grid Point Output

Demonstrates fom_number_of_assets() with output="grid_point" to get
the maximum number of assets simultaneously covering each grid point.

API: POST /Coverage/FOM/ValueByGridPoint/NumberOfAssets
"""

from astrox.coverage import fom_number_of_assets
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create a 6-satellite Walker constellation
    satellites = []
    altitude = 600000.0
    sma = 6378137.0 + altitude
    inclination = 55.0

    # 3 planes, 2 satellites per plane
    for plane in range(3):
        raan = plane * 120.0
        for sat in range(2):
            ta = sat * 180.0
            satellite = EntityPath(
                Name=f"Walker-P{plane}S{sat}",
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

    # Execute: Get per-grid-point asset counts
    result = fom_number_of_assets(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T06:00:00.000Z",
        grid=grid,
        assets=satellites,
        output="grid_point",
        step=120.0,
    )

    # Output: Display asset count distribution
    print(f"Success: {result['IsSuccess']}")
    print(f"Grid points: {len(result['FOMValues'])}")

    # Count distribution of asset coverage
    values = result["FOMValues"]
    max_assets = int(max(values))

    print(f"\nAsset count distribution:")
    for n in range(max_assets + 1):
        count = sum(1 for v in values if int(v) == n)
        pct = (count / len(values)) * 100
        print(f"  {n} assets: {count} points ({pct:.1f}%)")


if __name__ == "__main__":
    main()
