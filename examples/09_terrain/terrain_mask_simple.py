# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Terrain mask calculation using simple method.

API: POST /api/Terrain/AzElMaskSimple
"""

from astrox.terrain import get_terrain_mask
from astrox.models import SitePosition


def main():
    site = SitePosition(
        Latitude=39.0,
        Longitude=115.0,
        Altitude=100.0,
    )

    result = get_terrain_mask(
        site_position=site,
        method="simple",
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Mask data: {result}")


if __name__ == "__main__":
    main()
