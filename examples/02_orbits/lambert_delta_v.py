# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Lambert delta-v example using the curated public SDK style."""

from astrox import orbits


EARTH_MU_M3_S2 = 398600441500000.0


def main() -> None:
    platform_orbit = orbits.keplerian(
        semi_major_axis_m=42164000.0,
        eccentricity=0.0001,
        inclination_deg=0.2,
        argument_of_periapsis_deg=0.0,
        raan_deg=30.0,
        true_anomaly_deg=20.0,
    )
    target_orbit = orbits.keplerian(
        semi_major_axis_m=42164000.0,
        eccentricity=0.001,
        inclination_deg=1.0,
        argument_of_periapsis_deg=10.0,
        raan_deg=80.0,
        true_anomaly_deg=95.0,
    )

    departure_delta_v_m_s, arrival_delta_v_m_s = orbits.geo_ym_lambert_delta_v(
        platform_orbit=platform_orbit,
        target_orbit=target_orbit,
        time_of_flight_s=3600.0,
        platform_gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
    )

    print("Departure delta-v (m/s):")
    print(f"  x={departure_delta_v_m_s[0]:.6f}, y={departure_delta_v_m_s[1]:.6f}, z={departure_delta_v_m_s[2]:.6f}")
    print("Arrival delta-v (m/s):")
    print(f"  x={arrival_delta_v_m_s[0]:.6f}, y={arrival_delta_v_m_s[1]:.6f}, z={arrival_delta_v_m_s[2]:.6f}")


if __name__ == "__main__":
    main()
