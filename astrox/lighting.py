"""Lighting analysis functions."""

from __future__ import annotations

from collections.abc import Sequence
from numbers import Real
from typing import Any

from astrox import entities
from astrox._http import raw

__all__ = [
    "lighting_times",
    "solar_aer",
    "solar_intensity",
]


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _number_sequence_to_list(value: Sequence[float], *, parameter: str) -> list[float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    items = list(value)
    if not all(isinstance(item, Real) and not isinstance(item, bool) for item in items):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    return items


def _string_sequence_to_list(value: Sequence[str], *, parameter: str) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{parameter} must be a sequence of strings")
    items = list(value)
    if not all(isinstance(item, str) for item in items):
        raise TypeError(f"{parameter} must be a sequence of strings")
    return items


def lighting_times(
    *,
    start: str,
    stop: str,
    position: entities.EntityPosition,
    description: str | None = None,
    az_el_mask_data: Sequence[float] | None = None,
    occultation_bodies: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Compute sunlight, penumbra, and umbra intervals for a position source."""
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "Position": entities._position_to_wire(position),
    }
    _include_if_supplied(payload, "Description", description)
    if az_el_mask_data is not None:
        payload["AzElMaskData"] = _number_sequence_to_list(
            az_el_mask_data,
            parameter="az_el_mask_data",
        )
    if occultation_bodies is not None:
        payload["OccultationBodies"] = _string_sequence_to_list(
            occultation_bodies,
            parameter="occultation_bodies",
        )

    return raw.post("/Lighting/LightingTimes", json=payload)


def solar_intensity(
    *,
    start: str,
    stop: str,
    position: entities.EntityPosition,
    description: str | None = None,
    az_el_mask_data: Sequence[float] | None = None,
    step_s: float | None = None,
    occultation_bodies: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Compute solar intensity samples for a position source."""
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "Position": entities._position_to_wire(position),
    }
    _include_if_supplied(payload, "Description", description)
    _include_if_supplied(payload, "TimeStepSec", step_s)
    if az_el_mask_data is not None:
        payload["AzElMaskData"] = _number_sequence_to_list(
            az_el_mask_data,
            parameter="az_el_mask_data",
        )
    if occultation_bodies is not None:
        payload["OccultationBodies"] = _string_sequence_to_list(
            occultation_bodies,
            parameter="occultation_bodies",
        )

    return raw.post("/Lighting/SolarIntensity", json=payload)


def solar_aer(
    *,
    start: str,
    stop: str,
    site_position: entities.SitePosition,
    text: str | None = None,
    step_s: int | None = None,
) -> dict[str, Any]:
    """Compute solar azimuth, elevation, and range samples for a site position."""
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "sitePosition": entities._site_position_to_wire(site_position),
    }
    _include_if_supplied(payload, "Text", text)
    _include_if_supplied(payload, "TimeStepSec", step_s)

    return raw.post("/Lighting/SolarAER", json=payload)
