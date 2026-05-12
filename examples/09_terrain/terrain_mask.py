"""
Calculate terrain mask for ground station.

This example demonstrates terrain mask calculation which provides
azimuth-elevation constraints for ground stations based on surrounding
terrain, useful for satellite tracking and visibility analysis.

Verified API Response Structure:
    AzimuthElevationMaskOut:
        IsSuccess: bool - True if computation succeeded
        Message: string (nullable) - Error message if IsSuccess=False
        sitePosition: EntityPositionSite - Input site position echoed back
        AzElMaskData: array (nullable) - ElevationMaskData objects
            Each ElevationMaskData:
                Azimuth: number (radians) - Azimuth angle 0-2pi
                Elevation: number (radians) - Minimum elevation angle
                Items: array (optional) - Additional data points
"""

from astrox.terrain import get_terrain_mask
from astrox.models import SitePosition


def main():
    print("=" * 70)
    print("Terrain Mask Calculation for Ground Station")
    print("=" * 70)
    print()

    # Ground station in mountainous area: Xichang Satellite Launch Center
    ground_station = SitePosition.model_construct(
        **{
            "$type": "SitePosition",
            "cartographicDegrees": [
                102.0267,  # Longitude (deg E)
                28.2467,  # Latitude (deg N)
                1825.0,  # Altitude (m) - elevated location
            ]
        }
    )

    print("Ground Station: Xichang Satellite Launch Center, China")
    print(f"  Longitude: {ground_station.cartographicDegrees[0]:.4f}° E")
    print(f"  Latitude:  {ground_station.cartographicDegrees[1]:.4f}° N")
    print(f"  Altitude:  {ground_station.cartographicDegrees[2]:.1f} m")
    print()
    print("Note: Located in mountainous terrain of Sichuan Province")
    print()

    # Calculate terrain mask using default method
    print("Calculating terrain mask (default method)...")
    result = get_terrain_mask(
        site_position=ground_station,
        method="default",
        text="Xichang terrain mask - default",
    )

    print()
    print("Terrain Mask Results:")
    print("-" * 70)

    # Direct access to response fields - API schema guarantees these exist
    # No defensive checks - let KeyError surface if API contract is violated

    print(f"Status: {'Success' if result['IsSuccess'] else 'Failed'}")
    print(f"Message: {result['Message']}")

    # Direct access to mask data - null if computation failed
    mask_data = result["AzElMaskData"]
    print(f"Mask Data Points: {len(mask_data)} (360° coverage)")
    print()

    # Analyze terrain mask (convert radians to degrees)
    elevations = [point["Elevation"] for point in mask_data]
    elevations_deg = [el * 180 / 3.1415926535 for el in elevations]
    min_elevation = min(elevations_deg)
    max_elevation = max(elevations_deg)
    avg_elevation = sum(elevations_deg) / len(elevations_deg)

    print("Terrain Mask Statistics:")
    print(f"  Minimum Elevation Angle: {min_elevation:.2f}°")
    print(f"  Maximum Elevation Angle: {max_elevation:.2f}°")
    print(f"  Average Elevation Angle: {avg_elevation:.2f}°")
    print()

    # Find most obstructed directions (convert radians to degrees)
    obstructions = sorted(
        [(point["Azimuth"] * 180 / 3.1415926535, point["Elevation"] * 180 / 3.1415926535)
         for point in mask_data],
        key=lambda x: x[1],
        reverse=True
    )

    print("Most Obstructed Directions (highest terrain):")
    print(f"{'Azimuth (°)':<12} {'Elevation (°)':<15} {'Direction':<12}")
    print("-" * 45)

    for az, el in obstructions[:5]:
        # Determine cardinal direction
        if 337.5 <= az or az < 22.5:
            direction = "North"
        elif 22.5 <= az < 67.5:
            direction = "Northeast"
        elif 67.5 <= az < 112.5:
            direction = "East"
        elif 112.5 <= az < 157.5:
            direction = "Southeast"
        elif 157.5 <= az < 202.5:
            direction = "South"
        elif 202.5 <= az < 247.5:
            direction = "Southwest"
        elif 247.5 <= az < 292.5:
            direction = "West"
        else:
            direction = "Northwest"

        print(f"{az:>10.1f}   {el:>12.2f}   {direction:<12}")

    print()
    print("Sample Terrain Mask Data (by cardinal direction):")
    print(f"{'Direction':<12} {'Azimuth (°)':<12} {'Min Elevation (°)':<18}")
    print("-" * 50)

    cardinal_directions = {
        "North": 0,
        "Northeast": 45,
        "East": 90,
        "Southeast": 135,
        "South": 180,
        "Southwest": 225,
        "West": 270,
        "Northwest": 315,
    }

    for direction, target_az in cardinal_directions.items():
        closest = min(mask_data,
                      key=lambda x: abs(x["Azimuth"] * 180 / 3.1415926535 - target_az))
        az = closest["Azimuth"] * 180 / 3.1415926535
        el = closest["Elevation"] * 180 / 3.1415926535
        print(f"{direction:<12} {az:>10.1f}   {el:>15.2f}")

    print()

    # Visibility analysis
    print("Satellite Visibility Impact:")
    print("-" * 70)
    print(f"Minimum satellite elevation for tracking: {max_elevation:.2f}°")
    print()
    print("The terrain mask indicates that satellites must be at least")
    print(f"{max_elevation:.1f}° above the horizon in the most obstructed direction")
    print("to be visible from this ground station.")
    print()

    # Calculate usable sky percentage
    standard_min_el = 10.0
    terrain_restricted = sum(1 for el in elevations_deg if el > standard_min_el)
    percent_restricted = 100 * terrain_restricted / len(elevations_deg)

    if percent_restricted > 0:
        print(f"Terrain restricts {percent_restricted:.1f}% of azimuth directions")
        print(f"beyond standard {standard_min_el}° minimum elevation.")
    else:
        print(f"All terrain elevations below standard {standard_min_el}° threshold.")

    print()
    print("Applications:")
    print("-" * 70)
    print("  - Satellite pass predictions accounting for terrain")
    print("  - Ground station antenna pointing constraints")
    print("  - Satellite visibility time calculations")
    print("  - Tracking schedule optimization")
    print("  - Communication link budget analysis")
    print("  - Ground station site selection")


if __name__ == "__main__":
    main()
