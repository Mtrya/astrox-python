"""Conjunction analysis and collision avoidance functions (CAT2)."""

from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import EntityPositionCzml, TleInfo

__all__ = [
    "compute_close_approach",
    "debris_breakup",
    "get_tle",
    "compute_lifetime",
]


def compute_close_approach(
    start_utcg: str,
    stop_utcg: str,
    sat1: Union[TleInfo, EntityPositionCzml],
    *,
    version: str = "v4",
    tol_max_distance: Optional[float] = None,
    tol_cross_dt: Optional[float] = None,
    tol_theta: Optional[float] = None,
    tol_dh: Optional[float] = None,
    targets: Optional[list[TleInfo]] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Compute space debris close approach / collision analysis.

    Endpoints (merged):
    - POST /CAT/CA_ComputeV3 (version="v3", sat1 is TleInfo)
    - POST /CAT/CA_ComputeV4 (version="v4", sat1 is EntityPositionCzml for rockets)

    Args:
        start_utcg: Analysis start time (UTC) format: "yyyy-MM-ddTHH:mm:ss.fffZ"
        stop_utcg: Analysis end time (UTC)
        sat1: Primary satellite (TleInfo for v3, EntityPositionCzml for v4)
        version: API version ("v3" or "v4", default "v4")
        tol_max_distance: Maximum distance for close approach detection (km)
        tol_cross_dt: Time error tolerance for cross-plane detection (s)
        tol_theta: Orbital plane angle threshold (deg)
        tol_dh: Apogee/perigee altitude filtering error (km)
        targets: Target objects; if None, reads from database
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Collision analysis results with CA_Results array
    """
    sess = session or get_session()

    # Map version to endpoint
    endpoints = {
        "v3": "/CAT/CA_ComputeV3",
        "v4": "/CAT/CA_ComputeV4",
    }
    endpoint = endpoints.get(version, "/CAT/CA_ComputeV4")

    payload: dict = {
        "Start_UTCG": start_utcg,
        "Stop_UTCG": stop_utcg,
        "Sat1": sat1.model_dump(by_alias=True, exclude_none=True)
        if isinstance(sat1, BaseModel)
        else sat1,
    }

    if tol_max_distance is not None:
        payload["Tol_MaxDistance"] = tol_max_distance
    if tol_cross_dt is not None:
        payload["Tol_CrossDt"] = tol_cross_dt
    if tol_theta is not None:
        payload["Tol_Theta"] = tol_theta
    if tol_dh is not None:
        payload["Tol_dH"] = tol_dh
    if targets is not None:
        payload["Targets"] = [
            t.model_dump(by_alias=True, exclude_none=True)
            if isinstance(t, BaseModel)
            else t
            for t in targets
        ]

    return sess.post(endpoint=endpoint, data=payload)


def debris_breakup(
    mother_satellite: TleInfo,
    epoch: str,
    *,
    method: str = "simple",
    ssc_pre: Optional[str] = None,
    a2m: Optional[float] = None,
    count: Optional[int] = None,
    delta_v: Optional[float] = None,
    min_azimuth: Optional[float] = None,
    max_azimuth: Optional[float] = None,
    min_elevation: Optional[float] = None,
    max_elevation: Optional[float] = None,
    az_el_vel: Optional[list[float]] = None,
    mass_total: Optional[float] = None,
    min_lc: Optional[float] = None,
    compute_life_of_time: Optional[bool] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Generate space debris from satellite breakup.

    Endpoints (merged):
    - POST /CAT/DebrisBreakupSimple (method="simple")
    - POST /CAT/DebrisBreakup (method="default")
    - POST /CAT/DebrisBreakupNASA (method="nasa")

    Args:
        mother_satellite: Parent satellite TLE
        epoch: Debris generation time (UTC) format: "yyyy-MM-ddTHH:mm:ss.fffZ"
        method: Breakup model ("simple", "default", "nasa")
        ssc_pre: Debris SSC prefix (2 chars)
        a2m: Area-to-mass ratio (m²/kg)
        count: Total number of debris particles (simple method only, < 1000)
        delta_v: Relative velocity magnitude (m/s, simple method)
        min_azimuth: Minimum azimuth angle (deg, simple method)
        max_azimuth: Maximum azimuth angle (deg, simple method)
        min_elevation: Minimum elevation angle (deg, simple method)
        max_elevation: Maximum elevation angle (deg, simple method)
        az_el_vel: Azimuth, elevation, velocity parameters (default/nasa methods)
        mass_total: Total mass of parent satellite (nasa method)
        min_lc: Minimum characteristic length (nasa method)
        compute_life_of_time: Whether to compute debris orbital lifetime
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Debris TLEs, breakup parameters, lifetimes, altitudes, periods
    """
    sess = session or get_session()

    # Map method to endpoint
    endpoints = {
        "simple": "/CAT/DebrisBreakupSimple",
        "default": "/CAT/DebrisBreakup",
        "nasa": "/CAT/DebrisBreakupNASA",
    }
    endpoint = endpoints.get(method, "/CAT/DebrisBreakupSimple")

    payload: dict = {
        "MotherSate": mother_satellite.model_dump(
            by_alias=True, exclude_none=True
        )
        if isinstance(mother_satellite, BaseModel)
        else mother_satellite,
        "Epoch": epoch,
    }

    if ssc_pre is not None:
        payload["SSC_Pre"] = ssc_pre
    if a2m is not None:
        payload["A2M"] = a2m
    if count is not None:
        payload["Count"] = count
    if delta_v is not None:
        payload["DeltaV"] = delta_v
    if min_azimuth is not None:
        payload["MinAzimuth"] = min_azimuth
    if max_azimuth is not None:
        payload["MaxAzimuth"] = max_azimuth
    if min_elevation is not None:
        payload["MinElevation"] = min_elevation
    if max_elevation is not None:
        payload["MaxElevation"] = max_elevation
    if az_el_vel is not None:
        payload["AzElVel"] = az_el_vel
    if mass_total is not None:
        payload["MassTotal"] = mass_total
    if min_lc is not None:
        payload["MinLc"] = min_lc
    if compute_life_of_time is not None:
        payload["ComputeLifeOfTime"] = compute_life_of_time

    return sess.post(endpoint=endpoint, data=payload)


def get_tle(
    name: str,
    ssc: str,
    epoch: str,
    b_star: float,
    sma: float,
    ecc: float,
    inc: float,
    w: float,
    raan: float,
    ta: float,
    *,
    is_mean_elements: Optional[bool] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Generate two-line element set from orbital elements.

    Endpoint: POST /CAT/GetTLE

    Args:
        name: Space target name
        ssc: NORAD SSC (5-digit code)
        epoch: Orbital epoch (UTCG) format: "yyyy-MM-ddTHH:mm:ss.fffZ"
        b_star: Atmospheric drag coefficient
        sma: Semi-major axis (km)
        ecc: Eccentricity
        inc: Orbital inclination (deg, TEME)
        w: Argument of perigee (deg, TEME)
        raan: Right ascension of ascending node (deg, TEME)
        ta: True anomaly (deg, TEME)
        is_mean_elements: Whether elements are mean (True) or osculating (False)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Generated TLE information
    """
    sess = session or get_session()

    payload: dict = {
        "Name": name,
        "SSC": ssc,
        "Epoch": epoch,
        "B_star": b_star,
        "SMA": sma,
        "Ecc": ecc,
        "Inc": inc,
        "W": w,
        "RAAN": raan,
        "TA": ta,
    }

    if is_mean_elements is not None:
        payload["IsMeanElements"] = is_mean_elements

    return sess.post(endpoint="/CAT/GetTLE", data=payload)


def compute_lifetime(
    epoch: str,
    tles: TleInfo,
    sm: float,
    mass: float,
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate orbital lifetime from TLE.

    Endpoint: POST /CAT/LifeTimeTLE

    Args:
        epoch: Analysis epoch (UTCG)
        tles: Two-line element set
        sm: Surface area or related parameter
        mass: Satellite mass
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Calculated orbital lifetime
    """
    sess = session or get_session()

    payload = {
        "Epoch": epoch,
        "TLEs": tles.model_dump(by_alias=True, exclude_none=True)
        if isinstance(tles, BaseModel)
        else tles,
        "SM": sm,
        "Mass": mass,
    }

    return sess.post(endpoint="/CAT/LifeTimeTLE", data=payload)
