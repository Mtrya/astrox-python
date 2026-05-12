# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Two-body orbit propagation using Cartesian state parameterization.

API: POST /api/Propagator/TwoBody
"""

from astrox.propagator import propagate_two_body
from astrox.models import <models>


def main():
    # TODO: Setup for coord_type="Cartesian"
    # Example: coord_type="Cartesian"
    
    # Execute
    result = propagate_two_body(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbital_elements=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        coord_type="Cartesian",
    )
    
    # Output
    print(f"Success: {result['IsSuccess']}")


if __name__ == "__main__":
    main()
