"""
Example: Generate Geostationary Orbit (GEO)

This example demonstrates how to design a geostationary orbit using the orbit wizard.
GEO satellites orbit at approximately 35,786 km altitude with zero inclination,
maintaining a fixed position over the Earth's equator.
"""

from astrox.orbit_wizard import design_geo


def main():
    """Generate geostationary orbit with different configurations."""

    # Example 1: Classic GEO at 0° inclination over 100°E longitude
    print("=" * 80)
    print("Example 1: Classic GEO (0° inclination, 100°E)")
    print("=" * 80)

    result = design_geo(
        orbit_epoch="2024-01-15T00:00:00.000Z",
        inclination=0.0,  # Zero inclination for true geostationary
        sub_satellite_point=100.0,  # 100°E longitude
        description="Classic GEO satellite at 100°E"
    )

    print(f"\nGEO Orbit Parameters (100°E):")
    print(f"  Epoch: 2024-01-15T00:00:00.000Z")
    print(f"  Inclination: 0.0°")
    print(f"  Sub-satellite point: 100.0°E")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~4.2e7 m for GEO
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']}°")

    # Example 2: Slightly inclined GEO (0.05° inclination) over 0° longitude
    print("\n" + "=" * 80)
    print("Example 2: Inclined GEO (0.05° inclination, 0°E Prime Meridian)")
    print("=" * 80)

    result = design_geo(
        orbit_epoch="2024-06-21T12:00:00.000Z",
        inclination=0.05,  # Slight inclination (realistic after orbit maintenance)
        sub_satellite_point=0.0,  # Prime meridian
        description="Inclined GEO over Prime Meridian"
    )

    print(f"\nGEO Orbit Parameters (0°E):")
    print(f"  Epoch: 2024-06-21T12:00:00.000Z")
    print(f"  Inclination: 0.05°")
    print(f"  Sub-satellite point: 0.0°E")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~4.2e7 m for GEO
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']}°")

    # Example 3: GEO over Western Hemisphere (-75°W)
    print("\n" + "=" * 80)
    print("Example 3: GEO over Western Hemisphere (-75°W)")
    print("=" * 80)

    result = design_geo(
        orbit_epoch="2024-09-23T00:00:00.000Z",
        inclination=0.0,
        sub_satellite_point=-75.0,  # 75°W longitude (western hemisphere)
        description="GEO satellite at 75°W"
    )

    print(f"\nGEO Orbit Parameters (75°W):")
    print(f"  Epoch: 2024-09-23T00:00:00.000Z")
    print(f"  Inclination: 0.0°")
    print(f"  Sub-satellite point: -75.0°W")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~4.2e7 m for GEO
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']}°")

    # Example 4: GEO over Asia-Pacific region (145°E)
    print("\n" + "=" * 80)
    print("Example 4: GEO over Asia-Pacific (145°E)")
    print("=" * 80)

    result = design_geo(
        orbit_epoch="2024-12-31T23:59:59.000Z",
        inclination=0.0,
        sub_satellite_point=145.0,  # 145°E longitude (Asia-Pacific)
        description="GEO satellite at 145°E"
    )

    print(f"\nGEO Orbit Parameters (145°E):")
    print(f"  Epoch: 2024-12-31T23:59:59.000Z")
    print(f"  Inclination: 0.0°")
    print(f"  Sub-satellite point: 145.0°E")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~4.2e7 m for GEO
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']}°")

    print("\n" + "=" * 80)
    print("Note: GEO orbits are at approximately 35,786 km altitude")
    print("      with orbital period of 24 hours (sidereal day)")
    print("      Semimajor axis ≈ 42,166 km (Earth radius ~6,378 km)")
    print("=" * 80)


if __name__ == "__main__":
    main()
