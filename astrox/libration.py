"""CRTBP and Earth-Moon libration-dynamics functions."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any

from astrox._http import raw

__all__ = [
    "CrtbpSample",
    "CrtbpState",
    "CrtbpTrajectory",
    "LibrationPoint",
    "LibrationPoints",
    "LibrationUnitSystem",
    "PeriodicOrbit",
    "correct_periodic_orbit_fixed_x",
    "crtbp_state",
    "crtbp_trajectory",
    "earth_moon_dro",
    "earth_moon_l1_halo",
    "earth_moon_l2_halo",
    "positions",
    "units",
]


def _number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _optional_number(value: float | None, *, parameter: str) -> float | None:
    if value is None:
        return None
    return _number(value, field=parameter)


def _optional_boolean(value: bool | None, *, parameter: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TypeError(f"{parameter} must be a boolean")
    return value


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be an object")
    return value


def _sequence(value: Any, *, field: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field} must be an array")
    return value


def _boolean(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _boolean_query(value: bool | None, *, parameter: str) -> str | None:
    parsed = _optional_boolean(value, parameter=parameter)
    if parsed is None:
        return None
    return "true" if parsed else "false"


@dataclass(frozen=True, kw_only=True)
class LibrationPoint:
    """One nondimensional CRTBP equilibrium-point coordinate."""

    x: float
    y: float


@dataclass(frozen=True, kw_only=True)
class LibrationPoints:
    """The five CRTBP equilibrium points and collinear-point distances."""

    l1: LibrationPoint
    l2: LibrationPoint
    l3: LibrationPoint
    l4: LibrationPoint
    l5: LibrationPoint
    l1_distance_to_secondary: float
    l2_distance_to_secondary: float
    l3_distance_to_primary: float


@dataclass(frozen=True, kw_only=True)
class LibrationUnitSystem:
    """Dimensional scales for a nondimensional CRTBP system."""

    primary_gravitational_parameter_m3_s2: float
    secondary_gravitational_parameter_m3_s2: float
    mass_ratio: float
    length_unit_m: float
    time_unit_s: float
    velocity_unit_m_s: float


@dataclass(frozen=True, kw_only=True)
class CrtbpState:
    """Nondimensional CRTBP position and rotating-frame velocity."""

    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float

    def __post_init__(self) -> None:
        for field_name in ("x", "y", "z", "vx", "vy", "vz"):
            object.__setattr__(
                self,
                field_name,
                _number(getattr(self, field_name), field=field_name),
            )

    def to_wire(self) -> list[float]:
        """Lower to ASTROX ``[x, y, z, vx, vy, vz]`` order."""
        return [self.x, self.y, self.z, self.vx, self.vy, self.vz]


@dataclass(frozen=True, kw_only=True)
class CrtbpSample:
    """One nondimensional CRTBP state at a nondimensional time."""

    time: float
    state: CrtbpState


@dataclass(frozen=True, kw_only=True)
class CrtbpTrajectory:
    """A sampled nondimensional CRTBP trajectory."""

    mass_ratio: float
    is_barycentric: bool
    samples: tuple[CrtbpSample, ...]


@dataclass(frozen=True, kw_only=True)
class PeriodicOrbit:
    """A corrected periodic CRTBP orbit and one sampled period."""

    is_barycentric: bool
    period: float
    initial_state: CrtbpState
    corrected_state: CrtbpState
    samples: tuple[CrtbpSample, ...]


def crtbp_state(
    *,
    x: float,
    y: float,
    z: float,
    vx: float,
    vy: float,
    vz: float,
) -> CrtbpState:
    """Create a nondimensional rotating-frame CRTBP state."""
    return CrtbpState(x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)


def _state_to_wire(value: CrtbpState, *, parameter: str) -> list[float]:
    if not isinstance(value, CrtbpState):
        raise TypeError(f"{parameter} must be a CrtbpState value")
    return value.to_wire()


def _state_from_wire(value: Any, *, field: str) -> CrtbpState:
    values = _sequence(value, field=field)
    if len(values) != 6:
        raise TypeError(f"{field} must contain six numbers")
    return CrtbpState(
        x=_number(values[0], field=f"{field}[0]"),
        y=_number(values[1], field=f"{field}[1]"),
        z=_number(values[2], field=f"{field}[2]"),
        vx=_number(values[3], field=f"{field}[3]"),
        vy=_number(values[4], field=f"{field}[4]"),
        vz=_number(values[5], field=f"{field}[5]"),
    )


def _points_from_wire(value: Any) -> LibrationPoints:
    values = _sequence(value, field="positions response")
    if len(values) != 10:
        raise TypeError("positions response must contain ten numbers")
    numbers = tuple(
        _number(item, field=f"positions response[{index}]")
        for index, item in enumerate(values)
    )
    return LibrationPoints(
        l1=LibrationPoint(x=numbers[3], y=0.0),
        l2=LibrationPoint(x=numbers[4], y=0.0),
        l3=LibrationPoint(x=numbers[5], y=0.0),
        l4=LibrationPoint(x=numbers[6], y=numbers[8]),
        l5=LibrationPoint(x=numbers[7], y=numbers[9]),
        l1_distance_to_secondary=numbers[0],
        l2_distance_to_secondary=numbers[1],
        l3_distance_to_primary=numbers[2],
    )


def _units_from_wire(value: Any) -> LibrationUnitSystem:
    payload = _mapping(value, field="unit response")
    return LibrationUnitSystem(
        primary_gravitational_parameter_m3_s2=_number(
            payload["GravitationalParameter1"],
            field="GravitationalParameter1",
        ),
        secondary_gravitational_parameter_m3_s2=_number(
            payload["GravitationalParameter2"],
            field="GravitationalParameter2",
        ),
        mass_ratio=_number(payload["U"], field="U"),
        length_unit_m=_number(payload["UnitL"], field="UnitL"),
        time_unit_s=_number(payload["UnitT"], field="UnitT"),
        velocity_unit_m_s=_number(payload["UnitV"], field="UnitV"),
    )


def _trajectory_from_wire(value: Any) -> CrtbpTrajectory:
    payload = _mapping(value, field="crtbp trajectory response")
    positions = _sequence(payload["Positions"], field="Positions")
    if not positions or len(positions) % 7 != 0:
        raise TypeError("Positions must contain one or more seven-number samples")
    samples = tuple(
        CrtbpSample(
            time=_number(positions[index], field=f"Positions[{index}]"),
            state=_state_from_wire(
                positions[index + 1 : index + 7],
                field=f"Positions[{index + 1}:{index + 7}]",
            ),
        )
        for index in range(0, len(positions), 7)
    )
    return CrtbpTrajectory(
        mass_ratio=_number(payload["U"], field="U"),
        is_barycentric=_boolean(payload["IsBarycentric"], field="IsBarycentric"),
        samples=samples,
    )


def _periodic_orbit_from_wire(value: Any) -> PeriodicOrbit:
    payload = _mapping(value, field="periodic orbit response")
    times = _sequence(payload["ListT"], field="ListT")
    states = _sequence(payload["ListX"], field="ListX")
    if not times or len(times) != len(states):
        raise TypeError("ListT and ListX must be non-empty arrays of equal length")
    samples = tuple(
        CrtbpSample(
            time=_number(time, field=f"ListT[{index}]"),
            state=_state_from_wire(state, field=f"ListX[{index}]"),
        )
        for index, (time, state) in enumerate(zip(times, states, strict=True))
    )
    return PeriodicOrbit(
        is_barycentric=_boolean(payload["IsBarycentric"], field="IsBarycentric"),
        period=_number(payload["Period"], field="Period"),
        initial_state=_state_from_wire(payload["InitialX0"], field="InitialX0"),
        corrected_state=_state_from_wire(payload["X0"], field="X0"),
        samples=samples,
    )


def positions(*, mass_ratio: float) -> LibrationPoints:
    """Return the five barycentric CRTBP equilibrium points."""
    return _points_from_wire(
        raw.get(
            "/libration/positions",
            params={"u": _number(mass_ratio, field="mass_ratio")},
        )
    )


def units(
    *,
    primary_gravitational_parameter_m3_s2: float | None = None,
    secondary_gravitational_parameter_m3_s2: float | None = None,
    mean_separation_m: float | None = None,
) -> LibrationUnitSystem:
    """Return the dimensional scales for a CRTBP primary-secondary system."""
    params: dict[str, Any] = {}
    _include_if_supplied(
        params,
        "gm1",
        _optional_number(
            primary_gravitational_parameter_m3_s2,
            parameter="primary_gravitational_parameter_m3_s2",
        ),
    )
    _include_if_supplied(
        params,
        "gm2",
        _optional_number(
            secondary_gravitational_parameter_m3_s2,
            parameter="secondary_gravitational_parameter_m3_s2",
        ),
    )
    _include_if_supplied(
        params,
        "meanRange",
        _optional_number(mean_separation_m, parameter="mean_separation_m"),
    )
    return _units_from_wire(raw.get("/libration/unit", params=params))


def crtbp_trajectory(
    *,
    initial_state: CrtbpState,
    mass_ratio: float,
    start_time: float | None = None,
    end_time: float | None = None,
    barycentric: bool | None = None,
    output_step: float | None = None,
) -> CrtbpTrajectory:
    """Integrate a nondimensional CRTBP state in the rotating frame."""
    payload: dict[str, Any] = {
        "RV0": _state_to_wire(initial_state, parameter="initial_state"),
        "U": _number(mass_ratio, field="mass_ratio"),
    }
    _include_if_supplied(
        payload,
        "T0",
        _optional_number(start_time, parameter="start_time"),
    )
    _include_if_supplied(
        payload,
        "TEnd",
        _optional_number(end_time, parameter="end_time"),
    )
    _include_if_supplied(
        payload,
        "IsBarycentric",
        _optional_boolean(barycentric, parameter="barycentric"),
    )
    _include_if_supplied(
        payload,
        "OutStep",
        _optional_number(output_step, parameter="output_step"),
    )
    return _trajectory_from_wire(
        raw.post("/libration/crtbp-trajectory", json=payload)
    )


def earth_moon_l1_halo(
    *,
    z_amplitude: float | None = None,
    southern: bool | None = None,
) -> PeriodicOrbit:
    """Return a corrected Earth-Moon L1 Halo orbit."""
    params: dict[str, Any] = {}
    _include_if_supplied(
        params,
        "az",
        _optional_number(z_amplitude, parameter="z_amplitude"),
    )
    _include_if_supplied(
        params,
        "isSouth",
        _boolean_query(southern, parameter="southern"),
    )
    return _periodic_orbit_from_wire(
        raw.get("/libration/em-l1-halo", params=params)
    )


def earth_moon_l2_halo(
    *,
    x_amplitude: float | None = None,
    southern: bool | None = None,
) -> PeriodicOrbit:
    """Return a corrected Earth-Moon L2 Halo orbit."""
    params: dict[str, Any] = {}
    _include_if_supplied(
        params,
        "ax",
        _optional_number(x_amplitude, parameter="x_amplitude"),
    )
    _include_if_supplied(
        params,
        "isSouth",
        _boolean_query(southern, parameter="southern"),
    )
    return _periodic_orbit_from_wire(
        raw.get("/libration/em-l2-halo", params=params)
    )


def earth_moon_dro(*, x_amplitude: float | None = None) -> PeriodicOrbit:
    """Return a corrected planar Earth-Moon distant retrograde orbit."""
    params: dict[str, Any] = {}
    _include_if_supplied(
        params,
        "ax",
        _optional_number(x_amplitude, parameter="x_amplitude"),
    )
    return _periodic_orbit_from_wire(raw.get("/libration/em-dro", params=params))


def correct_periodic_orbit_fixed_x(
    *,
    initial_state: CrtbpState,
    period_guess: float,
    mass_ratio: float,
    barycentric: bool | None = None,
    output_step: float | None = None,
) -> PeriodicOrbit:
    """Correct an XZ-plane-crossing seed while holding its x coordinate fixed."""
    payload: dict[str, Any] = {
        "RV0": _state_to_wire(initial_state, parameter="initial_state"),
        "TEnd": _number(period_guess, field="period_guess"),
        "U": _number(mass_ratio, field="mass_ratio"),
    }
    _include_if_supplied(
        payload,
        "IsBarycentric",
        _optional_boolean(barycentric, parameter="barycentric"),
    )
    _include_if_supplied(
        payload,
        "OutStep",
        _optional_number(output_step, parameter="output_step"),
    )
    return _periodic_orbit_from_wire(
        raw.post("/libration/crtbp-period-orbit-fixed-x", json=payload)
    )
