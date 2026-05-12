# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Rocket trajectory using CZ7A guidance.

API: POST /api/Rocket/RocketGuid
"""

from astrox.rocket import compute_guided_trajectory
from astrox.models import RocketGuidCZ7A


def main():
    guidance = RocketGuidCZ7A(
        field_type="CZ7A",
        # TODO: Add required guidance parameters
    )

    result = compute_guided_trajectory(guidance_config=guidance)

    print(f"Success: {result['IsSuccess']}")
    print(f"Trajectory: {result.get('Trajectory', 'N/A')}")


if __name__ == "__main__":
    main()
