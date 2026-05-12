# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Batch SGP4 propagation - propagate multiple satellites from TLEs to common epoch.

API: POST /api/Propagator/MultiSgp4
"""

from astrox.propagator import propagate_sgp4_batch


def main():
    # Sample TLEs for multiple satellites
    # Each satellite requires 2 TLE lines

    tles = [
        # ISS (ZARYA) - TLE epoch: 2024-01-01
        "1 25544U 98067A   24001.50000000  .00020000  00000-0  28000-4 0  9993",
        "2 25544  51.6400  30.5000 0004000  50.0000  60.0000 15.50000000    20",

        # Hubble Space Telescope
        "1 20580U 90037B   24001.50000000  .00001000  00000-0  10000-4 0  9991",
        "2 20580  28.4700  75.0000 0002000  20.0000  30.0000 15.00000000    40",

        # NOAA-20 (JPSS-1)
        "1 43013U 17073A   24001.50000000  .00000100  00000-0  50000-5 0  9992",
        "2 43013  98.7000 120.0000 0001000  80.0000  90.0000 14.20000000    60",

        # Landsat-9
        "1 49260U 21088A   24001.50000000  .00000100  00000-0  40000-5 0  9994",
        "2 49260  98.2000  45.0000 0001000  10.0000  20.0000 14.30000000    80",
    ]

    # Target epoch for propagation
    target_epoch = "2024-01-02T00:00:00.000Z"

    result = propagate_sgp4_batch(
        epoch=target_epoch,
        tles=tles,
    )

    # Output - direct field access
    print(f"Success: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    # Results contain Kepler elements for all satellites
    results = result["Results"]
    num_satellites = len(results)
    print(f"\nPropagated {num_satellites} satellites to epoch: {target_epoch}")

    satellite_names = ["ISS", "Hubble", "NOAA-20", "Landsat-9"]

    for i, (sat_result, name) in enumerate(zip(results, satellite_names)):
        print(f"\n{name}:")
        print(f"  Semi-major axis: {sat_result['SemimajorAxis']:.3f} m")
        print(f"  Eccentricity: {sat_result['Eccentricity']:.6f}")
        print(f"  Inclination: {sat_result['Inclination']:.4f} deg")
        print(f"  RAAN: {sat_result['RightAscensionOfAscendingNode']:.4f} deg")
        print(f"  Argument of periapsis: {sat_result['ArgumentOfPeriapsis']:.4f} deg")
        print(f"  True anomaly: {sat_result['TrueAnomaly']:.4f} deg")

    print(f"\nNote: Results show osculating Kepler elements at target epoch")
    print(f"      in Earth inertial frame.")


if __name__ == "__main__":
    main()
