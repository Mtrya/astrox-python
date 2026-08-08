"""Conjunction-analysis endpoint functions and response views."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any, TypeAlias

from astrox import components
from astrox._http import raw
from astrox.orbits import Tle

__all__ = [
    "CloseApproachesResult",
    "CzmlCloseApproach",
    "TleCloseApproach",
    "find_czml_close_approaches",
    "find_tle_close_approaches",
]


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    return value


def _sequence(value: Any, *, field: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field} must be a sequence")
    return value


def _string(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    return value


def _boolean(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value


def _integer(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    return value


def _number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field} must be a number")
    return float(value)


def _request_optional_number(value: float | None, *, parameter: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{parameter} must be a number")
    return value


def _tle_to_wire(value: Tle, *, parameter: str) -> dict[str, str]:
    if not isinstance(value, Tle):
        raise TypeError(f"{parameter} must be an astrox.orbits.Tle instance")
    return value.to_tle_info_wire()


def _tles_to_wire(values: Sequence[Tle]) -> list[dict[str, str]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("targets must be a sequence of astrox.orbits.Tle values")
    items = tuple(values)
    if not all(isinstance(item, Tle) for item in items):
        raise TypeError("targets must be a sequence of astrox.orbits.Tle values")
    return [item.to_tle_info_wire() for item in items]


@dataclass(frozen=True, kw_only=True)
class TleCloseApproach:
    """One V3 close-approach result for two TLE objects."""

    primary: Tle
    target: Tle
    min_range_time: str
    min_range_km: float
    orbital_plane_angle_deg: float
    relative_speed_km_s: float
    collision_probability: float


@dataclass(frozen=True, kw_only=True)
class CzmlCloseApproach:
    """One V4 close-approach result for a CZML primary and TLE target."""

    target: Tle
    min_range_time: str
    min_range_km: float
    orbital_plane_angle_deg: float
    relative_speed_km_s: float
    collision_probability: float


CloseApproachItem: TypeAlias = TleCloseApproach | CzmlCloseApproach


@dataclass(frozen=True, kw_only=True)
class CloseApproachesResult:
    """Common CA envelope with a branch-specific result-item tuple."""

    is_success: bool
    message: str
    total_number: int
    after_apo_peri_filter_number: int
    after_cross_plane_number: int
    results: tuple[CloseApproachItem, ...]


def _tle_close_approach_from_wire(value: Any) -> TleCloseApproach:
    payload = _mapping(value, field="CA_Results item")
    return TleCloseApproach(
        primary=Tle.from_tle_info_wire(payload, prefix="SAT1"),
        target=Tle.from_tle_info_wire(payload, prefix="SAT2"),
        min_range_time=_string(payload["CA_MinRange_Time"], field="CA_MinRange_Time"),
        min_range_km=_number(payload["CA_MinRange"], field="CA_MinRange"),
        orbital_plane_angle_deg=_number(payload["CA_Theta"], field="CA_Theta"),
        relative_speed_km_s=_number(payload["CA_DeltaV"], field="CA_DeltaV"),
        collision_probability=_number(
            payload["CA_Probability"],
            field="CA_Probability",
        ),
    )


def _czml_close_approach_from_wire(value: Any) -> CzmlCloseApproach:
    payload = _mapping(value, field="CA_Results item")
    return CzmlCloseApproach(
        target=Tle.from_tle_info_wire(payload, prefix="SAT2"),
        min_range_time=_string(payload["CA_MinRange_Time"], field="CA_MinRange_Time"),
        min_range_km=_number(payload["CA_MinRange"], field="CA_MinRange"),
        orbital_plane_angle_deg=_number(payload["CA_Theta"], field="CA_Theta"),
        relative_speed_km_s=_number(payload["CA_DeltaV"], field="CA_DeltaV"),
        collision_probability=_number(
            payload["CA_Probability"],
            field="CA_Probability",
        ),
    )


def _close_approaches_result_from_wire(
    value: Any,
    *,
    item_parser: Any,
) -> CloseApproachesResult:
    payload = _mapping(value, field="CA response")
    return CloseApproachesResult(
        is_success=_boolean(payload["IsSuccess"], field="IsSuccess"),
        message=_string(payload["Message"], field="Message"),
        total_number=_integer(payload["TotalNumber"], field="TotalNumber"),
        after_apo_peri_filter_number=_integer(
            payload["AfterApoPeriFilterNumber"],
            field="AfterApoPeriFilterNumber",
        ),
        after_cross_plane_number=_integer(
            payload["AfterCrossPlaneNumber"],
            field="AfterCrossPlaneNumber",
        ),
        results=tuple(
            item_parser(item)
            for item in _sequence(payload["CA_Results"], field="CA_Results")
        ),
    )


def _ca_request_payload(
    *,
    start: str,
    stop: str,
    primary: dict[str, Any],
    targets: Sequence[Tle] | None,
    tol_max_distance_km: float | None,
    tol_cross_dt_s: float | None,
    tol_theta_deg: float | None,
    tol_dh_km: float | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "Start_UTCG": start,
        "Stop_UTCG": stop,
        "SAT1": primary,
    }
    _include_if_supplied(
        payload,
        "TolMaxDistance",
        _request_optional_number(
            tol_max_distance_km,
            parameter="tol_max_distance_km",
        ),
    )
    _include_if_supplied(
        payload,
        "TolCrossDt",
        _request_optional_number(tol_cross_dt_s, parameter="tol_cross_dt_s"),
    )
    _include_if_supplied(
        payload,
        "TolTheta",
        _request_optional_number(tol_theta_deg, parameter="tol_theta_deg"),
    )
    _include_if_supplied(
        payload,
        "TolDh",
        _request_optional_number(tol_dh_km, parameter="tol_dh_km"),
    )
    if targets is not None:
        payload["Targets"] = _tles_to_wire(targets)
    return payload


def find_tle_close_approaches(
    *,
    start: str,
    stop: str,
    tle: Tle,
    tol_max_distance_km: float | None = None,
    tol_cross_dt_s: float | None = None,
    tol_theta_deg: float | None = None,
    tol_dh_km: float | None = None,
    targets: Sequence[Tle] | None = None,
) -> CloseApproachesResult:
    """Find close approaches for a primary TLE and optional TLE targets."""
    result = raw.post(
        "/CAT/CA_ComputeV3",
        json=_ca_request_payload(
            start=start,
            stop=stop,
            primary=_tle_to_wire(tle, parameter="tle"),
            targets=targets,
            tol_max_distance_km=tol_max_distance_km,
            tol_cross_dt_s=tol_cross_dt_s,
            tol_theta_deg=tol_theta_deg,
            tol_dh_km=tol_dh_km,
        ),
    )
    return _close_approaches_result_from_wire(
        result,
        item_parser=_tle_close_approach_from_wire,
    )


def find_czml_close_approaches(
    *,
    start: str,
    stop: str,
    position: components.CzmlPosition,
    tol_max_distance_km: float | None = None,
    tol_cross_dt_s: float | None = None,
    tol_theta_deg: float | None = None,
    tol_dh_km: float | None = None,
    targets: Sequence[Tle] | None = None,
) -> CloseApproachesResult:
    """Find close approaches for a CZML primary and optional TLE targets."""
    if not isinstance(position, components.CzmlPosition):
        raise TypeError("position must be an astrox.components.CzmlPosition instance")
    result = raw.post(
        "/CAT/CA_ComputeV4",
        json=_ca_request_payload(
            start=start,
            stop=stop,
            primary=position.to_wire(),
            targets=targets,
            tol_max_distance_km=tol_max_distance_km,
            tol_cross_dt_s=tol_cross_dt_s,
            tol_theta_deg=tol_theta_deg,
            tol_dh_km=tol_dh_km,
        ),
    )
    return _close_approaches_result_from_wire(
        result,
        item_parser=_czml_close_approach_from_wire,
    )
