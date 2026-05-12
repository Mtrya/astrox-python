"""
Example: Generate Molniya Orbit

This example demonstrates how to design a Molniya orbit. Molniya orbits are
highly elliptical orbits used for high-latitude communications, with:
- High inclination (~63.4° to minimize apsidal precession)
- 12-hour period (semi-synchronous)
- Apogee over high latitudes
- Low perigee altitude (typically 600 km)
"""

from astrox.orbit_wizard import design_molniya


def main():
    """Generate Molniya orbits with different configurations."""

    # Example 1: Classic Molniya with apogee over Russia (90°E)
    print("=" * 80)
    print("Example 1: Classic Molniya (Apogee over Russia at 90°E)")
    print("=" * 80)

    result = design_molniya(
        orbit_epoch="2024-01-15T00:00:00.000Z",
        perigee_altitude=600.0,  # km - typical low perigee
        apogee_longitude=90.0,  # 90°E - over Russia
        argument_of_periapsis=270.0,  # deg - apogee in northern hemisphere
        description="Molniya orbit for Russian communications"
    )

    print(f"\nMolniya Orbit Parameters:")
    print(f"  Epoch: 2024-01-15T00:00:00.000Z")
    print(f"  Perigee altitude: 600.0 km")
    print(f"  Apogee longitude: 90.0°E")
    print(f"  Argument of periapsis: 270.0°")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~2.7e7 m for 12-hour orbit
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")           # Expected: ~0.7 (highly elliptical)
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")       # Expected: ~63.4° (critical inclination)
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']:.6f}°")
    # Semimajor axis should reflect 12-hour period (~26,600 km)

    # Example 2: Molniya with apogee over North America (-100°W)
    print("\n" + "=" * 80)
    print("Example 2: Molniya (Apogee over North America at 100°W)")
    print("=" * 80)

    result = design_molniya(
        orbit_epoch="2024-06-21T12:00:00.000Z",
        perigee_altitude=500.0,  # km - slightly lower perigee
        apogee_longitude=-100.0,  # 100°W - over North America
        argument_of_periapsis=270.0,  # deg - apogee in northern hemisphere
        description="Molniya orbit for North American coverage"
    )

    print(f"\nMolniya Orbit Parameters:")
    print(f"  Epoch: 2024-06-21T12:00:00.000Z")
    print(f"  Perigee altitude: 500.0 km")
    print(f"  Apogee longitude: -100.0°W")
    print(f"  Argument of periapsis: 270.0°")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~2.7e7 m for 12-hour orbit
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")           # Expected: ~0.7 (highly elliptical)
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")       # Expected: ~63.4° (critical inclination)
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']:.6f}°")

    # Example 3: Southern hemisphere Molniya (arg of periapsis = 90°)
    print("\n" + "=" * 80)
    print("Example 3: Southern Hemisphere Molniya (Apogee at 90°)")
    print("=" * 80)

    result = design_molniya(
        orbit_epoch="2024-09-23T00:00:00.000Z",
        perigee_altitude=600.0,  # km
        apogee_longitude=0.0,  # Prime meridian
        argument_of_periapsis=90.0,  # deg - apogee in southern hemisphere
        description="Molniya orbit for southern hemisphere"
    )

    print(f"\nMolniya Orbit Parameters:")
    print(f"  Epoch: 2024-09-23T00:00:00.000Z")
    print(f"  Perigee altitude: 600.0 km")
    print(f"  Apogee longitude: 0.0°")
    print(f"  Argument of periapsis: 90.0° (southern hemisphere)")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~2.7e7 m for 12-hour orbit
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")           # Expected: ~0.7 (highly elliptical)
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")       # Expected: ~63.4° (critical inclination)
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']:.6f}°")

    # Example 4: Higher perigee Molniya
    print("\n" + "=" * 80)
    print("Example 4: Higher Perigee Molniya (1000 km)")
    print("=" * 80)

    result = design_molniya(
        orbit_epoch="2024-12-31T23:59:59.000Z",
        perigee_altitude=1000.0,  # km - higher perigee
        apogee_longitude=45.0,  # 45°E
        argument_of_periapsis=270.0,  # deg
        description="Molniya orbit with higher perigee"
    )

    print(f"\nMolniya Orbit Parameters:")
    print(f"  Epoch: 2024-12-31T23:59:59.000Z")
    print(f"  Perigee altitude: 1000.0 km")
    print(f"  Apogee longitude: 45.0°E")
    print(f"  Argument of periapsis: 270.0°")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~2.7e7 m for 12-hour orbit
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")           # Expected: ~0.7 (highly elliptical)
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")       # Expected: ~63.4° (critical inclination)
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']:.6f}°")

    print("\n" + "=" * 80)
    print("Notes:")
    print("  - Molniya orbits have ~63.4° inclination (critical inclination)")
    print("  - 12-hour orbital period (semi-synchronous)")
    print("  - Apogee typically at ~40,000 km altitude")
    print("  - Arg of periapsis 270° = apogee over northern hemisphere")
    print("  - Arg of periapsis 90° = apogee over southern hemisphere")
    print("=" * 80)


if __name__ == "__main__":
    main()
