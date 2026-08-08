#!/usr/bin/env python3
"""Live snapshot validation for conjunction close-approach functions."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import components, conjunction, orbits, propagator  # noqa: E402
from tests.validation._support import (  # noqa: E402
    LiveSnapshotCase,
    SnapshotError,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("close_approaches.snap.json")
START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
PRIMARY_LINE1 = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995"
)
PRIMARY_LINE2 = (
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456"
)
TARGET_LINE1 = "1 25545U 99999A   24001.00000000  .00000000  00000-0  00000-0 0  9993"
TARGET_LINE2 = "2 25545  51.6264 339.8059 0009386 217.1816 137.7421 15.52489080    03"


def primary_tle() -> orbits.Tle:
    return orbits.tle(
        line1=PRIMARY_LINE1,
        line2=PRIMARY_LINE2,
        name="ISS",
        catalog_number="25544",
    )


def target_tle() -> orbits.Tle:
    return orbits.tle(
        line1=TARGET_LINE1,
        line2=TARGET_LINE2,
        name="probe",
        catalog_number="25545",
    )


def _require_results(result: conjunction.CloseApproachesResult) -> conjunction.CloseApproachesResult:
    if not result.is_success or not result.results:
        raise SnapshotError("close-approach response did not contain a successful result")
    return result


def close_approaches_v3() -> conjunction.CloseApproachesResult:
    return _require_results(
        conjunction.find_tle_close_approaches(
            start=START,
            stop=STOP,
            tle=primary_tle(),
            targets=[target_tle()],
            tol_max_distance_km=1000.0,
            tol_cross_dt_s=1000.0,
            tol_theta_deg=180.0,
            tol_dh_km=1000.0,
        )
    )


def propagated_czml_position() -> components.CzmlPosition:
    _, position = propagator.sgp4(
        start=START,
        stop=STOP,
        tle=primary_tle(),
        step_s=60.0,
    )
    return components.czml_position(
        epoch=position.epoch,
        central_body=position.central_body,
        interpolation_algorithm=position.interpolation_algorithm,
        interpolation_degree=position.interpolation_degree,
        reference_frame=position.reference_frame,
        cartesian_velocity=position.cartesian_velocity,
    )


def close_approaches_v4() -> conjunction.CloseApproachesResult:
    return _require_results(
        conjunction.find_czml_close_approaches(
            start=START,
            stop=STOP,
            position=propagated_czml_position(),
            targets=[target_tle()],
            tol_max_distance_km=1000.0,
        )
    )


CASES = [
    LiveSnapshotCase(
        id="tle_v3",
        description="V3 close-approach call with a TLE primary and target.",
        run=close_approaches_v3,
    ),
    LiveSnapshotCase(
        id="czml_v4",
        description="V4 close-approach call with a propagated CZML position and target.",
        run=close_approaches_v4,
    ),
]


def test_close_approaches_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
