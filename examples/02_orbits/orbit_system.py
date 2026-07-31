# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""使用精选公开 SDK 风格进行轨道参考系与天平动示例。"""

import math

from astrox import components, orbits


EPOCH = "2024-01-01T00:00:00Z"
EARTH_MU_M3_S2 = 398600441500000.0


def circular_leo_samples() -> list[float]:
    """构造 8 个采样点的 LEO 笛卡尔数组，用于 CZML 插值。"""
    radius_m = 7000000.0
    velocity_m_s = math.sqrt(EARTH_MU_M3_S2 / radius_m)
    period_s = 2 * math.pi * math.sqrt(radius_m**3 / EARTH_MU_M3_S2)
    n_samples = 8
    dt_s = period_s / (n_samples - 1)
    samples: list[float] = []
    for index in range(n_samples):
        t_s = index * dt_s
        angle = velocity_m_s / radius_m * t_s
        samples += [
            t_s,
            radius_m * math.cos(angle),
            radius_m * math.sin(angle),
            0.0,
        ]
    return samples


def main() -> None:
    position = components.czml_position(
        epoch=EPOCH,
        central_body="Earth",
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=circular_leo_samples(),
    )

    # 将惯性系地球位置转换到地固系。
    period_s, fixed_position = orbits.convert_czml_position(
        position,
        to_central_body="Earth",
        target_reference_frame="FIXED",
    )
    print("中心天体参考系转换:")
    print(f"  周期={period_s} s")
    print(f"  历元={fixed_position.epoch}")
    print(f"  参考系={fixed_position.reference_frame}")
    print(f"  笛卡尔坐标={list(fixed_position.cartesian or [])}")

    # 将同一位置转换到地月天平动参考系。
    libration_state = orbits.earth_moon_libration(position)
    print("地月天平动参考系:")
    print(f"  中心天体={libration_state.central_body}")
    print(f"  历元={libration_state.epoch}")
    print(f"  参考系={libration_state.reference_frame}")
    print(f"  笛卡尔坐标={list(libration_state.cartesian or [])}")
    print(f"  单位四元数={list(libration_state.unit_quaternion)}")
    print(
        f"  笛卡尔平移={list(libration_state.cartesian_translation or [])}"
    )


if __name__ == "__main__":
    main()
