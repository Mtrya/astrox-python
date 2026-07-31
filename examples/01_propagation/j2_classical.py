# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""使用经典开普勒根数进行 J2 摄动传播。"""

from astrox import orbits, propagator


# 地球引力参数（m^3/s^2）
EARTH_MU = 3.986004418e14

# 地球 J2 归一化系数与参考距离
EARTH_J2 = 0.000484165143790815
EARTH_RADIUS = 6378137.0  # 米


def main():
    # 类 ISS 轨道：高度 400 km，倾角 51.6°
    altitude = 400000.0  # 米
    semimajor_axis = EARTH_RADIUS + altitude

    orbit = orbits.keplerian(
        semi_major_axis_m=semimajor_axis,
        eccentricity=0.0008,
        inclination_deg=51.6,
        argument_of_periapsis_deg=0.0,
        raan_deg=120.0,
        true_anomaly_deg=45.0,
    )

    # 以 60 秒步长传播 2 天
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

    print(f"轨道周期: {period_s:.3f} s")
    print(f"历元: {position.epoch}")
    print(f"参考系: {position.reference_frame}")
    print(f"笛卡尔速度采样值数量: {len(position.cartesian_velocity)}")


if __name__ == "__main__":
    main()
