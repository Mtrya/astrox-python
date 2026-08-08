# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""运行一个包含初始状态和二体传播段的 Astrogator MCS。"""

from astrox import astrogator, propagator


START = "2026-01-01T00:00:00Z"
EARTH_MU_M3_S2 = 398600441500000.0
PROPAGATOR_NAME = "Earth_TwoBody_Example"


def two_body_propagator() -> propagator.HpopConfig:
    return propagator.hpop_config(
        name=PROPAGATOR_NAME,
        central_body="Earth",
        integrator=propagator.hpop_rkf78(
            name="RKF7th8th_Example",
            use_fixed_step=True,
            initial_step_s=0.1,
            max_step_s=0.1,
            min_step_s=0.1,
            max_abs_error=1e-10,
            max_rel_error=1e-13,
            max_iterations=100,
        ),
        gravity=propagator.hpop_two_body_gravity(
            name="TwoBody_Example",
            gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
        ),
    )


def main() -> None:
    initial_orbit = astrogator.keplerian_state(
        semi_major_axis_m=7_000_000.0,
        eccentricity=0.01,
        inclination_deg=28.5,
        raan_deg=15.0,
        argument_of_periapsis_deg=20.0,
        true_anomaly_deg=30.0,
        gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
    )

    result = astrogator.run_mcs(
        [
            astrogator.initial_state("Initial State", initial_orbit, epoch=START),
            astrogator.propagate(
                "Coast",
                propagator_name=PROPAGATOR_NAME,
                stop_conditions=[astrogator.duration_stop("One Second", 1.0)],
            ),
        ],
        propagators=[two_body_propagator()],
    )

    coast = result.main_sequence_results[-1]
    print(f"任务成功: {result.is_success}")
    print(f"传播时长: {coast.duration_s:.3f} s")
    print(f"停止条件: {coast.stopping_condition_name}")
    print(f"终止历元: {coast.final_state.epoch}")
    print(f"终止位置 X: {coast.final_state.cartesian.x_m:.3f} m")


if __name__ == "__main__":
    main()
