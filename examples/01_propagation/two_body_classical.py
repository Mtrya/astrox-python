# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""使用经典开普勒根数进行二体轨道传播。"""

from astrox import orbits, propagator


EARTH_MU = 3.986004418e14


def main():
    orbit = orbits.keplerian(
        semi_major_axis_m=6878000.0,
        eccentricity=0.001,
        inclination_deg=51.6,
        argument_of_periapsis_deg=0.0,
        raan_deg=120.0,
        true_anomaly_deg=45.0,
    )

    period_s, position = propagator.two_body(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbit=orbit,
        gravitational_parameter_m3_s2=EARTH_MU,
    )

    print(f"轨道周期: {period_s:.3f} s")
    print(f"位置历元: {position.epoch}")
    print(f"参考系: {position.reference_frame}")


if __name__ == "__main__":
    main()
