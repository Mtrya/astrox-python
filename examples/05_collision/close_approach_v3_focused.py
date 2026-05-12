# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Close Approach Analysis V3 - Focused screening against specified targets.

Screen ISS against specific debris objects (COSMOS 2251 DEB, IRIDIUM 33 DEB)
rather than the full catalog.

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

    # Setup - specific debris targets to check
    target1 = TleInfo(
        SAT_Name="COSMOS 2251 DEB",
        SAT_Number="34454",
        TLE_Line1="1 34454U 93036SX  21120.50000000  .00000100  00000-0  10000-3 0  9999",
        TLE_Line2="2 34454  74.0400 180.0000 0050000 270.0000  90.0000 14.00000000100000",
    )

    target2 = TleInfo(
        SAT_Name="IRIDIUM 33 DEB",
        SAT_Number="33442",
        TLE_Line1="1 33442U 97051C   21120.50000000  .00000050  00000-0  10000-3 0  9999",
        TLE_Line2="2 33442  86.4000 200.0000 0010000  90.0000 270.0000 14.34000000150000",
    )

    # Execute - compute close approaches against specified targets
    result = compute_close_approach(
        start_utcg="2021-04-30T00:00:00.000Z",
        stop_utcg="2021-05-02T00:00:00.000Z",
        sat1=iss_tle,
        version="v3",
        tol_max_distance=100.0,
        targets=[target1, target2],
    )

    # Output - display results
    print(f"Total events detected: {result['TotalNumber']}")
    print(f"Found {len(result['CA_Results'])} close approaches with specified targets")

    print("\nClose approach details:")
    for i, ca in enumerate(result["CA_Results"], 1):
        print(f"\n  Event {i}:")
        print(f"    Time: {ca['CA_MinRange_Time']}")
        print(f"    Miss Distance: {ca['CA_MinRange']:.3f} km")
        print(f"    Target: {ca['SAT2_Name']} (SSC: {ca['SAT2_Number']})")
        print(f"    Relative Velocity: {ca['CA_DeltaV']:.3f} m/s")


if __name__ == "__main__":
    main()
