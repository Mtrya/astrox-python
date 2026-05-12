"""Astrogator mission control sequence functions."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import (
    AgVAMCSSegment,
    EntityPath,
    IAgVAEngine,
    Propagator,
)

__all__ = ["run_mcs"]


def run_mcs(
    central_body: str,
    main_sequence: list[AgVAMCSSegment],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    gravitational_parameter: Optional[float] = None,
    entities: Optional[list[EntityPath]] = None,
    propagators: Optional[list[Propagator]] = None,
    engine_models: Optional[list[IAgVAEngine]] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Run Mission Control Sequence (MCS) for trajectory design.

    Endpoint: POST /Astrogator/RunMCS

    Args:
        central_body: Central body name (e.g., Earth, Moon, Mars, Sun)
        main_sequence: Flight segment mission sequence array
        name: Object name
        description: Object description
        gravitational_parameter: Central body gravitational constant (m³/s²)
        entities: Other objects collection
        propagators: All integrators
        engine_models: All engine models
        session: Optional HTTP session (uses default if not provided)

    Returns:
        MCS execution results
    """
    sess = session or get_session()

    payload: dict = {
        "CentralBody": central_body,
        "MainSequence": [
            seg.model_dump(by_alias=True, exclude_none=True)
            if isinstance(seg, BaseModel)
            else seg
            for seg in main_sequence
        ],
    }

    if name is not None:
        payload["Name"] = name
    if description is not None:
        payload["Description"] = description
    if gravitational_parameter is not None:
        payload["GravitationalParameter"] = gravitational_parameter
    if entities is not None:
        payload["Entities"] = [
            ent.model_dump(by_alias=True, exclude_none=True)
            if isinstance(ent, BaseModel)
            else ent
            for ent in entities
        ]
    if propagators is not None:
        payload["Propagators"] = [
            prop.model_dump(by_alias=True, exclude_none=True)
            if isinstance(prop, BaseModel)
            else prop
            for prop in propagators
        ]
    if engine_models is not None:
        payload["EngineModels"] = [
            eng.model_dump(by_alias=True, exclude_none=True)
            if isinstance(eng, BaseModel)
            else eng
            for eng in engine_models
        ]

    return sess.post(endpoint="/Astrogator/RunMCS", data=payload)
