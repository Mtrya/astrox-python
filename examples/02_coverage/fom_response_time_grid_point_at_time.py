# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Response Time FOM - Grid Point At Time Output

Demonstrates fom_response_time() with output="grid_point_at_time" to get
response times calculated from a specific time instant (not analysis start).

API: POST /Coverage/FOM/ValueByGridPointAtTime/ResponseTime
"""

from astrox.coverage import fom_response_time
from astrox.models import EntityPath, J2Position
from astrox._models import CoverageGridLatitudeBounds


def main():
    # Setup: Create a 3-satellite constellation
    satellites = []
    altitude = 650000.0
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
                    58.0,
                    0.0,
                    i * 120.0,
                    i * 60.0,
                ],
            ),
        )
        satellites.append(satellite)

    # Define coverage grid
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-45.0,
        MaxLatitude=45.0,
        Resolution=15.0,
        Height=0.0,
    )

    # Specific time for response calculation (2 hours after start)
    specific_time = "2024-01-01T02:00:00.000Z"

    # Execute: Get response times from specific time
    result = fom_response_time(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T06:00:00.000Z",
        grid=grid,
        assets=satellites,
        output="grid_point_at_time",
        time=specific_time,
        step=60.0,
    )

    # Output: Display response times from the specified time
    print(f"Success: {result['IsSuccess']}")
    print(f"Reference time: {specific_time}")
    print(f"Grid points: {len(result['FOMValues'])}")

    # Analyze response times from this specific instant
    times = result["FOMValues"]
    valid_times = [t for t in times if t >= 0]  # Filter valid responses

    print(f"\nResponse Time from {specific_time}:")
    print(f"  Minimum: {min(valid_times):.1f} s ({min(valid_times) / 60:.1f} min)")
    print(f"  Maximum: {max(valid_times):.1f} s ({max(valid_times) / 60:.1f} min)")
    print(f"  Mean: {sum(valid_times) / len(valid_times):.1f} s")


if __name__ == "__main__":
    main()
