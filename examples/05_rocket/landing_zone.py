# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Compute a rocket landing-zone boundary from launch and impact points."""

from astrox import rocket


def main() -> None:
    result = rocket.landing_zone(
        launch_longitude_deg=100.0,
        launch_latitude_deg=30.0,
        launch_height_m=0.0,
        impact_longitude_deg=101.0,
        impact_latitude_deg=30.5,
        impact_height_m=100.0,
        zone_xys_km=[
            1.0,
            0.5,
            -1.0,
            0.5,
            -1.0,
            -0.5,
            1.0,
            -0.5,
        ],
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    cartographic = result["cartographicDegrees"]
    num_vertices = len(cartographic) // 3
    print(f"Boundary vertices: {num_vertices}")
    for index in range(num_vertices):
        lon = cartographic[index * 3]
        lat = cartographic[index * 3 + 1]
        height = cartographic[index * 3 + 2]
        print(f"  {index}: lon={lon:.6f} deg, lat={lat:.6f} deg, height={height:.3f} m")


if __name__ == "__main__":
    main()
