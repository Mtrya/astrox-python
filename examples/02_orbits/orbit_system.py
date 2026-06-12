# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Orbit system frame and libration examples using the curated public SDK style."""

import math

from astrox import entities, orbits


EPOCH = "2024-01-01T00:00:00Z"
EARTH_MU_M3_S2 = 398600441500000.0


def circular_leo_samples() -> list[float]:
    """Build an 8-sample LEO cartesian array for CZML interpolation."""
    radius_m = 7000000.0
    velocity_m_s = math.sqrt(EARTH_MU_M3_S2 / radius_m)
    period_s = 2 * math.pi * math.sqrt(radius_m**3 / EARTH_MU_M3_S2)
    n_samples = 8
    dt_s = period_s / (n_samples - 1)
    samples: list[float] = []
    for index in range(n_samples):
        t_s = index * dt_s
        angle = velocity_m_s / radius_m * t_s
        samples += [
            t_s,
            radius_m * math.cos(angle),
            radius_m * math.sin(angle),
            0.0,
        ]
    return samples


def main() -> None:
    position = entities.czml_position(
        epoch=EPOCH,
        central_body="Earth",
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=circular_leo_samples(),
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
