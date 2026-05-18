# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Reference propagator examples using the curated public SDK style."""

from astrox import orbits, propagator


EARTH_MU_M3_S2 = 398600441500000.0
EARTH_J2_NORMALIZED = 0.000484165143790815
EARTH_RADIUS_M = 6378137.0


def main() -> None:
    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

    print("Classical wire order:", orbit.to_wire())

    j2_period_s, j2_position = propagator.j2(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        step_s=300.0,
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
        j2_normalized_value=EARTH_J2_NORMALIZED,
        ref_distance_m=EARTH_RADIUS_M,
    )
    print(f"J2 period: {j2_period_s:.3f} s")
    print(f"J2 frame: {j2_position.reference_frame}")

    two_body_period_s, two_body_position = propagator.two_body(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        step_s=300.0,
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
    )
    print(f"Two-body period: {two_body_period_s:.3f} s")
    print(f"Two-body frame: {two_body_position.reference_frame}")

    ballistic_period_s, ballistic_position = propagator.ballistic_delta_v(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude_deg=30.0,
        impact_longitude_deg=-70.0,
        launch_latitude_deg=28.5721,
        launch_longitude_deg=-80.648,
        launch_altitude_m=10.0,
        impact_altitude_m=0.0,
        delta_v_m_s=3000.0,
        step_s=30.0,
    )
    print(f"Ballistic period: {ballistic_period_s:.3f} s")
    print(f"Ballistic frame: {ballistic_position.reference_frame}")


if __name__ == "__main__":
    main()
