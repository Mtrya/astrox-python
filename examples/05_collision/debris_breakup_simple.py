# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Debris Breakup - Simple Model

Demonstrates the simple breakup model with uniform velocity distribution in cone.

API: POST /api/CAT/DebrisBreakupSimple
"""

from astrox.cat import debris_breakup
from astrox.models import TleInfo


# ============================================================
# WARNING: debris_breakup API calls are computationally intensive
# and often timeout. The simple model with compute_life_of_time=False
# typically runs within 30 seconds. Other models may require extended
# timeouts (120s+) or may not complete in reasonable time.
#
# Recommended: Run this script in background or with increased timeout.
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

    # Execute - Simple breakup model
    result = debris_breakup(
        mother_satellite=parent_satellite,
        epoch=breakup_epoch,
        method="simple",
        count=5,  # Generate only 5 debris particles for quicker execution
        delta_v=200.0,  # Relative velocity magnitude (m/s)
        min_azimuth=0.0,  # Azimuth range (deg)
        max_azimuth=360.0,
        min_elevation=-30.0,  # Elevation range (deg)
        max_elevation=30.0,
        a2m=0.05,  # Area-to-mass ratio (m²/kg)
        ssc_pre="D1",  # Debris SSC prefix (must be exactly 2 characters)
        compute_life_of_time=False,  # Set to False for faster execution
    )

    # Output - direct field access
    print(f"Generated {len(result['DebrisTLEs'])} debris TLEs")
    print(f"\nFirst 3 debris objects:")
    for i, tle in enumerate(result["DebrisTLEs"][:3], 1):
        print(f"\n  Debris {i}:")
        print(f"    Name: {tle['SAT_Name']}")
        print(f"    SSC: {tle['SAT_Number']}")
        print(f"    TLE Line 1: {tle['TLE_Line1'][:60]}...")

    print(f"\nOrbital lifetimes (years):")
    for i, lifetime in enumerate(result['LifeYears'][:3], 1):
        print(f"  Debris {i}: {lifetime:.2f}")

    print(f"\nBreakup parameters (from AzElVel[0]):")
    print(f"  Delta-V: {result['AzElVel'][0][2]} m/s")
    print(f"  Area-to-mass ratio: {result['AzElVel'][0][3]} m²/kg")
    print(f"  Input azimuth range: {0.0}-{360.0} deg")
    print(f"  Input elevation range: {-30.0}-{30.0} deg")


if __name__ == "__main__":
    main()
