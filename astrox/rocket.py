"""Rocket trajectory optimization and guidance functions."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import (
    IVAMCSProfile,
    RocketGuid,
    RocketSegmentInfo,
    VAMCSProfileDEOptimizer,
)

__all__ = [
    "optimize_trajectory",
    "optimize_landing",
    "compute_guided_trajectory",
]


def optimize_trajectory(
    gw: float,
    t1: float,
    alpham: float,
    natmos: int,
    rocket_segments: list[RocketSegmentInfo],
    sma0: float,
    ecc0: float,
    inc0: float,
    omg0: float,
    *,
    name: Optional[str] = None,
    text: Optional[str] = None,
    rocket_type: Optional[str] = None,
    use_mcs_profile: Optional[bool] = None,
    name_fa_she_dian: Optional[str] = None,
    fa_she_dian_lla: Optional[list[float]] = None,
    a0: Optional[float] = None,
    aero_params_file_name: Optional[str] = None,
    profile_optim: Optional[VAMCSProfileDEOptimizer] = None,
    mcs_profiles: Optional[list[IVAMCSProfile]] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Optimize rocket ascent trajectory using flight segment model.

    Endpoint: POST /Rocket/RocketSegmentFA

    Args:
        gw: Payload mass (kg)
        t1: Turn start time (s)
        alpham: Maximum angle of attack during atmospheric flight (deg)
        natmos: Number of atmospheric flight segments
        rocket_segments: Rocket flight segment sequence
        sma0: Target orbit semi-major axis (m)
        ecc0: Target orbit eccentricity
        inc0: Target orbit inclination (deg)
        omg0: Target orbit argument of perigee (deg)
        name: Mission name
        text: Mission description
        rocket_type: Rocket type (CZ3A, CZ3B, CZ3C, CZ4B, CZ4C, CZ2C, CZ2D, CZ7A)
        use_mcs_profile: Whether to use MCS file for trajectory
        name_fa_she_dian: Launch site name
        fa_she_dian_lla: Launch site coordinates [lon(deg), lat(deg), alt(m)]
        a0: Launch azimuth (deg)
        aero_params_file_name: Aerodynamic data table filename
        profile_optim: VAMCSProfileDEOptimizer configuration
        mcs_profiles: MCS file array
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Optimized trajectory results
    """
    sess = session or get_session()

    payload: dict = {
        "GW": gw,
        "T1": t1,
        "Alpham": alpham,
        "Natmos": natmos,
        "RocketSegments": [
            seg.model_dump(by_alias=True, exclude_none=True)
            if isinstance(seg, BaseModel)
            else seg
            for seg in rocket_segments
        ],
        "SMA0": sma0,
        "Ecc0": ecc0,
        "Inc0": inc0,
        "Omg0": omg0,
    }

    if name is not None:
        payload["Name"] = name
    if text is not None:
        payload["Text"] = text
    if rocket_type is not None:
        payload["RocketType"] = rocket_type
    if use_mcs_profile is not None:
        payload["UseMCSProfile"] = use_mcs_profile
    if name_fa_she_dian is not None:
        payload["NameFaSheDian"] = name_fa_she_dian
    if fa_she_dian_lla is not None:
        payload["FaSheDianLLA"] = fa_she_dian_lla
    if a0 is not None:
        payload["A0"] = a0
    if aero_params_file_name is not None:
        payload["AeroParamsFileName"] = aero_params_file_name
    if profile_optim is not None:
        payload["ProfileOptim"] = profile_optim.model_dump(
            by_alias=True, exclude_none=True
        )
    if mcs_profiles is not None:
        payload["MCSProfiles"] = [
            prof.model_dump(by_alias=True, exclude_none=True)
            if isinstance(prof, BaseModel)
            else prof
            for prof in mcs_profiles
        ]

    return sess.post(endpoint="/Rocket/RocketSegmentFA", data=payload)


def optimize_landing(
    *,
    name: Optional[str] = None,
    text: Optional[str] = None,
    is_optimize: Optional[bool] = None,
    a0: Optional[float] = None,
    fa_she_dian_lla: Optional[list[float]] = None,
    t0: Optional[float] = None,
    x0: Optional[list[float]] = None,
    phicx0: Optional[float] = None,
    psicx0: Optional[float] = None,
    sm: Optional[float] = None,
    dt1: Optional[float] = None,
    phicx20: Optional[float] = None,
    psicx20: Optional[float] = None,
    dt2: Optional[float] = None,
    force2: Optional[float] = None,
    ips2: Optional[float] = None,
    height4: Optional[float] = None,
    force4: Optional[float] = None,
    ips4: Optional[float] = None,
    sa4: Optional[float] = None,
    cons_h: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Optimize rocket vertical landing trajectory.

    Endpoint: POST /Rocket/RocketLanding

    Uses 4-segment model with aerodynamics for powered descent landing.

    Args:
        name: Mission name
        text: Mission description
        is_optimize: Whether to optimize trajectory
        a0: Launch azimuth (deg)
        fa_she_dian_lla: Launch site coordinates [lon(deg), lat(deg), alt(m)]
        t0: Initial segment time (s from launch)
        x0: Initial segment state (launch inertial frame: position(m), velocity(m/s), mass(kg))
        phicx0: Initial segment pitch angle (deg)
        psicx0: Initial segment yaw angle (deg)
        sm: Aerodynamic area (m²)
        dt1: Attitude adjustment segment duration (s)
        phicx20: Turn segment initial pitch angle (deg)
        psicx20: Turn segment initial yaw angle (deg)
        dt2: Turn segment working duration (s)
        force2: Turn segment vacuum thrust (N)
        ips2: Turn segment vacuum specific impulse (m/s)
        height4: Landing segment initial height (km)
        force4: Landing segment sea-level thrust (N)
        ips4: Landing segment sea-level specific impulse (m/s)
        sa4: Landing segment engine nozzle area (m²)
        cons_h: Landing point height (km)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Optimized landing trajectory
    """
    sess = session or get_session()

    payload: dict = {}

    if name is not None:
        payload["Name"] = name
    if text is not None:
        payload["Text"] = text
    if is_optimize is not None:
        payload["IsOptimize"] = is_optimize
    if a0 is not None:
        payload["A0"] = a0
    if fa_she_dian_lla is not None:
        payload["FaSheDianLLA"] = fa_she_dian_lla
    if t0 is not None:
        payload["T0"] = t0
    if x0 is not None:
        payload["X0"] = x0
    if phicx0 is not None:
        payload["Phicx0"] = phicx0
    if psicx0 is not None:
        payload["Psicx0"] = psicx0
    if sm is not None:
        payload["SM"] = sm
    if dt1 is not None:
        payload["DT1"] = dt1
    if phicx20 is not None:
        payload["Phicx20"] = phicx20
    if psicx20 is not None:
        payload["Psicx20"] = psicx20
    if dt2 is not None:
        payload["DT2"] = dt2
    if force2 is not None:
        payload["Force2"] = force2
    if ips2 is not None:
        payload["Ips2"] = ips2
    if height4 is not None:
        payload["Height4"] = height4
    if force4 is not None:
        payload["Force4"] = force4
    if ips4 is not None:
        payload["Ips4"] = ips4
    if sa4 is not None:
        payload["SA4"] = sa4
    if cons_h is not None:
        payload["ConsH"] = cons_h

    return sess.post(endpoint="/Rocket/RocketLanding", data=payload)


def compute_guided_trajectory(
    guidance_config: RocketGuid,
    *,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate rocket trajectory using guidance algorithms.

    Endpoint: POST /Rocket/RocketGuid

    Args:
        guidance_config: Guidance algorithm configuration (RocketGuid discriminated union)
                        Must include $type field: "CZ3BC", "CZ2CD", "CZ4BC", "KZ1A", or "CZ7A"
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Guided trajectory calculation results
    """
    sess = session or get_session()

    payload = (
        guidance_config.model_dump(by_alias=True, exclude_none=True)
        if isinstance(guidance_config, BaseModel)
        else guidance_config
    )

    return sess.post(endpoint="/Rocket/RocketGuid", data=payload)
