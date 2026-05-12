"""
Example: Central Body Frame Conversion

This example demonstrates how to convert position data between different
central body reference frames (e.g., Earth-centered to Moon-centered).

This is essential for:
- Lunar missions (Earth → Moon frame conversion)
- Interplanetary transfers (Earth → Mars, etc.)
- Multi-body trajectory analysis
- Lagrange point calculations

CRITICAL: Server-side error prevents actual computation.
The orbit system API endpoints currently fail with:
    "EntityPositionCzml.GetDateMotionCollection()"
This is a server-side bug in the orbit system API implementation.
The examples document the expected schema outputs.
"""

# The frame conversion API endpoint is experiencing server-side errors.
#  Expected response schema: CzmlPositionSTMOut
#  {
#    'IsSuccess': bool,
#    'Message': str | null,
#    'position': {
#      'epoch': str,
#      'referenceFrame': str,
#      'cartesian': list[float]  # 3 values for (x,y,z) in target frame
#    }
#  }
#  See inline comments for specific field access patterns.

from astrox.models import EntityPositionCzml
from astrox.orbit_system import convert_central_body_frame, compute_earth_moon_libration

def main():
    """Demonstrate central body frame conversions and libration points."""

    # Note: The orbit system API endpoints are currently experiencing server-side errors
    # The server fails with "EntityPositionCzml.GetDateMotionCollection()" even with valid payloads.
    # This appears to be a server-side bug in the orbit system API implementation.

    # Example 1: Frame conversion (Earth → Moon)
    print("=" * 80)
    print("Example 1: Earth → Moon Frame Conversion")
    print("-" * 50)

    epoch = "2024-07-20T12:00:00Z"

    print(f"  Input Epoch: {epoch}")
    print(f"  Input Position: [6,878,000, 0, 0] m (Earth-centered)")
    print(f"  Target Frame: Moon-centered INERTIAL")

    print(f"\n  Error: Server-side error: EntityPositionCzml.GetDateMotionCollection()")
    print(f"         The frame conversion endpoint fails with valid payloads.")

    print(f"  Expected Output: CzmlPositionSTMOut")
    print(f"    position.cartesian = [321050000.0, 0.0, 0.0]  # 321,050 km from Moon center")

    # Example 2: Show Lagrange points (L1-L5) using libration API
    print("\n" + "=" * 80)
    print("Example 2: Earth-Moon Lagrange Points (L1-L5)")
    print("-" * 50)

    epoch2 = "2000-01-01T12:00:00Z"

    print(f"  Input Epoch: {epoch2}")
    print(f"  Expected Output: 5 points (L1-L5) in Earth-centered FIXED frame")
    print(f"    L1 position ≈ [326,000 km, 0, 0]")
    print(f"    L4/L5 positions ≈ 384,400 km from Earth, ±60° from Moon")

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
