# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Orbit system frame and libration examples using the curated public SDK style."""

from astrox import _samples, entities, orbits


EPOCH = "2024-01-01T00:00:00Z"


def main() -> None:
    position = entities.czml_position(
        epoch=EPOCH,
        central_body="Earth",
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=_samples.circular_leo_samples(),
    )

    # Transform the inertial Earth position to the Earth fixed frame.
    period_s, fixed_position = orbits.central_body_frame(
        position,
        to_central_body="Earth",
        target_reference_frame="FIXED",
    )
    print("Central-body frame transform:")
    print(f"  period={period_s} s")
    print(f"  epoch={fixed_position.epoch}")
    print(f"  reference_frame={fixed_position.reference_frame}")
    print(f"  cartesian={list(fixed_position.cartesian or [])}")

    # Transform the same position into the Earth-Moon libration frame.
    # This wires to /OrbitSystem/EarthMoonLibration2.
    libration_state = orbits.earth_moon_libration(position)
    print("Earth-Moon libration frame:")
    print(f"  central_body={libration_state.central_body}")
    print(f"  epoch={libration_state.epoch}")
    print(f"  reference_frame={libration_state.reference_frame}")
    print(f"  cartesian={list(libration_state.cartesian or [])}")
    print(f"  unit_quaternion={list(libration_state.unit_quaternion)}")
    print(
        f"  cartesian_translation={list(libration_state.cartesian_translation or [])}"
    )


if __name__ == "__main__":
    main()
