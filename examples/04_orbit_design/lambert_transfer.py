# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Calculate Lambert transfer delta-V for GEO transfer.

API: POST /api/OrbitConvert/CalGEOYMLambertDv
"""

from astrox.orbit_convert import geo_lambert_transfer_dv
from astrox.models import KeplerElements


EARTH_MU = 3.986004418e14


def main():
    # GEO platform orbit
    platform = KeplerElements(
        SemimajorAxis=42164137.0,  # GEO
        Eccentricity=0.0,
        Inclination=0.0,
        ArgumentOfPeriapsis=0.0,
        RightAscensionOfAscendingNode=0.0,
        TrueAnomaly=0.0,
        GravitationalParameter=EARTH_MU,
    )

    # Target orbit (different longitude)
    target = KeplerElements(
        SemimajorAxis=42164137.0,
        Eccentricity=0.0,
        Inclination=0.0,
        ArgumentOfPeriapsis=0.0,
        RightAscensionOfAscendingNode=10.0,  # 10 deg different longitude
        TrueAnomaly=0.0,
        GravitationalParameter=EARTH_MU,
    )

    result = geo_lambert_transfer_dv(
        kepler_platform=platform,
        kepler_target=target,
        time_of_flight=3600.0,  # 1 hour transfer
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Delta-V: {result['DeltaV']}")


if __name__ == "__main__":
    main()
