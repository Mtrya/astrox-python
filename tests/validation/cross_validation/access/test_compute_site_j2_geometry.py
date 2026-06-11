"""AccessComputeV2 site-to-J2 cross-validation against local J2 geometry."""

# Coverage:
#   Branches:
#     - ground site -> J2 satellite: partial
#   Fields:
#     - Passes.AccessStart/AccessStop: verified against local J2 state plus WGS84 obstruction
#     - AllDatas.Azimuth/Elevation/Range: partial (checked for first returned pass when access exists)
#   Parameters:
#     - from_entity site coordinates: verified for the shared Hawaii site
#     - to_entity J2 orbit/constants: verified for the calibrated ASTROX-like J2 secular helper
#     - compute_aer/step_s: partial for compute_aer=True and 300 s cadence
#   Comparison:
#     - External: local calibrated J2 secular state and WGS84 segment-obstruction/topocentric geometry
#     - Constants: access shared site, EARTH_MU, EARTH_RADIUS_M, ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE
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
    j2_entity,
    site,
)
from tests.validation.cross_validation.access._geometry import j2_state_ecef
from tests.validation.cross_validation.access._mixed_model import compare_site_origin_access


def test_site_to_j2_matches_local_j2_obstruction_oracle() -> None:
    configure_astrox_from_env()
    result = compute_access(site(), j2_entity(), step_s=300.0, compute_aer=True)
    compare_site_origin_access(
        result,
        state_ecef=lambda offset_s: j2_state_ecef(access_orbit(), offset_s),
        start=START,
        stop=STOP,
    )


def main() -> int:
    try:
        test_site_to_j2_matches_local_j2_obstruction_oracle()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
