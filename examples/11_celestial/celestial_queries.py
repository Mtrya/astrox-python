# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""演示显式时间窗口的天体星历和坐标轴旋转查询。"""

from astrox import celestial


START = "2026-01-01T00:00:00.000Z"
STOP = "2026-01-02T00:00:00.000Z"


def main() -> None:
    for frame in ("J2000", "MeanEclpJ2000"):
        ephemeris = celestial.ephemeris(
            target_name="Moon",
            start=START,
            stop=STOP,
            observer_name="Earth",
            observer_frame=frame,
            step_s=43200.0,
        )
        samples = ephemeris["Position"]["cartesianVelocity"]
        print(f"Moon {frame}: {ephemeris['IsSuccess']}, {len(samples) // 7} 个状态样本")

    rotation = celestial.cb_axes_rotation(
        from_central_body="Earth",
        to_central_body="Moon",
        epoch=START,
        from_frame="INERTIAL",
        to_frame="INERTIAL",
        order=1,
    )
    print(f"Earth→Moon 旋转: {rotation['IsSuccess']}, {len(rotation['Rotation'])} 个数值")

    mpc = celestial.mpc_ephemeris(target_name="Ceres")
    print(f"Ceres MPC 星历: {mpc['IsSuccess']}, {mpc['Message']}")


if __name__ == "__main__":
    main()
