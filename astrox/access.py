"""Access computation functions."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import EntityPath, IEntityObject, LinkConnection

__all__ = ["compute_access", "compute_chain"]


def compute_access(
    start: str,
    stop: str,
    from_object: EntityPath,
    to_object: EntityPath,
    *,
    description: Optional[str] = None,
    out_step: Optional[float] = None,
    compute_aer: Optional[bool] = None,
    use_light_time_delay: Optional[bool] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Compute access between two objects.

    Endpoint: POST /access/AccessComputeV2

    Args:
        start: Analysis start time (UTCG) format: "yyyy-MM-ddTHH:mm:ssZ"
        stop: Analysis end time (UTCG)
        from_object: Source entity path
        to_object: Target entity path
        description: Description
        out_step: Output time step (s)
        compute_aer: Whether to calculate AER parameters
        use_light_time_delay: Whether to use light time delay
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Access computation results
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "FromObjectPath": from_object.model_dump(by_alias=True, exclude_none=True)
        if isinstance(from_object, BaseModel)
        else from_object,
        "ToObjectPath": to_object.model_dump(by_alias=True, exclude_none=True)
        if isinstance(to_object, BaseModel)
        else to_object,
    }

    if description is not None:
        payload["Description"] = description
    if out_step is not None:
        payload["OutStep"] = out_step
    if compute_aer is not None:
        payload["ComputeAER"] = compute_aer
    if use_light_time_delay is not None:
        payload["UseLightTimeDelay"] = use_light_time_delay

    return sess.post(endpoint="/access/AccessComputeV2", data=payload)


def compute_chain(
    start: str,
    stop: str,
    all_objects: list[IEntityObject],
    start_object: str,
    end_object: str,
    *,
    description: Optional[str] = None,
    connections: Optional[list[LinkConnection]] = None,
    use_light_time_delay: Optional[bool] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Compute access chain through multiple objects.

    Endpoint: POST /access/ChainCompute

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        all_objects: All link objects
        start_object: Start object name (usually Transmitter)
        end_object: End object name (usually Receiver)
        description: Description
        connections: All possible links between start and end objects
        use_light_time_delay: Whether to use light time delay
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Chain computation results
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "AllObjects": [
            obj.model_dump(by_alias=True, exclude_none=True)
            if isinstance(obj, BaseModel)
            else obj
            for obj in all_objects
        ],
        "StartObject": start_object,
        "EndObject": end_object,
    }

    if description is not None:
        payload["Description"] = description
    if connections is not None:
        payload["Connections"] = [
            conn.model_dump(by_alias=True, exclude_none=True)
            if isinstance(conn, BaseModel)
            else conn
            for conn in connections
        ]
    if use_light_time_delay is not None:
        payload["UseLightTimeDelay"] = use_light_time_delay

    return sess.post(endpoint="/access/ChainCompute", data=payload)
