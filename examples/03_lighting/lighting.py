# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Lighting calculations from entity position sources."""

from astrox import entities, lighting


ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def main() -> None:
    site = entities.site_position(
        longitude_deg=-155.468,
        latitude_deg=19.821,
        height_m=4205.0,
    )
    iss = entities.sgp4_position(tle_lines=ISS_TLE)

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
        site_position=site,
        step_s=900,
    )

    print(f"ISS sunlight intervals: {len(intervals['SunLight']['Intervals'])}")
    print(f"Site intensity samples: {len(intensity['Datas'])}")
    print(f"Site solar AER samples: {len(aer['Datas'])}")


if __name__ == "__main__":
    main()
