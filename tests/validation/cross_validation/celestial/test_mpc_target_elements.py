#!/usr/bin/env python3
"""Live cross-validation for the ASTROX MPC ephemeris explicit-elements branch.

The ``TargetElements`` branch of ``/celestial/mpc`` lets callers integrate
supplied MPC orbital elements directly instead of resolving the target name
through the MPC network query. The primary anchor is endpoint-to-endpoint:
the elements parsed from a name-based lookup must reproduce the name-based
ephemeris exactly when fed back through ``target_elements``. The
``reference_frame`` branch is pinned by a distinguishing case: the same
elements labelled ``MeanEclpJ2000`` (JPL) versus ``EclpJ2000ICRF`` (MPC) must
produce measurably different ephemerides.
"""

# Coverage:
#   Branches:
#     - mpc_ephemeris target_elements explicit-element integration: verified
#     - MpcOrbitalElements.reference_frame EclpJ2000ICRF/MeanEclpJ2000: verified
#       as a distinguishing frame pair
#   Fields:
#     - Position.cartesianVelocity samples: verified by exact endpoint-to-endpoint
#       reproduction of the name-based ephemeris
#   Parameters:
#     - target_elements: verified for the Ceres elements returned by the server
#   Comparison:
#     - Endpoint invariant: name-based MPC ephemeris versus explicit-elements
#       ephemeris for identical elements
#     - Distinguishing case: MeanEclpJ2000 versus EclpJ2000ICRF ephemeris
#       separation
#     - Tolerances: ROUNDTRIP_ABS_M, FRAME_SEPARATION_MIN_M

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import celestial
from tests.validation._support import LiveConfigError, configure_astrox_from_env


START = "2026-01-01T00:00:00.000Z"
STOP = "2026-01-02T00:00:00.000Z"
ROUNDTRIP_ABS_M = 1.0e-6
# The JPL/MPC mean-ecliptic variants differ by the frame bias between the two
# ecliptic definitions; the observed Ceres separation is about 87 km.
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
    return np.asarray(samples, dtype=float)


def compare_explicit_elements_roundtrip() -> None:
    name_based = celestial.mpc_ephemeris(target_name="Ceres", start=START, stop=STOP)
    elements = _elements_from_response(name_based)
    explicit = celestial.mpc_ephemeris(
        target_name="Ceres",
        start=START,
        stop=STOP,
        target_elements=elements,
    )
    residual_m = float(np.max(np.abs(_samples(name_based) - _samples(explicit))))
    print(f"MPC_TARGET_ELEMENTS_ROUNDTRIP_MAX_ABS={residual_m:.12g}")
    if residual_m > ROUNDTRIP_ABS_M:
        raise CrossValidationError(
            "explicit target_elements no longer reproduce the name-based MPC ephemeris: "
            f"max residual={residual_m:.12g} m, tolerance {ROUNDTRIP_ABS_M:.12g} m"
        )


def compare_reference_frame_separation() -> None:
    name_based = celestial.mpc_ephemeris(target_name="Ceres", start=START, stop=STOP)
    icrf = _elements_from_response(name_based, reference_frame="EclpJ2000ICRF")
    jpl = _elements_from_response(name_based, reference_frame="MeanEclpJ2000")
    icrf_samples = _samples(
        celestial.mpc_ephemeris(
            target_name="Ceres",
            start=START,
            stop=STOP,
            target_elements=icrf,
        )
    )
    jpl_samples = _samples(
        celestial.mpc_ephemeris(
            target_name="Ceres",
            start=START,
            stop=STOP,
            target_elements=jpl,
        )
    )
    separation_m = float(np.max(np.abs(icrf_samples - jpl_samples)))
    print(f"MPC_REFERENCE_FRAME_SEPARATION_M={separation_m:.12g}")
    if separation_m < FRAME_SEPARATION_MIN_M:
        raise CrossValidationError(
            "MeanEclpJ2000 and EclpJ2000ICRF no longer produce distinguishable "
            f"ephemerides: separation={separation_m:.12g} m, "
            f"minimum {FRAME_SEPARATION_MIN_M:.12g} m"
        )


def test_mpc_explicit_elements_roundtrip_and_frame_branch() -> None:
    configure_astrox_from_env()
    compare_explicit_elements_roundtrip()
    compare_reference_frame_separation()


def main() -> int:
    try:
        test_mpc_explicit_elements_roundtrip_and_frame_branch()
    except (CrossValidationError, LiveConfigError, ResponseShapeError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=2")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
