"""
Figure of Merit (FOM) Calculations Example

Demonstrates all 5 FOM functions:
1. fom_simple_coverage() - Binary coverage (0 or 1)
2. fom_coverage_time() - Total coverage time
3. fom_number_of_assets() - Number of assets providing coverage
4. fom_response_time() - Time to first coverage
5. fom_revisit_time() - Time between successive passes

Each FOM supports multiple output types:
- "grid_point": Values for each grid point over time
- "grid_point_at_time": Values at a specific time instant
- "grid_stats": Statistical summary (min, max, mean)
- "grid_stats_over_time": Statistics evolution over time
"""

from __future__ import annotations

from astrox.coverage import (
    fom_coverage_time,
    fom_number_of_assets,
    fom_response_time,
    fom_revisit_time,
    fom_simple_coverage,
)
from astrox.models import (
    EntityPath,
    J2Position,
)
from astrox._models import (
    CoverageGridLatitudeBounds,
)


def create_constellation():
    """Create a sample 6-satellite LEO constellation for FOM analysis."""
    satellites = []

    # Walker constellation: 3 planes, 2 satellites per plane
    # Orbit: 600 km altitude, 55° inclination
    altitude = 600000.0  # meters
    sma = 6378137.0 + altitude
    inclination = 55.0

    plane_spacing = 360.0 / 3  # 120° between planes
    sat_spacing = 360.0 / 2  # 180° between satellites in same plane

    for plane in range(3):
        raan = plane * plane_spacing
        for sat in range(2):
            true_anomaly = sat * sat_spacing

            satellite = EntityPath(
                Name=f"Walker-P{plane + 1}S{sat + 1}",
                Description=f"Plane {plane + 1}, Satellite {sat + 1}",
                Position=J2Position(
                    **{'$type': 'J2'},
                    CentralBody="Earth",
                    J2NormalizedValue=0.000484165143790815,
                    RefDistance=6378137.0,
                    OrbitEpoch="2024-01-01T00:00:00.000Z",
                    CoordSystem="Inertial",
                    CoordType="Classical",
                    OrbitalElements=[
                        sma,           # Semi-major axis (m)
                        0.001,         # Eccentricity
                        inclination,   # Inclination (deg)
                        0.0,           # Argument of periapsis (deg)
                        raan,          # RAAN (deg)
                        true_anomaly,  # True anomaly (deg)
                    ],
                ),
            )
            satellites.append(satellite)

    return satellites


def demo_simple_coverage():
    """Demonstrate simple binary coverage FOM (0 or 1)."""
    print("=" * 70)
    print("1. SIMPLE COVERAGE FOM - Binary Coverage Indicator")
    print("=" * 70)
    print("\nReturns 1 if grid point is covered, 0 otherwise.")

    # Time window
    start_time = "2024-01-01T00:00:00.000Z"
    stop_time = "2024-01-01T06:00:00.000Z"

    # Create constellation
    satellites = create_constellation()
    print(f"\nConstellation: {len(satellites)} satellites (3x2 Walker)")

    # Coverage grid
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-60.0,
        MaxLatitude=60.0,
        Resolution=15.0,  # 15° for faster computation
        Height=0.0,
    )

    # Example 1: Grid stats (summary statistics)
    print("\n--- Output: grid_stats (summary) ---")
    result = fom_simple_coverage(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        description="Simple coverage FOM - grid stats",
        step=120.0,  # 2-minute steps
    )

    if result["IsSuccess"]:
        print(f"✓ Computation successful")
        print(f"  Minimum coverage: {result['Minimum']}")
        print(f"  Maximum coverage: {result['Maximum']}")
        print(f"  Mean coverage: {result['Mean']:.4f}")
        print(f"  Std deviation: {result['StdDev']:.4f}")
    else:
        print(f"✗ Error: {result['Message']}")

    # Example 2: Grid point at specific time
    specific_time = "2024-01-01T03:00:00.000Z"
    print(f"\n--- Output: grid_point_at_time ({specific_time}) ---")
    result = fom_simple_coverage(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_point_at_time",
        time=specific_time,
        description="Simple coverage at specific time",
        step=120.0,
    )

    if result["IsSuccess"]:
        values = result["FOMValues"]
        covered = sum(1 for v in values if v > 0)
        total = len(values)
        coverage_pct = (covered / total * 100) if total > 0 else 0

        print(f"✓ Computation successful")
        print(f"  Total grid points: {total}")
        print(f"  Covered points at {specific_time}: {covered}")
        print(f"  Instantaneous coverage: {coverage_pct:.2f}%")
    else:
        print(f"✗ Error: {result['Message']}")


def demo_coverage_time():
    """Demonstrate coverage time FOM (total seconds of coverage)."""
    print("\n" + "=" * 70)
    print("2. COVERAGE TIME FOM - Total Coverage Duration")
    print("=" * 70)
    print("\nReturns total seconds each grid point is covered.")

    start_time = "2024-01-01T00:00:00.000Z"
    stop_time = "2024-01-01T24:00:00.000Z"  # Full day

    satellites = create_constellation()
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-60.0,
        MaxLatitude=60.0,
        Resolution=15.0,
        Height=0.0,
    )

    print("\n--- Output: grid_stats (24-hour analysis) ---")
    result = fom_coverage_time(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        description="Coverage time FOM",
        step=120.0,
    )

    if result["IsSuccess"]:
        total_seconds = 24 * 3600  # 24 hours in seconds
        min_time = result["Minimum"]
        max_time = result["Maximum"]
        mean_time = result["Mean"]

        print(f"✓ Computation successful")
        print(f"  Analysis period: 24 hours ({total_seconds} seconds)")
        print(f"  Minimum coverage time: {min_time:.1f} s ({min_time / 3600:.2f} hrs)")
        print(f"  Maximum coverage time: {max_time:.1f} s ({max_time / 3600:.2f} hrs)")
        print(f"  Mean coverage time: {mean_time:.1f} s ({mean_time / 3600:.2f} hrs)")
        print(f"  Mean coverage percentage: {(mean_time / total_seconds * 100):.2f}%")
    else:
        print(f"✗ Error: {result['Message']}")


def demo_number_of_assets():
    """Demonstrate number of assets FOM (satellite count)."""
    print("\n" + "=" * 70)
    print("3. NUMBER OF ASSETS FOM - Coverage Depth")
    print("=" * 70)
    print("\nReturns number of satellites simultaneously covering each point.")

    start_time = "2024-01-01T00:00:00.000Z"
    stop_time = "2024-01-01T12:00:00.000Z"

    satellites = create_constellation()
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-60.0,
        MaxLatitude=60.0,
        Resolution=15.0,
        Height=0.0,
    )

    # Grid stats over time shows how coverage depth evolves
    print("\n--- Output: grid_stats_over_time (12-hour evolution) ---")
    result = fom_number_of_assets(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats_over_time",
        description="Number of assets FOM over time",
        step=120.0,
    )

    if result["IsSuccess"]:
        stats_array = result["StatsArray"]
        print(f"✓ Computation successful")
        print(f"  Time points sampled: {len(stats_array)}")

        if stats_array:
            # Show statistics at a few sample times
            sample_indices = [0, len(stats_array) // 2, -1]
            for idx in sample_indices:
                if 0 <= idx < len(stats_array):
                    stat = stats_array[idx]
                    time = stat["Time"]
                    max_sats = stat["Maximum"]
                    mean_sats = stat["Mean"]
                    print(f"\n  Time: {time}")
                    print(f"    Max simultaneous satellites: {max_sats}")
                    print(f"    Mean simultaneous satellites: {mean_sats:.2f}")
    else:
        print(f"✗ Error: {result['Message']}")


def demo_response_time():
    """Demonstrate response time FOM (time to first coverage)."""
    print("\n" + "=" * 70)
    print("4. RESPONSE TIME FOM - Time to First Coverage")
    print("=" * 70)
    print("\nReturns seconds from analysis start until first coverage.")

    start_time = "2024-01-01T00:00:00.000Z"
    stop_time = "2024-01-01T12:00:00.000Z"

    satellites = create_constellation()
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-60.0,
        MaxLatitude=60.0,
        Resolution=15.0,
        Height=0.0,
    )

    print("\n--- Output: grid_stats (summary) ---")
    result = fom_response_time(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        description="Response time FOM",
        step=120.0,
    )

    if result["IsSuccess"]:
        min_response = result["Minimum"]
        max_response = result["Maximum"]
        mean_response = result["Mean"]

        print(f"✓ Computation successful")
        print(f"  Minimum response time: {min_response:.1f} s ({min_response / 60:.2f} min)")
        print(f"  Maximum response time: {max_response:.1f} s ({max_response / 60:.2f} min)")
        print(f"  Mean response time: {mean_response:.1f} s ({mean_response / 60:.2f} min)")
        print(
            f"\n  Interpretation: On average, a grid point waits {mean_response / 60:.1f} minutes"
        )
        print(f"                  from analysis start until first satellite coverage.")
    else:
        print(f"✗ Error: {result['Message']}")


def demo_revisit_time():
    """Demonstrate revisit time FOM (gap between coverage passes)."""
    print("\n" + "=" * 70)
    print("5. REVISIT TIME FOM - Coverage Gap Duration")
    print("=" * 70)
    print("\nReturns seconds between consecutive coverage passes (revisit gap).")

    start_time = "2024-01-01T00:00:00.000Z"
    stop_time = "2024-01-02T00:00:00.000Z"  # Full day for meaningful revisits

    satellites = create_constellation()
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-60.0,
        MaxLatitude=60.0,
        Resolution=15.0,
        Height=0.0,
    )

    print("\n--- Output: grid_stats (24-hour analysis) ---")
    result = fom_revisit_time(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        description="Revisit time FOM",
        step=120.0,
    )

    if result["IsSuccess"]:
        min_revisit = result["Minimum"]
        max_revisit = result["Maximum"]
        mean_revisit = result["Mean"]

        print(f"✓ Computation successful")
        print(
            f"  Minimum revisit time: {min_revisit:.1f} s ({min_revisit / 60:.2f} min)"
        )
        print(
            f"  Maximum revisit time: {max_revisit:.1f} s ({max_revisit / 3600:.2f} hrs)"
        )
        print(
            f"  Mean revisit time: {mean_revisit:.1f} s ({mean_revisit / 60:.2f} min)"
        )
        print(
            f"\n  Interpretation: On average, grid points have a {mean_revisit / 60:.1f}-minute gap"
        )
        print(f"                  between consecutive satellite passes.")
    else:
        print(f"✗ Error: {result['Message']}")


def demo_comparison():
    """Compare all FOMs for the same scenario."""
    print("\n" + "=" * 70)
    print("6. FOM COMPARISON - All Metrics Together")
    print("=" * 70)
    print("\nComparing all FOMs for same constellation and grid.")

    start_time = "2024-01-01T00:00:00.000Z"
    stop_time = "2024-01-01T12:00:00.000Z"

    satellites = create_constellation()
    grid = CoverageGridLatitudeBounds(
        MinLatitude=-30.0,
        MaxLatitude=30.0,
        Resolution=10.0,
        Height=0.0,
    )

    print(f"\nScenario: {len(satellites)}-satellite constellation")
    print(f"Grid: ±30° latitude, 10° resolution")
    print(f"Duration: 12 hours")

    results = {}

    # Simple coverage
    r = fom_simple_coverage(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        step=120.0,
    )
    if r["IsSuccess"]:
        results["Simple Coverage (mean)"] = f"{r['Mean']:.3f}"

    # Coverage time
    r = fom_coverage_time(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        step=120.0,
    )
    if r["IsSuccess"]:
        results["Coverage Time (mean hrs)"] = f"{r['Mean'] / 3600:.2f}"

    # Number of assets
    r = fom_number_of_assets(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        step=120.0,
    )
    if r["IsSuccess"]:
        results["Avg Satellites (mean)"] = f"{r['Mean']:.2f}"

    # Response time
    r = fom_response_time(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        step=120.0,
    )
    if r["IsSuccess"]:
        results["Response Time (mean min)"] = f"{r['Mean'] / 60:.1f}"

    # Revisit time
    r = fom_revisit_time(
        start=start_time,
        stop=stop_time,
        grid=grid,
        assets=satellites,
        output="grid_stats",
        step=120.0,
    )
    if r["IsSuccess"]:
        results["Revisit Time (mean min)"] = f"{r['Mean'] / 60:.1f}"

    # Display comparison table
    print("\n--- FOM Summary ---")
    for metric, value in results.items():
        print(f"  {metric:30s}: {value}")


def main():
    """Run all FOM examples."""
    print("\n" + "=" * 70)
    print("ASTROX FIGURE OF MERIT (FOM) EXAMPLES")
    print("=" * 70)
    print("\nDemonstrating 5 FOM functions:")
    print("  1. fom_simple_coverage() - Binary coverage indicator")
    print("  2. fom_coverage_time() - Total coverage duration")
    print("  3. fom_number_of_assets() - Simultaneous satellite count")
    print("  4. fom_response_time() - Time to first coverage")
    print("  5. fom_revisit_time() - Gap between passes")
    print()

    # Run examples
    demo_simple_coverage()
    demo_coverage_time()
    demo_number_of_assets()
    demo_response_time()
    demo_revisit_time()
    demo_comparison()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
