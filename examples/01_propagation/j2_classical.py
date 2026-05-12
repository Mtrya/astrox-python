# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
J2 perturbation propagation using classical orbital elements.

API: POST /api/Propagator/J2
"""

from astrox.propagator import propagate_j2


# Earth gravitational parameter (m^3/s^2)
EARTH_MU = 3.986004418e14

# Earth J2 normalized value and reference distance
EARTH_J2 = 0.000484165143790815
EARTH_RADIUS = 6378137.0  # meters


def main():
    # ISS-like orbit: 400 km altitude, 51.6° inclination
    altitude = 400000.0  # meters
    semimajor_axis = EARTH_RADIUS + altitude

    # Classical orbital elements
    # [SemiMajorAxis(m), Eccentricity, Inclination(deg), ArgOfPeriapsis(deg), RAAN(deg), TrueAnomaly(deg)]
    orbital_elements = [
        semimajor_axis,  # Semi-major axis (m)
        0.0008,          # Eccentricity (nearly circular)
        51.6,            # Inclination (deg) - ISS inclination
        0.0,             # Argument of periapsis (deg)
        120.0,           # RAAN (deg)
        45.0,            # True anomaly (deg)
    ]

    # Propagate for 2 days with 60-second step
    result = propagate_j2(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-03T00:00:00.000Z",
        j2_normalized_value=EARTH_J2,
        ref_distance=EARTH_RADIUS,
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbital_elements=orbital_elements,
        step=60.0,
        central_body="Earth",
        gravitational_parameter=EARTH_MU,
        coord_system="Inertial",
        coord_type="Classical",
    )

    # Output - direct field access
    print(f"Success: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    # Position data (CZML format)
    position = result["Position"]
    print(f"\nEpoch: {position['epoch']}")
    print(f"Cartesian data points: {len(position['cartesian']) // 6}")

    # Display first and last positions
    cartesian = position["cartesian"]
    print(f"\nInitial position (m):")
    print(f"  X: {cartesian[0]:.3f}")
    print(f"  Y: {cartesian[1]:.3f}")
    print(f"  Z: {cartesian[2]:.3f}")

    print(f"\nFinal position (m):")
    print(f"  X: {cartesian[-6]:.3f}")
    print(f"  Y: {cartesian[-5]:.3f}")
    print(f"  Z: {cartesian[-4]:.3f}")

    # Reference frame info
    print(f"\nReference frame: {position['referenceFrame']}")


if __name__ == "__main__":
    main()
