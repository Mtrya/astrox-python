# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Chain access calculation through named participants."""

from astrox import access, entities


ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
HUBBLE_TLE = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)


def main() -> None:
    ground = entities.entity(
        name="Ground",
        position=entities.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
    )
    iss = entities.entity(
        name="ISS",
        position=entities.sgp4_position(tle_lines=ISS_TLE),
    )
    hubble = entities.entity(
        name="Hubble",
        position=entities.sgp4_position(tle_lines=HUBBLE_TLE),
    )
    targets = entities.entity_group(
        name="Targets",
        members=[iss, hubble],
        to_restriction="AnyOf",
    )

    group_chain = access.chain(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        participants=[ground, targets],
        start_participant=ground,
        end_participant=targets,
    )
    explicit_chain = access.chain(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        participants=[ground, iss, hubble],
        start_participant=ground,
        end_participant=hubble,
        connections=[
            access.connection(ground, iss),
            access.connection(iss, hubble),
        ],
    )

    print(f"Group chain strands: {len(group_chain['ComputedStrands'])}")
    print(f"Group chain intervals: {len(group_chain['CompleteChainAccess'])}")
    print(f"Explicit chain strands: {len(explicit_chain['ComputedStrands'])}")
    print(f"Explicit chain intervals: {len(explicit_chain['CompleteChainAccess'])}")


if __name__ == "__main__":
    main()
