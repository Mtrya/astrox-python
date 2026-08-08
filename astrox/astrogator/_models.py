"""Typed ASTROX Astrogator RunMCS request fragments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from astrox.propagator import HpopConfig

MU_EARTH_M3_S2 = 3.986004415e14


def _include_if_supplied(payload: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        payload[key] = value


def _typed_tuple(
    values: Sequence[Any] | None,
    expected_type: type | tuple[type, ...],
    *,
    parameter: str,
) -> tuple[Any, ...] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{parameter} must be a sequence of typed values")
    items = tuple(values)
    if not all(isinstance(item, expected_type) for item in items):
        raise TypeError(f"{parameter} must be a sequence of typed values")
    return items


def _named_wire(
    *,
    type_name: str,
    name: str,
    description: str | None,
    user_comment: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"$type": type_name, "Name": name}
    _include_if_supplied(payload, "Description", description)
    _include_if_supplied(payload, "UserComment", user_comment)
    return payload


@dataclass(frozen=True, kw_only=True)
class KeplerianState:
    """ASTROX Keplerian initial-state element fragment."""

    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    raan_deg: float
    argument_of_periapsis_deg: float
    gravitational_parameter_m3_s2: float
    anomaly_type: str = "True"
    true_anomaly_deg: float | None = None
    mean_anomaly_deg: float | None = None
    element_type: str = "Osculating"

    def to_wire(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "$type": "Keplerian",
            "ElementType": self.element_type,
            "GravitationalParameter": self.gravitational_parameter_m3_s2,
            "SemiMajorAxis": self.semi_major_axis_m,
            "Eccentricity": self.eccentricity,
            "Inclination": self.inclination_deg,
            "RAAN": self.raan_deg,
            "ArgOfPeriapsis": self.argument_of_periapsis_deg,
            "AnomalyType": self.anomaly_type,
        }
        _include_if_supplied(payload, "TrueAnomaly", self.true_anomaly_deg)
        _include_if_supplied(payload, "MeanAnomaly", self.mean_anomaly_deg)
        return payload


@dataclass(frozen=True, kw_only=True)
class CartesianState:
    """ASTROX Cartesian initial-state element fragment."""

    x_m: float
    y_m: float
    z_m: float
    vx_m_s: float
    vy_m_s: float
    vz_m_s: float

    def to_wire(self) -> dict[str, Any]:
        return {
            "$type": "Cartesian",
            "X": self.x_m,
            "Y": self.y_m,
            "Z": self.z_m,
            "Vx": self.vx_m_s,
            "Vy": self.vy_m_s,
            "Vz": self.vz_m_s,
        }


@dataclass(frozen=True, kw_only=True)
class SphericalState:
    """ASTROX spherical initial-state element fragment."""

    right_ascension_deg: float
    declination_deg: float
    radius_m: float
    horizontal_fpa_deg: float
    velocity_azimuth_deg: float
    velocity_magnitude_m_s: float

    def to_wire(self) -> dict[str, Any]:
        return {
            "$type": "Spherical",
            "RightAscension": self.right_ascension_deg,
            "Declination": self.declination_deg,
            "RadiusMagnitude": self.radius_m,
            "HorizFPA": self.horizontal_fpa_deg,
            "VelocityAzimuth": self.velocity_azimuth_deg,
            "VelocityMagnitude": self.velocity_magnitude_m_s,
        }


@dataclass(frozen=True, kw_only=True)
class TargetVectorOutState:
    """ASTROX hyperbolic outgoing-asymptote initial-state fragment."""

    radius_of_periapsis_km: float
    c3_km2_s2: float
    asymptote_ra_deg: float
    asymptote_dec_deg: float
    gravitational_parameter_m3_s2: float
    velocity_azimuth_at_periapsis_deg: float = 0.0
    true_anomaly_deg: float = 0.0

    def to_wire(self) -> dict[str, Any]:
        return {
            "$type": "TargetVecOut",
            "GravitationalParameter": self.gravitational_parameter_m3_s2,
            "RadiusOfPeriapsis": self.radius_of_periapsis_km,
            "C3": self.c3_km2_s2,
            "AsympRA": self.asymptote_ra_deg,
            "AsympDec": self.asymptote_dec_deg,
            "VelAzAtPeriapsis": self.velocity_azimuth_at_periapsis_deg,
            "TrueAnomaly": self.true_anomaly_deg,
        }


InitialStateElement: TypeAlias = KeplerianState | CartesianState | SphericalState | TargetVectorOutState


def keplerian_state(
    *,
    semi_major_axis_m: float,
    eccentricity: float,
    inclination_deg: float,
    raan_deg: float,
    argument_of_periapsis_deg: float,
    gravitational_parameter_m3_s2: float,
    anomaly_type: str = "True",
    true_anomaly_deg: float | None = None,
    mean_anomaly_deg: float | None = None,
    element_type: str = "Osculating",
) -> KeplerianState:
    return KeplerianState(
        semi_major_axis_m=semi_major_axis_m,
        eccentricity=eccentricity,
        inclination_deg=inclination_deg,
        raan_deg=raan_deg,
        argument_of_periapsis_deg=argument_of_periapsis_deg,
        gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        anomaly_type=anomaly_type,
        true_anomaly_deg=true_anomaly_deg,
        mean_anomaly_deg=mean_anomaly_deg,
        element_type=element_type,
    )


def cartesian_state(
    *,
    x_m: float,
    y_m: float,
    z_m: float,
    vx_m_s: float,
    vy_m_s: float,
    vz_m_s: float,
) -> CartesianState:
    return CartesianState(x_m=x_m, y_m=y_m, z_m=z_m, vx_m_s=vx_m_s, vy_m_s=vy_m_s, vz_m_s=vz_m_s)


def spherical_state(
    *,
    right_ascension_deg: float,
    declination_deg: float,
    radius_m: float,
    horizontal_fpa_deg: float,
    velocity_azimuth_deg: float,
    velocity_magnitude_m_s: float,
) -> SphericalState:
    return SphericalState(
        right_ascension_deg=right_ascension_deg,
        declination_deg=declination_deg,
        radius_m=radius_m,
        horizontal_fpa_deg=horizontal_fpa_deg,
        velocity_azimuth_deg=velocity_azimuth_deg,
        velocity_magnitude_m_s=velocity_magnitude_m_s,
    )


def target_vector_out_state(
    *,
    radius_of_periapsis_km: float,
    c3_km2_s2: float,
    asymptote_ra_deg: float,
    asymptote_dec_deg: float,
    gravitational_parameter_m3_s2: float,
    velocity_azimuth_at_periapsis_deg: float = 0.0,
    true_anomaly_deg: float = 0.0,
) -> TargetVectorOutState:
    return TargetVectorOutState(
        radius_of_periapsis_km=radius_of_periapsis_km,
        c3_km2_s2=c3_km2_s2,
        asymptote_ra_deg=asymptote_ra_deg,
        asymptote_dec_deg=asymptote_dec_deg,
        gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        velocity_azimuth_at_periapsis_deg=velocity_azimuth_at_periapsis_deg,
        true_anomaly_deg=true_anomaly_deg,
    )


@dataclass(frozen=True, kw_only=True)
class DurationStop:
    name: str
    trip_s: float
    tolerance_s: float = 1.0e-6
    active: bool = True

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Duration", "Name": self.name, "Trip": self.trip_s,
                "Tolerance": self.tolerance_s, "Active": self.active}


@dataclass(frozen=True, kw_only=True)
class EpochStop:
    name: str
    trip_utc: str
    active: bool = True

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Epoch", "Name": self.name, "Trip": self.trip_utc, "Active": self.active}


@dataclass(frozen=True, kw_only=True)
class PeriapsisStop:
    name: str
    gravitational_parameter_m3_s2: float
    central_body_name: str = "Earth"
    repeat_count: int = 1
    tolerance: float = 1.0e-6
    active: bool = True

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Periapsis", "Name": self.name,
                "CentralBodyName": self.central_body_name,
                "Mu": self.gravitational_parameter_m3_s2,
                "RepeatCount": self.repeat_count, "Tolerance": self.tolerance,
                "Active": self.active}


@dataclass(frozen=True, kw_only=True)
class ApoapsisStop:
    name: str
    gravitational_parameter_m3_s2: float
    central_body_name: str = "Earth"
    repeat_count: int = 1
    tolerance: float = 1.0e-6
    active: bool = True

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Apoapsis", "Name": self.name,
                "CentralBodyName": self.central_body_name,
                "Mu": self.gravitational_parameter_m3_s2,
                "RepeatCount": self.repeat_count, "Tolerance": self.tolerance,
                "Active": self.active}


StoppingCondition: TypeAlias = DurationStop | EpochStop | PeriapsisStop | ApoapsisStop


def duration_stop(name: str, trip_s: float, *, tolerance_s: float = 1.0e-6, active: bool = True) -> DurationStop:
    return DurationStop(name=name, trip_s=trip_s, tolerance_s=tolerance_s, active=active)


def epoch_stop(name: str, trip_utc: str, *, active: bool = True) -> EpochStop:
    return EpochStop(name=name, trip_utc=trip_utc, active=active)


def periapsis_stop(
    name: str,
    *,
    gravitational_parameter_m3_s2: float,
    central_body_name: str = "Earth",
    repeat_count: int = 1,
    tolerance: float = 1.0e-6,
    active: bool = True,
) -> PeriapsisStop:
    return PeriapsisStop(name=name, gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
                         central_body_name=central_body_name, repeat_count=repeat_count,
                         tolerance=tolerance, active=active)


def apoapsis_stop(
    name: str,
    *,
    gravitational_parameter_m3_s2: float,
    central_body_name: str = "Earth",
    repeat_count: int = 1,
    tolerance: float = 1.0e-6,
    active: bool = True,
) -> ApoapsisStop:
    return ApoapsisStop(name=name, gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
                        central_body_name=central_body_name, repeat_count=repeat_count,
                        tolerance=tolerance, active=active)


@dataclass(frozen=True, kw_only=True)
class DurationScalar:
    name: str

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Duration", "Name": self.name}


@dataclass(frozen=True, kw_only=True)
class EpochScalar:
    name: str

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Epoch", "Name": self.name}


@dataclass(frozen=True, kw_only=True)
class KeplerianScalar:
    name: str
    component_name: str
    gravitational_parameter_m3_s2: float
    coord_system_name: str
    element_type: str = "Osculating"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "KeplerianElement", "Name": self.name,
                "ComponentName": self.component_name,
                "Mu": self.gravitational_parameter_m3_s2,
                "CoordSystemName": self.coord_system_name,
                "ElementType": self.element_type}


@dataclass(frozen=True, kw_only=True)
class ModifiedKeplerianScalar:
    name: str
    component_name: str
    gravitational_parameter_m3_s2: float
    coord_system_name: str

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "ModifiedKeplerianElement", "Name": self.name,
                "ComponentName": self.component_name,
                "Mu": self.gravitational_parameter_m3_s2,
                "CoordSystemName": self.coord_system_name}


@dataclass(frozen=True, kw_only=True)
class CartographicScalar:
    name: str
    component_name: str
    central_body_name: str

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Cartographic", "Name": self.name,
                "ComponentName": self.component_name,
                "CentralBodyName": self.central_body_name}


@dataclass(frozen=True, kw_only=True)
class PointScalar:
    name: str
    component_name: str
    coord_system_name: str

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "PointElement", "Name": self.name,
                "ComponentName": self.component_name,
                "CoordSystemName": self.coord_system_name}


@dataclass(frozen=True, kw_only=True)
class SphericalScalar:
    name: str
    component_name: str
    coord_system_name: str

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "SphericalElement", "Name": self.name,
                "ComponentName": self.component_name,
                "CoordSystemName": self.coord_system_name}


@dataclass(frozen=True, kw_only=True)
class DeltaSphericalScalar:
    name: str
    component_name: str
    central_body_name: str
    parent_central_body_name: str

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "DeltaSpherical", "Name": self.name,
                "ComponentName": self.component_name,
                "CentralBodyName": self.central_body_name,
                "ParentCbName": self.parent_central_body_name}


@dataclass(frozen=True, kw_only=True)
class BPlaneScalar:
    name: str
    component_name: str
    gravitational_parameter_m3_s2: float
    central_body_name: str

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "BPlane", "Name": self.name,
                "ComponentName": self.component_name,
                "Mu": self.gravitational_parameter_m3_s2,
                "CentralBodyName": self.central_body_name}


@dataclass(frozen=True, kw_only=True)
class RelativeScalar:
    name: str
    calc_object: "CalcScalar"
    reference_name: str | None = None

    def to_wire(self) -> dict[str, Any]:
        payload = {"$type": "Relative", "Name": self.name,
                   "CalcObject": self.calc_object.to_wire()}
        _include_if_supplied(payload, "ReferenceName", self.reference_name)
        return payload


CalcScalar: TypeAlias = (
    DurationScalar | EpochScalar | KeplerianScalar | ModifiedKeplerianScalar
    | CartographicScalar | PointScalar | SphericalScalar | DeltaSphericalScalar
    | BPlaneScalar | RelativeScalar
)


def duration_scalar(name: str) -> DurationScalar:
    return DurationScalar(name=name)


def epoch_scalar(name: str) -> EpochScalar:
    return EpochScalar(name=name)


def keplerian_scalar(name: str, component_name: str, *, gravitational_parameter_m3_s2: float, coord_system_name: str, element_type: str = "Osculating") -> KeplerianScalar:
    return KeplerianScalar(name=name, component_name=component_name,
                           gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
                           coord_system_name=coord_system_name, element_type=element_type)


def modified_keplerian_scalar(name: str, component_name: str, *, gravitational_parameter_m3_s2: float, coord_system_name: str) -> ModifiedKeplerianScalar:
    return ModifiedKeplerianScalar(name=name, component_name=component_name,
                                   gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
                                   coord_system_name=coord_system_name)


def cartographic_scalar(name: str, component_name: str, *, central_body_name: str) -> CartographicScalar:
    return CartographicScalar(name=name, component_name=component_name, central_body_name=central_body_name)


def point_scalar(name: str, component_name: str, *, coord_system_name: str) -> PointScalar:
    return PointScalar(name=name, component_name=component_name, coord_system_name=coord_system_name)


def spherical_scalar(name: str, component_name: str, *, coord_system_name: str) -> SphericalScalar:
    return SphericalScalar(name=name, component_name=component_name, coord_system_name=coord_system_name)


def delta_spherical_scalar(name: str, component_name: str, *, central_body_name: str, parent_central_body_name: str) -> DeltaSphericalScalar:
    return DeltaSphericalScalar(name=name, component_name=component_name,
                                central_body_name=central_body_name,
                                parent_central_body_name=parent_central_body_name)


def b_plane_scalar(name: str, component_name: str, *, gravitational_parameter_m3_s2: float, central_body_name: str) -> BPlaneScalar:
    return BPlaneScalar(name=name, component_name=component_name,
                        gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
                        central_body_name=central_body_name)


def relative_scalar(name: str, calc_object: CalcScalar, *, reference_name: str | None = None) -> RelativeScalar:
    if not isinstance(calc_object, _CALC_SCALAR_TYPES):
        raise TypeError("calc_object must be an astrogator CalcScalar value")
    return RelativeScalar(name=name, calc_object=calc_object, reference_name=reference_name)


@dataclass(frozen=True, kw_only=True)
class ImpulsiveVelocityVector:
    delta_v_m_s: float

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "VelocityVector", "DeltaVMagnitude": self.delta_v_m_s}


@dataclass(frozen=True, kw_only=True)
class ImpulsiveAntiVelocityVector:
    delta_v_m_s: float

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "AntiVelocityVector", "DeltaVMagnitude": self.delta_v_m_s}


@dataclass(frozen=True, kw_only=True)
class ImpulsiveThrustVectorCartesian:
    x_m_s: float
    y_m_s: float
    z_m_s: float
    thrust_axes_name: str = "VNC(Earth)"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "ThrustVector", "CoordType": "Cartesian",
                "ThrustAxesName": self.thrust_axes_name, "X": self.x_m_s,
                "Y": self.y_m_s, "Z": self.z_m_s}


@dataclass(frozen=True, kw_only=True)
class ImpulsiveThrustVectorSpherical:
    azimuth_deg: float
    elevation_deg: float
    magnitude_m_s: float
    thrust_axes_name: str = "VNC(Earth)"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "ThrustVector", "CoordType": "Spherical",
                "ThrustAxesName": self.thrust_axes_name, "Azimuth": self.azimuth_deg,
                "Elevation": self.elevation_deg, "Magnitude": self.magnitude_m_s}


@dataclass(frozen=True, kw_only=True)
class ImpulsiveAttitudeQuaternion:
    delta_v_m_s: float
    qx: float = 0.0
    qy: float = 0.0
    qz: float = 0.0
    qs: float = 1.0
    reference_axes_name: str = "VNC(Earth)"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Attitude", "DeltaVMagnitude": self.delta_v_m_s,
                "CoordType": "Quaternion", "RefAxesName": self.reference_axes_name,
                "QX": self.qx, "QY": self.qy, "QZ": self.qz, "QS": self.qs}


@dataclass(frozen=True, kw_only=True)
class ImpulsiveAttitudeEuler:
    delta_v_m_s: float
    a_deg: float
    b_deg: float
    c_deg: float
    sequence: str = "313"
    reference_axes_name: str = "VNC(Earth)"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Attitude", "DeltaVMagnitude": self.delta_v_m_s,
                "CoordType": "EulerAngles", "RefAxesName": self.reference_axes_name,
                "A": self.a_deg, "B": self.b_deg, "C": self.c_deg,
                "Sequence": self.sequence}


@dataclass(frozen=True, kw_only=True)
class FiniteVelocityVector:
    attitude_update: str = "DuringBurn"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "VelocityVector", "AttitudeUpdate": self.attitude_update}


@dataclass(frozen=True, kw_only=True)
class FiniteAntiVelocityVector:
    attitude_update: str = "DuringBurn"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "AntiVelocityVector", "AttitudeUpdate": self.attitude_update}


@dataclass(frozen=True, kw_only=True)
class FiniteThrustVectorCartesian:
    x: float
    y: float
    z: float
    thrust_axes_name: str = "VNC(Earth)"
    attitude_update: str = "DuringBurn"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "ThrustVector", "AttitudeUpdate": self.attitude_update,
                "CoordType": "Cartesian", "ThrustAxesName": self.thrust_axes_name,
                "X": self.x, "Y": self.y, "Z": self.z}


@dataclass(frozen=True, kw_only=True)
class FiniteThrustVectorSpherical:
    azimuth_deg: float
    elevation_deg: float
    magnitude: float
    thrust_axes_name: str = "VNC(Earth)"
    attitude_update: str = "DuringBurn"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "ThrustVector", "AttitudeUpdate": self.attitude_update,
                "CoordType": "Spherical", "ThrustAxesName": self.thrust_axes_name,
                "Azimuth": self.azimuth_deg, "Elevation": self.elevation_deg,
                "Magnitude": self.magnitude}


@dataclass(frozen=True, kw_only=True)
class FiniteAttitudeQuaternion:
    qx: float = 0.0
    qy: float = 0.0
    qz: float = 0.0
    qs: float = 1.0
    reference_axes_name: str = "VNC(Earth)"
    attitude_update: str = "DuringBurn"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Attitude", "AttitudeUpdate": self.attitude_update,
                "CoordType": "Quaternion", "RefAxesName": self.reference_axes_name,
                "QX": self.qx, "QY": self.qy, "QZ": self.qz, "QS": self.qs}


@dataclass(frozen=True, kw_only=True)
class FiniteAttitudeEuler:
    a_deg: float
    b_deg: float
    c_deg: float
    sequence: str = "313"
    reference_axes_name: str = "VNC(Earth)"
    attitude_update: str = "DuringBurn"

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "Attitude", "AttitudeUpdate": self.attitude_update,
                "CoordType": "EulerAngles", "RefAxesName": self.reference_axes_name,
                "A": self.a_deg, "B": self.b_deg, "C": self.c_deg,
                "Sequence": self.sequence}


ImpulsiveAttitudeControl: TypeAlias = (
    ImpulsiveVelocityVector | ImpulsiveAntiVelocityVector
    | ImpulsiveThrustVectorCartesian | ImpulsiveThrustVectorSpherical
    | ImpulsiveAttitudeQuaternion | ImpulsiveAttitudeEuler
)
FiniteAttitudeControl: TypeAlias = (
    FiniteVelocityVector | FiniteAntiVelocityVector
    | FiniteThrustVectorCartesian | FiniteThrustVectorSpherical
    | FiniteAttitudeQuaternion | FiniteAttitudeEuler
)


def impulsive_velocity_vector(delta_v_m_s: float) -> ImpulsiveVelocityVector:
    return ImpulsiveVelocityVector(delta_v_m_s=delta_v_m_s)


def impulsive_anti_velocity_vector(delta_v_m_s: float) -> ImpulsiveAntiVelocityVector:
    return ImpulsiveAntiVelocityVector(delta_v_m_s=delta_v_m_s)


def impulsive_thrust_vector_cartesian(x_m_s: float, y_m_s: float, z_m_s: float, *, thrust_axes_name: str = "VNC(Earth)") -> ImpulsiveThrustVectorCartesian:
    return ImpulsiveThrustVectorCartesian(x_m_s=x_m_s, y_m_s=y_m_s, z_m_s=z_m_s, thrust_axes_name=thrust_axes_name)


def impulsive_thrust_vector_spherical(azimuth_deg: float, elevation_deg: float, magnitude_m_s: float, *, thrust_axes_name: str = "VNC(Earth)") -> ImpulsiveThrustVectorSpherical:
    return ImpulsiveThrustVectorSpherical(azimuth_deg=azimuth_deg, elevation_deg=elevation_deg,
                                          magnitude_m_s=magnitude_m_s, thrust_axes_name=thrust_axes_name)


def impulsive_attitude_quaternion(delta_v_m_s: float, *, qx: float = 0.0, qy: float = 0.0, qz: float = 0.0, qs: float = 1.0, reference_axes_name: str = "VNC(Earth)") -> ImpulsiveAttitudeQuaternion:
    return ImpulsiveAttitudeQuaternion(delta_v_m_s=delta_v_m_s, qx=qx, qy=qy, qz=qz, qs=qs, reference_axes_name=reference_axes_name)


def impulsive_attitude_euler(delta_v_m_s: float, a_deg: float, b_deg: float, c_deg: float, *, sequence: str = "313", reference_axes_name: str = "VNC(Earth)") -> ImpulsiveAttitudeEuler:
    return ImpulsiveAttitudeEuler(delta_v_m_s=delta_v_m_s, a_deg=a_deg, b_deg=b_deg, c_deg=c_deg,
                                  sequence=sequence, reference_axes_name=reference_axes_name)


def finite_velocity_vector(*, attitude_update: str = "DuringBurn") -> FiniteVelocityVector:
    return FiniteVelocityVector(attitude_update=attitude_update)


def finite_anti_velocity_vector(*, attitude_update: str = "DuringBurn") -> FiniteAntiVelocityVector:
    return FiniteAntiVelocityVector(attitude_update=attitude_update)


def finite_thrust_vector_cartesian(x: float, y: float, z: float, *, thrust_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteThrustVectorCartesian:
    return FiniteThrustVectorCartesian(x=x, y=y, z=z,
                                       thrust_axes_name=thrust_axes_name, attitude_update=attitude_update)


def finite_thrust_vector_spherical(azimuth_deg: float, elevation_deg: float, magnitude: float, *, thrust_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteThrustVectorSpherical:
    return FiniteThrustVectorSpherical(azimuth_deg=azimuth_deg, elevation_deg=elevation_deg,
                                       magnitude=magnitude, thrust_axes_name=thrust_axes_name,
                                       attitude_update=attitude_update)


def finite_attitude_quaternion(*, qx: float = 0.0, qy: float = 0.0, qz: float = 0.0, qs: float = 1.0, reference_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteAttitudeQuaternion:
    return FiniteAttitudeQuaternion(qx=qx, qy=qy, qz=qz, qs=qs,
                                    reference_axes_name=reference_axes_name, attitude_update=attitude_update)


def finite_attitude_euler(a_deg: float, b_deg: float, c_deg: float, *, sequence: str = "313", reference_axes_name: str = "VNC(Earth)", attitude_update: str = "DuringBurn") -> FiniteAttitudeEuler:
    return FiniteAttitudeEuler(a_deg=a_deg, b_deg=b_deg, c_deg=c_deg, sequence=sequence,
                               reference_axes_name=reference_axes_name, attitude_update=attitude_update)


@dataclass(frozen=True, kw_only=True)
class EngineConstant:
    name: str
    thrust_n: float
    isp_s: float
    gravitational_acceleration_m_s2: float

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "EngineConstant", "Name": self.name,
                "Thrust": self.thrust_n, "Isp": self.isp_s,
                "g": self.gravitational_acceleration_m_s2}


def constant_engine(*, name: str, thrust_n: float, isp_s: float, gravitational_acceleration_m_s2: float = 9.80665) -> EngineConstant:
    return EngineConstant(name=name, thrust_n=thrust_n, isp_s=isp_s,
                          gravitational_acceleration_m_s2=gravitational_acceleration_m_s2)


@dataclass(frozen=True, kw_only=True)
class DifferentialCorrectorControl:
    name: str
    parent_name: str
    initial_value: float | str
    perturbation: float = 1.0
    max_step: float = 600.0
    tolerance: float = 1.0e-4
    enable: bool = True

    def to_wire(self) -> dict[str, Any]:
        return {"Enable": self.enable, "Name": self.name,
                "ParentName": self.parent_name, "InitialValue": str(self.initial_value),
                "Perturbation": self.perturbation, "MaxStep": self.max_step,
                "Tolerance": self.tolerance}


@dataclass(frozen=True, kw_only=True)
class DifferentialCorrectorConstraint:
    name: str
    parent_name: str
    desired_value: float | str
    tolerance: float = 0.1
    enable: bool = True

    def to_wire(self) -> dict[str, Any]:
        return {"Enable": self.enable, "Name": self.name,
                "DesiredValue": str(self.desired_value), "ParentName": self.parent_name,
                "Tolerance": self.tolerance}


@dataclass(frozen=True, kw_only=True)
class DifferentialCorrector:
    name: str
    controls: tuple[DifferentialCorrectorControl, ...]
    results: tuple[DifferentialCorrectorConstraint, ...]
    maximum_iterations: int = 50
    active: bool = True

    def to_wire(self) -> dict[str, Any]:
        return {"$type": "DifferentialCorrector", "Name": self.name,
                "Active": self.active, "MaximumIterations": self.maximum_iterations,
                "ControlParameters": [item.to_wire() for item in self.controls],
                "Results": [item.to_wire() for item in self.results]}


Profile: TypeAlias = DifferentialCorrector


def differential_corrector_control(name: str, initial_value: float | str, *, parent_name: str, perturbation: float = 1.0, max_step: float = 600.0, tolerance: float = 1.0e-4, enable: bool = True) -> DifferentialCorrectorControl:
    return DifferentialCorrectorControl(name=name, parent_name=parent_name, initial_value=initial_value,
                                        perturbation=perturbation, max_step=max_step,
                                        tolerance=tolerance, enable=enable)


def differential_corrector_constraint(name: str, desired_value: float | str, *, parent_name: str, tolerance: float = 0.1, enable: bool = True) -> DifferentialCorrectorConstraint:
    return DifferentialCorrectorConstraint(name=name, parent_name=parent_name,
                                           desired_value=desired_value, tolerance=tolerance,
                                           enable=enable)


def differential_corrector(name: str, *, controls: Sequence[DifferentialCorrectorControl], results: Sequence[DifferentialCorrectorConstraint], maximum_iterations: int = 50, active: bool = True) -> DifferentialCorrector:
    controls_tuple = _typed_tuple(controls, DifferentialCorrectorControl, parameter="controls")
    results_tuple = _typed_tuple(results, DifferentialCorrectorConstraint, parameter="results")
    return DifferentialCorrector(name=name, controls=controls_tuple or (), results=results_tuple or (),
                                 maximum_iterations=maximum_iterations, active=active)


@dataclass(frozen=True, kw_only=True)
class _SegmentBase:
    name: str
    description: str | None = None
    user_comment: str | None = None
    results: tuple[CalcScalar, ...] | None = None

    def _wire(self, type_name: str) -> dict[str, Any]:
        payload = _named_wire(type_name=type_name, name=self.name,
                              description=self.description, user_comment=self.user_comment)
        if self.results is not None:
            payload["Results"] = [item.to_wire() for item in self.results]
        return payload


@dataclass(frozen=True, kw_only=True)
class InitialStateSegment(_SegmentBase):
    state: InitialStateElement
    epoch: str
    coord_system_name: str = "Earth Inertial"
    dry_mass_kg: float = 500.0
    fuel_mass_kg: float = 500.0
    coefficient_of_drag: float | None = None
    coefficient_of_srp: float | None = None
    drag_area_m2: float | None = None
    srp_area_m2: float | None = None

    def to_wire(self) -> dict[str, Any]:
        payload = self._wire("InitialState")
        payload["InitialState"] = {
            "Epoch": self.epoch,
            "CoordSystemName": self.coord_system_name,
            "Element": self.state.to_wire(),
            "DryMass": self.dry_mass_kg,
            "FuelMass": self.fuel_mass_kg,
        }
        _include_if_supplied(payload["InitialState"], "Cd", self.coefficient_of_drag)
        _include_if_supplied(payload["InitialState"], "Cr", self.coefficient_of_srp)
        _include_if_supplied(payload["InitialState"], "DragArea", self.drag_area_m2)
        _include_if_supplied(payload["InitialState"], "SRPArea", self.srp_area_m2)
        return payload


@dataclass(frozen=True, kw_only=True)
class PropagateSegment(_SegmentBase):
    propagator_name: str
    stop_conditions: tuple[StoppingCondition, ...]
    variable_names: str | None = None
    max_propagation_time_s: float | None = None

    def to_wire(self) -> dict[str, Any]:
        payload = self._wire("Propagate")
        payload["PropagatorName"] = self.propagator_name
        payload["StopConditions"] = [item.to_wire() for item in self.stop_conditions]
        _include_if_supplied(payload, "VariableNames", self.variable_names)
        _include_if_supplied(payload, "MaxPropagationTime", self.max_propagation_time_s)
        return payload


@dataclass(frozen=True, kw_only=True)
class ImpulsiveManeuverSegment(_SegmentBase):
    attitude_control: ImpulsiveAttitudeControl
    propulsion_method_value: str
    update_mass: bool = False

    def to_wire(self) -> dict[str, Any]:
        payload = self._wire("ManeuverImpulsive")
        payload["AttitudeControl"] = self.attitude_control.to_wire()
        payload["PropulsionMethodValue"] = self.propulsion_method_value
        payload["UpdateMass"] = self.update_mass
        return payload


@dataclass(frozen=True, kw_only=True)
class FiniteManeuverSegment(_SegmentBase):
    attitude_control: FiniteAttitudeControl
    propagator_name: str
    stop_conditions: tuple[StoppingCondition, ...]
    propulsion_method_value: str
    thrust_efficiency: float = 1.0

    def to_wire(self) -> dict[str, Any]:
        payload = self._wire("ManeuverFinite")
        payload["AttitudeControl"] = self.attitude_control.to_wire()
        payload["PropagatorName"] = self.propagator_name
        payload["StopConditions"] = [item.to_wire() for item in self.stop_conditions]
        payload["PropulsionMethodValue"] = self.propulsion_method_value
        payload["ThrustEfficiency"] = self.thrust_efficiency
        return payload


@dataclass(frozen=True, kw_only=True)
class SequenceSegment(_SegmentBase):
    segments: tuple["MCSSegment", ...]

    def to_wire(self) -> dict[str, Any]:
        payload = self._wire("Sequence")
        payload["Segments"] = [item.to_wire() for item in self.segments]
        return payload


@dataclass(frozen=True, kw_only=True)
class TargetSequenceSegment(_SegmentBase):
    segments: tuple["MCSSegment", ...]
    action: str = "RunNominalSequence"
    profiles: tuple[Profile, ...] | None = None
    continue_on_failure: str | None = None
    when_profiles_finish: str | None = None

    def to_wire(self) -> dict[str, Any]:
        payload = self._wire("TargetSequence")
        payload["Action"] = self.action
        payload["Segments"] = [item.to_wire() for item in self.segments]
        if self.profiles is not None:
            payload["Profiles"] = [item.to_wire() for item in self.profiles]
        _include_if_supplied(payload, "ContinueOnFailure", self.continue_on_failure)
        _include_if_supplied(payload, "WhenProfilesFinish", self.when_profiles_finish)
        return payload


@dataclass(frozen=True, kw_only=True)
class StopSegment(_SegmentBase):
    enable: bool = True

    def to_wire(self) -> dict[str, Any]:
        payload = self._wire("Stop")
        payload["Enable"] = self.enable
        return payload


@dataclass(frozen=True, kw_only=True)
class FollowSegment(_SegmentBase):
    leader_name: str
    joining: str = "AtBeginning"
    separation: str = "AtEnd"
    joining_conditions: tuple[StoppingCondition, ...] | None = None
    separation_conditions: tuple[StoppingCondition, ...] | None = None
    x_offset_m: float = 0.0
    y_offset_m: float = 0.0
    z_offset_m: float = 0.0
    variable_names: str | None = None

    def to_wire(self) -> dict[str, Any]:
        payload = self._wire("Follow")
        payload["LeaderName"] = self.leader_name
        payload["Joining"] = self.joining
        payload["Separation"] = self.separation
        if self.joining_conditions is not None:
            payload["JoiningConditions"] = [item.to_wire() for item in self.joining_conditions]
        if self.separation_conditions is not None:
            payload["SeparationConditions"] = [item.to_wire() for item in self.separation_conditions]
        payload["XOffset"] = self.x_offset_m
        payload["YOffset"] = self.y_offset_m
        payload["ZOffset"] = self.z_offset_m
        _include_if_supplied(payload, "VariableNames", self.variable_names)
        return payload


MCSSegment: TypeAlias = (
    InitialStateSegment | PropagateSegment | ImpulsiveManeuverSegment
    | FiniteManeuverSegment | SequenceSegment | TargetSequenceSegment
    | StopSegment | FollowSegment
)
_SEGMENT_TYPES = (InitialStateSegment, PropagateSegment, ImpulsiveManeuverSegment,
                  FiniteManeuverSegment, SequenceSegment, TargetSequenceSegment,
                  StopSegment, FollowSegment)
_CALC_SCALAR_TYPES = (DurationScalar, EpochScalar, KeplerianScalar, ModifiedKeplerianScalar,
                      CartographicScalar, PointScalar, SphericalScalar, DeltaSphericalScalar,
                      BPlaneScalar, RelativeScalar)


def _segment_results(results: Sequence[CalcScalar] | None) -> tuple[CalcScalar, ...] | None:
    values = _typed_tuple(results, _CALC_SCALAR_TYPES, parameter="results")
    return None if values is None else values  # type: ignore[return-value]


def initial_state(
    name: str,
    state: InitialStateElement,
    *,
    epoch: str,
    coord_system_name: str = "Earth Inertial",
    dry_mass_kg: float = 500.0,
    fuel_mass_kg: float = 500.0,
    coefficient_of_drag: float | None = None,
    coefficient_of_srp: float | None = None,
    drag_area_m2: float | None = None,
    srp_area_m2: float | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> InitialStateSegment:
    if not isinstance(state, (KeplerianState, CartesianState, SphericalState, TargetVectorOutState)):
        raise TypeError("state must be an astrogator initial-state value")
    return InitialStateSegment(name=name, state=state, epoch=epoch,
                               coord_system_name=coord_system_name,
                               dry_mass_kg=dry_mass_kg, fuel_mass_kg=fuel_mass_kg,
                               coefficient_of_drag=coefficient_of_drag,
                               coefficient_of_srp=coefficient_of_srp,
                               drag_area_m2=drag_area_m2, srp_area_m2=srp_area_m2,
                               description=description, user_comment=user_comment,
                               results=_segment_results(results))


def propagate(
    name: str,
    *,
    propagator_name: str,
    stop_conditions: Sequence[StoppingCondition],
    variable_names: str | None = None,
    max_propagation_time_s: float | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> PropagateSegment:
    conditions = _typed_tuple(stop_conditions, (DurationStop, EpochStop, PeriapsisStop, ApoapsisStop), parameter="stop_conditions")
    return PropagateSegment(name=name, propagator_name=propagator_name,
                            stop_conditions=conditions or (), variable_names=variable_names,
                            max_propagation_time_s=max_propagation_time_s,
                            description=description, user_comment=user_comment,
                            results=_segment_results(results))


def impulsive_maneuver(
    name: str,
    *,
    attitude_control: ImpulsiveAttitudeControl,
    propulsion_method_value: str,
    update_mass: bool = False,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> ImpulsiveManeuverSegment:
    if not isinstance(attitude_control, (ImpulsiveVelocityVector, ImpulsiveAntiVelocityVector,
                                         ImpulsiveThrustVectorCartesian, ImpulsiveThrustVectorSpherical,
                                         ImpulsiveAttitudeQuaternion, ImpulsiveAttitudeEuler)):
        raise TypeError("attitude_control must be an impulsive Astrogator attitude-control value")
    return ImpulsiveManeuverSegment(name=name, attitude_control=attitude_control,
                                    propulsion_method_value=propulsion_method_value,
                                    update_mass=update_mass, description=description,
                                    user_comment=user_comment, results=_segment_results(results))


def finite_maneuver(
    name: str,
    *,
    attitude_control: FiniteAttitudeControl,
    propagator_name: str,
    stop_conditions: Sequence[StoppingCondition],
    propulsion_method_value: str,
    thrust_efficiency: float = 1.0,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> FiniteManeuverSegment:
    if not isinstance(attitude_control, (FiniteVelocityVector, FiniteAntiVelocityVector,
                                         FiniteThrustVectorCartesian, FiniteThrustVectorSpherical,
                                         FiniteAttitudeQuaternion, FiniteAttitudeEuler)):
        raise TypeError("attitude_control must be a finite Astrogator attitude-control value")
    conditions = _typed_tuple(stop_conditions, (DurationStop, EpochStop, PeriapsisStop, ApoapsisStop), parameter="stop_conditions")
    return FiniteManeuverSegment(name=name, attitude_control=attitude_control,
                                 propagator_name=propagator_name, stop_conditions=conditions or (),
                                 propulsion_method_value=propulsion_method_value,
                                 thrust_efficiency=thrust_efficiency, description=description,
                                 user_comment=user_comment, results=_segment_results(results))


def sequence(name: str, segments: Sequence[MCSSegment], *, description: str | None = None, user_comment: str | None = None, results: Sequence[CalcScalar] | None = None) -> SequenceSegment:
    values = _typed_tuple(segments, _SEGMENT_TYPES, parameter="segments")
    return SequenceSegment(name=name, segments=values or (), description=description,
                           user_comment=user_comment, results=_segment_results(results))


def target_sequence(
    name: str,
    segments: Sequence[MCSSegment],
    *,
    action: str = "RunNominalSequence",
    profiles: Sequence[Profile] | None = None,
    continue_on_failure: str | None = None,
    when_profiles_finish: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> TargetSequenceSegment:
    segment_values = _typed_tuple(segments, _SEGMENT_TYPES, parameter="segments")
    profile_values = _typed_tuple(profiles, DifferentialCorrector, parameter="profiles")
    return TargetSequenceSegment(name=name, segments=segment_values or (), action=action,
                                 profiles=None if profile_values is None else profile_values,  # type: ignore[arg-type]
                                 continue_on_failure=continue_on_failure,
                                 when_profiles_finish=when_profiles_finish, description=description,
                                 user_comment=user_comment, results=_segment_results(results))


def stop(name: str, *, enable: bool = True, description: str | None = None, user_comment: str | None = None, results: Sequence[CalcScalar] | None = None) -> StopSegment:
    return StopSegment(name=name, enable=enable, description=description,
                       user_comment=user_comment, results=_segment_results(results))


def follow(
    name: str,
    *,
    leader_name: str,
    joining: str = "AtBeginning",
    separation: str = "AtEnd",
    joining_conditions: Sequence[StoppingCondition] | None = None,
    separation_conditions: Sequence[StoppingCondition] | None = None,
    x_offset_m: float = 0.0,
    y_offset_m: float = 0.0,
    z_offset_m: float = 0.0,
    variable_names: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    results: Sequence[CalcScalar] | None = None,
) -> FollowSegment:
    joining_values = _typed_tuple(joining_conditions, (DurationStop, EpochStop, PeriapsisStop, ApoapsisStop), parameter="joining_conditions")
    separation_values = _typed_tuple(separation_conditions, (DurationStop, EpochStop, PeriapsisStop, ApoapsisStop), parameter="separation_conditions")
    return FollowSegment(name=name, leader_name=leader_name, joining=joining, separation=separation,
                         joining_conditions=joining_values, separation_conditions=separation_values,
                         x_offset_m=x_offset_m, y_offset_m=y_offset_m, z_offset_m=z_offset_m,
                         variable_names=variable_names, description=description,
                         user_comment=user_comment, results=_segment_results(results))


@dataclass(frozen=True, kw_only=True)
class MissionPosition:
    central_body: str = "Earth"
    main_sequence: tuple[MCSSegment, ...]
    compute_czml_positions: bool | None = None
    out_czml_frame_name: str = "INERTIAL"
    text: str | None = None
    propagators: tuple[HpopConfig, ...] | None = None
    engine_models: tuple[EngineConstant, ...] | None = None

    def to_wire(self) -> dict[str, Any]:
        return _mission_wire(
            central_body=self.central_body, main_sequence=self.main_sequence,
            compute_czml_positions=self.compute_czml_positions,
            out_czml_frame_name=self.out_czml_frame_name, text=self.text,
            propagators=self.propagators, engine_models=self.engine_models,
        )


def _propagator_tuple(values: Sequence[HpopConfig] | None) -> tuple[HpopConfig, ...] | None:
    result = _typed_tuple(values, HpopConfig, parameter="propagators")
    return None if result is None else result  # type: ignore[return-value]


def _engine_tuple(values: Sequence[EngineConstant] | None) -> tuple[EngineConstant, ...] | None:
    result = _typed_tuple(values, EngineConstant, parameter="engine_models")
    return None if result is None else result  # type: ignore[return-value]


def _mission_wire(
    *,
    central_body: str,
    main_sequence: Sequence[MCSSegment],
    compute_czml_positions: bool | None,
    out_czml_frame_name: str,
    text: str | None,
    propagators: Sequence[HpopConfig] | None,
    engine_models: Sequence[EngineConstant] | None,
) -> dict[str, Any]:
    sequence_values = _typed_tuple(main_sequence, _SEGMENT_TYPES, parameter="main_sequence")
    body: dict[str, Any] = {
        "$type": "AstrogatorMCS",
        "CentralBody": central_body,
        "OutCzmlFrameName": out_czml_frame_name,
        "MainSequence": [item.to_wire() for item in sequence_values or ()],
    }
    _include_if_supplied(body, "ComputeCzmlPositions", compute_czml_positions)
    _include_if_supplied(body, "Text", text)
    propagator_values = _propagator_tuple(propagators)
    if propagator_values is not None:
        body["Propagators"] = [item.to_wire() for item in propagator_values]
    engine_values = _engine_tuple(engine_models)
    if engine_values is not None:
        body["EngineModels"] = [item.to_wire() for item in engine_values]
    return body


def mission_position(
    *,
    main_sequence: Sequence[MCSSegment],
    central_body: str = "Earth",
    compute_czml_positions: bool | None = None,
    out_czml_frame_name: str = "INERTIAL",
    text: str | None = None,
    propagators: Sequence[HpopConfig] | None = None,
    engine_models: Sequence[EngineConstant] | None = None,
) -> MissionPosition:
    sequence_values = _typed_tuple(main_sequence, _SEGMENT_TYPES, parameter="main_sequence")
    return MissionPosition(central_body=central_body, main_sequence=sequence_values or (),
                           compute_czml_positions=compute_czml_positions,
                           out_czml_frame_name=out_czml_frame_name, text=text,
                           propagators=_propagator_tuple(propagators),
                           engine_models=_engine_tuple(engine_models))


@dataclass(frozen=True, kw_only=True)
class EntityPath:
    name: str
    position: MissionPosition
    description: str | None = None

    def to_wire(self) -> dict[str, Any]:
        payload = {"$type": "EntityPath", "Name": self.name, "Position": self.position.to_wire()}
        _include_if_supplied(payload, "Description", self.description)
        return payload


def entity_path(name: str, *, position: MissionPosition, description: str | None = None) -> EntityPath:
    if not isinstance(position, MissionPosition):
        raise TypeError("position must be an astrogator MissionPosition value")
    return EntityPath(name=name, position=position, description=description)


__all__ = [
    "ApoapsisStop", "BPlaneScalar", "CalcScalar", "CartesianState", "CartographicScalar",
    "DeltaSphericalScalar", "DifferentialCorrector", "DifferentialCorrectorConstraint",
    "DifferentialCorrectorControl", "DurationScalar", "DurationStop", "EngineConstant",
    "EntityPath", "EpochScalar", "EpochStop", "FiniteAntiVelocityVector", "FiniteAttitudeControl",
    "FiniteAttitudeEuler", "FiniteAttitudeQuaternion", "FiniteManeuverSegment",
    "FiniteThrustVectorCartesian", "FiniteThrustVectorSpherical",
    "FiniteVelocityVector", "FollowSegment", "ImpulsiveAntiVelocityVector",
    "ImpulsiveAttitudeControl", "ImpulsiveAttitudeEuler", "ImpulsiveAttitudeQuaternion",
    "ImpulsiveManeuverSegment", "ImpulsiveThrustVectorCartesian",
    "ImpulsiveThrustVectorSpherical", "ImpulsiveVelocityVector", "InitialStateElement",
    "InitialStateSegment", "KeplerianScalar", "KeplerianState", "MCSSegment", "MissionPosition",
    "ModifiedKeplerianScalar", "PeriapsisStop", "PointScalar", "Profile", "PropagateSegment",
    "RelativeScalar", "SequenceSegment", "SphericalScalar", "SphericalState", "StopSegment",
    "TargetSequenceSegment", "TargetVectorOutState", "StoppingCondition", "apoapsis_stop",
    "b_plane_scalar", "cartesian_state", "cartographic_scalar", "constant_engine",
    "delta_spherical_scalar", "differential_corrector", "differential_corrector_constraint",
    "differential_corrector_control", "duration_scalar", "duration_stop", "entity_path",
    "epoch_scalar", "epoch_stop", "finite_anti_velocity_vector", "finite_attitude_euler",
    "finite_attitude_quaternion", "finite_maneuver", "finite_thrust_vector_cartesian",
    "finite_thrust_vector_spherical", "finite_velocity_vector", "follow", "impulsive_anti_velocity_vector",
    "impulsive_attitude_euler", "impulsive_attitude_quaternion", "impulsive_maneuver", "impulsive_thrust_vector_cartesian",
    "impulsive_thrust_vector_spherical", "impulsive_velocity_vector", "initial_state",
    "keplerian_scalar", "keplerian_state", "mission_position", "modified_keplerian_scalar",
    "periapsis_stop", "point_scalar", "propagate", "relative_scalar", "sequence", "spherical_scalar",
    "spherical_state", "stop", "target_sequence", "target_vector_out_state",
]
