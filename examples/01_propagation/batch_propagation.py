"""Example: Batch Orbit Propagation

This example demonstrates batch propagation capabilities that allow
propagating multiple satellites to a common epoch simultaneously.
This is useful for:
- Constellation state updates
- Collision screening
- Mission planning with multiple assets

We'll demonstrate all three batch propagators:
1. Two-Body Batch: Fast, simple dynamics
2. J2 Batch: Includes Earth oblateness
3. SGP4 Batch: For TLE catalog propagation
"""

from astrox.propagator import (
    propagate_two_body_batch,
    propagate_j2_batch,
    propagate_sgp4_batch
)
from astrox.models import KeplerElementsWithEpoch


def example_two_body_batch():
    """Propagate a small constellation using two-body dynamics."""

    print("\n" + "=" * 60)
    print("Example 1: Two-Body Batch Propagation (3-satellite constellation)")
    print("=" * 60)

    # Define a small Walker constellation in LEO
    # 3 satellites in different orbital planes
    earth_radius = 6378137.0
    altitude = 550000.0  # 550 km (Starlink-like altitude)
    semi_major_axis = earth_radius + altitude

    # Create three satellites with different RAAN values
    satellites = []
    for i in range(3):
        sat = KeplerElementsWithEpoch(
            OrbitEpoch="2024-01-01T00:00:00.000Z",
            SemimajorAxis=semi_major_axis,
            Eccentricity=0.0001,
            Inclination=53.0,  # Starlink inclination
            ArgumentOfPeriapsis=0.0,
            RightAscensionOfAscendingNode=i * 120.0,  # 120° apart
            TrueAnomaly=0.0,
            GravitationalParameter=3.986004418e14,  # Earth's GM
        )
        satellites.append(sat)

    print(f"\nPropagating {len(satellites)} satellites to common epoch...")
    print(f"Initial epoch: 2024-01-01T00:00:00.000Z")
    print(f"Target epoch:  2024-01-02T00:00:00.000Z (1 day later)")

    # Propagate all satellites to 1 day later
    result = propagate_two_body_batch(
        epoch="2024-01-02T00:00:00.000Z",
        all_satellite_elements=satellites
    )

    # The API returns 'AllElementsAtEpoch' list with updated orbital elements
    updated_elements = result['AllElementsAtEpoch']
    print(f"\nUpdated orbital elements for {len(updated_elements)} satellites:")
    for i, elem in enumerate(updated_elements):
        print(f"\n  Satellite {i+1}:")
        print(f"    SMA: {elem['SemimajorAxis']/1e6:.3f} km")  # should be ~6.928 km
        print(f"    Inc: {elem['Inclination']:.4f}°")  # should be ~53.0°
        print(f"    RAAN: {elem['RightAscensionOfAscendingNode']:.4f}°")  # varies by 120° per sat
        print(f"    TA: {elem['TrueAnomaly']:.4f}°")  # should be ~19.77° after 1 day


def example_j2_batch():
    """Propagate satellites with J2 perturbation effects."""

    print("\n" + "=" * 60)
    print("Example 2: J2 Batch Propagation (5-satellite constellation)")
    print("=" * 60)

    # Sun-synchronous constellation at different altitudes
    earth_radius = 6378137.0
    altitudes = [500000, 600000, 700000, 800000, 900000]  # Different altitudes

    satellites = []
    for alt in altitudes:
        sma = earth_radius + alt
        sat = KeplerElementsWithEpoch(
            OrbitEpoch="2024-01-01T00:00:00.000Z",
            SemimajorAxis=sma,
            Eccentricity=0.001,
            Inclination=97.5,  # Sun-synchronous
            ArgumentOfPeriapsis=90.0,
            RightAscensionOfAscendingNode=0.0,
            TrueAnomaly=0.0,
            GravitationalParameter=3.986004418e14,
        )
        satellites.append(sat)

    print(f"\nPropagating {len(satellites)} satellites at different altitudes...")
    print(f"Altitudes: {[a/1000 for a in altitudes]} km")
    print(f"Initial epoch: 2024-01-01T00:00:00.000Z")
    print(f"Target epoch:  2024-01-08T00:00:00.000Z (7 days later)")

    # Propagate for 7 days to see J2 effects
    result = propagate_j2_batch(
        epoch="2024-01-08T00:00:00.000Z",
        all_satellite_elements=satellites
    )

    print(f"\nSuccess: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")
    updated_elements = result['AllElementsAtEpoch']
    print(f"\nJ2 Perturbation Effects (7 days):")
    print(f"{'Altitude (km)':<15} {'ΔRAAN (°)':<12} {'ΔArgPeri (°)':<15}")
    print("-" * 45)

    for i, (elem, alt) in enumerate(zip(updated_elements, altitudes)):
        delta_raan = elem['RightAscensionOfAscendingNode'] - 0.0  # should be ~6.9° for 500km
        delta_w = elem['ArgumentOfPeriapsis'] - 90.0  # should be ~ -24.5° for 500km
        print(f"{alt/1000:<15.0f} {delta_raan:<12.6f} {delta_w:<15.6f}")


def example_sgp4_batch():
    """Propagate multiple satellites from TLE catalog."""

    print("\n" + "=" * 60)
    print("Example 3: SGP4 Batch Propagation (4 satellites from TLEs)")
    print("=" * 60)

    # Sample TLEs for different satellites
    # ISS, HST (Hubble), and two fictional satellites
    # Note: Each satellite's two TLE lines are joined with \n into a single string
    tle_catalog = [
        # ISS
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9990\n2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
        # Hubble Space Telescope
        "1 20580U 90037B   24001.00000000  .00000000  00000-0  00000-0 0  9999\n2 20580  28.4690 123.4560 0002800  45.6780 314.4560 15.09730000123456",
        # Fictional LEO satellite 1
        "1 99991U 23001A   24001.00000000  .00001500  00000-0  35000-4 0  9999\n2 99991  98.2000  15.0000 0001000  90.0000   0.0000 14.57000000123456",
        # Fictional LEO satellite 2
        "1 99992U 23002A   24001.00000000  .00001500  00000-0  35000-4 0  9999\n2 99992  98.2000 135.0000 0001000  90.0000   0.0000 14.57000000123456",
    ]

    print(f"\nPropagating {len(tle_catalog)} satellites from TLE catalog...")
    print(f"TLE epoch: 2024-01-01")
    print(f"Target epoch: 2024-01-03T00:00:00.000Z (2 days later)")

    # Propagate all TLEs to common epoch
    result = propagate_sgp4_batch(
        epoch="2024-01-03T00:00:00.000Z",
        tles=tle_catalog
    )

    print(f"\nSuccess: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")
    updated_elements = result['AllElementsAtEpoch']
    satellite_names = ["ISS", "Hubble", "SSO-1", "SSO-2"]

    print(f"\nUpdated orbital elements:")
    print(f"{'Satellite':<10} {'SMA (km)':<12} {'Inc (°)':<10} {'Ecc':<12}")
    print("-" * 50)

    for name, elem in zip(satellite_names, updated_elements):
        sma_km = elem['SemimajorAxis'] / 1000.0  # should be ~6771 km for ISS
        inc = elem['Inclination']  # should be ~51.6° for ISS
        ecc = elem['Eccentricity']  # small value ~0.0002
        print(f"{name:<10} {sma_km:<12.2f} {inc:<10.4f} {ecc:<12.6f}")


def main():
    """Run all batch propagation examples."""

    print("\n" + "=" * 70)
    print(" BATCH ORBIT PROPAGATION EXAMPLES")
    print("=" * 70)
    print("\nBatch propagation allows efficient state updates for multiple")
    print("satellites simultaneously. This is essential for:")
    print("  - Constellation management")
    print("  - Conjunction screening")
    print("  - Multi-asset mission planning")

    # Run all three examples
    example_two_body_batch()
    example_j2_batch()
    example_sgp4_batch()

    print("\n" + "=" * 70)
    print("Batch Propagation Summary:")
    print("-" * 70)
    print("Two-Body Batch: Fastest, suitable for short durations")
    print("J2 Batch:       Accurate for most Earth satellites")
    print("SGP4 Batch:     Standard for TLE catalog processing")
    print()
    print("All batch methods propagate to a single common epoch,")
    print("enabling direct comparison and conjunction analysis.")
    print("=" * 70)


if __name__ == "__main__":
    main()
