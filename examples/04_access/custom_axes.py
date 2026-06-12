# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Access from a satellite using a named custom sensor frame."""

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
    body_axes = entities.vvlh_axes(name="Body VVLH")
    camera_axes = entities.fixed_axes(
        name="Camera Axes",
        reference_axes=body_axes,
        rotation=entities.euler_rotation(
            sequence="321",
            a_deg=0.0,
            b_deg=20.0,
            c_deg=0.0,
        ),
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
        vgt=entities.vgt(axes=[body_axes, camera_axes]),
        orientation=camera_axes,
        sensor=entities.conic_sensor(outer_half_angle_deg=8.0),
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

    print(f"Custom-axes sensor intervals: {len(result['Passes'])}")
    if result["Passes"]:
        first = result["Passes"][0]
        print(f"First interval: {first['AccessStart']} to {first['AccessStop']}")


if __name__ == "__main__":
    main()
