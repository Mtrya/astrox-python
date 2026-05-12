# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Batch J2 propagation - propagate multiple satellites to common epoch.

API: POST /api/Propagator/MultiJ2
"""

from astrox.propagator import propagate_j2_batch
from astrox.models import KeplerElementsWithEpoch


# Earth gravitational parameter (m^3/s^2)
EARTH_MU = 3.986004418e14

# Earth J2 normalized value and reference distance
EARTH_J2 = 0.000484165143790815
EARTH_RADIUS = 6378137.0


def main():
    # Create a constellation of 4 satellites with different orbits
    satellites = []

    # Satellite 1: LEO at 400 km, 30° inclination
    satellites.append(KeplerElementsWithEpoch(
        SemimajorAxis=EARTH_RADIUS + 400000.0,
        Eccentricity=0.001,
        Inclination=30.0,
        ArgumentOfPeriapsis=0.0,
        RightAscensionOfAscendingNode=0.0,
        TrueAnomaly=0.0,
        GravitationalParameter=EARTH_MU,
        J2NormalizedValue=EARTH_J2,
        RefDistance=EARTH_RADIUS,
        OrbitEpoch="2024-01-01T00:00:00.000Z",
    ))

    # Satellite 2: LEO at 500 km, 45° inclination
    satellites.append(KeplerElementsWithEpoch(
        SemimajorAxis=EARTH_RADIUS + 500000.0,
        Eccentricity=0.002,
        Inclination=45.0,
        ArgumentOfPeriapsis=45.0,
        RightAscensionOfAscendingNode=30.0,
        TrueAnomaly=60.0,
        GravitationalParameter=EARTH_MU,
        J2NormalizedValue=EARTH_J2,
        RefDistance=EARTH_RADIUS,
        OrbitEpoch="2024-01-01T02:00:00.000Z",  # Different epoch
    ))

    # Satellite 3: LEO at 600 km, 60° inclination
    satellites.append(KeplerElementsWithEpoch(
        SemimajorAxis=EARTH_RADIUS + 600000.0,
        Eccentricity=0.0015,
        Inclination=60.0,
        ArgumentOfPeriapsis=90.0,
        RightAscensionOfAscendingNode=60.0,
        TrueAnomaly=120.0,
        GravitationalParameter=EARTH_MU,
        J2NormalizedValue=EARTH_J2,
        RefDistance=EARTH_RADIUS,
        OrbitEpoch="2024-01-01T04:00:00.000Z",
    ))

    # Satellite 4: LEO at 700 km, 90° inclination (polar)
    satellites.append(KeplerElementsWithEpoch(
        SemimajorAxis=EARTH_RADIUS + 700000.0,
        Eccentricity=0.001,
        Inclination=90.0,
        ArgumentOfPeriapsis=0.0,
        RightAscensionOfAscendingNode=90.0,
        TrueAnomaly=180.0,
        GravitationalParameter=EARTH_MU,
        J2NormalizedValue=EARTH_J2,
        RefDistance=EARTH_RADIUS,
        OrbitEpoch="2024-01-01T06:00:00.000Z",
    ))

    # Propagate all satellites to common epoch
    target_epoch = "2024-01-02T00:00:00.000Z"

    result = propagate_j2_batch(
        epoch=target_epoch,
        all_satellite_elements=satellites,
    )

    # Output - direct field access
    print(f"Success: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    # Results contain Kepler elements for all satellites at target epoch
    results = result["Results"]
    print(f"\nPropagated {len(results)} satellites to epoch: {target_epoch}")

    for i, sat_result in enumerate(results):
        print(f"\nSatellite {i + 1}:")
        print(f"  Semi-major axis: {sat_result['SemimajorAxis']:.3f} m")
        print(f"  Eccentricity: {sat_result['Eccentricity']:.6f}")
        print(f"  Inclination: {sat_result['Inclination']:.4f} deg")
        print(f"  RAAN: {sat_result['RightAscensionOfAscendingNode']:.4f} deg")
        print(f"  Argument of periapsis: {sat_result['ArgumentOfPeriapsis']:.4f} deg")
        print(f"  True anomaly: {sat_result['TrueAnomaly']:.4f} deg")


if __name__ == "__main__":
    main()
