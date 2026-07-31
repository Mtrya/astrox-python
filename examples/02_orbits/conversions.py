# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""使用精选公开 SDK 风格进行轨道转换示例。"""

from astrox import orbits


EARTH_MU_M3_S2 = 398600441500000.0
ORBIT_EPOCH = "2024-01-01T00:00:00.000Z"


def describe_keplerian(label: str, elements: orbits.KeplerianElements) -> None:
    print(
        f"{label}: "
        f"a={elements.semi_major_axis_m:.3f} m, "
        f"e={elements.eccentricity:.8f}, "
        f"i={elements.inclination_deg:.6f} deg, "
        f"RAAN={elements.raan_deg:.6f} deg, "
        f"TA={elements.true_anomaly_deg:.6f} deg"
    )


def main() -> None:
    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )

    cartesian = orbits.keplerian_to_cartesian(
        orbit,
        gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
    )
    print("笛卡尔状态:")
    print(f"  位置: ({cartesian.x_m:.3f}, {cartesian.y_m:.3f}, {cartesian.z_m:.3f}) m")
    print(f"  速度: ({cartesian.vx_m_s:.6f}, {cartesian.vy_m_s:.6f}, {cartesian.vz_m_s:.6f}) m/s")

    round_trip = orbits.cartesian_to_keplerian(cartesian)
    describe_keplerian("转回开普勒根数", round_trip)

    longitude_deg, latitude_deg, height_m = orbits.lla_at_ascending_node(
        orbit,
        orbit_epoch=ORBIT_EPOCH,
    )
    print("升交点位置:")
    print(f"  经度={longitude_deg:.6f} deg，纬度={latitude_deg:.6f} deg，高度={height_m:.3f} m")

    mean_elements = orbits.kozai_izsak_mean_elements(orbit)
    print("Kozai-Izsak 平均根数:")
    print(f"  a={mean_elements.semi_major_axis_m:.3f} m")
    print(f"  e={mean_elements.eccentricity:.8f}")
    print(f"  i={mean_elements.inclination_deg:.6f} deg")
    print(f"  M={mean_elements.mean_anomaly_deg:.6f} deg")


if __name__ == "__main__":
    main()
