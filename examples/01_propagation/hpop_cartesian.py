# /// script
# dependencies = ["astrox-client"]
# requires-python = ">=3.10"
# ///
"""
High-precision orbit propagation using Cartesian state parameterization.

API: POST /api/Propagator/HPOP
"""

from astrox.propagator import propagate_hpop
from astrox.models import <models>


def main():
    # TODO: Setup for coord_type="Cartesian"
    # Example: coord_type="Cartesian"
    
    # Execute
    result = propagate_hpop(
        start="2024-01-01T00:00:00.000Z",
        stop="2024-01-02T00:00:00.000Z",
        orbit_epoch="2024-01-01T00:00:00.000Z",
        orbital_elements=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        coefficient_of_drag=0.0,
        area_mass_ratio_drag=0.0,
        coefficient_of_srp=0.0,
        area_mass_ratio_srp=0.0,
        hpop_propagator=None,
        coord_type="Cartesian",
    )
    
    # Output
    print(f"Success: {result['IsSuccess']}")


if __name__ == "__main__":
    main()
