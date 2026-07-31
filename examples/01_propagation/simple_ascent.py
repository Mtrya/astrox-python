# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""从发射点到熄火点的简单上升传播。"""

from astrox import propagator


def main() -> None:
    period_s, position = propagator.simple_ascent(
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

    print(f"轨道周期: {period_s:.3f} s")
    print(f"位置历元: {position.epoch}")
    print(f"参考系: {position.reference_frame}")


if __name__ == "__main__":
    main()
