"""AccessComputeV2 option semantics cross-validation."""

from __future__ import annotations

from tests.validation._support import configure_astrox_from_env
from tests.validation.cross_validation.access._cases import (
    CHAIN_INTERVAL_ABS_S,
    CrossValidationError,
    START,
    STOP,
    compute_access,
    remote_site,
    sgp4_entity,
    site,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    intervals_from_access_passes,
    seconds_since,
)

AER_KEYS = {
    "AccessBeginData",
    "AccessEndData",
    "AllDatas",
    "MaxElevationData",
    "MaxRangeData",
    "MinElevationData",
    "MinRangeData",
}


def test_compute_aer_false_matches_omitted_and_true_preserves_intervals() -> None:
    configure_astrox_from_env()
    ground = site()
    target = sgp4_entity()
    omitted = compute_access(ground, target, start=START, stop=STOP, compute_aer=None)
    explicit_false = compute_access(ground, target, start=START, stop=STOP, compute_aer=False)
    explicit_true = compute_access(ground, target, start=START, stop=STOP, compute_aer=True)

    compare_intervals(
        intervals_from_access_passes(omitted["Passes"]),
        intervals_from_access_passes(explicit_false["Passes"]),
        tolerance_s=CHAIN_INTERVAL_ABS_S,
    )
    compare_intervals(
        intervals_from_access_passes(omitted["Passes"]),
        intervals_from_access_passes(explicit_true["Passes"]),
        tolerance_s=CHAIN_INTERVAL_ABS_S,
    )

    omitted_keys = set(omitted["Passes"][0])
    false_keys = set(explicit_false["Passes"][0])
    true_keys = set(explicit_true["Passes"][0])
    if omitted_keys & AER_KEYS:
        raise CrossValidationError(f"ComputeAER omitted unexpectedly returned AER keys: {omitted_keys & AER_KEYS}")
    if false_keys & AER_KEYS:
        raise CrossValidationError(f"ComputeAER false unexpectedly returned AER keys: {false_keys & AER_KEYS}")
    missing_true_keys = AER_KEYS - true_keys
    if missing_true_keys:
        raise CrossValidationError(f"ComputeAER true did not return expected AER keys: {missing_true_keys}")


def test_out_step_controls_aer_sample_cadence_not_interval_boundaries() -> None:
    configure_astrox_from_env()
    ground = site()
    target = sgp4_entity()
    coarse = compute_access(
        ground,
        target,
        start=START,
        stop=STOP,
        step_s=600.0,
        compute_aer=True,
    )
    fine = compute_access(
        ground,
        target,
        start=START,
        stop=STOP,
        step_s=60.0,
        compute_aer=True,
    )

    compare_intervals(
        intervals_from_access_passes(coarse["Passes"]),
        intervals_from_access_passes(fine["Passes"]),
        tolerance_s=CHAIN_INTERVAL_ABS_S,
    )

    coarse_pass = coarse["Passes"][0]
    fine_pass = fine["Passes"][0]
    coarse_rows = coarse_pass["AllDatas"]
    fine_rows = fine_pass["AllDatas"]
    if len(coarse_rows) != 2:
        raise CrossValidationError(f"coarse OutStep expected only access-boundary AER rows, got {len(coarse_rows)}")
    if len(fine_rows) <= len(coarse_rows):
        raise CrossValidationError(
            f"fine OutStep did not add interior AER rows: coarse={len(coarse_rows)} fine={len(fine_rows)}"
        )

    if coarse_rows[0]["Time"] != coarse_pass["AccessStart"] or coarse_rows[-1]["Time"] != coarse_pass["AccessStop"]:
        raise CrossValidationError("coarse AER rows do not preserve access start/stop boundary samples")
    if fine_rows[0]["Time"] != fine_pass["AccessStart"] or fine_rows[-1]["Time"] != fine_pass["AccessStop"]:
        raise CrossValidationError("fine AER rows do not preserve access start/stop boundary samples")

    for index in range(len(fine_rows) - 2):
        spacing_s = seconds_since(str(fine_rows[index + 1]["Time"]), str(fine_rows[index]["Time"]))
        if abs(spacing_s - 60.0) > CHAIN_INTERVAL_ABS_S:
            raise CrossValidationError(
                f"fine AER row spacing at index {index} was {spacing_s:.12g} s, expected 60 s"
            )


def test_no_access_with_compute_aer_true_returns_empty_passes() -> None:
    configure_astrox_from_env()
    result = compute_access(
        site("Hawaii"),
        remote_site(),
        start=START,
        stop=STOP,
        step_s=60.0,
        compute_aer=True,
    )
    if result["Passes"] != []:
        raise CrossValidationError(f"blocked no-access case returned passes: {result['Passes']!r}")
