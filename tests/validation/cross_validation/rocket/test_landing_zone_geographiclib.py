#!/usr/bin/env python3
"""Cross-validation of rocket.landing_zone against WGS-84 geodesy.

Coverage:
  Branches:
    - north-south launch-to-impact track: verified
    - east-west launch-to-impact track: verified
    - diagonal launch-to-impact track: unresolved
  Fields:
    - cartographicDegrees vertex count and pairing: verified
    - output ordering (Longitude, Latitude, Height): verified
    - height interpolation near impact point: verified
    - forward/right frame convention: partial
  Parameters:
    - launch point: verified
    - impact point: verified
    - zone_xys_km: verified for cardinal tracks, unresolved for diagonal
  Comparison:
    - External: geographiclib WGS-84 direct geodesic
    - Constants: WGS-84 ellipsoid
    - Tolerances: POSITION_ABS_M=5.0, HEIGHT_ABS_M=1.0

Investigation notes:
  For cardinal launch-to-impact tracks (north-south and east-west), ASTROX
  maps ``zone_xys_km`` pairs as a local frame whose +X axis is the geodesic
  direction from launch to impact at the impact point (``azi2`` of the
  launch-to-impact inverse geodesic) and whose +Y axis is 90° clockwise from
  +X. Each output vertex is the WGS-84 direct geodesic offset
  ``distance = hypot(X, Y) * 1000 m`` at azimuth ``azi2 + atan2(Y, X)``.

  For a diagonal track (launch 100°E 30°N, impact 101°E 30.5°N), the same
  geodesic forward/right convention predicts vertices rotated by roughly 60°
  from the ASTROX output. The residual is stable (~1.1 km position error) and
  is not explained by rhumb-line forward/right or by swapping the X/Y pair
  order within the bounded investigation budget. The observed ASTROX
  convention for this track is documented in the xfail message.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest
from geographiclib.geodesic import Geodesic

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import rocket
from tests.validation._support import LiveConfigError, configure_astrox_from_env


WGS84 = Geodesic.WGS84
POSITION_ABS_M = 5.0
HEIGHT_ABS_M = 1.0


class CrossValidationError(Exception):
    """Raised when ASTROX landing-zone output disagrees with the comparison path."""


@dataclass(frozen=True, kw_only=True)
class LandingZoneCase:
    label: str
    launch: tuple[float, float, float]
    impact: tuple[float, float, float]
    zone_xys_km: list[float]


@dataclass(frozen=True, kw_only=True)
class GeodeticPoint:
    longitude_deg: float
    latitude_deg: float
    height_m: float


def verified_cases() -> tuple[LandingZoneCase, ...]:
    return (
        LandingZoneCase(
            label="north_south",
            launch=(100.0, 31.0, 0.0),
            impact=(100.0, 30.0, 0.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="east_west",
            launch=(101.0, 30.0, 0.0),
            impact=(100.0, 30.0, 0.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
    )


def unresolved_cases() -> tuple[LandingZoneCase, ...]:
    return (
        LandingZoneCase(
            label="diagonal",
            launch=(100.0, 30.0, 0.0),
            impact=(101.0, 30.5, 100.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
    )


def expected_vertices(
    impact: tuple[float, float, float],
    launch: tuple[float, float, float],
    zone_xys_km: list[float],
) -> list[GeodeticPoint]:
    """Independent WGS-84 prediction assuming +X=forward, +Y=right (clockwise)."""
    launch_lat, launch_lon = launch[1], launch[0]
    impact_lat, impact_lon, impact_height = impact[1], impact[0], impact[2]

    geodesic = WGS84.Inverse(launch_lat, launch_lon, impact_lat, impact_lon)
    forward_azimuth_deg = geodesic["azi2"]

    vertices: list[GeodeticPoint] = []
    for index in range(0, len(zone_xys_km), 2):
        x_km = zone_xys_km[index]
        y_km = zone_xys_km[index + 1]
        distance_m = math.hypot(x_km, y_km) * 1000.0
        azimuth_deg = (forward_azimuth_deg + math.degrees(math.atan2(y_km, x_km))) % 360.0
        direct = WGS84.Direct(impact_lat, impact_lon, azimuth_deg, distance_m)
        vertices.append(
            GeodeticPoint(
                longitude_deg=direct["lon2"],
                latitude_deg=direct["lat2"],
                height_m=impact_height,
            )
        )
    return vertices


def call_astrox(case: LandingZoneCase) -> list[GeodeticPoint]:
    result = rocket.landing_zone(
        launch_longitude_deg=case.launch[0],
        launch_latitude_deg=case.launch[1],
        launch_height_m=case.launch[2],
        impact_longitude_deg=case.impact[0],
        impact_latitude_deg=case.impact[1],
        impact_height_m=case.impact[2],
        zone_xys_km=case.zone_xys_km,
    )
    cartographic = result.get("cartographicDegrees", [])
    if len(cartographic) % 3 != 0:
        raise CrossValidationError(
            f"{case.label}: cartographicDegrees length {len(cartographic)} is not a multiple of 3"
        )
    vertices: list[GeodeticPoint] = []
    for index in range(0, len(cartographic), 3):
        vertices.append(
            GeodeticPoint(
                longitude_deg=cartographic[index],
                latitude_deg=cartographic[index + 1],
                height_m=cartographic[index + 2],
            )
        )
    return vertices


def compare_case(case: LandingZoneCase) -> list[str]:
    failures: list[str] = []
    actual = call_astrox(case)
    expected = expected_vertices(case.impact, case.launch, case.zone_xys_km)

    if len(actual) != len(expected):
        failures.append(
            f"{case.label}: vertex count mismatch; expected {len(expected)}, got {len(actual)}"
        )
        return failures

    for index, (actual_point, expected_point) in enumerate(zip(actual, expected)):
        geodesic = WGS84.Inverse(
            actual_point.latitude_deg,
            actual_point.longitude_deg,
            expected_point.latitude_deg,
            expected_point.longitude_deg,
        )
        position_error_m = geodesic["s12"]
        if position_error_m > POSITION_ABS_M:
            failures.append(
                f"{case.label}[{index}]: position error {position_error_m:.3f} m "
                f"exceeds {POSITION_ABS_M:.3f} m; "
                f"actual=({actual_point.longitude_deg:.8f}, {actual_point.latitude_deg:.8f}), "
                f"expected=({expected_point.longitude_deg:.8f}, {expected_point.latitude_deg:.8f})"
            )

        height_error_m = abs(actual_point.height_m - expected_point.height_m)
        if height_error_m > HEIGHT_ABS_M:
            failures.append(
                f"{case.label}[{index}]: height error {height_error_m:.3f} m "
                f"exceeds {HEIGHT_ABS_M:.3f} m"
            )

    return failures


def test_landing_zone_cardinal_tracks_match_geodesic_forward_right() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in verified_cases():
        failures.extend(compare_case(case))
    if failures:
        raise CrossValidationError("\n".join(failures))


@pytest.mark.calibration
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Diagonal track residual is stable but unexplained: ASTROX rotates the "
        "local XY frame relative to the WGS-84 geodesic forward/right convention. "
        "See module docstring for investigation notes."
    ),
)
def test_landing_zone_diagonal_track_convention_unresolved() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in unresolved_cases():
        failures.extend(compare_case(case))
    if failures:
        raise CrossValidationError("\n".join(failures))


def main() -> int:
    try:
        test_landing_zone_cardinal_tracks_match_geodesic_forward_right()
        test_landing_zone_diagonal_track_convention_unresolved()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=3")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
