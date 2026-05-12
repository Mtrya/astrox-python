# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Convert Kepler elements to LLA at ascending node.

API: POST /api/OrbitConvert/Kepler2LLAAtAscendNode
"""

from astrox.orbit_convert import kepler_to_lla_at_ascending_node


EARTH_MU = 3.986004418e14


def main():
    result = kepler_to_lla_at_ascending_node(
        semimajor_axis=6878000.0,  # ~500 km altitude
        eccentricity=0.001,
        inclination=51.6,
        argument_of_periapsis=0.0,
        right_ascension_of_ascending_node=120.0,
        true_anomaly=0.0,  # At ascending node
        gravitational_parameter=EARTH_MU,
        orbit_epoch="2024-01-01T00:00:00.000Z",
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"LLA: {result['LLA']}")  # [latitude, longitude, altitude]


if __name__ == "__main__":
    main()
