# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Batch two-body propagation - propagate multiple satellites to common epoch.

API: POST /api/Propagator/MultiTwoBody
"""

from astrox.propagator import propagate_two_body_batch
from astrox.models import KeplerElementsWithEpoch


EARTH_MU = 3.986004418e14


def main():
    # Setup: Create list of KeplerElementsWithEpoch for multiple satellites
    satellites = []
    # TODO: Add satellite elements with different epochs

    result = propagate_two_body_batch(
        epoch="2024-01-02T00:00:00.000Z",
        all_satellite_elements=satellites,
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Results: {result['Results']}")


if __name__ == "__main__":
    main()
