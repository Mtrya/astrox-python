# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""计算两个命名对象之间的直接访问。"""

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
    )
    iss = components.entity(
        name="ISS",
        position=components.sgp4_position(tle_lines=ISS_TLE),
    )

    result = access.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        from_entity=ground,
        to_entity=iss,
        step_s=600.0,
        compute_aer=True,
    )

    print(f"直接访问区间数: {len(result['Passes'])}")
    if result["Passes"]:
        first = result["Passes"][0]
        print(
            "第一个区间: "
            f"{first['AccessStart']} 至 {first['AccessStop']} "
            f"({first['Duration']:.1f} s)"
        )
        max_elevation = first.get("MaxElevationData")
        if isinstance(max_elevation, dict):
            elevation = max_elevation.get("Elevation")
            time = max_elevation.get("Time")
        else:
            elevation = None
            time = None
        if isinstance(elevation, (int, float)) and time is not None:
            print(
                "第一个区间内的最大仰角: "
                f"{elevation:.3f} deg，时刻 {time}"
            )
        else:
            print("第一个区间内未包含最大仰角数据")


if __name__ == "__main__":
    main()
