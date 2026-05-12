# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
Ballistic propagation variation using delta-v minimum eccentricity parameter.

API: POST /api/Propagator/Ballistic
"""

from astrox.propagator import propagate_ballistic
from astrox.models import <models>


def main():
    # TODO: Setup for ballistic_type="DeltaV_MinEcc"
    # Example: ballistic_type="DeltaV_MinEcc", ballistic_type_value=...
    
    # Execute
    result = propagate_ballistic(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude=0.0,
        impact_longitude=0.0,
        # Specify delta-v minimum eccentricity parameter
        ballistic_type="DeltaV_MinEcc",
        ballistic_type_value=0.0,
    )
    
    # Output
    print(f"Success: {result['IsSuccess']}")


if __name__ == "__main__":
    main()
