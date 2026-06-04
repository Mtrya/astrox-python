# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Batch propagator examples using the curated public SDK style."""

from astrox import orbits, propagator


EARTH_MU_M3_S2 = 398600441500000.0
ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
HUBBLE_TLE = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)


def describe(label: str, elements: tuple[orbits.KeplerianElements, ...]) -> None:
    print(label)
    for index, element in enumerate(elements, start=1):
        print(
            f"  {index}: a={element.semi_major_axis_m:.3f} m, "
            f"e={element.eccentricity:.8f}, "
            f"i={element.inclination_deg:.6f} deg, "
            f"RAAN={element.raan_deg:.6f} deg, "
            f"TA={element.true_anomaly_deg:.6f} deg"
        )


def main() -> None:
    leo = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )
    inclined = orbits.keplerian(
        semi_major_axis_m=7078137.0,
        eccentricity=0.002,
        inclination_deg=51.6,
        argument_of_periapsis_deg=10.0,
        raan_deg=120.0,
        true_anomaly_deg=5.0,
    )

    states = [
        ("2024-01-01T00:00:00.000Z", leo),
        ("2024-01-01T00:03:00.000Z", inclined),
    ]

    two_body = propagator.multi_two_body(
        epoch="2024-01-01T00:10:00.000Z",
        states=states,
        gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
    )
    describe("Multi two-body", two_body)

    j2 = propagator.multi_j2(
        epoch="2024-01-01T00:10:00.000Z",
        states=states,
        gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
    )
    describe("Multi J2", j2)

    sgp4 = propagator.multi_sgp4(
        epoch="2024-01-01T00:10:00.000Z",
        tle_sets=[
            ISS_TLE,
            HUBBLE_TLE,
        ],
    )
    describe("Multi SGP4", sgp4)


if __name__ == "__main__":
    main()
