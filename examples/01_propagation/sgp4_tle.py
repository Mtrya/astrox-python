# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""从两行根数（TLE）出发进行 SGP4 传播。"""

from astrox import orbits, propagator


ISS_TLE = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)


def main() -> None:
    period_s, position = propagator.sgp4(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-01T00:10:00.000Z",
        step_s=300.0,
        tle=orbits.tle(
            line1=ISS_TLE[0],
            line2=ISS_TLE[1],
            catalog_number="25544",
        ),
    )

    print(f"轨道周期: {period_s:.3f} s")
    print(f"位置历元: {position.epoch}")
    print(f"参考系: {position.reference_frame} (GCRF/GCRS 风格惯性系)")


if __name__ == "__main__":
    main()
