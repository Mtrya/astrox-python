# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Access from a satellite-mounted sensor to a ground site."""

from astrox import access, entities, orbits


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T02:00:00.000Z"


def observer_satellite() -> entities.Entity:
    orbit = orbits.keplerian(
        semi_major_axis_m=6878137.0,
        eccentricity=0.001,
        inclination_deg=45.0,
        argument_of_periapsis_deg=0.0,
        raan_deg=20.0,
        true_anomaly_deg=10.0,
    )
    return entities.entity(
        name="ObserverSat",
        position=entities.two_body_position(
            orbit_epoch=START,
            orbit=orbit,
            start=START,
            stop=STOP,
            step_s=120.0,
        ),
        orientation=entities.vvlh_axes(),
        sensor=entities.conic_sensor(outer_half_angle_deg=8.0),
        sensor_pointing=entities.fixed_sensor_pointing(
            rotation=entities.az_el_rotation(
                azimuth_deg=0.0,
                elevation_deg=-20.0,
            ),
        ),
    )


def target_site() -> entities.Entity:
    return entities.entity(
        name="TargetSite",
        position=entities.site_position(
            longitude_deg=-105.0,
            latitude_deg=40.0,
            height_m=1800.0,
        ),
    )


def main() -> None:
    result = access.compute(
        start=START,
        stop=STOP,
        from_entity=observer_satellite(),
        to_entity=target_site(),
        step_s=120.0,
        compute_aer=True,
    )

    print(f"Sensor-constrained intervals: {len(result['Passes'])}")
    if result["Passes"]:
        first = result["Passes"][0]
        print(f"First interval: {first['AccessStart']} to {first['AccessStop']}")


if __name__ == "__main__":
    main()
