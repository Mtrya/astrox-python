# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Debris Breakup - NASA Standard Breakup Model

Demonstrates the NASA Standard Breakup Model (most realistic).

API: POST /api/CAT/DebrisBreakupNASA
"""

from astrox.cat import debris_breakup
from astrox.models import TleInfo
from astrox import HTTPClient


# ============================================================
# WARNING: debris_breakup API calls are computationally intensive
# and often timeout. The NASA model is the most computationally
# intensive and requires longer timeouts (120s+).
#
# Recommended: Run this script with extended timeout session.
# ============================================================


def main():
    # Parent satellite TLE (simulated defunct satellite)
    parent_satellite = TleInfo(
        SAT_Name="ENVISAT",
        SAT_Number="27386",
        TLE_Line1="1 27386U 02009A   21120.50000000  .00000100  00000-0  10000-3 0  9999",
        TLE_Line2="2 27386  98.5400 180.0000 0001200 120.0000 240.0000 14.37000000950000",
    )

    # Breakup epoch
    breakup_epoch = "2021-04-30T06:30:00.000Z"

    # ENVISAT mass and size
    envisat_mass = 8211.0  # kg (actual ENVISAT mass)
    envisat_length = 10.0  # m (characteristic length)

    # Create HTTP session with extended timeout for NASA model
    nasa_session = HTTPClient(timeout=120)

    # Execute - NASA Standard Breakup Model
    result = debris_breakup(
        mother_satellite=parent_satellite,
        epoch=breakup_epoch,
        method="nasa",
        mass_total=envisat_mass,  # Total satellite mass (kg)
        min_lc=0.1,  # Minimum characteristic length (m)
        a2m=0.04,  # Area-to-mass ratio
        ssc_pre="DN",  # NASA debris prefix (must be exactly 2 characters)
        compute_life_of_time=True,  # Will likely timeout due to computational complexity
        session=nasa_session,  # Use extended timeout session
    )

    # Output - direct field access
    print(f"Generated {len(result['DebrisTLEs'])} debris objects using NASA model")
    print(f"Parent satellite mass: {envisat_mass} kg")
    print(f"Minimum characteristic length: {envisat_length} m")

    print(f"\nLifetime statistics:")
    print(f"  Shortest: {min(result['LifeYears']):.1f} years")
    print(f"  Longest: {max(result['LifeYears']):.1f} years")
    print(f"  Average: {sum(result['LifeYears']) / len(result['LifeYears']):.1f} years")
    print(f"  Debris with lifetime > 25 years: {sum(1 for lt in result['LifeYears'] if lt > 25)}")

    print(f"\nSample debris TLEs (NASA model):")
    for i, tle in enumerate(result["DebrisTLEs"][:3], 1):
        print(f"\n  Object {i}:")
        print(f"    {tle['TLE_Line1']}")
        print(f"    {tle['TLE_Line2']}")


if __name__ == "__main__":
    main()
