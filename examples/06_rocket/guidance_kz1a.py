# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Rocket trajectory using KZ1A guidance.

API: POST /api/Rocket/RocketGuid
"""

from astrox.rocket import compute_guided_trajectory
from astrox.models import RocketGuidKZ1A


def main():
    guidance = RocketGuidKZ1A(
        field_type="KZ1A",
        # TODO: Add required guidance parameters
    )

    result = compute_guided_trajectory(guidance_config=guidance)

    print(f"Success: {result['IsSuccess']}")
    print(f"Trajectory: {result.get('Trajectory', 'N/A')}")


if __name__ == "__main__":
    main()
