"""Celestial read-like and computational endpoint functions."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Any

from astrox._http import raw

__all__ = [
    "MpcOrbitalElements",
    "cb_axes_rotation",
    "ephemeris",
    "lambert_transfer_window",
    "mpc_ephemeris",
    "mpc_orbital_elements",
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


def _without_status_fields(value: Any, *, endpoint: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{endpoint} response must be an object")
    return {
        key: item
        for key, item in value.items()
        if key not in {"IsSuccess", "Message"}
    }


@dataclass(frozen=True, kw_only=True)
class MpcOrbitalElements:
    """MPC heliocentric orbital elements used by celestial transfer routes."""

    epoch_mjd_tdt: float | None = None
    periapsis_time_mjd_tdt: float | None = None
    periapsis_distance_au: float | None = None
    semi_major_axis_au: float | None = None
    eccentricity: float | None = None
    inclination_deg: float | None = None
    raan_deg: float | None = None
    argument_of_periapsis_deg: float | None = None
    mean_anomaly_deg: float | None = None
    reference_frame: str | None = None
    """Heliocentric mean-ecliptic variant: ``MeanEclpJ2000`` (JPL) or
    ``EclpJ2000ICRF`` (MPC, server default)."""

    def __post_init__(self) -> None:
        for field_name in (
            "epoch_mjd_tdt",
            "periapsis_time_mjd_tdt",
            "periapsis_distance_au",
            "semi_major_axis_au",
            "eccentricity",
            "inclination_deg",
            "raan_deg",
            "argument_of_periapsis_deg",
            "mean_anomaly_deg",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_number(
                    getattr(self, field_name),
                    parameter=field_name,
                ),
            )
        object.__setattr__(
            self,
            "reference_frame",
            _optional_string(self.reference_frame, parameter="reference_frame"),
        )

    def to_wire(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        _include_if_supplied(payload, "EpochMjdTdt", self.epoch_mjd_tdt)
        _include_if_supplied(payload, "PeriTimeMjdTdt", self.periapsis_time_mjd_tdt)
        _include_if_supplied(payload, "Q", self.periapsis_distance_au)
        _include_if_supplied(payload, "SemimajorAxis", self.semi_major_axis_au)
        _include_if_supplied(payload, "Eccentricity", self.eccentricity)
        _include_if_supplied(payload, "Inclination", self.inclination_deg)
        _include_if_supplied(payload, "Raan", self.raan_deg)
        _include_if_supplied(
            payload,
            "ArgOfPeriapsis",
            self.argument_of_periapsis_deg,
        )
        _include_if_supplied(payload, "MeanAnomaly", self.mean_anomaly_deg)
        _include_if_supplied(payload, "ReferenceFrame", self.reference_frame)
        return payload


def mpc_orbital_elements(
    *,
    epoch_mjd_tdt: float | None = None,
    periapsis_time_mjd_tdt: float | None = None,
    periapsis_distance_au: float | None = None,
    semi_major_axis_au: float | None = None,
    eccentricity: float | None = None,
    inclination_deg: float | None = None,
    raan_deg: float | None = None,
    argument_of_periapsis_deg: float | None = None,
    mean_anomaly_deg: float | None = None,
    reference_frame: str | None = None,
) -> MpcOrbitalElements:
    """Build an MPC orbital-element fragment without adding physics policy."""
    return MpcOrbitalElements(
        epoch_mjd_tdt=epoch_mjd_tdt,
        periapsis_time_mjd_tdt=periapsis_time_mjd_tdt,
        periapsis_distance_au=periapsis_distance_au,
        semi_major_axis_au=semi_major_axis_au,
        eccentricity=eccentricity,
        inclination_deg=inclination_deg,
        raan_deg=raan_deg,
        argument_of_periapsis_deg=argument_of_periapsis_deg,
        mean_anomaly_deg=mean_anomaly_deg,
        reference_frame=reference_frame,
    )


def _interval(start: str, stop: str, *, parameter: str) -> str:
    return "/".join(
        (
            _string(start, parameter=f"{parameter}_start"),
            _string(stop, parameter=f"{parameter}_stop"),
        )
    )


def _elements_to_wire(
    value: MpcOrbitalElements | None,
    *,
    parameter: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, MpcOrbitalElements):
        raise TypeError(f"{parameter} must be an MpcOrbitalElements value")
    return value.to_wire()


def lambert_transfer_window(
    *,
    departure_body: str,
    arrival_body: str,
    departure_start: str,
    departure_stop: str,
    arrival_start: str,
    arrival_stop: str,
    sun_frame: str | None = None,
    min_time_of_flight_days: int | None = None,
    departure_step_days: float | None = None,
    arrival_step_days: float | None = None,
    departure_elements: MpcOrbitalElements | None = None,
    arrival_elements: MpcOrbitalElements | None = None,
    max_departure_delta_v_m_s: int | None = None,
    max_arrival_delta_v_m_s: int | None = None,
    max_time_of_flight_days: int | None = None,
) -> dict[str, Any]:
    """Return a Lambert transfer-window scan from ASTROX.

    The returned dictionary preserves every server field except the transport
    success envelope fields ``IsSuccess`` and ``Message``. The transfer route
    itself returns one result for each sampled departure/arrival time pair that
    it evaluates; it is not the single-case ``orbits.lambert_delta_v`` route.
    """
    payload: dict[str, Any] = {
        "DepartureCbName": _string(departure_body, parameter="departure_body"),
        "ArrivalCbName": _string(arrival_body, parameter="arrival_body"),
        "DepartureInterval": _interval(
            departure_start,
            departure_stop,
            parameter="departure_interval",
        ),
        "ArrivalInterval": _interval(
            arrival_start,
            arrival_stop,
            parameter="arrival_interval",
        ),
    }
    _include_if_supplied(
        payload,
        "SunFrameName",
        _optional_string(sun_frame, parameter="sun_frame"),
    )
    _include_if_supplied(
        payload,
        "MinTofDays",
        _optional_integer(
            min_time_of_flight_days,
            parameter="min_time_of_flight_days",
        ),
    )
    _include_if_supplied(
        payload,
        "DepartureStepDay",
        _optional_number(
            departure_step_days,
            parameter="departure_step_days",
        ),
    )
    _include_if_supplied(
        payload,
        "ArrivalStepDay",
        _optional_number(
            arrival_step_days,
            parameter="arrival_step_days",
        ),
    )
    _include_if_supplied(
        payload,
        "DepartureElements",
        _elements_to_wire(departure_elements, parameter="departure_elements"),
    )
    _include_if_supplied(
        payload,
        "ArrivalElements",
        _elements_to_wire(arrival_elements, parameter="arrival_elements"),
    )
    _include_if_supplied(
        payload,
        "MaxDepartureDV",
        _optional_integer(
            max_departure_delta_v_m_s,
            parameter="max_departure_delta_v_m_s",
        ),
    )
    _include_if_supplied(
        payload,
        "MaxArrivalDV",
        _optional_integer(
            max_arrival_delta_v_m_s,
            parameter="max_arrival_delta_v_m_s",
        ),
    )
    _include_if_supplied(
        payload,
        "MaxTofDays",
        _optional_integer(
            max_time_of_flight_days,
            parameter="max_time_of_flight_days",
        ),
    )
    return _without_status_fields(
        raw.post("/celestial/transfer", json=payload),
        endpoint="/celestial/transfer",
    )


def ephemeris(
    *,
    target_name: str,
    start: str | None = None,
    stop: str | None = None,
    observer_name: str | None = None,
    observer_frame: str | None = None,
    step_s: float | None = None,
) -> dict[str, Any]:
    """Return ASTROX ephemeris output for a target and optional time window."""
    payload: dict[str, Any] = {
        "TargetName": _string(target_name, parameter="target_name"),
    }
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
    return _without_status_fields(
        raw.post("/celestial/ephemeris", json=payload),
        endpoint="/celestial/ephemeris",
    )


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
    return _without_status_fields(
        raw.post("/celestial/CbAxesRotation", json=payload),
        endpoint="/celestial/CbAxesRotation",
    )


def mpc_ephemeris(
    *,
    target_name: str,
    observer_frame: str | None = None,
    start: str | None = None,
    stop: str | None = None,
    step_s: float | None = None,
    target_elements: MpcOrbitalElements | None = None,
) -> dict[str, Any]:
    """Return ASTROX minor-planet ephemeris output from its MPC-backed route.

    When ``target_elements`` is supplied, the server integrates those MPC
    orbital elements directly instead of resolving ``target_name`` through the
    MPC network query. ``step_s`` controls the output sampling cadence; zero
    requests the server's internal integration grid.
    """
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
    _include_if_supplied(
        payload,
        "Step",
        _optional_number(step_s, parameter="step_s"),
    )
    _include_if_supplied(
        payload,
        "TargetElements",
        _elements_to_wire(target_elements, parameter="target_elements"),
    )
    return _without_status_fields(
        raw.post("/celestial/mpc", json=payload),
        endpoint="/celestial/mpc",
    )
