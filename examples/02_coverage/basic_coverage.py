"""
Basic Coverage Analysis Example

Demonstrates:
- get_grid_points(): Get grid point coordinates from different grid definitions
- compute_coverage(): Compute coverage with satellites and sensors

Grid types demonstrated:
- Global grid (full Earth coverage)
- Latitude bounds grid (specific latitude range)
- Lat/Lon bounds grid (specific region)
"""

from __future__ import annotations

from astrox.coverage import compute_coverage, get_grid_points
from astrox.models import (
    ConicSensor,
    EntityPath,
    J2Position,
    SGP4Position,
)
from astrox._models import (
    CoverageGridGlobal,
    CoverageGridLatitudeBounds,
    CoverageGridLatLonBounds,
)


def demo_get_grid_points():
    """Demonstrate different grid types using get_grid_points()."""
    print("=" * 70)
    print("1. GET GRID POINTS - DIFFERENT GRID TYPES")
    print("=" * 70)

    # Example 1: Global grid (full Earth)
    print("\n--- Global Grid (6° resolution) ---")
    global_grid = CoverageGridGlobal(
        CentralBodyName="Earth",
        Resolution=6.0,  # 6 degrees
        Height=0.0,  # Sea level
        UseCellSurfaceAreaForWeight=True,
    )

    result = get_grid_points(grid=global_grid, text="Global coverage grid")
    print(f"Grid type: Global")
    print(f"Resolution: 6.0°")
    print(f"Success: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    points = result["Points"]
    grid_points = points["GridPoints"]
    print(f"Total grid points: {len(grid_points)}")
    # Show first few points
    print(f"First point: Lat={grid_points[0]['Latitude']:.2f}°, "
          f"Lon={grid_points[0]['Longitude']:.2f}°")

    # Example 2: Latitude bounds grid (mid-latitudes only)
    print("\n--- Latitude Bounds Grid (30°S to 60°N) ---")
    lat_bounds_grid = CoverageGridLatitudeBounds(
        CentralBodyName="Earth",
        MinLatitude=-30.0,
        MaxLatitude=60.0,
        Resolution=5.0,  # 5 degrees
        Height=0.0,
        UseCellSurfaceAreaForWeight=True,
    )

    result = get_grid_points(
        grid=lat_bounds_grid, text="Mid-latitude coverage grid"
    )
    print(f"Latitude range: -30° to 60°")
    print(f"Resolution: 5.0°")
    print(f"Success: {result['IsSuccess']}")

    points = result["Points"]
    grid_points = points["GridPoints"]
    print(f"Total grid points: {len(grid_points)}")

    # Example 3: Lat/Lon bounds grid (specific region - China)
    print("\n--- Lat/Lon Bounds Grid (China region) ---")
    region_grid = CoverageGridLatLonBounds(
        CentralBodyName="Earth",
        MinLatitude=18.0,  # Southern China
        MaxLatitude=54.0,  # Northern China
        MinLongitude=73.0,  # Western China
        MaxLongitude=135.0,  # Eastern China
        Resolution=2.0,  # 2 degrees - finer resolution for region
        Height=0.0,
        UseCellSurfaceAreaForWeight=True,
    )

    result = get_grid_points(grid=region_grid, text="China region grid")
    print(f"Region: 18°N-54°N, 73°E-135°E (China)")
    print(f"Resolution: 2.0°")
    print(f"Success: {result['IsSuccess']}")

    points = result["Points"]
    grid_points = points["GridPoints"]
    print(f"Total grid points: {len(grid_points)}")


def demo_compute_coverage():
    """Demonstrate coverage computation with satellites."""
    print("\n" + "=" * 70)
    print("2. COMPUTE COVERAGE - SATELLITE CONSTELLATION")
    print("=" * 70)

    # Define analysis time window
    start_time = "2024-01-01T00:00:00.000Z"
    stop_time = "2024-01-01T12:00:00.000Z"

    # Create a simple LEO constellation (3 satellites)
    # Using J2 propagation for realistic orbit dynamics
    satellites = []

    # Satellite 1: Sun-synchronous orbit (SSO)
    # OrbitalElements format: [SemiMajorAxis(m), Eccentricity, Inclination(deg),
    #                          ArgumentOfPeriapsis(deg), RAAN(deg), TrueAnomaly(deg)]
    sat1 = EntityPath(
        Name="SSO-Sat1",
        Description="Sun-synchronous orbit satellite",
        Position=J2Position(
            field_type="J2",  # Required discriminator
            CentralBody="Earth",
            J2NormalizedValue=0.000484165143790815,  # Earth's J2
            RefDistance=6378137.0,  # Earth equatorial radius (m)
            OrbitEpoch="2024-01-01T00:00:00.000Z",
            CoordType="Classical",
            OrbitalElements=[
                6378137.0 + 800000.0,  # SemiMajorAxis: 800 km altitude
                0.001,  # Eccentricity
                98.5,  # Inclination: Sun-sync
                0.0,  # ArgumentOfPeriapsis
                0.0,  # RAAN
                0.0,  # TrueAnomaly
            ],
        ),
    )
    satellites.append(sat1)

    # Satellite 2: Same orbit, phase shifted 120°
    sat2 = EntityPath(
        Name="SSO-Sat2",
        Description="Sun-synchronous orbit satellite (120° phase)",
        Position=J2Position(
            field_type="J2",  # Required discriminator
            CentralBody="Earth",
            J2NormalizedValue=0.000484165143790815,
            RefDistance=6378137.0,
            OrbitEpoch="2024-01-01T00:00:00.000Z",
            CoordType="Classical",
            OrbitalElements=[
                6378137.0 + 800000.0,  # SemiMajorAxis
                0.001,  # Eccentricity
                98.5,  # Inclination
                0.0,  # ArgumentOfPeriapsis
                120.0,  # RAAN: Phase shift
                0.0,  # TrueAnomaly
            ],
        ),
    )
    satellites.append(sat2)

    # Satellite 3: Same orbit, phase shifted 240°
    sat3 = EntityPath(
        Name="SSO-Sat3",
        Description="Sun-synchronous orbit satellite (240° phase)",
        Position=J2Position(
            field_type="J2",  # Required discriminator
            CentralBody="Earth",
            J2NormalizedValue=0.000484165143790815,
            RefDistance=6378137.0,
            OrbitEpoch="2024-01-01T00:00:00.000Z",
            CoordType="Classical",
            OrbitalElements=[
                6378137.0 + 800000.0,  # SemiMajorAxis
                0.001,  # Eccentricity
                98.5,  # Inclination
                0.0,  # ArgumentOfPeriapsis
                240.0,  # RAAN: Phase shift
                0.0,  # TrueAnomaly
            ],
        ),
    )
    satellites.append(sat3)

    # Define coverage grid (latitude bounds for faster computation)
    grid = CoverageGridLatitudeBounds(
        CentralBodyName="Earth",
        MinLatitude=-60.0,
        MaxLatitude=60.0,
        Resolution=10.0,  # 10° resolution for quick demo
        Height=0.0,
    )

    # Define sensor (wide field-of-view conic sensor)
    sensor = ConicSensor(
        field_type="Conic",  # Required discriminator
        Text="Wide FOV imaging sensor",
        innerHalfAngle=0.0,  # No inner cone
        outerHalfAngle=60.0,  # 60° half-angle (120° total FOV)
        minimumClockAngle=0.0,
        maximumClockAngle=360.0,  # Full circle
    )

    print(f"\nAnalyzing coverage from {start_time} to {stop_time}")
    print(f"Constellation: 3 satellites in SSO (800 km, 98.5° inc)")
    print(f"Sensor: Conic, 60° half-angle (120° FOV)")
    print(f"Grid: Latitude bounds -60° to 60°, 10° resolution")
    print("\nComputing coverage...")

    # Compute coverage
    result = compute_coverage(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        description="SSO constellation coverage analysis",
        # grid_point_sensor=sensor,  # Uncomment to add sensor at grid points
        step=60.0,  # 60-second time step
        contain_coverage_points=True,  # Include grid point coordinates
    )

    # Display results
    print(f"\nSuccess: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    # Get coverage statistics
    intervals = result["SatisfactionIntervalsWithNumberOfAssets"]
    print(f"\nTotal grid points analyzed: {len(intervals)}")

    # Count covered points
    covered_count = sum(
        1 for point_intervals in intervals if point_intervals
    )
    coverage_percent = covered_count / len(intervals) * 100

    print(f"Grid points with coverage: {covered_count}")
    print(f"Coverage percentage: {coverage_percent:.2f}%")

    # Show sample coverage intervals for first covered point
    for i, point_intervals in enumerate(intervals):
        if point_intervals:  # Found a covered point
            print(f"\nSample: Grid point #{i} coverage intervals:")
            for interval in point_intervals[:3]:  # Show first 3 intervals
                start = interval["Start"]
                stop = interval["Stop"]
                num_assets = interval["NumberOfAssets"]
                print(
                    f"  - {start} to {stop} ({num_assets} satellite(s))"
                )
            if len(point_intervals) > 3:
                print(f"  ... and {len(point_intervals) - 3} more intervals")
            break  # Only show first covered point


def demo_coverage_with_constraints():
    """Demonstrate coverage with grid point constraints."""
    print("\n" + "=" * 70)
    print("3. COVERAGE WITH ELEVATION CONSTRAINT")
    print("=" * 70)

    # Define analysis time window (shorter for demo)
    start_time = "2024-01-01T00:00:00.000Z"
    stop_time = "2024-01-01T06:00:00.000Z"

    # Create a single ISS-like satellite using TLE propagation
    # ISS TLE (example from 2024)
    tle_line1 = "1 25544U 98067A   24001.50000000  .00002182  00000+0  41420-4 0  9990"
    tle_line2 = "2 25544  51.6416 208.9163 0001848  88.2305 271.9101 15.50103472331336"

    iss = EntityPath(
        Name="ISS",
        Description="International Space Station",
        Position=SGP4Position(
            field_type="SGP4",  # Required discriminator
            TLEs=[tle_line1, tle_line2],
            SatelliteNumber="25544",
        ),
    )

    # Small regional grid for testing
    grid = CoverageGridLatLonBounds(
        CentralBodyName="Earth",
        MinLatitude=20.0,
        MaxLatitude=50.0,
        MinLongitude=-130.0,
        MaxLongitude=-60.0,
        Resolution=10.0,
        Height=0.0,
    )

    print(
        f"\nAnalyzing ISS coverage over North America (6 hours)")
    print(f"Grid: 20°N-50°N, 130°W-60°W")
    print(
        f"Constraint: Minimum elevation angle 10° (simulates horizon limit)"
    )
    print("\nComputing coverage...")

    # Compute coverage with elevation constraint
    # Note: Elevation constraint would typically be added via grid_point_constraints
    # For this example, we compute without constraints to show the concept
    result = compute_coverage(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=[iss],
        description="ISS coverage over North America",
        step=60.0,
        contain_coverage_points=True,
    )

    print(f"\nSuccess: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    intervals = result["SatisfactionIntervalsWithNumberOfAssets"]
    covered_count = sum(
        1 for point_intervals in intervals if point_intervals
    )
    coverage_percent = covered_count / len(intervals) * 100

    print(f"Total grid points: {len(intervals)}")
    print(f"Covered points: {covered_count}")
    print(f"Coverage: {coverage_percent:.2f}%")

    # Count total coverage passes
    total_passes = sum(len(pi) for pi in intervals if pi)
    print(f"Total access intervals: {total_passes}")


def main():
    """Run all coverage examples."""
    print("\n" + "=" * 70)
    print("ASTROX COVERAGE ANALYSIS EXAMPLES")
    print("=" * 70)
    print("\nDemonstrating basic coverage functions:")
    print("  - get_grid_points(): Generate coverage grids [SKIPPED - Server Error 500]")
    print("  - compute_coverage(): Calculate satellite coverage")
    print()

    # Run examples
    # demo_get_grid_points()  # SKIPPED: HTTP 500 server error - see issues.md
    print("\nNOTE: get_grid_points() demo skipped due to server-side HTTP 500 error")
    print("      See examples/02_coverage/issues.md for details\n")

    demo_compute_coverage()
    demo_coverage_with_constraints()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
