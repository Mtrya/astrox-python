# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Direct access calculation between named entities."""

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

    print(f"Direct access intervals: {len(result['Passes'])}")
    if result["Passes"]:
        first = result["Passes"][0]
        print(
            "First interval: "
            f"{first['AccessStart']} to {first['AccessStop']} "
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
                "Max elevation in first interval: "
                f"{elevation:.3f} deg at {time}"
            )
        else:
            print("Max elevation data was not included in the first interval")


if __name__ == "__main__":
    main()
