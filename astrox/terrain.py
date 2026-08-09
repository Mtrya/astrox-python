"""Terrain-mask endpoint functions and request configuration."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Any

from astrox import components
from astrox._http import raw

__all__ = [
    "TerrainMaskConfig",
    "azimuth_elevation_mask",
    "azimuth_elevation_mask_simple",
]


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _optional_string(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{parameter} must be a string")
    return value


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


def _without_status_fields(value: Any, *, endpoint: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{endpoint} response must be an object")
    return {
        key: item
        for key, item in value.items()
        if key not in {"IsSuccess", "Message"}
    }


def _site_position_to_wire(
    value: components.SitePosition,
    *,
    parameter: str,
) -> dict[str, Any]:
    if not isinstance(value, components.SitePosition):
        raise TypeError(f"{parameter} must be an astrox.components.SitePosition value")
    return value.to_site_wire()


@dataclass(frozen=True, kw_only=True)
class TerrainMaskConfig:
    """Server terrain-source and sampling configuration."""

    text: str | None = None
    terrain_server_url: str | None = None
    flag_pole: int | None = None
    polar_dem_file_name: str | None = None
    terrain_zoom_level: int | None = None
    step_size_m: float | None = None
    max_search_range_km: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "text",
            _optional_string(self.text, parameter="text"),
        )
        object.__setattr__(
            self,
            "terrain_server_url",
            _optional_string(
                self.terrain_server_url,
                parameter="terrain_server_url",
            ),
        )
        object.__setattr__(
            self,
            "flag_pole",
            _optional_integer(self.flag_pole, parameter="flag_pole"),
        )
        object.__setattr__(
            self,
            "polar_dem_file_name",
            _optional_string(
                self.polar_dem_file_name,
                parameter="polar_dem_file_name",
            ),
        )
        object.__setattr__(
            self,
            "terrain_zoom_level",
            _optional_integer(
                self.terrain_zoom_level,
                parameter="terrain_zoom_level",
            ),
        )
        object.__setattr__(
            self,
            "step_size_m",
            _optional_number(self.step_size_m, parameter="step_size_m"),
        )
        object.__setattr__(
            self,
            "max_search_range_km",
            _optional_number(
                self.max_search_range_km,
                parameter="max_search_range_km",
            ),
        )

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX TerrainMaskConfig fragment."""
        payload: dict[str, Any] = {}
        _include_if_supplied(payload, "Text", self.text)
        _include_if_supplied(payload, "TerrainServerUrl", self.terrain_server_url)
        _include_if_supplied(payload, "FlagPole", self.flag_pole)
        _include_if_supplied(payload, "PolarDemFileName", self.polar_dem_file_name)
        _include_if_supplied(payload, "TerrainZoomLevel", self.terrain_zoom_level)
        _include_if_supplied(payload, "StepSize", self.step_size_m)
        _include_if_supplied(payload, "MaxSearchRange", self.max_search_range_km)
        return payload


def _terrain_mask_config_to_wire(
    value: TerrainMaskConfig | None,
    *,
    parameter: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, TerrainMaskConfig):
        raise TypeError(f"{parameter} must be a TerrainMaskConfig value")
    return value.to_wire()


def _mask_request(
    *,
    endpoint: str,
    site_position: components.SitePosition,
    config: TerrainMaskConfig | None,
    text: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "sitePosition": _site_position_to_wire(
            site_position,
            parameter="site_position",
        ),
    }
    _include_if_supplied(
        payload,
        "Text",
        _optional_string(text, parameter="text"),
    )
    _include_if_supplied(
        payload,
        "TerrainMaskPara",
        _terrain_mask_config_to_wire(config, parameter="config"),
    )
    return _without_status_fields(
        raw.post(endpoint, json=payload),
        endpoint=endpoint,
    )


def azimuth_elevation_mask(
    *,
    site_position: components.SitePosition,
    config: TerrainMaskConfig | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    """Return the full ASTROX terrain azimuth-elevation mask response."""
    return _mask_request(
        endpoint="/Terrain/AzElMask",
        site_position=site_position,
        config=config,
        text=text,
    )


def azimuth_elevation_mask_simple(
    *,
    site_position: components.SitePosition,
    config: TerrainMaskConfig | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    """Return the simplified ASTROX terrain azimuth-elevation mask response."""
    return _mask_request(
        endpoint="/Terrain/AzElMaskSimple",
        site_position=site_position,
        config=config,
        text=text,
    )
