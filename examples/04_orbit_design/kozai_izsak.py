# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Calculate mean Kepler elements using Kozai-Izsak method.

API: POST /api/OrbitConvert/GetKozaiIzsakMeanElements
"""

from astrox.orbit_convert import kozai_izsak_mean_elements


EARTH_MU = 3.986004418e14


def main():
    # Circular LEO orbit
    result = kozai_izsak_mean_elements(
        semimajor_axis=6878000.0,  # ~500 km altitude
        eccentricity=0.001,        # Nearly circular
        inclination=51.6,
        argument_of_periapsis=0.0,
        right_ascension_of_ascending_node=120.0,
        true_anomaly=45.0,
        gravitational_parameter=EARTH_MU,
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Mean elements: {result}")


if __name__ == "__main__":
    main()
