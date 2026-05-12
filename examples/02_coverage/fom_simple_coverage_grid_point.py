# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Simple Coverage FOM - Grid Point Output

Demonstrates fom_simple_coverage() with output="grid_point" to get
binary coverage values (0 or 1) for each individual grid point.

API: POST /Coverage/FOM/ValueByGridPoint/SimpleCoverage
"""

from astrox.coverage import fom_simple_coverage
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create a simple LEO satellite
    satellite = EntityPath(
        Name="LEO-Sat",
        Position=J2Position(
            **{"$type": "J2"},
            CentralBody="Earth",
            J2NormalizedValue=0.000484165143790815,
            RefDistance=6378137.0,
            OrbitEpoch="2024-01-01T00:00:00.000Z",
            CoordSystem="Inertial",
            CoordType="Classical",
            OrbitalElements=[
                6978137.0,  # Semi-major axis (600 km altitude)
                0.001,      # Eccentricity
                55.0,       # Inclination (deg)
                0.0,        # Argument of periapsis
                0.0,        # RAAN
                0.0,        # True anomaly
            ],
        ),
    )

    # Define coverage grid
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-30.0,
        MaxLatitude=30.0,
        Resolution=10.0,
        Height=0.0,
    )

    # Execute: Get per-grid-point coverage values
    result = fom_simple_coverage(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T06:00:00.000Z",
        grid=grid,
        assets=[satellite],
        output="grid_point",
        step=120.0,
    )

    # Output: Display coverage values for each grid point
    print(f"Success: {result['IsSuccess']}")
    print(f"Grid points analyzed: {len(result['FOMValues'])}")

    # Count covered vs uncovered points
    covered = sum(1 for v in result["FOMValues"] if v > 0)
    print(f"Points with coverage: {covered}")
    print(f"Points without coverage: {len(result['FOMValues']) - covered}")

    # Show first few values
    print(f"\nFirst 10 coverage values: {result['FOMValues'][:10]}")


if __name__ == "__main__":
    main()
