# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Close Approach Analysis V3 - High sensitivity parameters.

Screen ISS with tight tolerances to detect only the closest approaches
with similar orbital planes and altitudes.

API: POST /api/CAT/CloseApproach
"""

from astrox.cat import compute_close_approach
from astrox.models import TleInfo


def main():
    # Setup - ISS TLE data
    iss_tle = TleInfo(
        SAT_Name="ISS (ZARYA)",
        SAT_Number="25544",
        TLE_Line1="1 25544U 98067A   21120.75712704  .00001608  00000-0  37381-4 0  9990",
        TLE_Line2="2 25544  51.6441 217.3237 0002714 302.6679 206.5255 15.48964989281240",
    )

    # Execute - compute close approaches with tight tolerances
    result = compute_close_approach(
        start_utcg="2021-04-30T00:00:00.000Z",
        stop_utcg="2021-05-01T00:00:00.000Z",
        sat1=iss_tle,
        version="v3",
        tol_max_distance=20.0,  # Very close approaches only (20 km)
        tol_cross_dt=5.0,  # Tight time tolerance (5 seconds)
        tol_theta=2.0,  # Similar orbital planes (2 deg)
        tol_dh=50.0,  # Similar altitudes (50 km)
    )

    # Output - display results
    print(f"Total events detected: {result['TotalNumber']}")
    print(f"After apo/peri filter: {result['AfterApoPeriFilterNumber']}")
    print(f"After cross-plane filter: {result['AfterCrossPlaneNumber']}")
    print(f"High-sensitivity search found {len(result['CA_Results'])} events")
    print("(Narrower thresholds reduce false positives)")

    print("\nClose approach details:")
    for i, ca in enumerate(result["CA_Results"], 1):
        print(f"\n  Event {i}:")
        print(f"    Time: {ca['CA_MinRange_Time']}")
        print(f"    Miss Distance: {ca['CA_MinRange']:.3f} km")
        print(f"    Target: {ca['SAT2_Name']} (SSC: {ca['SAT2_Number']})")
        print(f"    Relative Velocity: {ca['CA_DeltaV']:.3f} m/s")
        print(f"    Plane Angle: {ca['CA_Theta']:.3f}°")


if __name__ == "__main__":
    main()
