# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Close Approach Analysis V4 - Trajectory-based screening for rockets.

Screen a rocket trajectory (defined via CZML positions) against the satellite
catalog. Useful for launch collision avoidance.

API: POST /api/CAT/CloseApproach
"""

from astrox.cat import compute_close_approach
from astrox.models import CzmlPosition


def main():
    # Setup - rocket trajectory using CZML positions
    rocket_position = CzmlPosition(
        **{"$type": "CzmlPosition"},
        CentralBody="Earth",
        referenceFrame="INERTIAL",
        interpolationAlgorithm="LAGRANGE",
        interpolationDegree=5,
        epoch="2021-04-30T12:00:00.000Z",
        cartesian=[
            # Time (seconds from epoch), X, Y, Z (meters)
            0.0, -2.0e6, 5.0e6, 3.0e6,
            300.0, -1.8e6, 5.2e6, 3.5e6,
            600.0, -1.5e6, 5.5e6, 4.0e6,
            900.0, -1.0e6, 6.0e6, 5.0e6,
            1200.0, -0.5e6, 6.5e6, 6.0e6,
        ],
    )

    # Execute - compute close approaches for rocket trajectory
    result = compute_close_approach(
        start_utcg="2021-04-30T12:00:00.000Z",
        stop_utcg="2021-04-30T12:30:00.000Z",
        sat1=rocket_position,
        version="v4",
        tol_max_distance=30.0,  # Stricter threshold for active rocket
        tol_cross_dt=10.0,  # Time error tolerance (seconds)
    )

    # Output - display results
    print(f"Total events detected: {result['TotalNumber']}")
    print(f"After apo/peri filter: {result['AfterApoPeriFilterNumber']}")
    print(f"After cross-plane filter: {result['AfterCrossPlaneNumber']}")
    print(f"Filtered to {len(result['CA_Results'])} events after plane/altitude filters")

    print("\nClose approach details:")
    for i, ca in enumerate(result["CA_Results"][:5], 1):
        print(f"\n  Event {i}:")
        print(f"    TCA: {ca['CA_MinRange_Time']}")
        print(f"    Miss Distance: {ca['CA_MinRange']:.3f} km")
        print(f"    Target: {ca['SAT2_Name']} (SSC: {ca['SAT2_Number']})")
        print(f"    Relative Velocity: {ca['CA_DeltaV']:.3f} m/s")


if __name__ == "__main__":
    main()
