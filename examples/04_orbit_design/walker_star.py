# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Walker Star constellation design.

API: POST /api/OrbitWizard/Walker
"""

from astrox.orbit_wizard import design_walker
from astrox.models import KeplerElements


EARTH_MU = 3.986004418e14


def main():
    # Seed orbit
    seed = KeplerElements(
        SemimajorAxis=7178000.0,  # 800 km LEO
        Eccentricity=0.0,
        Inclination=75.0,
        ArgumentOfPeriapsis=0.0,
        RightAscensionOfAscendingNode=0.0,
        TrueAnomaly=0.0,
        GravitationalParameter=EARTH_MU,
    )

    # Star constellation: 9 satellites, 3 planes, 3 per plane
    result = design_walker(
        seed_kepler=seed,
        num_planes=3,
        num_sats_per_plane=3,
        walker_type="Star",
        inter_plane_phase_increment=2,
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Constellation: {len(result['WalkerSatellites'])} planes")


if __name__ == "__main__":
    main()
