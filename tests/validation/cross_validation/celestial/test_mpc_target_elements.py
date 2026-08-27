#!/usr/bin/env python3
"""Live cross-validation for ASTROX MPC ephemeris elements and output cadence.

The ``TargetElements`` branch of ``/celestial/mpc`` lets callers integrate
supplied MPC orbital elements directly instead of resolving the target name
through the MPC network query. The primary anchor is endpoint-to-endpoint:
the elements parsed from a name-based lookup must reproduce the name-based
ephemeris exactly when fed back through ``target_elements``. The
``reference_frame`` branch is pinned by a distinguishing case: the same
elements labelled ``MeanEclpJ2000`` (JPL) versus ``EclpJ2000ICRF`` (MPC) must
produce measurably different ephemerides. The output-cadence branch is pinned
by endpoint-to-endpoint grid invariants for the server default, explicit fixed
steps, and ``step_s=0`` internal-step output.
"""

# Coverage:
#   Branches:
#     - mpc_ephemeris target_elements explicit-element integration: verified
#     - MpcOrbitalElements.reference_frame EclpJ2000ICRF/MeanEclpJ2000: verified
#       as a distinguishing frame pair
#     - mpc_ephemeris step_s omitted/86400/172800/0: verified for output-grid
#       selection and endpoint consistency on the maintained Ceres window
#   Fields:
#     - Position.cartesianVelocity samples: verified by exact endpoint-to-endpoint
#       reproduction of the name-based ephemeris
#   Parameters:
#     - target_elements: verified for the Ceres elements returned by the server
#     - step_s: verified for omission, 86400 s, 172800 s, and 0
#   Comparison:
#     - Endpoint invariant: name-based MPC ephemeris versus explicit-elements
#       ephemeris for identical elements
#     - Distinguishing case: MeanEclpJ2000 versus EclpJ2000ICRF ephemeris
#       separation
#     - Output-grid invariants: omission equals 86400 s, the 172800 s result is
#       the matching subset of the 86400 s grid, and step 0 exposes a distinct
#       strictly increasing grid with matching interval endpoints
#     - Tolerances: ROUNDTRIP_ABS_M, FRAME_SEPARATION_MIN_M,
#       OUTPUT_GRID_ABS_TOL

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import celestial
from tests.validation._support import LiveConfigError, configure_astrox_from_env


ROUNDTRIP_ABS_M = 1.0e-6
OUTPUT_GRID_ABS_TOL = 1.0e-6
DEFAULT_OUTPUT_STEP_S = 86400.0
COARSE_OUTPUT_STEP_S = 172800.0
CADENCE_WINDOW_DAYS = 6
# The JPL/MPC mean-ecliptic variants differ by the frame bias between the two
# ecliptic definitions; the observed Ceres separation is tens of kilometres.
FRAME_SEPARATION_MIN_M = 1000.0


class CrossValidationError(Exception):
    """Raised when the explicit-elements branch disagrees with the anchors."""


class ResponseShapeError(Exception):
    """Raised when a live MPC response is unusable for validation."""


def _elements_from_response(payload: object, *, reference_frame: str | None = None) -> celestial.MpcOrbitalElements:
    if not isinstance(payload, dict) or not isinstance(payload.get("OrbitElements"), dict):
        raise ResponseShapeError("MPC response must contain an OrbitElements object")
    wire = payload["OrbitElements"]
    required = (
        "EpochMjdTdt",
        "PeriTimeMjdTdt",
        "Q",
        "SemimajorAxis",
        "Eccentricity",
        "Inclination",
        "Raan",
        "ArgOfPeriapsis",
        "MeanAnomaly",
        "ReferenceFrame",
    )
    for key in required:
        if key not in wire:
            raise ResponseShapeError(f"MPC OrbitElements missing {key}")
    return celestial.mpc_orbital_elements(
        epoch_mjd_tdt=wire["EpochMjdTdt"],
        periapsis_time_mjd_tdt=wire["PeriTimeMjdTdt"],
        periapsis_distance_au=wire["Q"],
        semi_major_axis_au=wire["SemimajorAxis"],
        eccentricity=wire["Eccentricity"],
        inclination_deg=wire["Inclination"],
        raan_deg=wire["Raan"],
        argument_of_periapsis_deg=wire["ArgOfPeriapsis"],
        mean_anomaly_deg=wire["MeanAnomaly"],
        reference_frame=reference_frame if reference_frame is not None else wire["ReferenceFrame"],
    )


def _samples(payload: object) -> np.ndarray:
    if not isinstance(payload, dict) or not isinstance(payload.get("Position"), dict):
        raise ResponseShapeError("MPC response must contain a Position object")
    samples = payload["Position"].get("cartesianVelocity")
    if not isinstance(samples, list) or not samples or len(samples) % 7 != 0:
        raise ResponseShapeError("MPC Position.cartesianVelocity must be a 7-grouped list")
    return np.asarray(samples, dtype=float).reshape((-1, 7))


def _validation_window(payload: object) -> tuple[str, str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("Position"), dict):
        raise ResponseShapeError("MPC response must contain a Position object")
    epoch = payload["Position"].get("epoch")
    if not isinstance(epoch, str):
        raise ResponseShapeError("MPC Position.epoch must be a string")
    start = datetime.fromisoformat(epoch.replace("Z", "+00:00"))
    if start.tzinfo is None:
        raise ResponseShapeError("MPC Position.epoch must include a timezone")
    stop = start + timedelta(days=CADENCE_WINDOW_DAYS)
    return epoch, stop.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def compare_explicit_elements_roundtrip(
    *,
    elements: celestial.MpcOrbitalElements,
    start: str,
    stop: str,
) -> None:
    name_based = celestial.mpc_ephemeris(target_name="Ceres", start=start, stop=stop)
    explicit = celestial.mpc_ephemeris(
        target_name="Ceres",
        start=start,
        stop=stop,
        target_elements=elements,
    )
    residual_m = float(np.max(np.abs(_samples(name_based) - _samples(explicit))))
    print(f"MPC_TARGET_ELEMENTS_ROUNDTRIP_MAX_ABS={residual_m:.12g}")
    if residual_m > ROUNDTRIP_ABS_M:
        raise CrossValidationError(
            "explicit target_elements no longer reproduce the name-based MPC ephemeris: "
            f"max residual={residual_m:.12g} m, tolerance {ROUNDTRIP_ABS_M:.12g} m"
        )


def compare_reference_frame_separation(
    *,
    elements_payload: object,
    start: str,
    stop: str,
) -> None:
    icrf = _elements_from_response(elements_payload, reference_frame="EclpJ2000ICRF")
    jpl = _elements_from_response(elements_payload, reference_frame="MeanEclpJ2000")
    icrf_samples = _samples(
        celestial.mpc_ephemeris(
            target_name="Ceres",
            start=start,
            stop=stop,
            target_elements=icrf,
        )
    )
    jpl_samples = _samples(
        celestial.mpc_ephemeris(
            target_name="Ceres",
            start=start,
            stop=stop,
            target_elements=jpl,
        )
    )
    separation_m = float(
        np.max(np.abs(icrf_samples[:, 1:4] - jpl_samples[:, 1:4]))
    )
    print(f"MPC_REFERENCE_FRAME_SEPARATION_M={separation_m:.12g}")
    if separation_m < FRAME_SEPARATION_MIN_M:
        raise CrossValidationError(
            "MeanEclpJ2000 and EclpJ2000ICRF no longer produce distinguishable "
            f"ephemerides: separation={separation_m:.12g} m, "
            f"minimum {FRAME_SEPARATION_MIN_M:.12g} m"
        )


def compare_output_cadence(
    *,
    elements: celestial.MpcOrbitalElements,
    start: str,
    stop: str,
) -> None:
    common = {
        "target_name": "Ceres",
        "start": start,
        "stop": stop,
        "target_elements": elements,
    }
    server_default = _samples(celestial.mpc_ephemeris(**common))
    daily = _samples(
        celestial.mpc_ephemeris(**common, step_s=DEFAULT_OUTPUT_STEP_S)
    )
    coarse = _samples(
        celestial.mpc_ephemeris(**common, step_s=COARSE_OUTPUT_STEP_S)
    )
    internal = _samples(celestial.mpc_ephemeris(**common, step_s=0))

    expected_daily_offsets = np.arange(
        0.0,
        CADENCE_WINDOW_DAYS * DEFAULT_OUTPUT_STEP_S + DEFAULT_OUTPUT_STEP_S,
        DEFAULT_OUTPUT_STEP_S,
    )
    expected_coarse_offsets = np.arange(
        0.0,
        CADENCE_WINDOW_DAYS * DEFAULT_OUTPUT_STEP_S + COARSE_OUTPUT_STEP_S,
        COARSE_OUTPUT_STEP_S,
    )
    if not np.array_equal(daily[:, 0], expected_daily_offsets):
        raise CrossValidationError(
            f"step_s={DEFAULT_OUTPUT_STEP_S:g} returned offsets {daily[:, 0].tolist()}, "
            f"expected {expected_daily_offsets.tolist()}"
        )
    if not np.array_equal(coarse[:, 0], expected_coarse_offsets):
        raise CrossValidationError(
            f"step_s={COARSE_OUTPUT_STEP_S:g} returned offsets {coarse[:, 0].tolist()}, "
            f"expected {expected_coarse_offsets.tolist()}"
        )

    default_residual = float(np.max(np.abs(server_default - daily)))
    coarse_residual = float(np.max(np.abs(coarse - daily[::2])))
    print(f"MPC_DEFAULT_STEP_MAX_ABS={default_residual:.12g}")
    print(f"MPC_COARSE_GRID_MAX_ABS={coarse_residual:.12g}")
    if default_residual > OUTPUT_GRID_ABS_TOL:
        raise CrossValidationError(
            "omitted step no longer matches explicit 86400-second output: "
            f"max residual={default_residual:.12g}, tolerance {OUTPUT_GRID_ABS_TOL:.12g}"
        )
    if coarse_residual > OUTPUT_GRID_ABS_TOL:
        raise CrossValidationError(
            "172800-second output no longer matches the common 86400-second samples: "
            f"max residual={coarse_residual:.12g}, tolerance {OUTPUT_GRID_ABS_TOL:.12g}"
        )

    internal_offsets = internal[:, 0]
    internal_deltas = np.diff(internal_offsets)
    interval_duration_s = CADENCE_WINDOW_DAYS * DEFAULT_OUTPUT_STEP_S
    if (
        internal_offsets[0] != 0.0
        or internal_offsets[-1] != interval_duration_s
        or not np.all(internal_deltas > 0.0)
    ):
        raise CrossValidationError(
            "step_s=0 must return a strictly increasing internal grid spanning the requested interval"
        )
    if np.array_equal(internal_offsets, daily[:, 0]) or np.allclose(
        internal_deltas,
        DEFAULT_OUTPUT_STEP_S,
        rtol=0.0,
        atol=1.0e-9,
    ):
        raise CrossValidationError(
            "step_s=0 did not produce a grid distinguishable from fixed 86400-second output"
        )
    endpoint_residual = float(
        np.max(np.abs(internal[[0, -1], :] - daily[[0, -1], :]))
    )
    print(f"MPC_INTERNAL_STEP_SAMPLE_COUNT={len(internal)}")
    print(
        "MPC_INTERNAL_STEP_RANGE_S="
        f"{float(np.min(internal_deltas)):.12g}/{float(np.max(internal_deltas)):.12g}"
    )
    print(f"MPC_INTERNAL_ENDPOINT_MAX_ABS={endpoint_residual:.12g}")
    if endpoint_residual > OUTPUT_GRID_ABS_TOL:
        raise CrossValidationError(
            "step_s=0 interval endpoints no longer match the fixed-step output: "
            f"max residual={endpoint_residual:.12g}, tolerance {OUTPUT_GRID_ABS_TOL:.12g}"
        )


def test_mpc_explicit_elements_roundtrip_and_frame_branch() -> None:
    configure_astrox_from_env()
    elements_payload = celestial.mpc_ephemeris(target_name="Ceres")
    elements = _elements_from_response(elements_payload)
    start, stop = _validation_window(elements_payload)
    print(f"MPC_VALIDATION_WINDOW={start}/{stop}")
    compare_explicit_elements_roundtrip(elements=elements, start=start, stop=stop)
    compare_reference_frame_separation(
        elements_payload=elements_payload,
        start=start,
        stop=stop,
    )
    compare_output_cadence(elements=elements, start=start, stop=stop)


def main() -> int:
    try:
        test_mpc_explicit_elements_roundtrip_and_frame_branch()
    except (CrossValidationError, LiveConfigError, ResponseShapeError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=5")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
