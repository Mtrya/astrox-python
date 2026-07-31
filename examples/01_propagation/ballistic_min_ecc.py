# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""使用最小偏心率速度增量分支进行弹道传播。"""

from astrox import propagator


def main():
    period_s, position = propagator.ballistic_delta_v_min_ecc(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude_deg=30.0,
        impact_longitude_deg=-70.0,
        launch_latitude_deg=28.5721,
        launch_longitude_deg=-80.6480,
        launch_altitude_m=10.0,
        impact_altitude_m=0.0,
        delta_v_m_s=1000.0,
        step_s=5.0,
    )

    print(f"轨道周期: {period_s:.3f} s")
    print(f"位置历元: {position.epoch}")


if __name__ == "__main__":
    main()
