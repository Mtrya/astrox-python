"""
Example: Generate Walker Constellation

This example demonstrates how to design Walker constellations, which are
symmetric satellite distributions used for global coverage (GPS, Galileo, etc.).

Walker notation: T/P/F where:
- T = Total number of satellites
- P = Number of orbital planes
- F = Phase factor (relative phasing between planes)

Common constellations:
- GPS: 24/6/1 (24 satellites, 6 planes, phase factor 1)
- Galileo: 27/3/1 (27 satellites, 3 planes, phase factor 1)
- OneWeb: 648/18/1 (648 satellites, 18 planes, phase factor 1)
"""

from astrox.models import KeplerElements
from astrox.orbit_wizard import design_walker


# Earth gravitational parameter (m³/s²)
EARTH_MU = 3.986004418e14


def main():
    """Generate Walker constellations with different configurations."""

    # Example 1: GPS-like constellation (24:6:1 Delta pattern)
    print("=" * 80)
    print("Example 1: GPS-like Walker Delta Constellation (24:6:1)")
    print("=" * 80)

    # Seed orbit: MEO at ~20,200 km altitude, 55° inclination
    seed_kepler = KeplerElements(
        SemimajorAxis=26560000.0,  # ~20,200 km altitude (m)
        Eccentricity=0.0,  # Circular orbit
        Inclination=55.0,  # deg
        ArgumentOfPeriapsis=0.0,  # deg (circular, so doesn't matter)
        RightAscensionOfAscendingNode=0.0,  # deg (seed plane)
        TrueAnomaly=0.0,  # deg
        GravitationalParameter=EARTH_MU
    )

    result = design_walker(
        seed_kepler=seed_kepler,
        num_planes=6,
        num_sats_per_plane=4,  # 6 planes × 4 sats = 24 total
        walker_type="Delta",
        inter_plane_phase_increment=1,  # Phase factor F=1
    )

    print(f"\nWalker Constellation: 24:6:1 (GPS-like)")
    print(f"  Total satellites: 24")
    print(f"  Number of planes: 6")
    print(f"  Satellites per plane: 4")
    print(f"  Pattern: Delta")
    print(f"  Phase factor: 1")
    print(f"\nSeed orbit:")
    print(f"  Altitude: ~20,200 km")
    print(f"  Inclination: 55.0°")
    print(f"  Eccentricity: 0.0 (circular)")
    print(f"\nConstellation data structure:")
    # API returns a dict with 'IsSuccess', 'Message', and 'WalkerSatellites' keys
    # 'WalkerSatellites' contains a 2D list [plane][satellite] of Kepler element dicts
    print(f"  Result keys: {list(result.keys())}")
    constellation = result['WalkerSatellites']
    print(f"  Number of planes: {len(constellation)}")  # Expected: 6 for GPS-like
    print(f"  Satellites in plane 0: {len(constellation[0])} satellites")  # Expected: 4 per plane
    print(f"\nSample Kepler elements for plane 0, satellite 0:")
    print(f"  Semimajor axis: {constellation[0][0]['SemimajorAxis']:.3f} m")  # Expected: ~2.7e7 m for MEO
    print(f"  Eccentricity: {constellation[0][0]['Eccentricity']}")          # Expected: ~0 (circular)
    print(f"  Inclination: {constellation[0][0]['Inclination']:.6f}°")      # Expected: 55° for GPS
    print(f"  RAAN: {constellation[0][0]['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {constellation[0][0]['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {constellation[0][0]['TrueAnomaly']:.6f}°")

    # Example 2: Smaller LEO constellation (18:3:1 Delta pattern)
    print("\n" + "=" * 80)
    print("Example 2: LEO Walker Delta Constellation (18:3:1)")
    print("=" * 80)

    # Seed orbit: LEO at 1000 km altitude, 87° inclination (near-polar)
    seed_kepler = KeplerElements(
        SemimajorAxis=7378000.0,  # 1000 km altitude (Earth radius ~6378 km)
        Eccentricity=0.0,  # Circular orbit
        Inclination=87.0,  # deg (near-polar for global coverage)
        ArgumentOfPeriapsis=0.0,  # deg
        RightAscensionOfAscendingNode=0.0,  # deg
        TrueAnomaly=0.0,  # deg
        GravitationalParameter=EARTH_MU
    )

    result = design_walker(
        seed_kepler=seed_kepler,
        num_planes=3,
        num_sats_per_plane=6,  # 3 planes × 6 sats = 18 total
        walker_type="Delta",
        inter_plane_phase_increment=1,  # Phase factor F=1
    )

    
    print(f"\nWalker Constellation: 18:3:1 (LEO)")
    print(f"  Total satellites: 18")
    print(f"  Number of planes: 3")
    print(f"  Satellites per plane: 6")
    print(f"  Pattern: Delta")
    print(f"  Phase factor: 1")
    print(f"\nKepler elements for plane 0, satellite 0:")
    constellation = result['WalkerSatellites']
    print(f"  Semimajor axis: {constellation[0][0]['SemimajorAxis']:.3f} m")  # Expected: ~7.4e6 m for 1000 km LEO
    print(f"  Eccentricity: {constellation[0][0]['Eccentricity']}")          # Expected: 0
    print(f"  Inclination: {constellation[0][0]['Inclination']:.6f}°")      # Expected: 87° near-polar
    print(f"  RAAN: {constellation[0][0]['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {constellation[0][0]['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {constellation[0][0]['TrueAnomaly']:.6f}°")


    # Example 3: Polar constellation (12:4:1 Delta pattern)
    print("\n" + "=" * 80)
    print("Example 3: Polar Walker Delta Constellation (12:4:1)")
    print("=" * 80)

    # Seed orbit: LEO at 600 km altitude, 90° inclination (polar)
    seed_kepler = KeplerElements(
        SemimajorAxis=6978000.0,  # 600 km altitude
        Eccentricity=0.0,  # Circular orbit
        Inclination=90.0,  # deg (polar orbit)
        ArgumentOfPeriapsis=0.0,  # deg
        RightAscensionOfAscendingNode=0.0,  # deg
        TrueAnomaly=0.0,  # deg
        GravitationalParameter=EARTH_MU
    )

    result = design_walker(
        seed_kepler=seed_kepler,
        num_planes=4,
        num_sats_per_plane=3,  # 4 planes × 3 sats = 12 total
        walker_type="Delta",
        inter_plane_phase_increment=1,  # Phase factor F=1 (must be 1 to num_planes-1)
    )

    print(f"\nWalker Constellation: 12:4:1")
    print(f"  Total satellites: 12")
    print(f"  Number of planes: 4")
    print(f"  Satellites per plane: 3")
    print(f"  Pattern: Delta")
    print(f"  Phase factor: 1")
    print(f"\nSeed orbit:")
    print(f"  Altitude: 600 km")
    print(f"  Inclination: 90.0° (polar)")
    print(f"\nKepler elements for plane 0, satellite 0:")
    constellation = result['WalkerSatellites']
    print(f"  Semimajor axis: {constellation[0][0]['SemimajorAxis']:.3f} m")  # Expected: ~6.978e6 m for 600 km LEO
    print(f"  Eccentricity: {constellation[0][0]['Eccentricity']}")          # Expected: 0
    print(f"  Inclination: {constellation[0][0]['Inclination']:.6f}°")      # Expected: 90° (polar)
    print(f"  RAAN: {constellation[0][0]['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {constellation[0][0]['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {constellation[0][0]['TrueAnomaly']:.6f}°")

    # Example 4: Custom constellation with manual spacing
    print("\n" + "=" * 80)
    print("Example 4: Custom Walker Constellation (8 satellites)")
    print("=" * 80)

    # Seed orbit: MEO at 10,000 km altitude, 60° inclination
    seed_kepler = KeplerElements(
        SemimajorAxis=16378000.0,  # 10,000 km altitude
        Eccentricity=0.0,  # Circular orbit
        Inclination=60.0,  # deg
        ArgumentOfPeriapsis=0.0,  # deg
        RightAscensionOfAscendingNode=0.0,  # deg
        TrueAnomaly=0.0,  # deg
        GravitationalParameter=EARTH_MU
    )

    result = design_walker(
        seed_kepler=seed_kepler,
        num_planes=2,
        num_sats_per_plane=4,  # 2 planes × 4 sats = 8 total
        walker_type="Custom",
        inter_plane_true_anomaly_increment=45.0,  # deg spacing in true anomaly
        raan_increment=90.0,  # deg spacing between planes
    )

    print(f"\nCustom Walker Constellation:")
    print(f"  Total satellites: 8")
    print(f"  Number of planes: 2")
    print(f"  Satellites per plane: 4")
    print(f"  Pattern: Custom")
    print(f"  True anomaly increment: 45.0°")
    print(f"  RAAN increment: 90.0°")
    print(f"\nSeed orbit:")
    print(f"  Altitude: 10,000 km")
    print(f"  Inclination: 60.0°")
    print(f"\nKepler elements for plane 0, satellite 0:")
    constellation = result['WalkerSatellites']
    print(f"  Semimajor axis: {constellation[0][0]['SemimajorAxis']:.3f} m")  # Expected: ~1.638e7 m for 10,000 km MEO
    print(f"  Eccentricity: {constellation[0][0]['Eccentricity']}")          # Expected: 0
    print(f"  Inclination: {constellation[0][0]['Inclination']:.6f}°")      # Expected: 60° (seed orbit)
    print(f"  RAAN: {constellation[0][0]['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {constellation[0][0]['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {constellation[0][0]['TrueAnomaly']:.6f}°")

    # Example 5: Star pattern constellation
    print("\n" + "=" * 80)
    print("Example 5: Walker Star Constellation (9:3:2)")
    print("=" * 80)

    # Seed orbit: LEO at 800 km altitude, 75° inclination
    seed_kepler = KeplerElements(
        SemimajorAxis=7178000.0,  # 800 km altitude
        Eccentricity=0.0,  # Circular orbit
        Inclination=75.0,  # deg
        ArgumentOfPeriapsis=0.0,  # deg
        RightAscensionOfAscendingNode=0.0,  # deg
        TrueAnomaly=0.0,  # deg
        GravitationalParameter=EARTH_MU
    )

    result = design_walker(
        seed_kepler=seed_kepler,
        num_planes=3,
        num_sats_per_plane=3,  # 3 planes × 3 sats = 9 total
        walker_type="Star",
        inter_plane_phase_increment=2,  # Phase factor F=2
    )

    print(f"\nWalker Constellation: 9:3:2 (Star)")
    print(f"  Total satellites: 9")
    print(f"  Number of planes: 3")
    print(f"  Satellites per plane: 3")
    print(f"  Pattern: Star")
    print(f"  Phase factor: 2")
    print(f"\nSeed orbit:")
    print(f"  Altitude: 800 km")
    print(f"  Inclination: 75.0°")
    print(f"\nKepler elements for plane 0, satellite 0:")
    constellation = result['WalkerSatellites']
    print(f"  Semimajor axis: {constellation[0][0]['SemimajorAxis']:.3f} m")  # Expected: ~7.178e6 m for 800 km LEO
    print(f"  Eccentricity: {constellation[0][0]['Eccentricity']}")          # Expected: 0
    print(f"  Inclination: {constellation[0][0]['Inclination']:.6f}°")      # Expected: 75° (seed orbit)
    print(f"  RAAN: {constellation[0][0]['RightAscensionOfAscendingNode']:.6f}°")
    print(f"  Argument of periapsis: {constellation[0][0]['ArgumentOfPeriapsis']:.6f}°")
    print(f"  True anomaly: {constellation[0][0]['TrueAnomaly']:.6f}°")

    print("\n" + "=" * 80)
    print("Notes on Walker Constellations:")
    print("  - Delta pattern: Most common, provides uniform coverage")
    print("  - Star pattern: Alternative symmetric distribution")
    print("  - Custom pattern: Manual control over spacing")
    print("  - Phase factor F: Controls relative phasing between planes")
    print("    IMPORTANT: F must be in range [1, num_planes-1]")
    print("    F cannot be 0 or >= num_planes")
    print("    For 4 planes: valid F values are 1, 2, 3")
    print("    For 6 planes: valid F values are 1, 2, 3, 4, 5")
    print("  - RAAN spacing: Planes equally distributed around equator")
    print("  - True anomaly: Satellites equally spaced within each plane")
    print("  - API returns 2D list of Kepler element dicts per satellite")
    print("=" * 80)


if __name__ == "__main__":
    main()
