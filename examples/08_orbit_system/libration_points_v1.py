# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Earth-Moon libration points calculation using v1 API.

API: POST /api/OrbitSystem/EarthMoonLibration
"""

from astrox.orbit_system import compute_earth_moon_libration


def main():
    result = compute_earth_moon_libration(
        epoch="2024-01-01T00:00:00.000Z",
        version="v1",
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Libration points: {result}")


if __name__ == "__main__":
    main()
