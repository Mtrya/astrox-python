# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Response Time FOM - Grid Point Output

Demonstrates fom_response_time() with output="grid_point" to get
the time (in seconds) until first coverage for each individual grid point.

API: POST /Coverage/FOM/ValueByGridPoint/ResponseTime
"""

from astrox.coverage import fom_response_time
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create a 2-satellite constellation
    satellites = []
    altitude = 550000.0  # 550 km - Starlink-like
    sma = 6378137.0 + altitude

    for i in range(2):
        satellite = EntityPath(
            Name=f"Response-Sat-{i+1}",
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
                    53.0,           # Starlink-like inclination
                    0.0,
                    i * 180.0,      # Opposite RAAN
                    i * 90.0,       # Phased
                ],
            ),
        )
        satellites.append(satellite)

    # Define regional grid
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-40.0,
        MaxLatitude=40.0,
        Resolution=15.0,
        Height=0.0,
    )

    # Execute: Get per-grid-point response times
    result = fom_response_time(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T04:00:00.000Z",
        grid=grid,
        assets=satellites,
        output="grid_point",
        step=60.0,
    )

    # Output: Display response time statistics
    print(f"Success: {result['IsSuccess']}")
    print(f"Grid points: {len(result['FOMValues'])}")

    # Analyze response times
    times = result["FOMValues"]
    max_response = max(times)
    min_response = min(times)

    print(f"\nResponse Time Analysis:")
    print(f"  Fastest response: {min_response:.1f} s ({min_response / 60:.1f} min)")
    print(f"  Slowest response: {max_response:.1f} s ({max_response / 60:.1f} min)")
    print(f"  Mean response: {sum(times) / len(times):.1f} s")

    # Count points with sub-30-minute response
    fast_count = sum(1 for t in times if t < 1800)
    print(f"  Points with <30 min response: {fast_count} ({fast_count / len(times) * 100:.1f}%)")


if __name__ == "__main__":
    main()
