# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Rocket trajectory using CZ3BC guidance.

API: POST /api/Rocket/RocketGuid
"""

from astrox.rocket import compute_guided_trajectory
from astrox.models import RocketGuidCZ3BC


def main():
    guidance = RocketGuidCZ3BC(
        field_type="CZ3BC",
        GJ_dL=200000.0,
        GJ_Va=7500.0,
        GJ_Sma1=24578137.0,
        GJ_Sma2=42164137.0,
    )

    result = compute_guided_trajectory(guidance_config=guidance)

    print(f"Success: {result['IsSuccess']}")
    print(f"Name: {result.get('Name', 'N/A')}")


if __name__ == "__main__":
    main()
