"""
Calculate solar intensity at spacecraft location.

This example demonstrates solar intensity calculation considering
Earth occultation (umbra/penumbra) for a LEO satellite.
"""

from astrox.lighting import solar_intensity
from astrox.models import EntityPositionJ2


def main():
    print("=" * 70)
    print("Solar Intensity Calculation for LEO Satellite")
    print("=" * 70)
    print()

    # Define analysis time window (3 orbits)
    start = "2024-01-15T00:00:00Z"
    stop = "2024-01-15T06:00:00Z"

    # LEO satellite in sun-synchronous orbit
    spacecraft = EntityPositionJ2(
        **{
            "$type": "J2",
            "OrbitEpoch": "15 Jan 2024 00:00:00.000000",
            "CoordSystem": "Inertial",
            "CoordType": "Classical",
            "J2NormalizedValue": 0.000484165143790815,  # Earth J2 (EGM2008)
            "RefDistance": 6378136.3,  # Earth equatorial radius (m, EGM2008)
            "OrbitalElements": [
                6928137.0,  # Semi-major axis (m) - ~550km altitude (typical SSO)
                0.001,  # Eccentricity
                97.6,  # Inclination (deg) - sun-synchronous
                0.0,  # RAAN (deg)
                0.0,  # Argument of perigee (deg)
                0.0,  # True anomaly (deg)
            ],
        }
    )

    print(f"Analysis Period: {start} to {stop}")
    print("Spacecraft Orbit:")
    print(f"  Altitude: ~550 km")
    print(f"  Inclination: 97.6° (Sun-synchronous)")
    print(f"  Period: ~95 minutes")
    print()

    # Calculate solar intensity with Earth occultation
    print("Calculating solar intensity with Earth occultation...")
    result = solar_intensity(
        start=start,
        stop=stop,
        position=spacecraft,
        time_step_sec=60.0,  # Sample every 60 seconds
        occultation_bodies=["Earth"],  # Consider Earth shadowing
        description="SSO satellite solar intensity",
    )

    # Display results
    # API response structure verified:
    # {
    #   "IsSuccess": true,
    #   "Message": "Success",
    #   "Datas": [
    #     {
    #       "$type": "SolarIntensityScData",
    #       "CurrentCondition": "SunLight" | "Penumbra" | "Umbra",
    #       "Obstruction": "None" | ...,
    #       "Time": "ISO 8601 timestamp",
    #       "Intensity": 0.0-1.0,
    #       "PercentShadow": 0-100,
    #       "ApparentSolarRange": meters,
    #       "SolarDiskHalfAngle": degrees,
    #       "SolarGrazingAngle": degrees,
    #       "RelativeAngle": degrees
    #     }
    #   ]
    # }
    print()
    print("Solar Intensity Results:")
    print("-" * 70)

    data_points = result["Datas"]
    print(f"Total Data Points: {len(data_points)}")  # 361 samples in 6-hour window with 60s timestep
    print()

    # Analyze lighting conditions
    sunlight_count = 0
    penumbra_count = 0
    umbra_count = 0

    for point in data_points:
        intensity = point["Intensity"]
        if intensity > 0.99:
            sunlight_count += 1
        elif intensity > 0.0:
            penumbra_count += 1
        else:
            umbra_count += 1

    total = len(data_points)
    print("Lighting Condition Distribution:")
    print(f"  Sunlight (100%):  {sunlight_count:4d} samples ({100*sunlight_count/total:5.1f}%)")
    print(f"  Penumbra (0-100%): {penumbra_count:4d} samples ({100*penumbra_count/total:5.1f}%)")
    print(f"  Umbra (0%):        {umbra_count:4d} samples ({100*umbra_count/total:5.1f}%)")
    print()

    # Show sample data points
    print("Sample Data Points:")
    print(f"{'Time':<25} {'Intensity':<12} {'Condition':<12}")
    print("-" * 50)

    for i in [0, len(data_points)//4, len(data_points)//2,
              3*len(data_points)//4, len(data_points)-1]:
        point = data_points[i]
        time = point["Time"]
        intensity = point["Intensity"]

        if intensity > 0.99:
            condition = "Sunlight"
        elif intensity > 0.0:
            condition = "Penumbra"
        else:
            condition = "Umbra"

        print(f"{time:<25} {intensity:>8.4f}     {condition:<12}")

    print()

    # Calculate total eclipse time
    if umbra_count > 0:
        eclipse_minutes = (umbra_count * 60) / 60  # time_step_sec = 60
        print(f"Total Eclipse Time: {eclipse_minutes:.1f} minutes")  # ~70.0 minutes for SSO
        print(f"Average Eclipse per Orbit: {eclipse_minutes / 3:.1f} minutes")  # ~23.3 minutes
    else:
        print("No eclipse periods detected (continuous sunlight).")

    print()
    print("Solar intensity calculation completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
