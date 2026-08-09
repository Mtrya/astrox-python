"""Read-like catalog query functions."""

from __future__ import annotations

from numbers import Real
from typing import Any

from astrox._http import raw

__all__ = [
    "query_cities",
    "query_facilities",
    "query_satellites",
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


def _optional_boolean_query(value: bool | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TypeError(f"{parameter} must be a boolean")
    return "true" if value else "false"


def _without_status_fields(value: Any, *, endpoint: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{endpoint} response must be an object")
    return {
        key: item
        for key, item in value.items()
        if key not in {"IsSuccess", "Message"}
    }


def query_cities(
    *,
    city_name: str | None = None,
    province_name: str | None = None,
    country_name: str | None = None,
    city_type: str | None = None,
) -> dict[str, Any]:
    """Query the server-owned city catalog."""
    params: dict[str, Any] = {}
    _include_if_supplied(
        params,
        "cityName",
        _optional_string(city_name, parameter="city_name"),
    )
    _include_if_supplied(
        params,
        "provinceName",
        _optional_string(province_name, parameter="province_name"),
    )
    _include_if_supplied(
        params,
        "countryName",
        _optional_string(country_name, parameter="country_name"),
    )
    _include_if_supplied(
        params,
        "typeOfCity",
        _optional_string(city_type, parameter="city_type"),
    )
    return _without_status_fields(
        raw.get("/city", params=params),
        endpoint="/city",
    )


def query_facilities(
    *,
    facility_name: str | None = None,
    network_name: str | None = None,
) -> dict[str, Any]:
    """Query the server-owned facility catalog."""
    params: dict[str, Any] = {}
    _include_if_supplied(
        params,
        "facilityName",
        _optional_string(facility_name, parameter="facility_name"),
    )
    _include_if_supplied(
        params,
        "networkName",
        _optional_string(network_name, parameter="network_name"),
    )
    return _without_status_fields(
        raw.get("/facility", params=params),
        endpoint="/facility",
    )


def query_satellites(
    *,
    name: str | None = None,
    catalog_number: str | None = None,
    mission: str | None = None,
    owner: str | None = None,
    active: bool | None = None,
    minimum_perigee_m: float | None = None,
    maximum_perigee_m: float | None = None,
    minimum_apogee_m: float | None = None,
    maximum_apogee_m: float | None = None,
    minimum_inclination_deg: float | None = None,
    maximum_inclination_deg: float | None = None,
) -> dict[str, Any]:
    """Query the server-owned satellite catalog."""
    params: dict[str, Any] = {}
    _include_if_supplied(
        params,
        "sscName",
        _optional_string(name, parameter="name"),
    )
    _include_if_supplied(
        params,
        "sscNumber",
        _optional_string(catalog_number, parameter="catalog_number"),
    )
    _include_if_supplied(
        params,
        "mission",
        _optional_string(mission, parameter="mission"),
    )
    _include_if_supplied(
        params,
        "owner",
        _optional_string(owner, parameter="owner"),
    )
    _include_if_supplied(
        params,
        "active",
        _optional_boolean_query(active, parameter="active"),
    )
    _include_if_supplied(
        params,
        "minimumPerigee",
        _optional_number(minimum_perigee_m, parameter="minimum_perigee_m"),
    )
    _include_if_supplied(
        params,
        "maximumPerigee",
        _optional_number(maximum_perigee_m, parameter="maximum_perigee_m"),
    )
    _include_if_supplied(
        params,
        "minmumApogee",
        _optional_number(minimum_apogee_m, parameter="minimum_apogee_m"),
    )
    _include_if_supplied(
        params,
        "maximumApogee",
        _optional_number(maximum_apogee_m, parameter="maximum_apogee_m"),
    )
    _include_if_supplied(
        params,
        "minimumInclination",
        _optional_number(
            minimum_inclination_deg,
            parameter="minimum_inclination_deg",
        ),
    )
    _include_if_supplied(
        params,
        "maximumInclination",
        _optional_number(
            maximum_inclination_deg,
            parameter="maximum_inclination_deg",
        ),
    )
    return _without_status_fields(
        raw.get("/ssc", params=params),
        endpoint="/ssc",
    )
