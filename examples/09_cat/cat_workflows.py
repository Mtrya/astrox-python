# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""演示 TLE 生成、寿命估算与三种碎片解体分支。"""

from astrox import cat


START = "2024-01-01T00:00:00.000Z"


def main() -> None:
    tle = cat.generate_tle(
        name="probe",
        catalog_number="25545",
        epoch=START,
        bstar=0.0001,
        semi_major_axis_km=6778.0,
        eccentricity=0.0005,
        inclination_deg=51.6,
        argument_of_perigee_deg=60.0,
        raan_deg=340.0,
        true_anomaly_deg=0.0,
    )
    print(f"生成 TLE: {tle.name} ({tle.catalog_number})")
    print(tle.line1)
    print(tle.line2)

    lifetime = cat.estimate_tle_lifetime(
        epoch=START,
        tle=tle,
        sm=0.01,
        mass=100.0,
    )
    print(f"寿命结果: {lifetime.life_years:.6g} 年")

    simple = cat.simulate_debris_breakup_simple(
        mother_tle=tle,
        epoch=START,
        count=50,
        ssc_prefix="AF",
        delta_v_m_s=400.0,
        area_to_mass_ratio_m2_kg=0.002,
    )
    print(f"简单解体碎片数: {len(simple.debris_tles)}")

    impulses = [
        cat.DebrisImpulse(
            azimuth_deg=90.0,
            elevation_deg=1.0,
            delta_v_m_s=400.0,
            area_to_mass_ratio_m2_kg=0.002,
        ),
        cat.DebrisImpulse(
            azimuth_deg=120.0,
            elevation_deg=0.0,
            delta_v_m_s=300.0,
            area_to_mass_ratio_m2_kg=0.01,
        ),
    ]
    explicit = cat.simulate_debris_breakup(
        mother_tle=tle,
        epoch=START,
        impulses=impulses,
        ssc_prefix="AF",
    )
    print(f"显式脉冲解体碎片数: {len(explicit.debris_tles)}")

    nasa = cat.simulate_debris_breakup_nasa(
        mother_tle=tle,
        epoch=START,
        ssc_prefix="AF",
        total_mass=100.0,
        minimum_characteristic_length=0.1,
    )
    print(f"NASA 解体碎片数: {len(nasa.debris_tles)}")


if __name__ == "__main__":
    main()
