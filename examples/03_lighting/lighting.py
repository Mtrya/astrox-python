# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""从命名对象位置源进行光照计算。"""

from astrox import components, lighting


ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def main() -> None:
    site = components.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    )
    iss = components.sgp4_position(tle_lines=ISS_TLE)

    intervals = lighting.lighting_times(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:30:00.000Z",
        position=iss,
        occultation_bodies=["Earth", "Moon"],
    )
    intensity = lighting.solar_intensity(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:30:00.000Z",
        position=site,
        step_s=900.0,
    )
    aer = lighting.solar_aer(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:30:00.000Z",
        position=site,
        step_s=900,
    )

    print(f"ISS 光照区间段数: {len(intervals['SunLight']['Intervals'])}")
    first_intensity = intensity["Datas"][0]
    first_aer = aer["Datas"][0]
    print(
        "地面站首个太阳辐射强度采样: "
        f"可见比例 {first_intensity['Intensity']:.3f}, "
        f"阴影比例 {first_intensity['PercentShadow']:.3f}"
    )
    print(
        "地面站首个太阳 AER 采样: "
        f"方位角={first_aer['Azimuth']:.3f} deg, "
        f"仰角={first_aer['Elevation']:.3f} deg, "
        f"距离={first_aer['Range']:.1f} km"
    )


if __name__ == "__main__":
    main()
