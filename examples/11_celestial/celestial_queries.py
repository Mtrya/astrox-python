# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""演示显式时间窗口的天体星历、坐标轴旋转、Lambert 转移窗口与 MPC 轨道根数。"""

from astrox import celestial


START = "2026-01-01T00:00:00.000Z"
STOP = "2026-01-02T00:00:00.000Z"


def main() -> None:
    for frame in ("J2000", "MeanEclpJ2000", "EclpJ2000ICRF"):
        ephemeris = celestial.ephemeris(
            target_name="Moon",
            start=START,
            stop=STOP,
            observer_name="Earth",
            observer_frame=frame,
            step_s=43200.0,
        )
        samples = ephemeris["Position"]["cartesianVelocity"]
        print(f"Moon {frame}: {len(samples) // 7} 个状态样本")

    rotation = celestial.cb_axes_rotation(
        from_central_body="Earth",
        to_central_body="Moon",
        epoch=START,
        from_frame="INERTIAL",
        to_frame="INERTIAL",
        order=1,
    )
    print(f"Earth→Moon 旋转: {len(rotation['Rotation'])} 个数值")

    mpc = celestial.mpc_ephemeris(target_name="Ceres", step_s=172800.0)
    print(f"Ceres MPC 星历: {len(mpc['Position']['cartesianVelocity']) // 7} 个状态样本")

    transfer = celestial.lambert_transfer_window(
        departure_body="Earth",
        arrival_body="Mars",
        departure_start="2028-06-01T00:00:00Z",
        departure_stop="2028-06-03T00:00:00Z",
        arrival_start="2029-04-01T00:00:00Z",
        arrival_stop="2029-04-03T00:00:00Z",
        sun_frame="ICRF",
        min_time_of_flight_days=10,
        departure_step_days=2.0,
        arrival_step_days=1.0,
        # 2026-08-20 起服务端按 MaxDepartureDV/MaxArrivalDV（缺省各 10000 m/s）
        # 与 MaxTofDays（缺省 500 d）过滤结果；该窗口的出发双曲超速约 15 km/s，
        # 需要显式放宽上限才能得到结果。
        max_departure_delta_v_m_s=20000,
    )
    results = transfer["TransferResults"]
    first = results[0]
    print(f"Lambert 窗口: {len(results)} 个转移结果")
    print(
        f"  首个: {first['DepartureTime']} → {first['ArrivalTime']}, "
        f"|DeltaV1|={first['DV1_Mag']:.1f} m/s, |DeltaV2|={first['DV2_Mag']:.1f} m/s, "
        f"TOF={first['TimeOfFlightDays']:.0f} d"
    )

    elements = celestial.mpc_orbital_elements(
        epoch_mjd_tdt=61000.0,
        periapsis_time_mjd_tdt=60900.0,
        periapsis_distance_au=0.6740515,
        semi_major_axis_au=0.9898367,
        eccentricity=0.3190276,
        inclination_deg=0.79379,
        raan_deg=209.81829,
        argument_of_periapsis_deg=100.88187,
        mean_anomaly_deg=120.0,
        reference_frame="EclpJ2000ICRF",
    )
    print(f"MPC 根数片段: {elements.to_wire()}")


if __name__ == "__main__":
    main()
