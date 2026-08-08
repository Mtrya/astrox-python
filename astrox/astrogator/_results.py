"""Typed ASTROX Astrogator RunMCS response views."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from astrox import components
from astrox.orbits import CartesianState as OrbitsCartesianState


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


def _optional_string(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field=field)


def _boolean(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value


def _optional_boolean(value: Any, *, field: str) -> bool | None:
    if value is None:
        return None
    return _boolean(value, field=field)


def _integer(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    return value


def _number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    return float(value)


def _optional_number(value: Any, *, field: str) -> float | None:
    if value is None:
        return None
    return _number(value, field=field)


def _number_tuple(value: Any, *, field: str) -> tuple[float, ...]:
    return tuple(_number(item, field=field) for item in _sequence(value, field=field))


def _unknown_fields(payload: Mapping[str, Any], consumed: set[str]) -> Mapping[str, Any]:
    return {key: value for key, value in payload.items() if key not in consumed}


def _readonly_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    return dict(_mapping(value, field=field))


def _optional_number_tuple(payload: Mapping[str, Any], key: str) -> tuple[float, ...] | None:
    if key not in payload or payload[key] is None:
        return None
    return _number_tuple(payload[key], field=key)


@dataclass(frozen=True, kw_only=True)
class ReturnedKeplerianState:
    """Keplerian representation returned inside a RunMCS segment state."""

    element_type: str
    gravitational_parameter_m3_s2: float
    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    raan_deg: float
    argument_of_periapsis_deg: float
    mean_anomaly_deg: float
    true_anomaly_deg: float
    anomaly_type: str
    period_s: float
    unknown_fields: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class ReturnedSphericalState:
    """Spherical representation returned inside a RunMCS segment state."""

    right_ascension_deg: float
    declination_deg: float
    radius_m: float
    horizontal_fpa_deg: float
    velocity_azimuth_deg: float
    velocity_magnitude_m_s: float
    unknown_fields: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class SegmentState:
    """A complete state at a RunMCS segment boundary."""

    epoch: str
    coord_system_name: str
    cartesian: OrbitsCartesianState
    keplerian: ReturnedKeplerianState
    spherical: ReturnedSphericalState
    dry_mass_kg: float
    fuel_mass_kg: float
    coefficient_of_drag: float
    coefficient_of_srp: float
    drag_area_m2: float
    srp_area_m2: float
    geodetic_latitude_deg: float
    geodetic_longitude_deg: float
    geodetic_altitude_m: float
    geocentric_latitude_deg: float
    geocentric_longitude_deg: float
    unknown_fields: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class ManeuverInformation:
    """Raw-preserving maneuver summary shared by impulsive and finite results."""

    start: str
    stop: str
    duration_s: float
    fuel_used_kg: float
    delta_v_magnitude_m_s: float
    maneuver_attitude_name: str
    delta_v_inertial: tuple[float, ...]
    delta_v_vnc: tuple[float, ...]
    update_mass: bool | None
    estimated_fuel_used_kg: float | None
    delta_v_body: tuple[float, ...] | None
    quaternion: tuple[float, ...] | None
    unknown_fields: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class DifferentialCorrectorControlResult:
    """One returned differential-corrector control variable."""

    enable: bool
    name: str
    initial_value: str
    final_value: str
    correction: float
    last_update: float
    dimension: str
    max_step: float
    parent_name: str
    perturbation: float
    scaling_method: str
    scaling_value: float
    tolerance: float
    unit: str
    values: tuple[float, ...]
    unknown_fields: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class DifferentialCorrectorConstraintResult:
    """One returned differential-corrector target constraint."""

    enable: bool
    name: str
    desired_value: str
    parent_name: str
    current_value: str
    unit: str
    difference: float
    scaling_method: str
    scaling_value: float
    tolerance: float
    weight: float
    values: tuple[float, ...]
    unknown_fields: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class OperatorResult:
    """Base result view for a TargetSequence operator."""

    wire_type: str
    type_name: str
    name: str
    description: str | None
    user_comment: str | None
    unknown_fields: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class DifferentialCorrectorResult(OperatorResult):
    """Returned differential-corrector convergence and trace values."""

    converged: bool
    total_iterations: int
    control_parameters: tuple[DifferentialCorrectorControlResult, ...]
    results: tuple[DifferentialCorrectorConstraintResult, ...]


@dataclass(frozen=True, kw_only=True)
class SegmentResult:
    """Base result view shared by all RunMCS segment result branches."""

    wire_type: str | None
    type_name: str
    name: str
    description: str | None
    user_comment: str | None
    initial_state: SegmentState
    final_state: SegmentState
    duration_s: float
    scalar_results: Mapping[str, Any]
    unknown_fields: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class InitialStateResult(SegmentResult):
    """InitialState segment result."""


@dataclass(frozen=True, kw_only=True)
class PropagateResult(SegmentResult):
    """Propagate segment result."""

    stopped_on_maximum_duration: bool
    stopping_condition_name: str | None


@dataclass(frozen=True, kw_only=True)
class ManeuverImpulsiveResult(SegmentResult):
    """Impulsive maneuver segment result."""

    maneuver_information: ManeuverInformation


@dataclass(frozen=True, kw_only=True)
class ManeuverFiniteResult(SegmentResult):
    """Finite maneuver segment result."""

    maneuver_information: ManeuverInformation


@dataclass(frozen=True, kw_only=True)
class SequenceResult(SegmentResult):
    """Sequence segment result with recursively parsed child results."""

    segment_results: tuple[SegmentResultValue, ...]


@dataclass(frozen=True, kw_only=True)
class TargetSequenceResult(SegmentResult):
    """TargetSequence result with operator traces and child results."""

    operator_results: tuple[OperatorResult, ...]
    segment_results: tuple[SegmentResultValue, ...]


@dataclass(frozen=True, kw_only=True)
class FollowResult(SegmentResult):
    """Follow result; live responses use TypeName rather than a $type discriminator."""


SegmentResultValue: TypeAlias = (
    InitialStateResult
    | PropagateResult
    | ManeuverImpulsiveResult
    | ManeuverFiniteResult
    | SequenceResult
    | TargetSequenceResult
    | FollowResult
    | SegmentResult
)


@dataclass(frozen=True, kw_only=True)
class RunMCSResult:
    """Curated success-path result returned by :func:`run_mcs`."""

    is_success: bool
    message: str
    main_sequence_results: tuple[SegmentResultValue, ...]
    positions: components.CzmlPositions | None
    unknown_fields: Mapping[str, Any]


def _returned_keplerian_from_wire(value: Any) -> ReturnedKeplerianState:
    payload = _mapping(value, field="Keplerian")
    consumed = {
        "ElementType",
        "GravitationalParameter",
        "SemiMajorAxis",
        "Eccentricity",
        "Inclination",
        "RAAN",
        "ArgOfPeriapsis",
        "MeanAnomaly",
        "TrueAnomaly",
        "AnomalyType",
        "Period",
    }
    return ReturnedKeplerianState(
        element_type=_string(payload["ElementType"], field="ElementType"),
        gravitational_parameter_m3_s2=_number(payload["GravitationalParameter"], field="GravitationalParameter"),
        semi_major_axis_m=_number(payload["SemiMajorAxis"], field="SemiMajorAxis"),
        eccentricity=_number(payload["Eccentricity"], field="Eccentricity"),
        inclination_deg=_number(payload["Inclination"], field="Inclination"),
        raan_deg=_number(payload["RAAN"], field="RAAN"),
        argument_of_periapsis_deg=_number(payload["ArgOfPeriapsis"], field="ArgOfPeriapsis"),
        mean_anomaly_deg=_number(payload["MeanAnomaly"], field="MeanAnomaly"),
        true_anomaly_deg=_number(payload["TrueAnomaly"], field="TrueAnomaly"),
        anomaly_type=_string(payload["AnomalyType"], field="AnomalyType"),
        period_s=_number(payload["Period"], field="Period"),
        unknown_fields=_unknown_fields(payload, consumed),
    )


def _returned_spherical_from_wire(value: Any) -> ReturnedSphericalState:
    payload = _mapping(value, field="Spherical")
    consumed = {
        "RightAscension",
        "Declination",
        "RadiusMagnitude",
        "HorizFPA",
        "VelocityAzimuth",
        "VelocityMagnitude",
    }
    return ReturnedSphericalState(
        right_ascension_deg=_number(payload["RightAscension"], field="RightAscension"),
        declination_deg=_number(payload["Declination"], field="Declination"),
        radius_m=_number(payload["RadiusMagnitude"], field="RadiusMagnitude"),
        horizontal_fpa_deg=_number(payload["HorizFPA"], field="HorizFPA"),
        velocity_azimuth_deg=_number(payload["VelocityAzimuth"], field="VelocityAzimuth"),
        velocity_magnitude_m_s=_number(payload["VelocityMagnitude"], field="VelocityMagnitude"),
        unknown_fields=_unknown_fields(payload, consumed),
    )


def _segment_state_from_wire(value: Any) -> SegmentState:
    payload = _mapping(value, field="segment state")
    cartesian = _mapping(payload["Cartesian"], field="Cartesian")
    consumed = {
        "Epoch",
        "CoordSystemName",
        "Cartesian",
        "Keplerian",
        "Spherical",
        "DryMass",
        "FuelMass",
        "Cd",
        "Cr",
        "DragArea",
        "SRPArea",
        "Geodetic_Latitude",
        "Geodetic_Longitude",
        "Geodetic_Altitude",
        "Geocentric_Latitude",
        "Geocentric_Longitude",
    }
    return SegmentState(
        epoch=_string(payload["Epoch"], field="Epoch"),
        coord_system_name=_string(payload["CoordSystemName"], field="CoordSystemName"),
        cartesian=OrbitsCartesianState(
            x_m=_number(cartesian["X"], field="Cartesian.X"),
            y_m=_number(cartesian["Y"], field="Cartesian.Y"),
            z_m=_number(cartesian["Z"], field="Cartesian.Z"),
            vx_m_s=_number(cartesian["Vx"], field="Cartesian.Vx"),
            vy_m_s=_number(cartesian["Vy"], field="Cartesian.Vy"),
            vz_m_s=_number(cartesian["Vz"], field="Cartesian.Vz"),
        ),
        keplerian=_returned_keplerian_from_wire(payload["Keplerian"]),
        spherical=_returned_spherical_from_wire(payload["Spherical"]),
        dry_mass_kg=_number(payload["DryMass"], field="DryMass"),
        fuel_mass_kg=_number(payload["FuelMass"], field="FuelMass"),
        coefficient_of_drag=_number(payload["Cd"], field="Cd"),
        coefficient_of_srp=_number(payload["Cr"], field="Cr"),
        drag_area_m2=_number(payload["DragArea"], field="DragArea"),
        srp_area_m2=_number(payload["SRPArea"], field="SRPArea"),
        geodetic_latitude_deg=_number(payload["Geodetic_Latitude"], field="Geodetic_Latitude"),
        geodetic_longitude_deg=_number(payload["Geodetic_Longitude"], field="Geodetic_Longitude"),
        geodetic_altitude_m=_number(payload["Geodetic_Altitude"], field="Geodetic_Altitude"),
        geocentric_latitude_deg=_number(payload["Geocentric_Latitude"], field="Geocentric_Latitude"),
        geocentric_longitude_deg=_number(payload["Geocentric_Longitude"], field="Geocentric_Longitude"),
        unknown_fields=_unknown_fields(payload, consumed),
    )


def _maneuver_information_from_wire(value: Any) -> ManeuverInformation:
    payload = _mapping(value, field="ManeuverInformation")
    consumed = {
        "Start",
        "Stop",
        "Duration",
        "FuelUsed",
        "DeltaV_Mag",
        "ManeuverAttitudeName",
        "DeltaV_Inertial",
        "DeltaV_VNC",
        "UpdateMass",
        "EstimatedFuelUsed",
        "DeltaV_Body",
        "Quanternion",
    }
    return ManeuverInformation(
        start=_string(payload["Start"], field="Start"),
        stop=_string(payload["Stop"], field="Stop"),
        duration_s=_number(payload["Duration"], field="Duration"),
        fuel_used_kg=_number(payload["FuelUsed"], field="FuelUsed"),
        delta_v_magnitude_m_s=_number(payload["DeltaV_Mag"], field="DeltaV_Mag"),
        maneuver_attitude_name=_string(payload["ManeuverAttitudeName"], field="ManeuverAttitudeName"),
        delta_v_inertial=_number_tuple(payload["DeltaV_Inertial"], field="DeltaV_Inertial"),
        delta_v_vnc=_number_tuple(payload["DeltaV_VNC"], field="DeltaV_VNC"),
        update_mass=(
            _optional_boolean(payload["UpdateMass"], field="UpdateMass")
            if "UpdateMass" in payload
            else None
        ),
        estimated_fuel_used_kg=(
            _optional_number(payload["EstimatedFuelUsed"], field="EstimatedFuelUsed")
            if "EstimatedFuelUsed" in payload
            else None
        ),
        delta_v_body=_optional_number_tuple(payload, "DeltaV_Body"),
        quaternion=_optional_number_tuple(payload, "Quanternion"),
        unknown_fields=_unknown_fields(payload, consumed),
    )


def _control_result_from_wire(value: Any) -> DifferentialCorrectorControlResult:
    payload = _mapping(value, field="ControlParameters item")
    consumed = {
        "Enable",
        "Name",
        "InitialValue",
        "FinalValue",
        "Correction",
        "LastUpdate",
        "Dimension",
        "MaxStep",
        "ParentName",
        "Perturbation",
        "ScalingMethod",
        "ScalingValue",
        "Tolerance",
        "Unit",
        "Values",
    }
    return DifferentialCorrectorControlResult(
        enable=_boolean(payload["Enable"], field="Enable"),
        name=_string(payload["Name"], field="Name"),
        initial_value=_string(payload["InitialValue"], field="InitialValue"),
        final_value=_string(payload["FinalValue"], field="FinalValue"),
        correction=_number(payload["Correction"], field="Correction"),
        last_update=_number(payload["LastUpdate"], field="LastUpdate"),
        dimension=_string(payload["Dimension"], field="Dimension"),
        max_step=_number(payload["MaxStep"], field="MaxStep"),
        parent_name=_string(payload["ParentName"], field="ParentName"),
        perturbation=_number(payload["Perturbation"], field="Perturbation"),
        scaling_method=_string(payload["ScalingMethod"], field="ScalingMethod"),
        scaling_value=_number(payload["ScalingValue"], field="ScalingValue"),
        tolerance=_number(payload["Tolerance"], field="Tolerance"),
        unit=_string(payload["Unit"], field="Unit"),
        values=_number_tuple(payload["Values"], field="Values"),
        unknown_fields=_unknown_fields(payload, consumed),
    )


def _constraint_result_from_wire(value: Any) -> DifferentialCorrectorConstraintResult:
    payload = _mapping(value, field="operator Results item")
    consumed = {
        "Enable",
        "Name",
        "DesiredValue",
        "ParentName",
        "CurrentValue",
        "Unit",
        "Difference",
        "ScalingMethod",
        "ScalingValue",
        "Tolerance",
        "Weight",
        "Values",
    }
    return DifferentialCorrectorConstraintResult(
        enable=_boolean(payload["Enable"], field="Enable"),
        name=_string(payload["Name"], field="Name"),
        desired_value=_string(payload["DesiredValue"], field="DesiredValue"),
        parent_name=_string(payload["ParentName"], field="ParentName"),
        current_value=_string(payload["CurrentValue"], field="CurrentValue"),
        unit=_string(payload["Unit"], field="Unit"),
        difference=_number(payload["Difference"], field="Difference"),
        scaling_method=_string(payload["ScalingMethod"], field="ScalingMethod"),
        scaling_value=_number(payload["ScalingValue"], field="ScalingValue"),
        tolerance=_number(payload["Tolerance"], field="Tolerance"),
        weight=_number(payload["Weight"], field="Weight"),
        values=_number_tuple(payload["Values"], field="Values"),
        unknown_fields=_unknown_fields(payload, consumed),
    )


def _operator_result_from_wire(value: Any) -> OperatorResult:
    payload = _mapping(value, field="OperatorResults item")
    wire_type = _string(payload["$type"], field="$type")
    base_consumed = {"$type", "TypeName", "Name", "Description", "UserComment"}
    if wire_type != "DifferentialCorrectorResults":
        return OperatorResult(
            wire_type=wire_type,
            type_name=_string(payload["TypeName"], field="TypeName"),
            name=_string(payload["Name"], field="Name"),
            description=_optional_string(payload["Description"], field="Description"),
            user_comment=_optional_string(payload["UserComment"], field="UserComment"),
            unknown_fields=_unknown_fields(payload, base_consumed),
        )

    consumed = base_consumed | {"Converged", "TotalIterations", "ControlParameters", "Results"}
    return DifferentialCorrectorResult(
        wire_type=wire_type,
        type_name=_string(payload["TypeName"], field="TypeName"),
        name=_string(payload["Name"], field="Name"),
        description=_optional_string(payload["Description"], field="Description"),
        user_comment=_optional_string(payload["UserComment"], field="UserComment"),
        converged=_boolean(payload["Converged"], field="Converged"),
        total_iterations=_integer(payload["TotalIterations"], field="TotalIterations"),
        control_parameters=tuple(
            _control_result_from_wire(item)
            for item in _sequence(payload["ControlParameters"], field="ControlParameters")
        ),
        results=tuple(
            _constraint_result_from_wire(item)
            for item in _sequence(payload["Results"], field="Results")
        ),
        unknown_fields=_unknown_fields(payload, consumed),
    )


def _segment_base_values(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "wire_type": (
            _optional_string(payload["$type"], field="$type") if "$type" in payload else None
        ),
        "type_name": _string(payload["TypeName"], field="TypeName"),
        "name": _string(payload["Name"], field="Name"),
        "description": _optional_string(payload["Description"], field="Description"),
        "user_comment": _optional_string(payload["UserComment"], field="UserComment"),
        "initial_state": _segment_state_from_wire(payload["InitialState"]),
        "final_state": _segment_state_from_wire(payload["FinalState"]),
        "duration_s": _number(payload["DurationSec"], field="DurationSec"),
        "scalar_results": _readonly_mapping(payload["Results"], field="Results"),
    }


def _segment_result_from_wire(value: Any) -> SegmentResultValue:
    payload = _mapping(value, field="segment result")
    type_name = payload["TypeName"]
    wire_type = payload["$type"] if "$type" in payload else None
    base_consumed = {
        "$type",
        "TypeName",
        "Name",
        "Description",
        "UserComment",
        "InitialState",
        "FinalState",
        "DurationSec",
        "Results",
    }
    base_values = _segment_base_values(payload)

    if wire_type == "PropagateResult" or type_name == "Propagate":
        consumed = base_consumed | {"StoppedOnMaximumDuration", "StoppingConditionName"}
        return PropagateResult(
            **base_values,
            stopped_on_maximum_duration=_boolean(payload["StoppedOnMaximumDuration"], field="StoppedOnMaximumDuration"),
            stopping_condition_name=_optional_string(payload["StoppingConditionName"], field="StoppingConditionName"),
            unknown_fields=_unknown_fields(payload, consumed),
        )
    if wire_type == "ManeuverImpulsiveResult" or type_name == "ManeuverImpulsive":
        consumed = base_consumed | {"ManeuverInformation"}
        return ManeuverImpulsiveResult(
            **base_values,
            maneuver_information=_maneuver_information_from_wire(payload["ManeuverInformation"]),
            unknown_fields=_unknown_fields(payload, consumed),
        )
    if wire_type == "ManeuverFiniteResult" or type_name == "ManeuverFinite":
        consumed = base_consumed | {"ManeuverInformation"}
        return ManeuverFiniteResult(
            **base_values,
            maneuver_information=_maneuver_information_from_wire(payload["ManeuverInformation"]),
            unknown_fields=_unknown_fields(payload, consumed),
        )
    if wire_type == "SequenceResult" or type_name == "Sequence":
        consumed = base_consumed | {"SegmentResults"}
        return SequenceResult(
            **base_values,
            segment_results=tuple(
                _segment_result_from_wire(item)
                for item in _sequence(payload["SegmentResults"], field="SegmentResults")
            ),
            unknown_fields=_unknown_fields(payload, consumed),
        )
    if wire_type == "TargetSequenceResult" or type_name == "TargetSequence":
        consumed = base_consumed | {"OperatorResults", "SegmentResults"}
        return TargetSequenceResult(
            **base_values,
            operator_results=tuple(
                _operator_result_from_wire(item)
                for item in _sequence(payload["OperatorResults"], field="OperatorResults")
            ),
            segment_results=tuple(
                _segment_result_from_wire(item)
                for item in _sequence(payload["SegmentResults"], field="SegmentResults")
            ),
            unknown_fields=_unknown_fields(payload, consumed),
        )
    if type_name == "InitialState":
        return InitialStateResult(
            **base_values,
            unknown_fields=_unknown_fields(payload, base_consumed),
        )
    if type_name == "Follow":
        return FollowResult(
            **base_values,
            unknown_fields=_unknown_fields(payload, base_consumed),
        )
    return SegmentResult(
        **base_values,
        unknown_fields=_unknown_fields(payload, base_consumed),
    )


def _positions_from_wire(value: Any) -> components.CzmlPositions:
    payload = _mapping(value, field="Positions")
    positions = tuple(
        _czml_position_from_wire(item)
        for item in _sequence(payload["CzmlPositions"], field="CzmlPositions")
    )
    return components.CzmlPositions(
        central_body=_string(payload["CentralBody"], field="CentralBody"),
        positions=positions,
    )


def _czml_position_from_wire(value: Any) -> components.CzmlPosition:
    payload = _mapping(value, field="CzmlPositions item")
    return components.CzmlPosition(
        central_body=_string(payload["CentralBody"], field="CentralBody"),
        epoch=_string(payload["epoch"], field="epoch"),
        interpolation_algorithm=_string(payload["interpolationAlgorithm"], field="interpolationAlgorithm"),
        interpolation_degree=_integer(payload["interpolationDegree"], field="interpolationDegree"),
        reference_frame=_string(payload["referenceFrame"], field="referenceFrame"),
        interval=(
            _optional_string(payload["interval"], field="interval")
            if "interval" in payload
            else None
        ),
        cartesian=_optional_number_tuple(payload, "cartesian"),
        cartesian_velocity=_optional_number_tuple(payload, "cartesianVelocity"),
    )


def run_mcs_result_from_wire(value: Any) -> RunMCSResult:
    """Build a curated RunMCS result from a successful ASTROX response."""

    payload = _mapping(value, field="RunMCS response")
    consumed = {"IsSuccess", "Message", "MainSequenceResults", "Positions"}
    positions_value = payload["Positions"] if "Positions" in payload else None
    positions = _positions_from_wire(positions_value) if positions_value is not None else None
    return RunMCSResult(
        is_success=_boolean(payload["IsSuccess"], field="IsSuccess"),
        message=_string(payload["Message"], field="Message"),
        main_sequence_results=tuple(
            _segment_result_from_wire(item)
            for item in _sequence(payload["MainSequenceResults"], field="MainSequenceResults")
        ),
        positions=positions,
        unknown_fields=_unknown_fields(payload, consumed),
    )


__all__ = [
    "DifferentialCorrectorConstraintResult",
    "DifferentialCorrectorControlResult",
    "DifferentialCorrectorResult",
    "FollowResult",
    "InitialStateResult",
    "ManeuverFiniteResult",
    "ManeuverImpulsiveResult",
    "ManeuverInformation",
    "OperatorResult",
    "PropagateResult",
    "ReturnedKeplerianState",
    "ReturnedSphericalState",
    "RunMCSResult",
    "SegmentResult",
    "SegmentResultValue",
    "SegmentState",
    "SequenceResult",
    "TargetSequenceResult",
    "run_mcs_result_from_wire",
]
