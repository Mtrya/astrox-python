"""
Example: Earth-Moon Libration (Lagrange) Points

This example demonstrates how to calculate the five Earth-Moon Lagrange points
(L1, L2, L3, L4, L5). These are points of gravitational equilibrium in the
Earth-Moon system, crucial for mission planning to:

- L1: Gateway to Moon, solar observation (between Earth and Moon)
- L2: Far-side Moon communications, deep space observation
- L3: Opposite Moon's orbit, research purposes
- L4/L5: Trojan points, stable locations for space stations

Lagrange points are used for missions like:
- NASA's Artemis Lunar Gateway (Near Rectilinear Halo Orbit around L2)
- James Webb Space Telescope (Sun-Earth L2)
- Future communication relays and space stations

CRITICAL: Server-side error prevents actual computation.
The orbit system API endpoints currently fail with:
    "EntityPositionCzml.GetDateMotionCollection()"
This is a server-side bug in the orbit system API implementation.
The examples document the expected schema outputs.
"""

# The libration API endpoint is experiencing server-side errors.
#  Expected response schema: CzmlPositionSTMOut
#  {
#    'IsSuccess': bool,
#    'Message': str | null,
#    'position': {
#      'epoch': str,
#      'referenceFrame': str,
#      'cartesian': list[float]  # 15 values for 5 Lagrange points (x,y,z each)
#    }
#  }
#  See inline comments for specific field access patterns.

from astrox.orbit_system import compute_earth_moon_libration


def main():
    """Calculate Earth-Moon Lagrange points at different epochs."""

    print("=" * 80)
    print("Earth-Moon Lagrange Points Computation")
    print("=" * 80)

    # Note: The orbit system API endpoints are currently experiencing server-side errors
    # The server fails with "EntityPositionCzml.GetDateMotionCollection()" even with valid payloads.
    # This appears to be a server-side bug in the orbit system API implementation.

    # Example 1: Compute libration points at J2000 epoch (v2 API)
    print("\nExample 1: J2000 Epoch (v2 API)")
    print("-" * 50)

    epoch = "2000-01-01T12:00:00Z"  # J2000 standard epoch

    print(f"\nInput:")
    print(f"  Epoch: {epoch} (J2000)")
    print(f"  Version: v2 (default)")
    print(f"  Central body: Earth (default)")
    print(f"  Reference frame: FIXED (default)")
    print(f"  Interpolation: LAGRANGE order 7 (default)")

    print(f"\nError: Server-side error: EntityPositionCzml.GetDateMotionCollection()")
    print(f"       The libration endpoint fails to process even valid payloads.")

    print(f"  Expected Output: CzmlPositionSTMOut")
    print(f"    position.cartesian: 15 values (5 Lagrange points × 3 coordinates)")
    print(f"    L1 ≈ [326,000 km, 0, 0] from Earth")
    print(f"    L2 ≈ [449,000 km, 0, 0] from Earth")
    print(f"    L3 ≈ [381,000 km, 0, 0] from Earth")
    print(f"    L4/L5 ≈ 384,400 km from Earth, ±60° from Moon")

    # Example 2: Different epoch and settings
    print("\n" + "=" * 80)
    print("Example 2: Different Configurations")
    print("=" * 80)

    print("\n2a. Apollo 11 Anniversary (2024)")
    print("-" * 30)
    epoch = "2024-07-20T20:17:00Z"
    print(f"  Epoch: {epoch}")
    print(f"  Note: Same server-side error.")

    print("\n2b. INERTIAL Frame")
    print("-" * 30)
    epoch = "2024-12-31T00:00:00Z"
    print(f"  Epoch: {epoch}")
    print(f"  Reference frame: INERTIAL")
    print(f"  Note: Would return non-rotating coordinates.")

    print("\n2c. v1 API (Legacy)")
    print("-" * 30)
    epoch = "2024-03-20T00:00:00Z"
    print(f"  Epoch: {epoch} (Vernal equinox)")
    print(f"  Version: v1")
    print(f"  Note: Both v1 and v2 endpoints have errors.")

    print("\n2d. Custom Interpolation")
    print("-" * 30)
    epoch = "2024-06-21T00:00:00Z"
    print(f"  Epoch: {epoch} (Summer solstice)")
    print(f"  Interpolation: HERMITE, degree 5")
    print(f"  Note: Server-side error prevents computation.")

    print("\n2e. Moon-centered Frame")
    print("-" * 30)
    epoch = "2024-09-23T00:00:00Z"
    print(f"  Epoch: {epoch} (Autumnal equinox)")
    print(f"  Central body: Moon")
    print(f"  Note: Would return Moon-centered Lagrange points.")

    print("\n2f. Time Interval")
    print("-" * 30)
    epoch = "2025-01-01T00:00:00Z"
    interval = "2025-01-01T00:00:00Z/2025-01-02T00:00:00Z"
    print(f"  Epoch: {epoch}")
    print(f"  Interval: {interval} (24 hours)")
    print(f"  Note: Would return time series of positions.")

    print("\n" + "=" * 80)
    print("Earth-Moon Lagrange Points Overview:")
    print("=" * 80)
    print("\nL1 (Unstable, ~326,000 km from Earth):")
    print("  - Between Earth and Moon")
    print("  - Gateway to lunar operations")
    print("  - Solar observation missions")
    print("  - Requires station-keeping: ~2-5 m/s/year delta-V")
    print("\nL2 (Unstable, ~449,000 km from Earth):")
    print("  - Beyond Moon from Earth")
    print("  - Lunar far-side communications relay")
    print("  - Deep space observation")
    print("  - Artemis Gateway baseline orbit (NRHO)")
    print("  - Requires station-keeping: ~2-5 m/s/year delta-V")
    print("\nL3 (Unstable, ~381,000 km from Earth):")
    print("  - Opposite Moon's orbit from Earth")
    print("  - Limited practical use")
    print("  - Research and theoretical interest")
    print("\nL4/L5 (Stable, ~384,400 km from Earth, ±60° from Moon):")
    print("  - Stable equilibrium points (Trojan points)")
    print("  - Natural dust/debris accumulation (Kordylewski clouds)")
    print("  - Potential space station locations")
    print("  - Only ~10 m/s/year station-keeping needed")
    print("\nApplications:")
    print("  - NASA Artemis Lunar Gateway (NRHO near L2)")
    print("  - Communication relays for lunar far side")
    print("  - Staging points for deep space missions")
    print("  - Long-duration space habitats (L4/L5)")
    print("=" * 80)


if __name__ == "__main__":
    main()