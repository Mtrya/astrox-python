# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Direct access with entity elevation, range, and azimuth/elevation constraints."""

import math

from astrox import access, entities


ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def main() -> None:
    ground = entities.entity(
        name="Ground",
        position=entities.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
        constraints=[
            entities.elevation_constraint(minimum_deg=10.0),
            entities.range_constraint(maximum_km=2500.0, maximum_enabled=True),
        ],
    )

    satellite = entities.entity(
        name="ISS",
        position=entities.sgp4_position(tle_lines=ISS_TLE),
    )

    result = access.compute(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T03:00:00.000Z",
        from_entity=ground,
        to_entity=satellite,
        step_s=60.0,
        compute_aer=True,
    )

    print(f"Constrained access intervals: {len(result['Passes'])}")
    if result["Passes"]:
        first = result["Passes"][0]
        print(f"First interval: {first['AccessStart']} to {first['AccessStop']}")

    # A flat azimuth/elevation mask behaves like an elevation minimum that
    # varies with azimuth. AzEl masks are only meaningful for SitePosition
    # participants; attaching one to a moving position source raises an error.
    masked_ground = entities.entity(
        name="MaskedGround",
        position=entities.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
        constraints=[
            entities.az_el_mask_constraint(
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
    print(f"Masked access intervals: {len(masked_result['Passes'])}")


if __name__ == "__main__":
    main()
