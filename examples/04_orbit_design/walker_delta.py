# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Walker Delta constellation design.

API: POST /api/OrbitWizard/Walker
"""

from astrox.orbit_wizard import design_walker
from astrox.models import KeplerElements


EARTH_MU = 3.986004418e14


def main():
    # Seed orbit for GPS-like constellation
    seed = KeplerElements(
        SemimajorAxis=26560000.0,  # ~20,200 km (MEO)
        Eccentricity=0.0,
        Inclination=55.0,
        ArgumentOfPeriapsis=0.0,
        RightAscensionOfAscendingNode=0.0,
        TrueAnomaly=0.0,
        GravitationalParameter=EARTH_MU,
    )

    # GPS-like: 24 satellites, 6 planes, 4 per plane
    result = design_walker(
        seed_kepler=seed,
        num_planes=6,
        num_sats_per_plane=4,
        walker_type="Delta",
        inter_plane_phase_increment=1,
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Constellation: {len(result['WalkerSatellites'])} planes")


if __name__ == "__main__":
    main()
