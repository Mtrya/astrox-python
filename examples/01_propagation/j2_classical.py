# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""J2 perturbation propagation using classical orbital elements."""

from astrox import orbits, propagator


# Earth gravitational parameter (m^3/s^2)
EARTH_MU = 3.986004418e14

# Earth J2 normalized value and reference distance
EARTH_J2 = 0.000484165143790815
EARTH_RADIUS = 6378137.0  # meters


def main():
    # ISS-like orbit: 400 km altitude, 51.6° inclination
    altitude = 400000.0  # meters
    semimajor_axis = EARTH_RADIUS + altitude

    orbit = orbits.keplerian(
        semi_major_axis_m=semimajor_axis,
        eccentricity=0.0008,
        inclination_deg=51.6,
        argument_of_periapsis_deg=0.0,
        raan_deg=120.0,
        true_anomaly_deg=45.0,
    )

    # Propagate for 2 days with 60-second step
    period_s, position = propagator.j2(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-03T00:00:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        step_s=60.0,
        central_body="Earth",
        gravitational_parameter_m3_s2=EARTH_MU,
        coord_system="Inertial",
        j2_normalized_value=EARTH_J2,
        ref_distance_m=EARTH_RADIUS,
    )

    print(f"Period: {period_s:.3f} s")
    print(f"Epoch: {position.epoch}")
    print(f"Reference frame: {position.reference_frame}")
    print(f"Cartesian-velocity values: {len(position.cartesian_velocity)}")


if __name__ == "__main__":
    main()
