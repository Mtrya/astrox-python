"""AccessComputeV2 SGP4-to-J2 cross-validation against local geometry."""

# Coverage:
#   Branches:
#     - SGP4 satellite -> J2 satellite: verified for the no-access sample window
#   Fields:
#     - Passes.AccessStart/AccessStop: verified (empty interval set matches independent segment-obstruction oracle)
#     - AllDatas: partial (checked to exist if ASTROX ever returns a pass, but the covered case has no access)
#   Parameters:
#     - from_entity SGP4 TLEs: verified for TLE_A
#     - to_entity J2 Keplerian orbit and J2 constants: verified for the calibrated ASTROX-like secular J2 helper
#     - compute_aer: partial (requested; no AER rows exist because the verified case has no pass)
#   Comparison:
#     - External: Skyfield SGP4 state plus local calibrated J2 secular state, both tested with WGS84 segment obstruction
#     - Constants: TLE_A, EARTH_MU, EARTH_RADIUS_M, ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE
#     - Tolerances: INTERVAL_ABS_S

from __future__ import annotations

import sys

from tests.validation._support import LiveConfigError, configure_astrox_from_env
from tests.validation.cross_validation.access._aer import first_aer_rows
from tests.validation.cross_validation.access._cases import (
    CrossValidationError,
    INTERVAL_ABS_S,
    START,
    STOP,
    access_orbit,
    compute_access,
    j2_entity,
    sgp4_entity,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    intervals_from_access_passes,
    j2_state_ecef,
    sampled_satellite_visibility_intervals,
    sgp4_state_ecef,
)


def test_sgp4_to_j2_no_access_matches_segment_obstruction_oracle() -> None:
    configure_astrox_from_env()
    result = compute_access(
        sgp4_entity(),
        j2_entity(),
        compute_aer=True,
        step_s=300.0,
    )
    actual = intervals_from_access_passes(result["Passes"])
    expected = sampled_satellite_visibility_intervals(
        start=START,
        stop=STOP,
        left_state=sgp4_state_ecef,
        right_state=lambda offset_s: j2_state_ecef(access_orbit(), offset_s),
    )
    compare_intervals(expected, actual, tolerance_s=INTERVAL_ABS_S)
    if actual:
        rows = list(first_aer_rows(result, max_passes=1))
        if not rows:
            raise CrossValidationError("ASTROX returned SGP4-to-J2 passes without AER samples")


def main() -> int:
    try:
        test_sgp4_to_j2_no_access_matches_segment_obstruction_oracle()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
