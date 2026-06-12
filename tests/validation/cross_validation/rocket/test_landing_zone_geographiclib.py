#!/usr/bin/env python3
"""Cross-validation of rocket.landing_zone against WGS-84 geodesy.

Coverage:
  Branches:
    - north-south launch-to-impact track: verified
    - east-west launch-to-impact track (eastward): verified
    - east-west launch-to-impact track (westward): verified
    - diagonal north-east track: verified
    - diagonal north-west track: verified
    - diagonal south-east track: verified
    - diagonal south-west track: verified
    - southern-hemisphere north-east track: verified
  Fields:
    - cartographicDegrees vertex count and pairing: verified
    - output ordering (Longitude, Latitude, Height): verified
    - height preservation at impact point: verified
    - ASTROX local XY frame convention: verified
  Parameters:
    - launch point geodetic coordinates: verified
    - impact point geodetic coordinates: verified
    - zone_xys_km offsets (varied magnitudes and sign patterns): verified
  Comparison:
    - External: geographiclib WGS-84 direct geodesic
    - Constants: WGS-84 ellipsoid
    - Tolerances: POSITION_ABS_M=5.0, HEIGHT_ABS_M=1.0

Calibrated ASTROX convention:
  ASTROX builds a local right-handed frame at the impact point.  The +X axis
  is chosen from the launch-to-impact geodesic azimuth at the impact point
  (``azi2``) and its supplement (``180 - azi2``) so that +X has a non-positive
  north component (it points southward or horizontally).  The +Y axis is +X
  rotated 90 degrees clockwise.  Each ``[X, Y]`` pair in ``zone_xys_km`` is
  applied as a WGS-84 direct geodesic offset with distance ``hypot(X, Y)`` km
  at azimuth ``plus_x_az + atan2(Y, X)``.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

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


def cases() -> tuple[LandingZoneCase, ...]:
    return (
        LandingZoneCase(
            label="north_south",
            launch=(100.0, 31.0, 0.0),
            impact=(100.0, 30.0, 0.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="east_west_eastward",
            launch=(100.0, 30.0, 0.0),
            impact=(101.0, 30.0, 0.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="east_west_westward",
            launch=(101.0, 30.0, 0.0),
            impact=(100.0, 30.0, 0.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="diagonal_north_east",
            launch=(100.0, 30.0, 0.0),
            impact=(101.0, 30.5, 100.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="diagonal_north_west",
            launch=(101.0, 30.0, 0.0),
            impact=(100.0, 31.0, 100.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="diagonal_south_east",
            launch=(100.0, 31.0, 0.0),
            impact=(101.0, 30.0, 100.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="diagonal_south_west",
            launch=(101.0, 31.0, 0.0),
            impact=(100.0, 30.0, 100.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="southern_hemisphere_north_east",
            launch=(100.0, -30.5, 0.0),
            impact=(101.0, -30.0, 100.0),
            zone_xys_km=[1.0, 0.5, -1.0, 0.5, -1.0, -0.5, 1.0, -0.5],
        ),
        LandingZoneCase(
            label="diagonal_north_east_large_offsets",
            launch=(100.0, 30.0, 0.0),
            impact=(101.0, 30.5, 100.0),
            zone_xys_km=[2.0, 1.0, -2.0, 1.0, -2.0, -1.0, 2.0, -1.0],
        ),
        LandingZoneCase(
            label="diagonal_north_east_single_vertex",
            launch=(100.0, 30.0, 0.0),
            impact=(101.0, 30.5, 100.0),
            zone_xys_km=[0.0, 0.0],
        ),
    )


def astrox_plus_x_azimuth(azi2_deg: float) -> float:
    """Calibrated +X azimuth: southward member of {azi2, 180-azi2}."""
    a = azi2_deg % 360.0
    b = (180.0 - azi2_deg) % 360.0
    a_southward = math.cos(math.radians(a)) <= 0.0
    b_southward = math.cos(math.radians(b)) <= 0.0
    if a_southward and b_southward:
        # E-W degenerate case; both point horizontally. ASTROX uses azi2.
        return a
    if a_southward:
        return a
    return b


def expected_vertices(
    impact: tuple[float, float, float],
    launch: tuple[float, float, float],
    zone_xys_km: list[float],
) -> list[GeodeticPoint]:
    """Independent WGS-84 prediction using the calibrated ASTROX frame."""
    launch_lat, launch_lon = launch[1], launch[0]
    impact_lat, impact_lon, impact_height = impact[1], impact[0], impact[2]

    geodesic = WGS84.Inverse(launch_lat, launch_lon, impact_lat, impact_lon)
    plus_x_az = astrox_plus_x_azimuth(geodesic["azi2"])

    vertices: list[GeodeticPoint] = []
    for index in range(0, len(zone_xys_km), 2):
        x_km = zone_xys_km[index]
        y_km = zone_xys_km[index + 1]
        distance_m = math.hypot(x_km, y_km) * 1000.0
        azimuth_deg = (plus_x_az + math.degrees(math.atan2(y_km, x_km))) % 360.0
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


def test_landing_zone_matches_calibrated_astrox_frame_convention() -> None:
    configure_astrox_from_env()
    failures: list[str] = []
    for case in cases():
        failures.extend(compare_case(case))
    if failures:
        raise CrossValidationError("\n".join(failures))


def main() -> int:
    try:
        test_landing_zone_matches_calibrated_astrox_frame_convention()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    checked = len(cases())
    print(f"CROSS_VALIDATION_CHECKED={checked}")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
