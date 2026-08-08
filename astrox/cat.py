"""CAT endpoint functions and thin typed response views."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any

from astrox._http import raw
from astrox.orbits import Tle

__all__ = [
    "DebrisBreakupResult",
    "DebrisImpulse",
    "TleLifetimeResult",
    "estimate_tle_lifetime",
    "generate_tle",
    "simulate_debris_breakup",
    "simulate_debris_breakup_nasa",
    "simulate_debris_breakup_simple",
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


def _request_string(value: str, *, parameter: str) -> str:
    return _string(value, field=parameter)


def _request_number(value: float, *, parameter: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{parameter} must be a number")
    return value


def _request_integer(value: int, *, parameter: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{parameter} must be an integer")
    return value


def _request_optional_string(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    return _request_string(value, parameter=parameter)


def _request_optional_number(value: float | None, *, parameter: str) -> float | None:
    if value is None:
        return None
    return _request_number(value, parameter=parameter)


def _request_optional_integer(value: int | None, *, parameter: str) -> int | None:
    if value is None:
        return None
    return _request_integer(value, parameter=parameter)


def _request_optional_boolean(value: bool | None, *, parameter: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TypeError(f"{parameter} must be a boolean")
    return value


def _tle_to_wire(value: Tle, *, parameter: str) -> dict[str, str]:
    if not isinstance(value, Tle):
        raise TypeError(f"{parameter} must be an astrox.orbits.Tle instance")
    return value.to_tle_info_wire()


@dataclass(frozen=True, kw_only=True)
class DebrisImpulse:
    """One explicit debris breakup impulse row."""

    azimuth_deg: float
    elevation_deg: float
    delta_v_m_s: float
    area_to_mass_ratio_m2_kg: float

    def __post_init__(self) -> None:
        _request_number(self.azimuth_deg, parameter="azimuth_deg")
        _request_number(self.elevation_deg, parameter="elevation_deg")
        _request_number(self.delta_v_m_s, parameter="delta_v_m_s")
        _request_number(
            self.area_to_mass_ratio_m2_kg,
            parameter="area_to_mass_ratio_m2_kg",
        )

    def to_wire(self) -> list[float]:
        """Lower to an ASTROX ``AzElVel`` row."""
        return [
            self.azimuth_deg,
            self.elevation_deg,
            self.delta_v_m_s,
            self.area_to_mass_ratio_m2_kg,
        ]


def _impulse_to_wire(value: DebrisImpulse, *, parameter: str) -> list[float]:
    if not isinstance(value, DebrisImpulse):
        raise TypeError(f"{parameter} must contain DebrisImpulse values")
    return value.to_wire()


def _impulses_to_wire(values: Sequence[DebrisImpulse]) -> list[list[float]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("impulses must be a sequence of DebrisImpulse values")
    return [
        _impulse_to_wire(value, parameter="impulses")
        for value in values
    ]


@dataclass(frozen=True, kw_only=True)
class TleLifetimeResult:
    """Lifetime response returned by the TLE lifetime endpoint."""

    is_success: bool
    message: str
    life_years: float


@dataclass(frozen=True, kw_only=True)
class DebrisBreakupResult:
    """Typed debris breakup response with synchronized output arrays."""

    is_success: bool
    message: str
    debris_tles: tuple[Tle, ...]
    impulses: tuple[DebrisImpulse, ...]
    life_years: tuple[float, ...]
    altitude_of_perigee_km: tuple[float, ...]
    altitude_of_apogee_km: tuple[float, ...]
    periods_min: tuple[float, ...]


def _tle_lifetime_result_from_wire(value: Any) -> TleLifetimeResult:
    payload = _mapping(value, field="LifeTimeTLE response")
    return TleLifetimeResult(
        is_success=_boolean(payload["IsSuccess"], field="IsSuccess"),
        message=_string(payload["Message"], field="Message"),
        life_years=_number(payload["LifeYears"], field="LifeYears"),
    )


def _number_tuple(value: Any, *, field: str) -> tuple[float, ...]:
    return tuple(
        _number(item, field=field)
        for item in _sequence(value, field=field)
    )


def _impulses_from_wire(value: Any) -> tuple[DebrisImpulse, ...]:
    rows = _sequence(value, field="AzElVel")
    parsed: list[DebrisImpulse] = []
    for item in rows:
        row = _sequence(item, field="AzElVel item")
        if len(row) != 4:
            raise TypeError("AzElVel item must contain four numbers")
        parsed.append(
            DebrisImpulse(
                azimuth_deg=_number(row[0], field="AzElVel item"),
                elevation_deg=_number(row[1], field="AzElVel item"),
                delta_v_m_s=_number(row[2], field="AzElVel item"),
                area_to_mass_ratio_m2_kg=_number(row[3], field="AzElVel item"),
            )
        )
    return tuple(parsed)


def _debris_breakup_result_from_wire(value: Any) -> DebrisBreakupResult:
    payload = _mapping(value, field="DebrisBreakup response")
    debris_tles = tuple(
        Tle.from_tle_info_wire(item)
        for item in _sequence(payload["DebrisTLEs"], field="DebrisTLEs")
    )
    impulses = _impulses_from_wire(payload["AzElVel"])
    life_years = _number_tuple(payload["LifeYears"], field="LifeYears")
    altitude_of_perigee_km = _number_tuple(
        payload["AltitudeOfPerigee"],
        field="AltitudeOfPerigee",
    )
    altitude_of_apogee_km = _number_tuple(
        payload["AltitudeOfApogee"],
        field="AltitudeOfApogee",
    )
    periods_min = _number_tuple(payload["Periods"], field="Periods")
    lengths = {
        "DebrisTLEs": len(debris_tles),
        "AzElVel": len(impulses),
        "LifeYears": len(life_years),
        "AltitudeOfPerigee": len(altitude_of_perigee_km),
        "AltitudeOfApogee": len(altitude_of_apogee_km),
        "Periods": len(periods_min),
    }
    if len(set(lengths.values())) != 1:
        raise TypeError(
            "DebrisBreakup response arrays must have synchronized lengths: "
            + ", ".join(f"{field}={length}" for field, length in lengths.items())
        )
    return DebrisBreakupResult(
        is_success=_boolean(payload["IsSuccess"], field="IsSuccess"),
        message=_string(payload["Message"], field="Message"),
        debris_tles=debris_tles,
        impulses=impulses,
        life_years=life_years,
        altitude_of_perigee_km=altitude_of_perigee_km,
        altitude_of_apogee_km=altitude_of_apogee_km,
        periods_min=periods_min,
    )


def generate_tle(
    *,
    name: str,
    catalog_number: str,
    epoch: str,
    bstar: float,
    semi_major_axis_km: float,
    eccentricity: float,
    inclination_deg: float,
    argument_of_perigee_deg: float,
    raan_deg: float,
    true_anomaly_deg: float,
    is_mean_elements: bool | None = None,
) -> Tle:
    """Generate TLE lines from TEME Keplerian elements."""
    payload: dict[str, Any] = {
        "Name": _request_string(name, parameter="name"),
        "SSC": _request_string(catalog_number, parameter="catalog_number"),
        "Epoch": _request_string(epoch, parameter="epoch"),
        "BStar": _request_number(bstar, parameter="bstar"),
        "Sma": _request_number(semi_major_axis_km, parameter="semi_major_axis_km"),
        "Ecc": _request_number(eccentricity, parameter="eccentricity"),
        "Inc": _request_number(inclination_deg, parameter="inclination_deg"),
        "W": _request_number(
            argument_of_perigee_deg,
            parameter="argument_of_perigee_deg",
        ),
        "RAAN": _request_number(raan_deg, parameter="raan_deg"),
        "TA": _request_number(true_anomaly_deg, parameter="true_anomaly_deg"),
    }
    _include_if_supplied(
        payload,
        "IsMeanElements",
        _request_optional_boolean(is_mean_elements, parameter="is_mean_elements"),
    )
    result = raw.post("/CAT/GetTLE", json=payload)
    return Tle.from_tle_info_wire(result)


def estimate_tle_lifetime(
    *,
    epoch: str,
    tle: Tle,
    sm: float | None = None,
    mass: float | None = None,
) -> TleLifetimeResult:
    """Estimate lifetime from TLE data and optional server-owned parameters."""
    payload: dict[str, Any] = {
        "Epoch": _request_string(epoch, parameter="epoch"),
        "TLEs": _tle_to_wire(tle, parameter="tle"),
    }
    _include_if_supplied(payload, "Sm", _request_optional_number(sm, parameter="sm"))
    _include_if_supplied(payload, "Mass", _request_optional_number(mass, parameter="mass"))
    result = raw.post("/CAT/LifeTimeTLE", json=payload)
    return _tle_lifetime_result_from_wire(result)


def simulate_debris_breakup_simple(
    *,
    mother_tle: Tle,
    epoch: str,
    count: int | None = None,
    ssc_prefix: str | None = None,
    delta_v_m_s: float | None = None,
    area_to_mass_ratio_m2_kg: float | None = None,
    min_azimuth_deg: float | None = None,
    max_azimuth_deg: float | None = None,
    min_elevation_deg: float | None = None,
    max_elevation_deg: float | None = None,
    compute_lifetime: bool | None = None,
) -> DebrisBreakupResult:
    """Generate debris with a shared relative-speed and area-to-mass ratio."""
    payload: dict[str, Any] = {
        "MotherSate": _tle_to_wire(mother_tle, parameter="mother_tle"),
        "Epoch": _request_string(epoch, parameter="epoch"),
    }
    _include_if_supplied(payload, "Count", _request_optional_integer(count, parameter="count"))
    _include_if_supplied(
        payload,
        "SSC_Pre",
        _request_optional_string(ssc_prefix, parameter="ssc_prefix"),
    )
    _include_if_supplied(
        payload,
        "DeltaV",
        _request_optional_number(delta_v_m_s, parameter="delta_v_m_s"),
    )
    _include_if_supplied(
        payload,
        "A2M",
        _request_optional_number(
            area_to_mass_ratio_m2_kg,
            parameter="area_to_mass_ratio_m2_kg",
        ),
    )
    _include_if_supplied(
        payload,
        "MinAzimuth",
        _request_optional_number(min_azimuth_deg, parameter="min_azimuth_deg"),
    )
    _include_if_supplied(
        payload,
        "MaxAzimuth",
        _request_optional_number(max_azimuth_deg, parameter="max_azimuth_deg"),
    )
    _include_if_supplied(
        payload,
        "MinElevation",
        _request_optional_number(min_elevation_deg, parameter="min_elevation_deg"),
    )
    _include_if_supplied(
        payload,
        "MaxElevation",
        _request_optional_number(max_elevation_deg, parameter="max_elevation_deg"),
    )
    _include_if_supplied(
        payload,
        "ComputeLifeOfTime",
        _request_optional_boolean(compute_lifetime, parameter="compute_lifetime"),
    )
    result = raw.post("/CAT/DebrisBreakupSimple", json=payload)
    return _debris_breakup_result_from_wire(result)


def simulate_debris_breakup(
    *,
    mother_tle: Tle,
    epoch: str,
    impulses: Sequence[DebrisImpulse],
    ssc_prefix: str | None = None,
    area_to_mass_ratio_m2_kg: float | None = None,
    compute_lifetime: bool | None = None,
) -> DebrisBreakupResult:
    """Generate debris from explicit azimuth, elevation, velocity, and A2M rows."""
    payload: dict[str, Any] = {
        "MotherSate": _tle_to_wire(mother_tle, parameter="mother_tle"),
        "Epoch": _request_string(epoch, parameter="epoch"),
        "AzElVel": _impulses_to_wire(impulses),
    }
    _include_if_supplied(
        payload,
        "SSC_Pre",
        _request_optional_string(ssc_prefix, parameter="ssc_prefix"),
    )
    _include_if_supplied(
        payload,
        "A2M",
        _request_optional_number(
            area_to_mass_ratio_m2_kg,
            parameter="area_to_mass_ratio_m2_kg",
        ),
    )
    _include_if_supplied(
        payload,
        "ComputeLifeOfTime",
        _request_optional_boolean(compute_lifetime, parameter="compute_lifetime"),
    )
    result = raw.post("/CAT/DebrisBreakup", json=payload)
    return _debris_breakup_result_from_wire(result)


def simulate_debris_breakup_nasa(
    *,
    mother_tle: Tle,
    epoch: str,
    ssc_prefix: str | None = None,
    total_mass: float | None = None,
    minimum_characteristic_length: float | None = None,
) -> DebrisBreakupResult:
    """Generate debris using the NASA breakup branch."""
    payload: dict[str, Any] = {
        "MotherSate": _tle_to_wire(mother_tle, parameter="mother_tle"),
        "Epoch": _request_string(epoch, parameter="epoch"),
    }
    _include_if_supplied(
        payload,
        "SSC_Pre",
        _request_optional_string(ssc_prefix, parameter="ssc_prefix"),
    )
    _include_if_supplied(
        payload,
        "MassTotal",
        _request_optional_number(total_mass, parameter="total_mass"),
    )
    _include_if_supplied(
        payload,
        "MinLc",
        _request_optional_number(
            minimum_characteristic_length,
            parameter="minimum_characteristic_length",
        ),
    )
    result = raw.post("/CAT/DebrisBreakupNASA", json=payload)
    return _debris_breakup_result_from_wire(result)
