# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""使用 TLE 和 CZML 采样轨迹执行近距离交会筛查。"""

from astrox import components, conjunction, orbits, propagator


START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
PRIMARY = orbits.tle(
    line1="1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    line2="2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    name="ISS",
    catalog_number="25544",
)
TARGET = orbits.tle(
    line1="1 25545U 99999A   24001.00000000  .00000000  00000-0  00000-0 0  9993",
    line2="2 25545  51.6264 339.8059 0009386 217.1816 137.7421 15.52489080    03",
    name="probe",
    catalog_number="25545",
)


CA_TOLERANCES = {
    "tol_max_distance_km": 1000.0,
    "tol_cross_dt_s": 1000.0,
    "tol_theta_deg": 180.0,
    "tol_dh_km": 1000.0,
}


def print_results(label: str, result: conjunction.CloseApproachesResult) -> None:
    print(f"{label}: {len(result.results)} reported close approaches")
    for approach in result.results:
        print(
            f"  {approach.min_range_time}: "
            f"range={approach.min_range_km:.3f} km, "
            f"relative speed={approach.relative_speed_km_s:.4f} km/s"
        )


def main() -> None:
    tle_result = conjunction.find_tle_close_approaches(
        start=START,
        stop=STOP,
        tle=PRIMARY,
        targets=[TARGET],
        **CA_TOLERANCES,
    )
    print_results("TLE primary", tle_result)

    _, position = propagator.sgp4(
        start=START,
        stop=STOP,
        step_s=60.0,
        tle=PRIMARY,
    )
    czml_position = components.czml_position(
        epoch=position.epoch,
        central_body=position.central_body,
        interpolation_algorithm=position.interpolation_algorithm,
        interpolation_degree=position.interpolation_degree,
        reference_frame=position.reference_frame,
        cartesian_velocity=position.cartesian_velocity,
    )
    czml_result = conjunction.find_czml_close_approaches(
        start=START,
        stop=STOP,
        position=czml_position,
        targets=[TARGET],
        **CA_TOLERANCES,
    )
    print_results("CZML primary", czml_result)


if __name__ == "__main__":
    main()
