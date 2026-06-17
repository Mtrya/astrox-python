# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Access from a calibrated VVLH satellite sensor to a ground site."""

from astrox import access, components, orbits


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T02:00:00.000Z"
EARTH_MU_M3_S2 = 398600441500000.0


def observer_satellite() -> components.Entity:
    orbit = orbits.keplerian(
        semi_major_axis_m=6878137.0,
        eccentricity=0.001,
        inclination_deg=45.0,
        argument_of_periapsis_deg=0.0,
        raan_deg=20.0,
        true_anomaly_deg=10.0,
    )
    return components.entity(
        name="ObserverSat",
        position=components.two_body_position(
            orbit_epoch=START,
            orbit=orbit,
            start=START,
            stop=STOP,
            step_s=120.0,
            gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
        ),
        orientation=components.vvlh_axes(),
        sensor=components.conic_sensor(outer_half_angle_deg=8.0),
        sensor_pointing=components.fixed_sensor_pointing(
            rotation=components.quaternion_rotation(
                scalar=1.0,
                x=0.0,
                y=0.0,
                z=0.0,
            ),
        ),
    )


def target_site() -> components.Entity:
    return components.entity(
        name="TargetSite",
        position=components.site_position(
            longitude_deg=-72.7164158261611,
            latitude_deg=7.1862428649977526,
            height_m=0.0,
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
