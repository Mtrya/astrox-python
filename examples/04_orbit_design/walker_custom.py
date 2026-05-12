# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Custom Walker constellation design.

API: POST /api/OrbitWizard/Walker
"""

from astrox.orbit_wizard import design_walker
from astrox.models import KeplerElements


EARTH_MU = 3.986004418e14


def main():
    # Seed orbit
    seed = KeplerElements(
        SemimajorAxis=16378000.0,  # 10,000 km MEO
        Eccentricity=0.0,
        Inclination=60.0,
        ArgumentOfPeriapsis=0.0,
        RightAscensionOfAscendingNode=0.0,
        TrueAnomaly=0.0,
        GravitationalParameter=EARTH_MU,
    )

    # Custom constellation with manual spacing
    result = design_walker(
        seed_kepler=seed,
        num_planes=2,
        num_sats_per_plane=4,
        walker_type="Custom",
        inter_plane_true_anomaly_increment=45.0,
        raan_increment=90.0,
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Constellation: {len(result['WalkerSatellites'])} planes")


if __name__ == "__main__":
    main()
