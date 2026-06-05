# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Orbit wizard examples using the curated public SDK style."""

from astrox import orbits


ORBIT_EPOCH = "2024-01-01T00:00:00.000Z"


def describe_pair(
    label: str,
    pair: tuple[orbits.KeplerianElements, orbits.KeplerianElements],
) -> None:
    elements_tod, elements_inertial = pair
    print(label)
    print(
        f"  TOD: a={elements_tod.semi_major_axis_m:.3f} m, "
        f"i={elements_tod.inclination_deg:.6f} deg, "
        f"RAAN={elements_tod.raan_deg:.6f} deg"
    )
    print(
        f"  Inertial: a={elements_inertial.semi_major_axis_m:.3f} m, "
        f"i={elements_inertial.inclination_deg:.6f} deg, "
        f"RAAN={elements_inertial.raan_deg:.6f} deg"
    )


def describe_walker(
    label: str,
    walker: tuple[tuple[orbits.KeplerianElements, ...], ...],
) -> None:
    print(label)
    for plane_index, plane in enumerate(walker, start=1):
        print(f"  plane {plane_index}: {len(plane)} satellites")
        for sat_index, satellite in enumerate(plane, start=1):
            print(
                f"    sat {sat_index}: "
                f"RAAN={satellite.raan_deg:.6f} deg, "
                f"TA={satellite.true_anomaly_deg:.6f} deg"
            )


def seed_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=53.0,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=0.0,
    )


def main() -> None:
    describe_pair(
        "GEO",
        orbits.geo(
            orbit_epoch=ORBIT_EPOCH,
            inclination_deg=10.0,
            subsatellite_longitude_deg=120.0,
        ),
    )
    describe_pair(
        "Molniya",
        orbits.molniya(
            orbit_epoch=ORBIT_EPOCH,
            perigee_altitude_km=600.0,
            apogee_longitude_deg=100.0,
            argument_of_periapsis_deg=270.0,
        ),
    )
    describe_pair(
        "SSO",
        orbits.sso(
            orbit_epoch=ORBIT_EPOCH,
            altitude_km=600.0,
            local_time_of_descending_node_hours=14.5,
        ),
    )

    seed = seed_orbit()
    describe_walker(
        "Walker Delta",
        orbits.walker_delta(
            seed_orbit=seed,
            num_planes=3,
            num_sats_per_plane=2,
            inter_plane_phase_increment=1,
        ),
    )
    describe_walker(
        "Walker Star",
        orbits.walker_star(
            seed_orbit=seed,
            num_planes=3,
            num_sats_per_plane=2,
            inter_plane_phase_increment=1,
        ),
    )
    describe_walker(
        "Walker Custom",
        orbits.walker_custom(
            seed_orbit=seed,
            num_planes=3,
            num_sats_per_plane=2,
            inter_plane_true_anomaly_increment_deg=30.0,
            raan_increment_deg=60.0,
        ),
    )


if __name__ == "__main__":
    main()
