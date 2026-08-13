# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""演示平动点、无量纲轨迹、周期轨道族与固定 x 微分修正。"""

from astrox import libration


# Earth-Moon periodic-family routes use this maintained nondimensional mass ratio.
EARTH_MOON_FAMILY_MASS_RATIO = 0.01215058560962404


def main() -> None:
    unit_system = libration.units()
    points = libration.positions(mass_ratio=unit_system.mass_ratio)
    print(f"单位系统质量比: {unit_system.mass_ratio:.15f}")
    print(f"L1 质心坐标: ({points.l1.x:.12f}, {points.l1.y:.1f})")

    halo = libration.earth_moon_l1_halo(
        z_amplitude=0.05,
        southern=False,
    )
    trajectory = libration.crtbp_trajectory(
        initial_state=halo.corrected_state,
        mass_ratio=EARTH_MOON_FAMILY_MASS_RATIO,
        start_time=0.0,
        end_time=halo.period,
        barycentric=halo.is_barycentric,
        output_step=0.05,
    )
    print(f"L1 Halo 周期: {halo.period:.12f}")
    print(f"轨迹样本数: {len(trajectory.samples)}")

    corrected = libration.correct_periodic_orbit_fixed_x(
        initial_state=halo.corrected_state,
        period_guess=halo.period,
        mass_ratio=EARTH_MOON_FAMILY_MASS_RATIO,
        barycentric=halo.is_barycentric,
        output_step=0.05,
    )
    print(f"修正前后 x: {corrected.initial_state.x:.12f} -> {corrected.corrected_state.x:.12f}")

    l2_halo = libration.earth_moon_l2_halo(
        x_amplitude=0.10,
        southern=True,
    )
    dro = libration.earth_moon_dro(x_amplitude=0.1801)
    print(f"南族 L2 Halo 初始 z: {l2_halo.corrected_state.z:.12f}")
    print(f"DRO 周期: {dro.period:.12f}")


if __name__ == "__main__":
    main()
