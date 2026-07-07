"""Shared Sun/Moon exclusion-angle oracle for access and coverage validation.

Coverage:
  Branches:
    - fixed-site SunExclusionAngle predicate intervals: verified by importing runners
    - fixed-site MoonExclusionAngle predicate intervals: verified by importing runners
    - SGP4-observer SunExclusionAngle predicate intervals with Earth occultation: verified by importing runners
    - SGP4-observer MoonExclusionAngle predicate intervals with Earth occultation: verified by importing runners
    - zero-altitude grid-point topocentric-horizon visibility mode: verified by importing coverage runners
  Fields:
    - interval start/stop times after combining line-of-sight visibility and exclusion predicates: verified by importing runners
  Parameters:
    - MinimumValue: verified by importing runners at permissive and restrictive values
  Comparison:
    - External: Skyfield SGP4, DE421 Sun/Moon ephemerides, apparent topocentric body altitude gate, astrometric topocentric/satellite-observer body-separation angle, satellite body Earth-occultation, WGS84 segment-obstruction visibility for elevated fixed sites, and topocentric-horizon visibility for zero-altitude coverage grid points
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
from skyfield.api import wgs84

from tests.validation._support import load_skyfield_ephemeris, skyfield_loader_from_env
from tests.validation.cross_validation.access._constraints import predicate_intervals
from tests.validation.cross_validation.access._geometry import (
    Interval,
    intersect_intervals,
    parse_time,
    segment_intersects_wgs84,
    sgp4_site_visibility_intervals,
    skyfield_satellite,
    skyfield_site,
    time_at_offset,
    visibility_intervals,
)

EXCLUSION_INTERVAL_ABS_S = 0.35


@dataclass(frozen=True, kw_only=True)
class ExclusionEphemeris:
    timescale: object
    eph: object


@dataclass(frozen=True, kw_only=True)
class SiteExclusionOracle:
    start: str
    minimum_deg: float
    timescale: object
    observer_site: object
    observer_barycentric: object
    satellite: object
    body: object

    def satisfied(self, offset_s: float) -> bool:
        instant = self.timescale.from_datetime(
            parse_time(self.start) + timedelta(seconds=offset_s)
        )
        apparent = self.observer_barycentric.at(instant).observe(self.body).apparent()
        altitude, _, _ = apparent.altaz()
        if altitude.degrees <= 0.0:
            return True

        line_of_sight_km = (
            self.satellite.at(instant).position.km
            - self.observer_site.at(instant).position.km
        )
        # Calibration note: ASTROX fixed-site exclusion boundaries match the
        # astrometric topocentric body vector after applying the apparent
        # horizon gate above. Apparent body direction or geocentric body vectors
        # produced stable boundary mismatches during bounded calibration.
        body_astrometric_km = (
            self.observer_barycentric.at(instant).observe(self.body).position.km
        )
        return (
            vector_angle_deg(line_of_sight_km, body_astrometric_km)
            >= self.minimum_deg
        )


@dataclass(frozen=True, kw_only=True)
class SatelliteExclusionOracle:
    start: str
    minimum_deg: float
    timescale: object
    observer_satellite: object
    observer_barycentric: object
    target_site: object
    body: object

    def satisfied(self, offset_s: float) -> bool:
        instant = self.timescale.from_datetime(
            parse_time(self.start) + timedelta(seconds=offset_s)
        )
        satellite_state = self.observer_satellite.at(instant)
        target_state = self.target_site.at(instant)
        line_of_sight_km = target_state.position.km - satellite_state.position.km
        body_astrometric_km = (
            self.observer_barycentric.at(instant).observe(self.body).position.km
        )
        # Calibration note: ASTROX treats Sun/Moon exclusion as satisfied while
        # Earth occults the body from the satellite. Once the body center is
        # visible, ASTROX matches the astrometric satellite-to-body separation.
        if body_is_earth_occulted(
            satellite_state=satellite_state,
            body_astrometric_km=body_astrometric_km,
            instant=instant,
        ):
            return True
        return (
            vector_angle_deg(line_of_sight_km, body_astrometric_km)
            >= self.minimum_deg
        )


def load_exclusion_ephemeris() -> ExclusionEphemeris:
    loader = skyfield_loader_from_env()
    return ExclusionEphemeris(
        timescale=loader.timescale(builtin=True),
        eph=load_skyfield_ephemeris(loader, "de421.bsp"),
    )


def expected_site_exclusion_intervals(
    *,
    body_name: str,
    minimum_deg: float,
    start: str,
    stop: str,
    tle_lines: tuple[str, str],
    satellite_name: str,
    latitude_deg: float,
    longitude_deg: float,
    height_m: float,
    visibility_mode: str = "wgs84_obstruction",
    predicate_sample_step_s: float = 15.0,
    predicate_bracket_abs_s: float = 0.005,
    ephemeris: ExclusionEphemeris | None = None,
) -> list[Interval]:
    context = ephemeris or load_exclusion_ephemeris()
    observer_site = wgs84.latlon(
        latitude_degrees=latitude_deg,
        longitude_degrees=longitude_deg,
        elevation_m=height_m,
    )
    satellite = skyfield_satellite(tle_lines, satellite_name)
    if visibility_mode == "wgs84_obstruction":
        access_intervals = sgp4_site_visibility_intervals(
            start=start,
            stop=stop,
            satellite=satellite,
            site_position=observer_site,
        )
    elif visibility_mode == "topocentric_elevation":
        access_intervals = sgp4_site_elevation_intervals(
            start=start,
            stop=stop,
            satellite=satellite,
            site_position=observer_site,
        )
    else:
        raise ValueError(f"unknown visibility_mode: {visibility_mode}")
    oracle = SiteExclusionOracle(
        start=start,
        minimum_deg=minimum_deg,
        timescale=context.timescale,
        observer_site=observer_site,
        observer_barycentric=context.eph["earth"] + observer_site,
        satellite=satellite,
        body=context.eph[body_name],
    )
    exclusion_intervals = predicate_intervals(
        start=start,
        stop=stop,
        predicate=oracle.satisfied,
        sample_step_s=predicate_sample_step_s,
        bracket_abs_s=predicate_bracket_abs_s,
    )
    return intersect_intervals(access_intervals, exclusion_intervals)


def expected_satellite_exclusion_intervals(
    *,
    body_name: str,
    minimum_deg: float,
    start: str,
    stop: str,
    tle_lines: tuple[str, str],
    satellite_name: str,
    target_latitude_deg: float,
    target_longitude_deg: float,
    target_height_m: float,
    predicate_sample_step_s: float = 15.0,
    predicate_bracket_abs_s: float = 0.005,
    ephemeris: ExclusionEphemeris | None = None,
) -> list[Interval]:
    context = ephemeris or load_exclusion_ephemeris()
    satellite = skyfield_satellite(tle_lines, satellite_name)
    target_site = skyfield_site(
        target_latitude_deg,
        target_longitude_deg,
        target_height_m,
    )
    access_intervals = sgp4_site_visibility_intervals(
        start=start,
        stop=stop,
        satellite=satellite,
        site_position=target_site,
    )
    oracle = SatelliteExclusionOracle(
        start=start,
        minimum_deg=minimum_deg,
        timescale=context.timescale,
        observer_satellite=satellite,
        observer_barycentric=context.eph["earth"] + satellite,
        target_site=target_site,
        body=context.eph[body_name],
    )
    exclusion_intervals = predicate_intervals(
        start=start,
        stop=stop,
        predicate=oracle.satisfied,
        sample_step_s=predicate_sample_step_s,
        bracket_abs_s=predicate_bracket_abs_s,
    )
    return intersect_intervals(access_intervals, exclusion_intervals)


def sgp4_site_elevation_intervals(
    *,
    start: str,
    stop: str,
    satellite: object,
    site_position: object,
) -> list[Interval]:
    """Return intervals where the SGP4 asset is above the site's local horizon.

    Coverage grid points are zero-altitude surface samples. Their live
    line-of-sight intervals match Skyfield's topocentric altitude crossing,
    while the elevated fixed-site access fixture is calibrated with WGS84
    segment-obstruction visibility.
    """

    def visible(offset_s: float) -> bool:
        altitude, _, _ = (
            (satellite - site_position)
            .at(time_at_offset(start, offset_s))
            .altaz()
        )
        return altitude.degrees >= 0.0

    return visibility_intervals(start=start, stop=stop, visible=visible)


def body_is_earth_occulted(
    *,
    satellite_state: object,
    body_astrometric_km: object,
    instant: object,
) -> bool:
    from skyfield.framelib import itrs

    satellite_ecef_m = np.array(satellite_state.frame_xyz(itrs).m)
    body_endpoint_gcrs_m = (
        satellite_state.position.km + np.array(body_astrometric_km, dtype=float)
    ) * 1000.0
    body_endpoint_ecef_m = np.array(itrs.rotation_at(instant) @ body_endpoint_gcrs_m)
    return segment_intersects_wgs84(satellite_ecef_m, body_endpoint_ecef_m)


def vector_angle_deg(left: object, right: object) -> float:
    left_unit = unit_vector(left)
    right_unit = unit_vector(right)
    cosine = float(np.clip(np.dot(left_unit, right_unit), -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def unit_vector(value: object) -> np.ndarray:
    vector = np.array(value, dtype=float)
    return vector / np.linalg.norm(vector)
