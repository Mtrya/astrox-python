# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Debris Breakup - Default Model

Demonstrates the default breakup model with directional velocity parameters.

API: POST /api/CAT/DebrisBreakupDefault
"""

from astrox.cat import debris_breakup
from astrox.models import TleInfo


# ============================================================
# WARNING: debris_breakup API calls are computationally intensive
# and often timeout. Set compute_life_of_time=False for faster execution.
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

    # Execute - Default breakup model with directional parameters
    result = debris_breakup(
        mother_satellite=parent_satellite,
        epoch=breakup_epoch,
        method="default",
        az_el_vel=[
            # Each row: [Azimuth (deg), Elevation (deg), Velocity (m/s)]
            [0.0, 10.0, 150.0],  # Forward cone
            [90.0, 0.0, 100.0],  # Sideways
            [180.0, -10.0, 180.0],  # Backward cone
            [270.0, 5.0, 120.0],  # Other side
        ],
        a2m=0.03,  # Lower area-to-mass ratio (denser fragments)
        ssc_pre="D2",  # Must be exactly 2 characters
        compute_life_of_time=False,  # Set to False to avoid timeout
    )

    # Output - direct field access
    print(f"Generated {len(result['DebrisTLEs'])} debris objects")
    print(f"\nFirst 3 debris objects:")
    for i, tle in enumerate(result["DebrisTLEs"][:3], 1):
        print(f"\n  Debris {i}:")
        print(f"    Name: {tle['SAT_Name']}")
        print(f"    SSC: {tle['SAT_Number']}")
        print(f"    TLE Line 1: {tle['TLE_Line1'][:60]}...")

    print(f"\nOrbital characteristics (first 5 debris):")
    print(f"  Perigee range: {result['AltitudeOfPerigee'][0]:.1f} km")
    print(f"  Apogee range: {result['AltitudeOfApogee'][0]:.1f} km")
    print(f"  Period: {result['Periods'][0]:.1f} min")
    print(f"  Lifetime: {result['LifeYears'][0]:.2f} years")


if __name__ == "__main__":
    main()
