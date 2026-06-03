# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Reference propagator examples using the curated public SDK style."""

from astrox import orbits, propagator


EARTH_MU_M3_S2 = 398600441500000.0
EARTH_J2_NORMALIZED = 0.000484165143790815
EARTH_RADIUS_M = 6378137.0
ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


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

    sgp4_period_s, sgp4_position = propagator.sgp4(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        step_s=300.0,
        satellite_number="25544",
        tle_lines=ISS_TLE,
    )
    print(f"SGP4 period: {sgp4_period_s:.3f} s")
    print(f"SGP4 frame: {sgp4_position.reference_frame}")

    simple_ascent_period_s, simple_ascent_position = propagator.simple_ascent(
        start="2024-01-01T03:00:00.000Z",
        stop="2024-01-01T03:02:00.000Z",
        step_s=30.0,
        central_body="Earth",
        launch_latitude_deg=40.9575,
        launch_longitude_deg=100.2912,
        launch_altitude_m=1000.0,
        burnout_velocity_m_s=7800.0,
        burnout_latitude_deg=41.3,
        burnout_longitude_deg=101.0,
        burnout_altitude_m=200000.0,
    )
    print(f"Simple ascent period: {simple_ascent_period_s:.3f} s")
    print(f"Simple ascent frame: {simple_ascent_position.reference_frame}")


if __name__ == "__main__":
    main()
