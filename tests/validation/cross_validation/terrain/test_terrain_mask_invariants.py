#!/usr/bin/env python3
"""Live terrain-mask invariant validation across the full and simple routes."""

# Coverage:
#   Branches:
#     - AzElMask and AzElMaskSimple with an explicit Moon polar DEM
#       configuration: verified for response structure and cross-endpoint pair
#       consistency
#   Fields:
#     - AzElMaskData full entries and simple numeric pairs: verified as aligned
#       response data; terrain elevation semantics are not independently verified
#   Parameters:
#     - Moon site at latitude -89 degrees
#     - FlagPole=1, Moon_LDEM_80s_20m, TerrainZoomLevel=-1, StepSize=30 m,
#       MaxSearchRange=15 km, and an explicit empty TerrainServerUrl required by
#       the maintained server route
#   Comparison:
#     - Independent invariants: 361 full entries correspond to 722 simple values,
#       azimuth covers 0 through 2*pi monotonically, every full entry has a
#       non-empty Items collection, and the two routes expose identical pairs
#     - Tolerance: 1e-12 for pair and endpoint-angle comparisons

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import components, terrain  # noqa: E402
from tests.validation._support import configure_astrox_from_env  # noqa: E402


SITE = components.site_position(
    longitude_deg=0.0,
    latitude_deg=-89.0,
    height_m=0.0,
    central_body="Moon",
)
CONFIG = terrain.TerrainMaskConfig(
    terrain_server_url="",
    flag_pole=1,
    polar_dem_file_name="Moon_LDEM_80s_20m",
    terrain_zoom_level=-1,
    step_size_m=30.0,
    max_search_range_km=15.0,
)
ABS_TOL = 1.0e-12


class CrossValidationError(Exception):
    """Raised when the maintained terrain response invariants disagree."""


def require_numeric(value: Any, *, field: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise CrossValidationError(f"{field} must be numeric")
    return float(value)


def require_success(response: Any, *, route: str) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise CrossValidationError(f"{route} response must be an object")
    if response.get("IsSuccess") is not True:
        raise CrossValidationError(
            f"{route} returned IsSuccess={response.get('IsSuccess')!r}: "
            f"{response.get('Message')!r}"
        )
    data = response.get("AzElMaskData")
    if not isinstance(data, list):
        raise CrossValidationError(f"{route} AzElMaskData must be an array")
    return response


def check_mask_invariants() -> None:
    full_response = require_success(
        terrain.azimuth_elevation_mask(site_position=SITE, config=CONFIG),
        route="AzElMask",
    )
    simple_response = require_success(
        terrain.azimuth_elevation_mask_simple(site_position=SITE, config=CONFIG),
        route="AzElMaskSimple",
    )
    full_data = full_response["AzElMaskData"]
    simple_data = simple_response["AzElMaskData"]
    if len(full_data) != 361:
        raise CrossValidationError(f"AzElMask returned {len(full_data)} entries, expected 361")
    if len(simple_data) != 722:
        raise CrossValidationError(
            f"AzElMaskSimple returned {len(simple_data)} values, expected 722"
        )
    if len(simple_data) != 2 * len(full_data):
        raise CrossValidationError("full and simple mask lengths are not synchronized")

    previous_azimuth: float | None = None
    for index, entry in enumerate(full_data):
        if not isinstance(entry, dict):
            raise CrossValidationError(f"AzElMaskData[{index}] must be an object")
        azimuth = require_numeric(entry.get("Azimuth"), field=f"AzElMaskData[{index}].Azimuth")
        elevation = require_numeric(
            entry.get("Elevation"),
            field=f"AzElMaskData[{index}].Elevation",
        )
        items = entry.get("Items")
        if not isinstance(items, list) or not items:
            raise CrossValidationError(
                f"AzElMaskData[{index}].Items must be a non-empty array"
            )
        if previous_azimuth is not None and azimuth < previous_azimuth:
            raise CrossValidationError(
                f"AzElMaskData azimuth decreased at index {index}: "
                f"{previous_azimuth:g} -> {azimuth:g}"
            )
        previous_azimuth = azimuth
        simple_azimuth = require_numeric(
            simple_data[index * 2],
            field=f"AzElMaskSimple[{index * 2}]",
        )
        simple_elevation = require_numeric(
            simple_data[index * 2 + 1],
            field=f"AzElMaskSimple[{index * 2 + 1}]",
        )
        if not math.isclose(azimuth, simple_azimuth, abs_tol=ABS_TOL, rel_tol=0.0):
            raise CrossValidationError(
                f"azimuth pair mismatch at index {index}: {azimuth!r} vs {simple_azimuth!r}"
            )
        if not math.isclose(elevation, simple_elevation, abs_tol=ABS_TOL, rel_tol=0.0):
            raise CrossValidationError(
                f"elevation pair mismatch at index {index}: {elevation!r} vs {simple_elevation!r}"
            )

    first_azimuth = require_numeric(full_data[0]["Azimuth"], field="first Azimuth")
    last_azimuth = require_numeric(full_data[-1]["Azimuth"], field="last Azimuth")
    if not math.isclose(first_azimuth, 0.0, abs_tol=ABS_TOL, rel_tol=0.0):
        raise CrossValidationError(f"first Azimuth={first_azimuth:g}, expected 0")
    if not math.isclose(last_azimuth, 2.0 * math.pi, abs_tol=ABS_TOL, rel_tol=0.0):
        raise CrossValidationError(
            f"last Azimuth={last_azimuth:.12g}, expected 2*pi={2.0 * math.pi:.12g}"
        )


def test_terrain_mask_routes_preserve_shared_pairs() -> None:
    configure_astrox_from_env()
    check_mask_invariants()


def main() -> int:
    try:
        test_terrain_mask_routes_preserve_shared_pairs()
    except Exception as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
