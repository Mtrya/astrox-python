"""Example: SGP4 Orbit Propagation from TLE

This example demonstrates SGP4 propagation using Two-Line Element (TLE) sets.
SGP4 is the standard model for propagating satellite orbits from publicly
available TLE data.

We'll propagate the International Space Station (ISS) orbit using real TLE data.
"""

from astrox.propagator import propagate_sgp4


def main():
    # ISS TLE (Two-Line Element Set)
    # These are NORAD catalog elements that encode the orbit and drag parameters
    # Line 1: Catalog number, epoch, ballistic coefficient, etc.
    # Line 2: Orbital elements in TEME (True Equator Mean Equinox) frame

    tle_lines = [
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9990",
        "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456"
    ]

    print("Propagating ISS orbit using SGP4...")
    print(f"TLE Line 1: {tle_lines[0]}")
    print(f"TLE Line 2: {tle_lines[1]}")
    print()

    # Propagate for 3 days with 2-minute steps
    result = propagate_sgp4(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-04T00:00:00.000Z",
        tles=tle_lines,
        step=120.0,  # 2-minute steps
        satellite_number="25544",  # ISS NORAD catalog number
    )

    # Print results
    print("=" * 60)
    print("SGP4 Propagation Results (ISS)")
    print("=" * 60)
    print(f"Success: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    # Access position data from 'Position' dict's 'cartesianVelocity' field
    positions = result['Position']['cartesianVelocity']
    num_points = len(positions) // 3
    print(f"\nGenerated {num_points} position points")  # should be 2161 for 3 days at 120s steps
    print(f"Step size: 120 seconds (2 minutes)")
    print(f"Duration: 3 days")

    # ISS orbital period is approximately 92.9 minutes
    iss_period_minutes = 92.9
    orbits_per_day = 1440 / iss_period_minutes

    print(f"\nISS orbital period: ~{iss_period_minutes:.1f} minutes")
    print(f"Orbits per day: ~{orbits_per_day:.1f}")
    print(f"Total orbits in 3 days: ~{orbits_per_day * 3:.0f}")

    # Show sample positions
    print(f"\nSample positions (first 3 points):")
    for i in range(min(3, num_points)):
        idx = i * 3
        if idx + 2 < len(positions):
            x, y, z = positions[idx:idx+3]
            r = (x**2 + y**2 + z**2) ** 0.5
            altitude_km = (r - 6378137.0) / 1000.0
            print(f"  Point {i+1}: r={r/1e6:.3f} km, alt={altitude_km:.1f} km")

    print("\n" + "=" * 60)
    print("SGP4 Model Features:")
    print("- Incorporates atmospheric drag (from TLE B* parameter)")
    print("- Includes simplified perturbations (J2, J3, J4)")
    print("- Standard for NORAD catalog orbit predictions")
    print("- Accuracy degrades after 5-7 days from TLE epoch")
    print("=" * 60)


if __name__ == "__main__":
    main()
