"""Shared helpers for ASTROX reusable component value objects."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any

from astrox.orbits import CartesianState, KeplerianElements
from astrox.propagator import HpopConfig

_GROUP_RESTRICTIONS = {"AnyOf", "AtLeastN"}


_RELATIVE_TO_VALUES = {"Earth", "Moon", "Mars", "Sun", "CBF"}


_AXIS_DIRECTIONS = {"+X", "-X", "+Y", "-Y", "+Z", "-Z"}


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _real_number(value: float, *, parameter: str) -> float:
    if not isinstance(value, Real) or isinstance(value, bool):
        raise TypeError(f"{parameter} must be a number")
    return value


def _string(value: str, *, parameter: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{parameter} must be a string")
    return value


def _optional_string(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    return _string(value, parameter=parameter)


def _number_sequence_to_list(value: Sequence[float], *, parameter: str) -> list[float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    items = list(value)
    if not all(isinstance(item, Real) and not isinstance(item, bool) for item in items):
        raise TypeError(f"{parameter} must be a sequence of numbers")
    return items


def _tle_lines_to_list(value: tuple[str, str] | list[str]) -> list[str]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or not all(isinstance(line, str) for line in value)
    ):
        raise TypeError("tle_lines must be a two-item sequence of TLE strings")
    return list(value)


def _orbit_elements_to_wire(orbit: KeplerianElements, *, parameter: str) -> list[float]:
    if not isinstance(orbit, KeplerianElements):
        raise TypeError(f"{parameter} must be a KeplerianElements instance")
    return orbit.to_wire()


def _cartesian_state_to_wire(state: CartesianState, *, parameter: str) -> list[float]:
    if not isinstance(state, CartesianState):
        raise TypeError(f"{parameter} must be a CartesianState instance")
    return state.to_wire()


def _hpop_config_to_wire(
    config: HpopConfig | Mapping[str, Any],
    *,
    parameter: str,
) -> dict[str, Any]:
    if isinstance(config, HpopConfig):
        return config.to_wire()
    if isinstance(config, Mapping):
        return dict(config)
    raise TypeError(f"{parameter} must be an HpopConfig value or mapping fragment")


def _validate_group_restriction(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    if value not in _GROUP_RESTRICTIONS:
        accepted = ", ".join(sorted(_GROUP_RESTRICTIONS))
        raise ValueError(f"{parameter} must be one of: {accepted}")
    return value


def _validate_relative_to(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    if value not in _RELATIVE_TO_VALUES:
        accepted = ", ".join(sorted(_RELATIVE_TO_VALUES))
        raise ValueError(f"{parameter} must be one of: {accepted}")
    return value


def _validate_axis_direction(value: str, *, parameter: str) -> str:
    if value not in _AXIS_DIRECTIONS:
        accepted = ", ".join(sorted(_AXIS_DIRECTIONS))
        raise ValueError(f"{parameter} must be one of: {accepted}")
    return value


def _axes_type(family: str, relative_to: str | None) -> str:
    return family if relative_to is None else f"{family}({relative_to})"


def _include_axes_metadata(
    payload: dict[str, Any],
    *,
    name: str | None,
    description: str | None,
    start: str | None,
    stop: str | None,
) -> None:
    _include_if_supplied(payload, "Name", name)
    _include_if_supplied(payload, "Description", description)
    _include_if_supplied(payload, "Start", start)
    _include_if_supplied(payload, "Stop", stop)


def _typed_tuple(
    values: Sequence[Any],
    accepted_types: tuple[type[Any], ...],
    *,
    parameter: str,
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{parameter} must be a sequence")
    items = tuple(values)
    if not all(isinstance(item, accepted_types) for item in items):
        raise TypeError(f"{parameter} contains unsupported item values")
    return items
