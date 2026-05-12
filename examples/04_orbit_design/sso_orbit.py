"""
Example: Generate Sun-Synchronous Orbit (SSO)

This example demonstrates how to design sun-synchronous orbits. SSO satellites
maintain a constant angle relative to the Sun, enabling consistent lighting
conditions for Earth observation missions.

Common local times:
- Dawn/dusk orbit: 6:00 or 18:00 (low solar interference)
- Morning orbit: 10:00-10:30 (optimal for optical imaging)
- Afternoon orbit: 13:00-14:00 (good contrast for SAR)
"""

from astrox.orbit_wizard import design_sso


def main():
    """Generate sun-synchronous orbits with different local times and altitudes."""

    # Example 1: Dawn/dusk orbit at 600 km
    print("=" * 80)
    print("Example 1: Dawn/Dusk SSO (6:00 AM, 600 km)")
    print("=" * 80)

    result = design_sso(
        orbit_epoch="2024-01-15T00:00:00.000Z",
        altitude=600.0,  # km - typical LEO altitude
        local_time_of_descending_node=6.0,  # 6:00 AM (dawn)
        description="Dawn/dusk SSO for low solar interference"
    )

    print(f"\nSSO Orbit Parameters:")
    print(f"  Epoch: 2024-01-15T00:00:00.000Z")
    print(f"  Altitude: 600.0 km")
    print(f"  Local time (descending node): 06:00 (dawn)")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}° (should be ~97.6° for SSO)")
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']:.6f}°")

    # Example 2: Morning orbit at 800 km (common for Earth observation)
    print("\n" + "=" * 80)
    print("Example 2: Morning SSO (10:30 AM, 800 km)")
    print("=" * 80)

    result = design_sso(
        orbit_epoch="2024-03-20T12:00:00.000Z",
        altitude=800.0,  # km - higher altitude for wider coverage
        local_time_of_descending_node=10.5,  # 10:30 AM
        description="Morning SSO for optical Earth observation"
    )

    print(f"\nSSO Orbit Parameters:")
    print(f"  Epoch: 2024-03-20T12:00:00.000Z")
    print(f"  Altitude: 800.0 km")
    print(f"  Local time (descending node): 10:30 (mid-morning)")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~7.0e6 m for 600-800 km altitude
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")           # Expected: ~0 (circular)
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")       # Expected: ~98° for SSO
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']}°")

    # Example 3: Afternoon orbit at 700 km
    print("\n" + "=" * 80)
    print("Example 3: Afternoon SSO (13:30 PM, 700 km)")
    print("=" * 80)

    result = design_sso(
        orbit_epoch="2024-06-21T18:00:00.000Z",
        altitude=700.0,  # km
        local_time_of_descending_node=13.5,  # 1:30 PM
        description="Afternoon SSO for SAR missions"
    )

    print(f"\nSSO Orbit Parameters:")
    print(f"  Epoch: 2024-06-21T18:00:00.000Z")
    print(f"  Altitude: 700.0 km")
    print(f"  Local time (descending node): 13:30 (early afternoon)")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")  # Expected: ~7.0e6 m for 600-800 km altitude
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")           # Expected: ~0 (circular)
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}°")       # Expected: ~98° for SSO
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']}°")

    # Example 4: Dusk orbit at 500 km
    print("\n" + "=" * 80)
    print("Example 4: Dusk SSO (18:00 PM, 500 km)")
    print("=" * 80)

    result = design_sso(
        orbit_epoch="2024-09-23T06:00:00.000Z",
        altitude=500.0,  # km - lower altitude for higher resolution
        local_time_of_descending_node=18.0,  # 6:00 PM (dusk)
        description="Dusk SSO for twilight imaging"
    )

    print(f"\nSSO Orbit Parameters:")
    print(f"  Epoch: 2024-09-23T06:00:00.000Z")
    print(f"  Altitude: 500.0 km")
    print(f"  Local time (descending node): 18:00 (dusk)")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}° (higher for lower altitude)")
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']}°")

    # Example 5: High-altitude SSO at 1000 km
    print("\n" + "=" * 80)
    print("Example 5: High-altitude SSO (12:00 PM, 1000 km)")
    print("=" * 80)

    result = design_sso(
        orbit_epoch="2024-12-21T00:00:00.000Z",
        altitude=1000.0,  # km - higher altitude for environmental monitoring
        local_time_of_descending_node=12.0,  # Noon
        description="High-altitude noon SSO"
    )

    print(f"\nSSO Orbit Parameters:")
    print(f"  Epoch: 2024-12-21T00:00:00.000Z")
    print(f"  Altitude: 1000.0 km")
    print(f"  Local time (descending node): 12:00 (noon)")
    print(f"\nKepler Elements (TOD frame):")
    print(f"  Semimajor axis: {result['Elements_TOD']['SemimajorAxis']:.3f} m")
    print(f"  Eccentricity: {result['Elements_TOD']['Eccentricity']}")
    print(f"  Inclination: {result['Elements_TOD']['Inclination']:.6f}° (lower for higher altitude)")
    print(f"  RAAN: {result['Elements_TOD']['RightAscensionOfAscendingNode']}°")
    print(f"  Argument of periapsis: {result['Elements_TOD']['ArgumentOfPeriapsis']}°")
    print(f"  True anomaly: {result['Elements_TOD']['TrueAnomaly']}°")

    print("\n" + "=" * 80)
    print("Notes:")
    print("  - SSO inclination varies with altitude (~97-98° for 600-800 km)")
    print("  - Lower altitude = higher inclination required")
    print("  - Local time is at descending node (southbound equatorial crossing)")
    print("  - Dawn/dusk orbits (6:00/18:00) minimize solar panel shadowing")
    print("  - Mid-morning orbits (10:00-10:30) optimal for optical imaging")
    print("  - Afternoon orbits (13:00-14:00) good for SAR and thermal imaging")
    print("=" * 80)


if __name__ == "__main__":
    main()
