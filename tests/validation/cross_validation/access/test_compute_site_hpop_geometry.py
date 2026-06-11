"""AccessComputeV2 site-to-HPOP cross-validation against local two-body geometry."""

# Coverage:
#   Branches:
#     - ground site -> HPOP satellite with two-body HPOP gravity config: partial
#   Fields:
#     - Passes.AccessStart/AccessStop: verified against local two-body state plus WGS84 obstruction
#     - AllDatas.Azimuth/Elevation/Range: partial (checked for first returned pass when access exists)
#   Parameters:
#     - from_entity site coordinates: verified for the shared Hawaii site
#     - to_entity HPOP two-body orbit/config: partial (validated against the matching local Keplerian state)
#     - compute_aer/step_s: partial for compute_aer=True and 300 s cadence
#   Comparison:
#     - External: local Keplerian two-body propagation and WGS84 segment-obstruction/topocentric geometry
#     - Constants: access shared site, EARTH_MU
#     - Tolerances: INTERVAL_ABS_S and mixed-model AER tolerances

from __future__ import annotations

import sys

from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._cases import (
    CrossValidationError,
    START,
    STOP,
    access_orbit,
    compute_access,
    hpop_entity,
    site,
)
from tests.validation.cross_validation.access._geometry import two_body_state_ecef
from tests.validation.cross_validation.access._mixed_model import compare_site_origin_access


def test_site_to_hpop_two_body_config_matches_kepler_obstruction_oracle() -> None:
    configure_astrox_from_env()
    result = compute_access(site(), hpop_entity(), step_s=300.0, compute_aer=True)
    compare_site_origin_access(
        result,
        state_ecef=lambda offset_s: two_body_state_ecef(access_orbit(), offset_s),
        start=START,
        stop=STOP,
    )


def main() -> int:
    try:
        test_site_to_hpop_two_body_config_matches_kepler_obstruction_oracle()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
