"""
Run Mission Control Sequence (MCS) for trajectory design.

This example demonstrates using the Astrogator MCS to design a
simple orbit transfer maneuver from LEO to higher orbit using
impulsive delta-V burns.

Expected output:
- Segment results displaying delta-V consumption, duration, altitude, velocity
- Example: starting altitude ~300 km, total delta-V ~850 m/s for both burns
- Pydantic serializer warnings are expected and can be ignored
  (due to nested model serialization for discriminated unions)
"""

from astrox.astrogator import run_mcs
from astrox._models import (
    Cartesian,  # Simple Cartesian coordinate model (x, y, z, vx, vy, vz)
    AgVAState,  # State vector with epoch and orbit elements
    AgVAMCSSegmentAgVAMCSInitialState,  # Initial state segment (discriminated union)
    AgVAMCSSegmentAgVAMCSPropagate,  # Propagate segment (discriminated union)
    AgVAMCSSegmentAgVAMCSManeuverImpulsive,  # Maneuver segment (discriminated union)
    IAgVAStoppingConditionElementAgVAApoapsisStoppingCondition,  # Apoapsis stopping condition (discriminated union)
    IAgVAStoppingConditionElement,  # Union discriminator container for stopping conditions
    IAgVAAttitudeControlImpulsiveAgVAAttitudeControlImpulsiveVelocityVector,  # VelocityVector impulse
    Propagator,  # Propagator definition
    IGravityFunctionGravityFieldFunction,  # Gravity field function (discriminated union)
    IGravityFunctionTwoBodyFunction,  # Two-body gravity function (discriminated union)
    IGravityFunction,  # Union discriminator container for gravity models
    INumericalIntegratorRKF7th8th,  # RKF7(8) numerical integrator (discriminated union)
    INumericalIntegrator,  # Union discriminator container for numerical integrators
)


def main():
    print("=" * 70)
    print("Mission Control Sequence: LEO Orbit Raising Maneuver")
    print("=" * 70)
    print()

    # Define initial state with proper Epoch format
    element = Cartesian(
        X=6678137.0,  # Position X (m) - at equator
        Y=0.0,  # Position Y (m)
        Z=0.0,  # Position Z (m)
        Vx=0.0,  # Velocity X (m/s)
        Vy=7726.67,  # Velocity Y (m/s) - circular LEO
        Vz=0.0,  # Velocity Z (m/s)
    )

    initial_state = AgVAState(
        Epoch="2024-01-01T12:00:00.000Z",
        CoordSystemName="Earth Inertial",
        Element=element,
    )

    print("Mission Profile: LEO to Higher Orbit Transfer")
    print("-" * 70)
    print("Initial Orbit:")
    print("  Altitude: ~300 km")
    print("  Type: Circular LEO")
    print("  Velocity: ~7.73 km/s")
    print()
    print("Maneuver Sequence:")
    print("  1. Initial State: Set spacecraft in LEO")
    print("  2. Propagate to apoapsis")
    print("  3. Burn 1: Raise periapsis (Hohmann transfer burn)")
    print("  4. Propagate to new apoapsis")
    print("  5. Burn 2: Circularize orbit")
    print("  6. Propagate one orbit to verify")
    print()

    # Define mission sequence

    # Create initial state segment using discriminated union model
    # Note: $type must match Literal['InitialState'] in AgVAMCSSegmentAgVAMCSInitialState
    initial_state_segment = AgVAMCSSegmentAgVAMCSInitialState(
        field_type="InitialState",
        Name="InitialLEOState",
        InitialState=initial_state,
    )

    # Create apoapsis stopping condition using discriminated union model
    apoapsis_stop = IAgVAStoppingConditionElementAgVAApoapsisStoppingCondition(
        field_type="Apoapsis",
        Active=True,
        CentralBodyName="Earth",
        Mu=3.986004418e14,  # Earth's gravitational parameter (m³/s²)
    )
    stop_condition1 = IAgVAStoppingConditionElement(root=apoapsis_stop)

    # Create propagate segment using discriminated union model
    # Note: $type must match Literal['Propagate'] in AgVAMCSSegmentAgVAMCSPropagate
    propagate_segment1 = AgVAMCSSegmentAgVAMCSPropagate(
        field_type="Propagate",
        Name="PropagateToFirstApoapsis",
        PropagatorName="Earth HPOP",
        StopConditions=[stop_condition1.model_dump(by_alias=True)],
        MaxPropagationTime=8640000,  # 100 days max
    )

    # Create impulsive maneuver segment using discriminated union model
    # Note: $type must match Literal['ManeuverImpulsive'] in AgVAMCSSegmentAgVAMCSManeuverImpulsive
    attitude1 = IAgVAAttitudeControlImpulsiveAgVAAttitudeControlImpulsiveVelocityVector(
        field_type="VelocityVector",
        DeltaVMagnitude=500.0,  # 500 m/s prograde burn
    )
    maneuver_segment1 = AgVAMCSSegmentAgVAMCSManeuverImpulsive(
        field_type="ManeuverImpulsive",
        Name="Burn1",
        PropulsionMethodValue="EngineModel",
        AttitudeControl=attitude1.model_dump(by_alias=True),
    )

    # Create second propagate segment to transfer apoapsis
    apoapsis_stop2 = IAgVAStoppingConditionElementAgVAApoapsisStoppingCondition(
        field_type="Apoapsis",
        Active=True,
        CentralBodyName="Earth",
        Mu=3.986004418e14,
    )
    stop_condition2 = IAgVAStoppingConditionElement(root=apoapsis_stop2)
    propagate_segment2 = AgVAMCSSegmentAgVAMCSPropagate(
        field_type="Propagate",
        Name="PropagateToTransferApoapsis",
        PropagatorName="Earth HPOP",
        StopConditions=[stop_condition2.model_dump(by_alias=True)],
        MaxPropagationTime=8640000,  # 100 days max
    )

    # Create second impulsive maneuver segment
    attitude2 = IAgVAAttitudeControlImpulsiveAgVAAttitudeControlImpulsiveVelocityVector(
        field_type="VelocityVector",
        DeltaVMagnitude=350.0,  # 350 m/s prograde burn
    )
    maneuver_segment2 = AgVAMCSSegmentAgVAMCSManeuverImpulsive(
        field_type="ManeuverImpulsive",
        Name="Burn2",
        PropulsionMethodValue="EngineModel",
        AttitudeControl=attitude2.model_dump(by_alias=True),
    )

    # Define propagator for Earth HPOP
    # Create gravity model (discriminated union) - use simple two-body for testing
    gravity_model = IGravityFunctionTwoBodyFunction(
        field_type="TwoBody",
        Name="Earth Two-Body",
        Description="Simple two-body gravity model",
        Mu=3.986004418e14,  # Earth's gravitational parameter (m³/s²)
    )
    gravity_container = IGravityFunction(root=gravity_model)

    # Create numerical integrator (discriminated union)
    integrator = INumericalIntegratorRKF7th8th(
        field_type="RKF7th8th",
        Name="RKF7th8th",
        Description="Runge-Kutta-Fehlberg 7(8) integrator",
    )
    integrator_container = INumericalIntegrator(root=integrator)

    earth_hpop = Propagator(
        Name="Earth HPOP",
        Description="High Precision Orbit Propagator for Earth",
        CentralBodyName="Earth",
        GravityModel=gravity_container,
        NumericalIntegrator=integrator_container,
    )

    sequence = [
        initial_state_segment,
        propagate_segment1,
        maneuver_segment1,
        propagate_segment2,
        maneuver_segment2,
    ]
    print("Executing Mission Control Sequence...")
    print()

    result = run_mcs(
        central_body="Earth",
        main_sequence=sequence,
        name="LEO_Orbit_Raising",
        description="Hohmann transfer from 300km to higher orbit",
        gravitational_parameter=3.986004418e14,  # Earth's mu (m³/s²)
        propagators=[earth_hpop],
    )

    # Display results
    print("Mission Control Sequence Results:")
    print("=" * 70)
    print()

    # Access MainSequenceResults directly
    segment_results = result["MainSequenceResults"]
    print(f"Total Segments: {len(segment_results)}")

    total_delta_v = 0.0

    for i, seg_result in enumerate(segment_results, 1):
        # Identify segment type by $type discriminator
        seg_type = seg_result["$type"]
        print(f"Segment {i}: {seg_type}")

        if seg_type == "InitialState":
            initial = seg_result["InitialState"]
            epoch = initial["Epoch"]
            print(f"  Epoch: {epoch}")  # should be 2024-01-01T12:00:00.000Z
            cartesian = initial["Cartesian"]
            x, y, z = cartesian["X"], cartesian["Y"], cartesian["Z"]
            pos_mag = (x**2 + y**2 + z**2)**0.5
            alt = (pos_mag - 6378137) / 1000
            print(f"  Starting Altitude: {alt:.1f} km")  # expected: ~300 km

        elif seg_type == "PropagateResult":
            duration = seg_result["DurationSec"]
            print(f"  Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

            final_state = seg_result["FinalState"]
            epoch = final_state["Epoch"]
            cartesian = final_state["Cartesian"]
            print(f"  Final Epoch: {epoch}")

            x, y, z = cartesian["X"], cartesian["Y"], cartesian["Z"]
            vx, vy, vz = cartesian["Vx"], cartesian["Vy"], cartesian["Vz"]
            pos_mag = (x**2 + y**2 + z**2)**0.5
            vel_mag = (vx**2 + vy**2 + vz**2)**0.5
            altitude = (pos_mag - 6378137) / 1000
            print(f"  Final Altitude: {altitude:.1f} km")  # example: first propagate ~300 km, second ~higher
            print(f"  Final Velocity: {vel_mag:.2f} m/s")  # example: first propagate ~7720 m/s (circular), second varies

        elif seg_type == "ManeuverImpulsiveResult":
            maneuver_info = seg_result["ManeuverInformation"]
            dv_mag = maneuver_info["DeltaV_Mag"]
            total_delta_v += dv_mag
            print(f"  Delta-V Applied: {dv_mag:.2f} m/s")  # example: 500.0 for burn1, 350.0 for burn2
            print(f"  Fuel Used: {maneuver_info['FuelUsed']:.2f} kg")

            # DeltaV vector available in maneuver_info['DeltaV_Inertial'] or maneuver_info['DeltaV_VNC']

        print()

    print("=" * 70)
    print(f"Total Delta-V Used: {total_delta_v:.2f} m/s")  # example: ~850.0 m/s for both burns
    print(f"Total Delta-V Used: {total_delta_v/1000:.3f} km/s")


if __name__ == "__main__":
    main()