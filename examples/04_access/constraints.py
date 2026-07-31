# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""在命名对象上附加仰角、距离和方位-仰角遮罩约束后进行直接访问计算。"""

import math

from astrox import access, components


ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def main() -> None:
    ground = components.entity(
        name="Ground",
        position=components.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
        constraints=[
            components.elevation_constraint(minimum_deg=10.0),
            components.range_constraint(maximum_km=2500.0, maximum_enabled=True),
        ],
    )

    satellite = components.entity(
        name="ISS",
        position=components.sgp4_position(tle_lines=ISS_TLE),
    )

    result = access.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        from_entity=ground,
        to_entity=satellite,
        step_s=60.0,
        compute_aer=True,
    )

    print(f"带约束的访问区间数: {len(result['Passes'])}")
    if result["Passes"]:
        first = result["Passes"][0]
        print(f"第一个区间: {first['AccessStart']} 至 {first['AccessStop']}")

    # 平坦的方位-仰角遮罩相当于一个随方位角变化的仰角下限。
    # 方位-仰角遮罩约束只对 SitePosition 位置源有效；
    # 将其附加到移动位置源会引发错误。
    masked_ground = components.entity(
        name="MaskedGround",
        position=components.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
        constraints=[
            components.az_el_mask_constraint(
                az_el_mask_rad=[
                    0.0,
                    math.radians(20.0),
                    math.radians(90.0),
                    math.radians(20.0),
                    math.radians(180.0),
                    math.radians(20.0),
                    math.radians(270.0),
                    math.radians(20.0),
                ],
            ),
        ],
    )

    masked_result = access.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        from_entity=masked_ground,
        to_entity=satellite,
        step_s=60.0,
    )
    print(f"带遮罩的访问区间数: {len(masked_result['Passes'])}")


if __name__ == "__main__":
    main()
