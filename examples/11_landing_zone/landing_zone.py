"""Example: Landing Zone Computation

This example demonstrates how to compute landing zone parameters for
rocket stages or debris impact areas.

The API returns landing zone vertices as a flattened array of cartographic
coordinates in degrees: [lon1, lat1, alt1, lon2, lat2, alt2, ...]
where longitude and latitude are in degrees, and altitude is in meters.
"""

from astrox.landing_zone import compute_landing_zone


def parse_cartographic_degrees(result):
    """Parse cartographicDegrees array and display zone information.

    Args:
        result: API response dict containing cartographicDegrees array

    API Response Schema:
        {
            "IsSuccess": bool,      # indicates API call success
            "Message": str,         # status message from API
            "cartographicDegrees": [lon1, lat1, alt1, lon2, lat2, alt2, ...]
        }
        where longitude and latitude are in degrees, altitude in meters
    """
    coords = result["cartographicDegrees"]
    num_vertices = len(coords) // 3
    print(f"Number of vertices: {num_vertices}")  # should be 4
    print("Zone vertices (geographic coordinates):")
    for i in range(num_vertices):
        idx = i * 3
        lon = coords[idx]          # degrees
        lat = coords[idx + 1]      # degrees
        alt = coords[idx + 2]      # meters
        vertex_num = i + 1
        print(f"  Vertex {vertex_num}: Lon={lon:.6f}°, Lat={lat:.6f}°, Alt={alt:.3f}m")
        # Example formatted output (actual values will vary):
        #   Vertex 1: Lon=-74.954089°, Lat=27.770377°, Alt=2.938m

    # Calculate center as centroid of all vertices
    center_lon = sum(coords[0::3]) / num_vertices
    center_lat = sum(coords[1::3]) / num_vertices
    center_alt = sum(coords[2::3]) / num_vertices
    print(f"\nZone center (centroid): Lon={center_lon:.6f}°, Lat={center_lat:.6f}°, Alt={center_alt:.3f}m")
    # Example formatted output (actual values will vary):
    #   Zone center (centroid): Lon=-75.000003°, Lat=27.799991°, Alt=2.936m


def main():
    """Compute landing zone for rocket first stage.

    This example calculates the landing zone parameters given:
    - Launch point coordinates
    - Landing point coordinates
    - Zone boundary points

    Useful for:
    - First stage splashdown zones
    - Debris impact predictions
    - Range safety analysis
    - Landing ellipse calculations
    """

    print("Computing landing zone parameters...")
    print("=" * 70)

    # Example 1: First stage landing zone in the Atlantic Ocean
    # Launch: Cape Canaveral, Florida
    # Landing: Downrange in Atlantic Ocean

    print("\nExample 1: Atlantic Ocean Splashdown Zone")
    print("-" * 70)

    result1 = compute_landing_zone(
        # Launch point (Cape Canaveral)
        fa_she_dian=[-80.6, 28.5, 0],  # [lon(deg), lat(deg), alt(m)]

        # Landing point (downrange in Atlantic)
        luo_dian=[-75.0, 27.8, 0],  # [lon(deg), lat(deg), alt(m)]

        # Zone boundary (rectangular zone in local coordinates)
        # Front is +X axis, Right is +Y axis, unit: km
        # This defines a 10km x 5km landing ellipse
        zone_xys=[
            5.0, 2.5,    # Point 1: Front-right corner
            5.0, -2.5,   # Point 2: Front-left corner
            -5.0, -2.5,  # Point 3: Rear-left corner
            -5.0, 2.5    # Point 4: Rear-right corner
        ]
    )

    # Parse cartographicDegrees array for Example 1
    parse_cartographic_degrees(result1)

    # Example 2: Landing zone for Chinese rocket over Pacific
    # Launch: Jiuquan, China
    # Landing: Pacific Ocean

    print("\n" + "=" * 70)
    print("\nExample 2: Pacific Ocean Landing Zone")
    print("-" * 70)

    result2 = compute_landing_zone(
        # Launch point (Jiuquan)
        fa_she_dian=[100.3, 40.6, 1000],  # [lon(deg), lat(deg), alt(m)]

        # Landing point (Pacific Ocean)
        luo_dian=[170.0, 10.0, 0],  # [lon(deg), lat(deg), alt(m)]

        # Larger zone for long-range flight
        # 20km x 10km ellipse
        zone_xys=[
            10.0, 5.0,    # Point 1
            10.0, -5.0,   # Point 2
            -10.0, -5.0,  # Point 3
            -10.0, 5.0    # Point 4
        ]
    )

    # Parse cartographicDegrees array for Example 2
    parse_cartographic_degrees(result2)

    # Display full API response for reference
    print("\n" + "=" * 70)
    print("Full API Response (Example 1):")
    print("-" * 70)
    import json
    print(json.dumps(result1, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

