# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""High-precision orbit propagation with HPOP."""

from astrox import orbits, propagator


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
EARTH_MU_M3_S2 = 398600441500000.0


def earth_gravity_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            use_fixed_step=True,
            initial_step_s=60.0,
            max_step_s=60.0,
            min_step_s=0.001,
            max_abs_error=1e-10,
            max_rel_error=1e-12,
            max_iterations=50,
        ),
        gravity=propagator.hpop_gravity_field(
            gravity_file_name="EGM2008.grv",
            degree=4,
            order=4,
            use_secular_variations=False,
            solid_tide_type="Permanent tide only",
            eop_file_path="EOP-v1.1.txt",
        ),
    )


def two_body_config() -> propagator.HpopConfig:
    return propagator.hpop_config(
        central_body="Earth",
        gravity=propagator.hpop_two_body_gravity(),
    )


def main() -> None:
    orbit = orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

    period_s, position = propagator.hpop(
        start=START,
        stop=STOP,
        orbit_epoch=START,
        orbit=orbit,
        coord_system="Inertial",
        gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
        config=earth_gravity_config(),
    )

    print("Classical HPOP")
    print(f"  period: {period_s:.3f} s")
    print(f"  position epoch: {position.epoch}")
    print(f"  reference frame: {position.reference_frame}")

    state = orbits.cartesian_state(
        x_m=7000000.0,
        y_m=1000.0,
        z_m=2000.0,
        vx_m_s=-1.0,
        vy_m_s=7500.0,
        vz_m_s=10.0,
    )

    cartesian_period_s, cartesian_position = propagator.hpop(
        start=START,
        stop=STOP,
        orbit_epoch=START,
        state=state,
        coord_system="Inertial",
        config=two_body_config(),
    )

    print("Cartesian HPOP")
    print(f"  period: {cartesian_period_s:.3f} s")
    print(f"  position epoch: {cartesian_position.epoch}")
    print(f"  reference frame: {cartesian_position.reference_frame}")


if __name__ == "__main__":
    main()
