"""AccessComputeV2 J2-to-two-body cross-validation against local geometry."""

# Coverage:
#   Branches:
#     - J2 satellite -> two_body satellite: partial
#   Fields:
#     - Passes.AccessStart/AccessStop: verified against local J2/two-body states plus WGS84 obstruction
#     - AllDatas: partial (satellite-origin AER convention not asserted in this script)
#   Parameters:
#     - from_entity J2 orbit/constants: verified for the calibrated ASTROX-like J2 secular helper
#     - to_entity two_body orbit and Earth mu: verified for the shared access orbit
#     - compute_aer/step_s: partial for compute_aer=True and 300 s cadence
#   Comparison:
#     - External: local calibrated J2 secular state, local two-body propagation, and WGS84 segment obstruction
#     - Constants: EARTH_MU, EARTH_RADIUS_M, ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE
#     - Tolerances: INTERVAL_ABS_S

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
    two_body_entity,
)
from tests.validation.cross_validation.access._geometry import (
    j2_state_ecef,
    two_body_state_ecef,
)
from tests.validation.cross_validation.access._mixed_model import compare_satellite_pair_access


def test_j2_to_two_body_matches_local_segment_obstruction_oracle() -> None:
    configure_astrox_from_env()
    result = compute_access(j2_entity(), two_body_entity(), step_s=300.0, compute_aer=True)
    compare_satellite_pair_access(
        result,
        left_state_ecef=lambda offset_s: j2_state_ecef(access_orbit(), offset_s),
        right_state_ecef=lambda offset_s: two_body_state_ecef(access_orbit(), offset_s),
        start=START,
        stop=STOP,
    )


def main() -> int:
    try:
        test_j2_to_two_body_matches_local_segment_obstruction_oracle()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
