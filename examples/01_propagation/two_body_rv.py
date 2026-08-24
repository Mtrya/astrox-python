# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""从初始位置速度进行二体轨道递推（简化 RV 积分器）。"""

from astrox import orbits, propagator


EARTH_MU = 3.986004418e14


def main():
    state = orbits.cartesian_state(
        x_m=7000000.0,
        y_m=0.0,
        z_m=0.0,
        vx_m_s=0.0,
        vy_m_s=7546.053290114564,
        vz_m_s=0.0,
    )

    positions = propagator.two_body_rv(
        state=state,
        time_of_flight_s=3600.0,
        step_s=600.0,
        gravitational_parameter_m3_s2=EARTH_MU,
    )

    print(f"星历样本数: {len(positions) // 7}")
    first = positions[:7]
    last = positions[-7:]
    print(f"首个样本: t={first[0]:.0f} s, x={first[1]:.1f} m, y={first[2]:.1f} m")
    print(f"末个样本: t={last[0]:.0f} s, x={last[1]:.1f} m, y={last[2]:.1f} m")


if __name__ == "__main__":
    main()
