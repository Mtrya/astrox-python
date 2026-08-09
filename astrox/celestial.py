"""Read-like celestial endpoint functions."""

from __future__ import annotations

from numbers import Real
from typing import Any

from astrox._http import raw

__all__ = [
    "cb_axes_rotation",
    "ephemeris",
    "mpc_ephemeris",
]


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _string(value: str, *, parameter: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{parameter} must be a string")
    return value


def _optional_string(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    return _string(value, parameter=parameter)


def _optional_number(value: float | None, *, parameter: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{parameter} must be a number")
    return float(value)


def _optional_integer(value: int | None, *, parameter: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{parameter} must be an integer")
    return value


def ephemeris(
    *,
    target_name: str,
    start: str,
    stop: str,
    observer_name: str | None = None,
    observer_frame: str | None = None,
    step_s: float | None = None,
) -> dict[str, Any]:
    """Return ASTROX ephemeris output for a target and explicit time window."""
    payload: dict[str, Any] = {
        "TargetName": _string(target_name, parameter="target_name"),
        "Start": _string(start, parameter="start"),
        "Stop": _string(stop, parameter="stop"),
    }
    _include_if_supplied(
        payload,
        "ObserverName",
        _optional_string(observer_name, parameter="observer_name"),
    )
    _include_if_supplied(
        payload,
        "ObserverFrame",
        _optional_string(observer_frame, parameter="observer_frame"),
    )
    _include_if_supplied(
        payload,
        "Step",
        _optional_number(step_s, parameter="step_s"),
    )
    return raw.post("/celestial/ephemeris", json=payload)


def cb_axes_rotation(
    *,
    from_central_body: str,
    to_central_body: str,
    epoch: str,
    from_frame: str | None = None,
    to_frame: str | None = None,
    order: int | None = None,
) -> dict[str, Any]:
    """Return ASTROX axes-rotation output between two central-body frames."""
    payload: dict[str, Any] = {
        "FromCbName": _string(
            from_central_body,
            parameter="from_central_body",
        ),
        "ToCbName": _string(to_central_body, parameter="to_central_body"),
        "Epoch": _string(epoch, parameter="epoch"),
    }
    _include_if_supplied(
        payload,
        "FromCbFrame",
        _optional_string(from_frame, parameter="from_frame"),
    )
    _include_if_supplied(
        payload,
        "ToCbFrame",
        _optional_string(to_frame, parameter="to_frame"),
    )
    _include_if_supplied(
        payload,
        "Order",
        _optional_integer(order, parameter="order"),
    )
    return raw.post("/celestial/CbAxesRotation", json=payload)


def mpc_ephemeris(
    *,
    target_name: str,
    observer_frame: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> dict[str, Any]:
    """Return ASTROX minor-planet ephemeris output from its MPC-backed route."""
    payload: dict[str, Any] = {
        "TargetName": _string(target_name, parameter="target_name"),
    }
    _include_if_supplied(
        payload,
        "ObserverFrame",
        _optional_string(observer_frame, parameter="observer_frame"),
    )
    _include_if_supplied(
        payload,
        "Start",
        _optional_string(start, parameter="start"),
    )
    _include_if_supplied(
        payload,
        "Stop",
        _optional_string(stop, parameter="stop"),
    )
    return raw.post("/celestial/mpc", json=payload)
