"""
Example: Orbit Coordinate Conversions

This example demonstrates various orbital coordinate system conversions:
1. Kepler elements to position/velocity vectors (Kepler → R/V)
2. Position/velocity vectors to Kepler elements (R/V → Kepler)
3. Kepler elements to Latitude/Longitude/Altitude at ascending node
4. Lambert transfer delta-V calculation (GEO platform to target orbit)
5. Kozai-Izsak mean elements (J2 perturbation corrections)

These conversions are essential for orbit analysis, mission planning,
and trajectory optimization.
"""

from astrox.models import KeplerElements
from astrox.orbit_convert import (
    kepler_to_rv,
    rv_to_kepler,
    kepler_to_lla_at_ascending_node,
    geo_lambert_transfer_dv,
    kozai_izsak_mean_elements,
)


# Earth gravitational parameter (m³/s²)
EARTH_MU = 3.986004418e14


def main():
    """Demonstrate all orbital coordinate conversion functions."""

    # Example 1: Kepler to R/V (ISS-like orbit)
    print("=" * 80)
    print("Example 1: Kepler Elements → Position/Velocity Vectors")
    print("=" * 80)

    print("\nInput Kepler Elements (ISS-like LEO orbit):")
    print(f"  Semi-major axis: 6,778,000 m (~400 km altitude)")
    print(f"  Eccentricity: 0.0005 (nearly circular)")
    print(f"  Inclination: 51.6°")
    print(f"  Argument of periapsis: 0.0°")
    print(f"  RAAN: 45.0°")
    print(f"  True anomaly: 30.0°")

    result = kepler_to_rv(
        semimajor_axis=6778000.0,  # m (~400 km altitude)
        eccentricity=0.0005,  # Nearly circular
        inclination=51.6,  # deg (ISS inclination)
        argument_of_periapsis=0.0,  # deg
        right_ascension_of_ascending_node=45.0,  # deg
        true_anomaly=30.0,  # deg
        gravitational_parameter=EARTH_MU
    )

    print(f"\nResult (Position and Velocity):")
    print(f"  Position X: {result[0]:.3f} m")  # Expected: ~10^6 m for LEO
    print(f"  Position Y: {result[1]:.3f} m")
    print(f"  Position Z: {result[2]:.3f} m")
    print(f"  Velocity dX: {result[3]:.3f} m/s")  # Expected: ~10^3 m/s for LEO
    print(f"  Velocity dY: {result[4]:.3f} m/s")
    print(f"  Velocity dZ: {result[5]:.3f} m/s")

    # Example 2: R/V to Kepler (reverse conversion)
    print("\n" + "=" * 80)
    print("Example 2: Position/Velocity Vectors → Kepler Elements")
    print("=" * 80)

    # Use sample R/V from a GEO-like orbit
    position_velocity = [
        42164000.0, 0.0, 0.0,  # Position (m) - on X-axis at GEO radius
        0.0, 3074.66, 0.0  # Velocity (m/s) - circular velocity at GEO
    ]

    print(f"\nInput Position/Velocity:")
    print(f"  Position: [{position_velocity[0]:.1f}, {position_velocity[1]:.1f}, {position_velocity[2]:.1f}] m")
    print(f"  Velocity: [{position_velocity[3]:.3f}, {position_velocity[4]:.3f}, {position_velocity[5]:.3f}] m/s")

    result = rv_to_kepler(position_velocity=position_velocity)

    print(f"\nResult (Kepler Elements):")
    print(f"  Semimajor axis: {result['SemimajorAxis']} m")  # Expected: ~4.2e7 m for GEO
    print(f"  Eccentricity: {result['Eccentricity']}")       # Expected: ~0 (circular)
    print(f"  Inclination: {result['Inclination']}°")          # Expected: ~0° (equatorial)
    print(f"  Argument of periapsis: {result['ArgumentOfPeriapsis']}°")
    print(f"  RAAN: {result['RightAscensionOfAscendingNode']}°")
    print(f"  True anomaly: {result['TrueAnomaly']}°")


    # Example 3: Kepler to LLA at ascending node
    print("\n" + "=" * 80)
    print("Example 3: Kepler → Lat/Lon/Alt at Ascending Node")
    print("=" * 80)

    print("\nInput Kepler Elements (SSO orbit):")
    print(f"  Semi-major axis: 7,178,000 m (~800 km altitude)")
    print(f"  Eccentricity: 0.001 (nearly circular)")
    print(f"  Inclination: 98.0° (sun-synchronous)")
    print(f"  Argument of periapsis: 0.0°")
    print(f"  RAAN: 120.0°")
    print(f"  True anomaly: 0.0°")
    print(f"  Epoch: 2024-06-21T12:00:00.000Z")

    result = kepler_to_lla_at_ascending_node(
        semimajor_axis=7178000.0,  # m (~800 km altitude)
        eccentricity=0.001,  # Nearly circular
        inclination=98.0,  # deg (sun-synchronous)
        argument_of_periapsis=0.0,  # deg
        right_ascension_of_ascending_node=120.0,  # deg
        true_anomaly=0.0,  # deg
        gravitational_parameter=EARTH_MU,
        orbit_epoch="2024-06-21T12:00:00.000Z"
    )

    print(f"\nResult (LLA at Ascending Node):")
    print(f"  Latitude: {result[0]:.6f}°")   # Expected: ~0° (equator crossing)
    print(f"  Longitude: {result[1]:.6f}°")  # Expected: near input RAAN (120°)
    print(f"  Altitude: {result[2]:.3f} m")    # Expected: ~800 km (altitude)

    # Example 4: GEO Lambert transfer delta-V
    print("\n" + "=" * 80)
    print("Example 4: GEO Lambert Transfer Delta-V Calculation")
    print("=" * 80)

    # GEO platform orbit
    kepler_platform = KeplerElements(
        SemimajorAxis=42164000.0,  # m (GEO radius)
        Eccentricity=0.0,  # Circular
        Inclination=0.0,  # deg (equatorial)
        ArgumentOfPeriapsis=0.0,  # deg
        RightAscensionOfAscendingNode=0.0,  # deg
        TrueAnomaly=0.0,  # deg
        GravitationalParameter=EARTH_MU
    )

    # Target orbit (slightly inclined GEO)
    kepler_target = KeplerElements(
        SemimajorAxis=42164000.0,  # m (same altitude)
        Eccentricity=0.0,  # Circular
        Inclination=5.0,  # deg (5° plane change)
        ArgumentOfPeriapsis=0.0,  # deg
        RightAscensionOfAscendingNode=90.0,  # deg (different RAAN)
        TrueAnomaly=0.0,  # deg
        GravitationalParameter=EARTH_MU
    )

    time_of_flight = 3600.0  # 1 hour transfer

    print(f"\nPlatform orbit (GEO):")
    print(f"  Semi-major axis: 42,164 km")
    print(f"  Inclination: 0.0°")
    print(f"  RAAN: 0.0°")

    print(f"\nTarget orbit (inclined GEO):")
    print(f"  Semi-major axis: 42,164 km")
    print(f"  Inclination: 5.0°")
    print(f"  RAAN: 90.0°")

    print(f"\nTransfer time: {time_of_flight} seconds (1 hour)")

    result = geo_lambert_transfer_dv(
        kepler_platform=kepler_platform,
        kepler_target=kepler_target,
        time_of_flight=time_of_flight
    )

    print(f"\nResult (Delta-V components):")
    print(f"  Delta-V 1: {result[0]} m/s")  # Expected: ~10^3 m/s for plane change
    print(f"  Delta-V 2: {result[1]} m/s")  # Expected: ~10^3 m/s for plane change
    print(f"  Transfer time: {time_of_flight} s")

    # Example 5: Kozai-Izsak mean elements (J2 corrections)
    print("\n" + "=" * 80)
    print("Example 5: Kozai-Izsak Mean Elements (J2 Perturbations)")
    print("=" * 80)

    print("\nInput Osculating Kepler Elements (LEO circular orbit):")
    print(f"  Semi-major axis: 6,928,000 m (~550 km altitude)")
    print(f"  Eccentricity: 0.0 (circular)")
    print(f"  Inclination: 55.0°")
    print(f"  Argument of periapsis: 0.0°")
    print(f"  RAAN: 30.0°")
    print(f"  True anomaly: 45.0°")

    result = kozai_izsak_mean_elements(
        semimajor_axis=6928000.0,  # m (~550 km altitude)
        eccentricity=0.0,  # Circular orbit
        inclination=55.0,  # deg
        argument_of_periapsis=0.0,  # deg
        right_ascension_of_ascending_node=30.0,  # deg
        true_anomaly=45.0,  # deg
        gravitational_parameter=EARTH_MU
    )

    print(f"\nResult (Mean Kepler Elements accounting for J2):")
    print(f"  {result}")
    print("  Mean elements account for J2 short-period perturbations,")
    print("  providing more stable orbital parameters for propagation.")

    print("\n" + "=" * 80)
    print("Summary of Conversion Functions:")
    print("  1. kepler_to_rv: Classical elements → Cartesian state vectors")
    print("  2. rv_to_kepler: Cartesian state vectors → Classical elements")
    print("  3. kepler_to_lla_at_ascending_node: Elements → Ground track position")
    print("  4. geo_lambert_transfer_dv: Calculate transfer maneuver delta-V")
    print("  5. kozai_izsak_mean_elements: Osculating → Mean elements (J2)")
    print("=" * 80)


if __name__ == "__main__":
    main()
