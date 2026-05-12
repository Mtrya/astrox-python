# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Two-body orbit propagation using classical orbital elements.

API: POST /api/Propagator/TwoBody
"""

from astrox.propagator import propagate_two_body


EARTH_MU = 3.986004418e14


def main():
    # Setup: Classical orbital elements
    # [SemiMajorAxis(m), Eccentricity, Inclination(deg), ArgOfPeriapsis(deg), RAAN(deg), TrueAnomaly(deg)]
    orbital_elements = [
        6878000.0,  # Semi-major axis (m) - ~500 km altitude
        0.001,      # Eccentricity
        51.6,       # Inclination (deg)
        0.0,        # Argument of periapsis (deg)
        120.0,      # RAAN (deg)
        45.0,       # True anomaly (deg)
    ]

    result = propagate_two_body(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbital_elements=orbital_elements,
        coord_type="Classical",
        gravitational_parameter=EARTH_MU,
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Position: {result['Position']}")


if __name__ == "__main__":
    main()
