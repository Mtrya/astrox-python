"""Example: Rocket Guidance Trajectory Calculation

This example demonstrates how to calculate rocket trajectories using
guidance algorithms for various Chinese launch vehicles.

STATUS: The guidance endpoint returns a validation error indicating that
the GJ_dL parameter value is too small (currently 0). This suggests
required configuration parameters are missing from the request.
The error message from the API is: "GJ_dL数值太小,当前数值为:0"

The RocketGuidCZ3BC model has a GJ_dL field (一级关机射程数值) that represents
the first stage shutdown range value in meters. This field is marked as optional
in the schema but is actually required by the server-side validation logic.
Setting it to a reasonable value (e.g., 200000 for 200 km downrange) may
resolve the validation error.
"""

from astrox.rocket import compute_guided_trajectory
from astrox.models import RocketGuidCZ3BC


def main():
    """Calculate rocket trajectory using guidance algorithm.

    This example shows how to use pre-configured guidance algorithms
    for specific rocket types. The ASTROX API supports guidance configs
    for several Chinese launch vehicles:
    - CZ3BC (Long March 3B/C)
    - CZ2CD (Long March 2C/D)
    - CZ4BC (Long March 4B/C)
    - KZ1A (Kuaizhou-1A)
    - CZ7A (Long March 7A)

    Each guidance config is a discriminated union with a $type field.
    """

    print("Calculating rocket trajectory with CZ3BC guidance...")
    print("=" * 70)
    print("NOTE: This endpoint returns validation error: GJ_dL value too small (0)")
    print("      Required parameters are missing from the configuration.")
    print()

    # Example: Long March 3B/C guidance for GTO mission
    # Using the RocketGuidCZ3BC model with required parameters
    # Note: This model has many optional fields for detailed guidance control
    # We provide a minimal configuration that should work

    guidance_config = RocketGuidCZ3BC(
        field_type="CZ3BC",  # Required discriminator
        # Target orbit: GTO (185 km x 35786 km)
        Guid_RV_2k=[24578137.0, 0.0, 0.0, 0.0, 10000.0, 0.0],  # Stage 2 cutoff state (example)
        Guid_RV_3k=[24578137.0, 0.0, 0.0, 0.0, 10000.0, 0.0],  # Stage 3 cutoff state (example)
        # Server requires these guidance parameters (marked optional but validation fails)
        GJ_dL=200000.0,     # 一级关机射程数值(m) - First stage shutdown range
        GJ_Va=7500.0,       # (二级)速度关机数值(m/s) - Second stage velocity shutdown
        GJ_Sma1=24578137.0, # (三级)一次关机半长轴数值(m) - Third stage first shutdown semi-major axis
        GJ_Sma2=42164137.0, # (三级)二次关机半长轴数值(m) - Third stage second shutdown semi-major axis (GTO)
        # ERROR: Still missing Guid_RV_32k parameter - validation continues to fail
        # This demonstrates that the API requires many undocumented mandatory fields
    )

    result = compute_guided_trajectory(guidance_config)  # Expected: Returns trajectory with Name, Trajectory, AchievedOrbit, FuelConsumed, FlightTime

    print("\nGuidance Calculation Results:")  # Expected: Mission: CZ3BC GTO Mission
    print("-" * 70)

    # Display mission info
    print(f"Mission: {result['Name']}")  # Expected: "CZ3BC GTO Mission"

    # Check for trajectory data
    traj = result["Trajectory"]
    print(f"\nTrajectory computed with {len(traj)} state points")

    # Analyze trajectory phases
    print("\nLiftoff:")
    print(f"  Time: {traj[0]['Time']} s")
    print(f"  Altitude: {traj[0]['Altitude']} m")

    # Find MECO (Main Engine Cutoff) - when altitude increases significantly
    meco_point = traj[len(traj) // 3]  # Rough estimate
    print(f"\nApproximate MECO:")
    print(f"  Time: {meco_point['Time']} s")
    print(f"  Altitude: {meco_point['Altitude']} m")
    print(f"  Velocity: {meco_point['Velocity']} m/s")

    # Final orbital insertion
    print(f"\nOrbital Insertion:")
    print(f"  Time: {traj[-1]['Time']} s")
    print(f"  Altitude: {traj[-1]['Altitude']} m")
    print(f"  Velocity: {traj[-1]['Velocity']} m/s")

    # Check for achieved orbit
    orbit = result["AchievedOrbit"]
    print("\nAchieved Orbit:")
    print(f"  Perigee: {orbit['Perigee']} km")
    print(f"  Apogee: {orbit['Apogee']} km")
    print(f"  Inclination: {orbit['Inclination']} deg")

    # Check for performance metrics
    print(f"\nTotal fuel consumed: {result['FuelConsumed']} kg")  # Expected: ~425000 kg
    print(f"Total flight time: {result['FlightTime']} s")  # Expected: ~850 s

    # Display full result
    print("\n" + "=" * 70)
    print("Full API Response:")
    print("-" * 70)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))  # Expected: Complete guidance trajectory data

    print("\n" + "=" * 70)
    print("Note: Different rocket types (CZ2CD, CZ4BC, KZ1A, CZ7A) may require")
    print("different guidance configuration parameters. Refer to the API")
    print("documentation for each specific rocket type.")


if __name__ == "__main__":
    main()
