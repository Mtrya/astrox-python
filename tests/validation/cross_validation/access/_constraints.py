"""Independent constraint predicate geometry for access validation.

Coverage:
  Branches:
    - ground-origin elevation/range/AzElMask predicate intervals: partial
    - satellite-origin elevation/range/AzElMask predicate intervals: partial
    - combined predicate intersection: partial
    - light-time-shifted range predicate: partial
  Fields:
    - predicate interval start/stop times: partial
  Parameters:
    - elevation minimum/maximum thresholds: partial
    - range minimum/maximum thresholds: partial
    - AzElMask sample azimuth/elevation in radians: partial
  Comparison:
    - External: Skyfield SGP4 topocentric geometry
    - Constants: TLE_A, WGS84 ellipsoid via Skyfield
    - Tolerances: shared INTERVAL_ABS_S for boundary precision; dense sampling at 5-10 s
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from skyfield.api import wgs84
from skyfield.framelib import itrs

from tests.validation.cross_validation.access._cases import (
    SITE_HEIGHT_M,
    SITE_LATITUDE_DEG,
    SITE_LONGITUDE_DEG,
    TLE_A,
)
from tests.validation.cross_validation.access._geometry import (
    Interval,
    bisect_transition,
    skyfield_satellite,
    skyfield_site,
    time_at_offset,
    visibility_intervals,
)

DENSE_SAMPLE_STEP_S = 15.0
PREDICATE_BRACKET_ABS_S = 0.005


@dataclass(frozen=True, kw_only=True)
class AerState:
    """Topocentric azimuth/elevation/range state for constraint evaluation."""

    azimuth_deg: float
    elevation_deg: float
    range_m: float


def ground_origin_aer_at(offset_s: float, *, start: str) -> AerState:
    """Skyfield topocentric AER from the fixed site to the ISS TLE_A."""
    satellite = skyfield_satellite(TLE_A, "ISS")
    observer = skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M)
    instant = time_at_offset(start, offset_s)
    altitude, azimuth, distance = (satellite - observer).at(instant).altaz()
    return AerState(
        azimuth_deg=azimuth.degrees,
        elevation_deg=altitude.degrees,
        range_m=distance.m,
    )


def satellite_origin_aer_at(offset_s: float, *, start: str) -> AerState:
    """Topocentric AER from the satellite subpoint to the fixed site.

    This mirrors the geodetic local-frame convention used for ASTROX
    satellite-origin AER rows, not a spacecraft body frame.
    """
    satellite = skyfield_satellite(TLE_A, "ISS")
    target = skyfield_site(SITE_LATITUDE_DEG, SITE_LONGITUDE_DEG, SITE_HEIGHT_M)
    instant = time_at_offset(start, offset_s)
    satellite_state = satellite.at(instant)
    satellite_subpoint = wgs84.geographic_position_of(satellite_state)
    satellite_ecef = np.array(satellite_state.frame_xyz(itrs).m)
    target_ecef = np.array(target.at(instant).frame_xyz(itrs).m)
    azimuth, elevation, range_m = _site_topocentric_from_ecef(
        satellite_ecef,
        target_ecef,
        latitude_deg=satellite_subpoint.latitude.degrees,
        longitude_deg=satellite_subpoint.longitude.degrees,
    )
    return AerState(
        azimuth_deg=azimuth,
        elevation_deg=elevation,
        range_m=range_m,
    )


def _site_topocentric_from_ecef(
    observer_ecef_m: np.ndarray,
    target_ecef_m: np.ndarray,
    *,
    latitude_deg: float,
    longitude_deg: float,
) -> tuple[float, float, float]:
    latitude_rad = math.radians(latitude_deg)
    longitude_rad = math.radians(longitude_deg)
    east = np.array([-math.sin(longitude_rad), math.cos(longitude_rad), 0.0])
    north = np.array(
        [
            -math.sin(latitude_rad) * math.cos(longitude_rad),
            -math.sin(latitude_rad) * math.sin(longitude_rad),
            math.cos(latitude_rad),
        ]
    )
    up = np.array(
        [
            math.cos(latitude_rad) * math.cos(longitude_rad),
            math.cos(latitude_rad) * math.sin(longitude_rad),
            math.sin(latitude_rad),
        ]
    )
    vector_m = target_ecef_m - observer_ecef_m
    east_m = float(np.dot(vector_m, east))
    north_m = float(np.dot(vector_m, north))
    up_m = float(np.dot(vector_m, up))
    range_m = float(np.linalg.norm(vector_m))
    return (
        math.degrees(math.atan2(east_m, north_m)),
        math.degrees(math.asin(up_m / range_m)),
        range_m,
    )


def predicate_intervals(
    *,
    start: str,
    stop: str,
    predicate: Callable[[float], bool],
    sample_step_s: float = DENSE_SAMPLE_STEP_S,
    bracket_abs_s: float = PREDICATE_BRACKET_ABS_S,
) -> list[Interval]:
    """Return intervals where ``predicate(offset_s)`` is true.

    Uses dense sampling followed by bisection on each predicate crossing.
    """

    def visible(offset_s: float) -> bool:
        return predicate(offset_s)

    return visibility_intervals(
        start=start,
        stop=stop,
        visible=visible,
        sample_step_s=sample_step_s,
        bracket_abs_s=bracket_abs_s,
    )


def elevation_predicate(
    offset_s: float,
    *,
    start: str,
    origin: str,
    minimum_deg: float | None,
    maximum_deg: float | None,
) -> bool:
    """Evaluate an elevation-angle constraint predicate at ``offset_s``.

    ``origin`` is ``"ground"`` for the fixed-site topocentric frame or
    ``"satellite"`` for the satellite-subpoint geodetic local frame.
    """
    aer = _aer_at(offset_s, start=start, origin=origin)
    if minimum_deg is not None and aer.elevation_deg < minimum_deg:
        return False
    if maximum_deg is not None and aer.elevation_deg > maximum_deg:
        return False
    return True


def range_predicate(
    offset_s: float,
    *,
    start: str,
    origin: str,
    minimum_km: float | None,
    maximum_km: float | None,
) -> bool:
    """Evaluate a range constraint predicate at ``offset_s``.

    ``origin`` is ``"ground"`` or ``"satellite"`` (see ``elevation_predicate``).
    """
    aer = _aer_at(offset_s, start=start, origin=origin)
    range_km = aer.range_m / 1000.0
    if minimum_km is not None and range_km < minimum_km:
        return False
    if maximum_km is not None and range_km > maximum_km:
        return False
    return True


def _aer_at(offset_s: float, *, start: str, origin: str) -> AerState:
    if origin == "ground":
        return ground_origin_aer_at(offset_s, start=start)
    if origin == "satellite":
        return satellite_origin_aer_at(offset_s, start=start)
    raise ValueError(f"unknown origin: {origin}")


def az_el_mask_predicate(
    offset_s: float,
    *,
    start: str,
    origin: str,
    az_el_mask_rad: tuple[float, ...],
    max_range_km: float | None,
) -> bool:
    """Evaluate an AzElMask constraint predicate at ``offset_s``.

    ``az_el_mask_rad`` is a flat ``(az0, el0, az1, el1, ...)`` sequence in radians.
    The mask is interpolated piecewise-linearly in azimuth using the same
    north-zero/east-positive convention as the access AER rows.  Elevation is
    considered satisfied when the line-of-sight elevation is greater than or
    equal to the interpolated mask elevation.
    """
    aer = _aer_at(offset_s, start=start, origin=origin)
    if max_range_km is not None and aer.range_m / 1000.0 > max_range_km:
        return False
    mask_elevation_deg = _interpolate_mask_elevation(aer.azimuth_deg, az_el_mask_rad)
    if mask_elevation_deg is None:
        return False
    return aer.elevation_deg >= mask_elevation_deg


def _interpolate_mask_elevation(
    azimuth_deg: float,
    az_el_mask_rad: tuple[float, ...],
) -> float | None:
    """Return interpolated mask elevation in degrees for ``azimuth_deg``.

    Handles azimuth wraparound by unwrapping the sorted sample azimuths before
    piecewise-linear interpolation.  If the input samples do not cover the
    azimuth domain, returns ``None`` (no constraint information).
    """
    if len(az_el_mask_rad) < 4 or len(az_el_mask_rad) % 2 != 0:
        return None
    samples: list[tuple[float, float]] = []
    for index in range(0, len(az_el_mask_rad), 2):
        az_deg = math.degrees(az_el_mask_rad[index])
        el_deg = math.degrees(az_el_mask_rad[index + 1])
        samples.append((az_deg, el_deg))
    samples.sort(key=lambda item: item[0])
    azimuths = np.array([item[0] for item in samples])
    elevations = np.array([item[1] for item in samples])

    # Ensure the first/last pair spans the 0/360 boundary if needed.
    # ASTROX appears to close the mask circle by interpolating from the last
    # supplied sample to the first sample across the 0/360 boundary.
    if azimuths[-1] - azimuths[0] < 360.0 - 1.0e-6 and len(azimuths) >= 2:
        azimuths = np.append(azimuths, azimuths[0] + 360.0)
        elevations = np.append(elevations, elevations[0])

    # Normalize target azimuth into the first interval modulo 360.
    target = azimuth_deg % 360.0
    if target < azimuths[0]:
        target += 360.0
    if target > azimuths[-1]:
        # Try wrapping to the duplicated first sample.
        target -= 360.0

    if target < azimuths[0] or target > azimuths[-1]:
        return None

    for index in range(len(azimuths) - 1):
        if azimuths[index] <= target <= azimuths[index + 1]:
            fraction = (target - azimuths[index]) / (
                azimuths[index + 1] - azimuths[index]
            )
            return float(
                elevations[index]
                + fraction * (elevations[index + 1] - elevations[index])
            )
    return None
