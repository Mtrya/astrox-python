"""Orbit propagation functions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from astrox._http import raw
from astrox.orbits import CartesianState, KeplerianElements

__all__ = [
    "HpopAtmosphere",
    "HpopConfig",
    "HpopGravity",
    "HpopIntegrator",
    "HpopJacchiaRoberts",
    "HpopGravityField",
    "HpopRkf78",
    "HpopSrp",
    "HpopSrpSpherical",
    "HpopThirdBody",
    "HpopTwoBodyGravity",
    "PropagatorPosition",
    "ballistic",
    "ballistic_apogee_altitude",
    "ballistic_delta_v",
    "ballistic_delta_v_min_ecc",
    "ballistic_time_of_flight",
    "hpop",
    "hpop_config",
    "hpop_gravity_field",
    "hpop_jacchia_roberts",
    "hpop_rkf78",
    "hpop_srp_spherical",
    "hpop_third_body",
    "hpop_two_body_gravity",
    "j2",
    "multi_j2",
    "multi_sgp4",
    "multi_two_body",
    "sgp4",
    "simple_ascent",
    "two_body",
]


@dataclass(frozen=True, kw_only=True)
class PropagatorPosition:
    """Nested propagated position output."""

    central_body: str
    epoch: str
    reference_frame: str
    interpolation_algorithm: str
    interpolation_degree: int
    cartesian_velocity: tuple[float, ...]

    @classmethod
    def from_wire(cls, position_payload: dict[str, Any]) -> PropagatorPosition:
        """Build from the ASTROX nested Position payload."""
        return cls(
            central_body=position_payload["CentralBody"],
            epoch=position_payload["epoch"],
            reference_frame=position_payload["referenceFrame"],
            interpolation_algorithm=position_payload["interpolationAlgorithm"],
            interpolation_degree=position_payload["interpolationDegree"],
            cartesian_velocity=tuple(position_payload["cartesianVelocity"]),
        )


def _success_path(result: dict[str, Any]) -> tuple[float, PropagatorPosition]:
    return result["Period"], PropagatorPosition.from_wire(result["Position"])


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _sequence_to_list(value: Sequence[str], *, parameter: str) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{parameter} must be a sequence of strings")
    items = list(value)
    if not all(isinstance(item, str) for item in items):
        raise TypeError(f"{parameter} must be a sequence of strings")
    return items


def _hpop_value_to_wire(
    value: Any,
    *,
    expected_type: type | tuple[type, ...],
    parameter: str,
) -> dict[str, Any]:
    if not isinstance(value, expected_type):
        raise TypeError(f"{parameter} must be an HPOP config value")
    return value.to_wire()


@dataclass(frozen=True, kw_only=True)
class HpopRkf78:
    """HPOP RKF7(8) integrator configuration."""

    name: str | None = None
    description: str | None = None
    user_comment: str | None = None
    use_fixed_step: bool | None = None
    initial_step_s: float | None = None
    max_step_s: float | None = None
    min_step_s: float | None = None
    max_abs_error: float | None = None
    max_rel_error: float | None = None
    max_iterations: int | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX RKF7(8) integrator fragment."""
        payload: dict[str, Any] = {"$type": "RKF7th8th"}
        _include_if_supplied(payload, "Name", self.name)
        _include_if_supplied(payload, "Description", self.description)
        _include_if_supplied(payload, "UserComment", self.user_comment)
        _include_if_supplied(payload, "UseFixedStep", self.use_fixed_step)
        _include_if_supplied(payload, "InitialStep", self.initial_step_s)
        _include_if_supplied(payload, "MaxStep", self.max_step_s)
        _include_if_supplied(payload, "MinStep", self.min_step_s)
        _include_if_supplied(payload, "MaxAbsErr", self.max_abs_error)
        _include_if_supplied(payload, "MaxRelErr", self.max_rel_error)
        _include_if_supplied(payload, "MaxIterations", self.max_iterations)
        return payload


@dataclass(frozen=True, kw_only=True)
class HpopTwoBodyGravity:
    """HPOP two-body gravity configuration."""

    name: str | None = None
    description: str | None = None
    user_comment: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX two-body gravity fragment."""
        payload: dict[str, Any] = {"$type": "TwoBody"}
        _include_if_supplied(payload, "Name", self.name)
        _include_if_supplied(payload, "Description", self.description)
        _include_if_supplied(payload, "UserComment", self.user_comment)
        return payload


@dataclass(frozen=True, kw_only=True)
class HpopGravityField:
    """HPOP gravity-field configuration."""

    gravity_file_name: str
    degree: int
    order: int
    name: str | None = None
    description: str | None = None
    user_comment: str | None = None
    use_secular_variations: bool | None = None
    solid_tide_type: str | None = None
    eop_file_path: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX gravity-field fragment."""
        payload: dict[str, Any] = {
            "$type": "GravityField",
            "GravityFileName": self.gravity_file_name,
            "Degree": self.degree,
            "Order": self.order,
        }
        _include_if_supplied(payload, "Name", self.name)
        _include_if_supplied(payload, "Description", self.description)
        _include_if_supplied(payload, "UserComment", self.user_comment)
        _include_if_supplied(payload, "UseSecularVariations", self.use_secular_variations)
        _include_if_supplied(payload, "SolidTideType", self.solid_tide_type)
        _include_if_supplied(payload, "EOPfilePath", self.eop_file_path)
        return payload


@dataclass(frozen=True, kw_only=True)
class HpopJacchiaRoberts:
    """HPOP Jacchia-Roberts atmosphere configuration."""

    name: str | None = None
    description: str | None = None
    user_comment: str | None = None
    drag_model_type: str | None = None
    atmos_data_source: str | None = None
    f10p7: float | None = None
    f10p7_avg: float | None = None
    kp: float | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX Jacchia-Roberts atmosphere fragment."""
        payload: dict[str, Any] = {"$type": "JacchiaRoberts"}
        _include_if_supplied(payload, "Name", self.name)
        _include_if_supplied(payload, "Description", self.description)
        _include_if_supplied(payload, "UserComment", self.user_comment)
        _include_if_supplied(payload, "DragModelType", self.drag_model_type)
        _include_if_supplied(payload, "AtmosDataSource", self.atmos_data_source)
        _include_if_supplied(payload, "F10p7", self.f10p7)
        _include_if_supplied(payload, "F10p7Avg", self.f10p7_avg)
        _include_if_supplied(payload, "Kp", self.kp)
        return payload


@dataclass(frozen=True, kw_only=True)
class HpopSrpSpherical:
    """HPOP spherical solar-radiation-pressure configuration."""

    name: str | None = None
    description: str | None = None
    user_comment: str | None = None
    shadow_model: str | None = None
    sun_position: str | None = None
    eclipsing_bodies: tuple[str, ...] | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX spherical SRP fragment."""
        payload: dict[str, Any] = {"$type": "SRPSpherical"}
        _include_if_supplied(payload, "Name", self.name)
        _include_if_supplied(payload, "Description", self.description)
        _include_if_supplied(payload, "UserComment", self.user_comment)
        _include_if_supplied(payload, "ShadowModel", self.shadow_model)
        _include_if_supplied(payload, "SunPosition", self.sun_position)
        if self.eclipsing_bodies is not None:
            payload["EclipsingBodies"] = list(self.eclipsing_bodies)
        return payload


@dataclass(frozen=True, kw_only=True)
class HpopThirdBody:
    """HPOP third-body force configuration."""

    third_body_name: str
    name: str | None = None
    description: str | None = None
    user_comment: str | None = None
    mode_type: str | None = None
    ephem_source: str | None = None
    grav_source: str | None = None
    mu_m3_s2: float | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX third-body force fragment."""
        payload: dict[str, Any] = {"ThirdBodyName": self.third_body_name}
        _include_if_supplied(payload, "Name", self.name)
        _include_if_supplied(payload, "Description", self.description)
        _include_if_supplied(payload, "UserComment", self.user_comment)
        _include_if_supplied(payload, "ModeType", self.mode_type)
        _include_if_supplied(payload, "EphemSource", self.ephem_source)
        _include_if_supplied(payload, "GravSource", self.grav_source)
        _include_if_supplied(payload, "Mu", self.mu_m3_s2)
        return payload


HpopIntegrator: TypeAlias = HpopRkf78
HpopGravity: TypeAlias = HpopTwoBodyGravity | HpopGravityField
HpopAtmosphere: TypeAlias = HpopJacchiaRoberts
HpopSrp: TypeAlias = HpopSrpSpherical


@dataclass(frozen=True, kw_only=True)
class HpopConfig:
    """HPOP propagator configuration."""

    name: str | None = None
    description: str | None = None
    user_comment: str | None = None
    central_body: str | None = None
    integrator: HpopIntegrator | None = None
    gravity: HpopGravity | None = None
    atmosphere: HpopAtmosphere | None = None
    srp: HpopSrp | None = None
    third_bodies: tuple[HpopThirdBody, ...] | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to the ASTROX HPOP propagator fragment."""
        payload: dict[str, Any] = {}
        _include_if_supplied(payload, "Name", self.name)
        _include_if_supplied(payload, "Description", self.description)
        _include_if_supplied(payload, "UserComment", self.user_comment)
        _include_if_supplied(payload, "CentralBodyName", self.central_body)
        if self.integrator is not None:
            payload["NumericalIntegrator"] = self.integrator.to_wire()
        if self.gravity is not None:
            payload["GravityModel"] = self.gravity.to_wire()
        if self.atmosphere is not None:
            payload["AtmosphericModel"] = self.atmosphere.to_wire()
        if self.srp is not None:
            payload["SRPModel"] = self.srp.to_wire()
        if self.third_bodies is not None:
            payload["ThirdBodyForce"] = [
                third_body.to_wire()
                for third_body in self.third_bodies
            ]
        return payload


def _keplerian_from_elements_object(payload: dict[str, Any]) -> KeplerianElements:
    return KeplerianElements(
        semi_major_axis_m=payload["SemimajorAxis"],
        eccentricity=payload["Eccentricity"],
        inclination_deg=payload["Inclination"],
        argument_of_periapsis_deg=payload["ArgumentOfPeriapsis"],
        raan_deg=payload["RightAscensionOfAscendingNode"],
        true_anomaly_deg=payload["TrueAnomaly"],
    )


def _batch_success_path(result: dict[str, Any]) -> tuple[KeplerianElements, ...]:
    return tuple(
        _keplerian_from_elements_object(item)
        for item in result["AllElementsAtEpoch"]
    )


def _state_item_to_wire(
    item: Sequence[object],
    *,
    gravitational_parameter_m3_s2: float | None,
) -> dict[str, Any]:
    if not isinstance(item, (list, tuple)) or len(item) != 2:
        raise TypeError("states items must be two-item sequences of orbit epoch and KeplerianElements")
    orbit_epoch, orbit = item
    if not isinstance(orbit_epoch, str):
        raise TypeError("states item orbit epoch must be a string")
    if not isinstance(orbit, KeplerianElements):
        raise TypeError("states item orbit must be a KeplerianElements instance")

    payload: dict[str, Any] = {
        "OrbitEpoch": orbit_epoch,
        "SemimajorAxis": orbit.semi_major_axis_m,
        "Eccentricity": orbit.eccentricity,
        "Inclination": orbit.inclination_deg,
        "ArgumentOfPeriapsis": orbit.argument_of_periapsis_deg,
        "RightAscensionOfAscendingNode": orbit.raan_deg,
        "TrueAnomaly": orbit.true_anomaly_deg,
    }
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    return payload


def _states_to_wire(
    states: Sequence[Sequence[object]],
    *,
    gravitational_parameter_m3_s2: float | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(states, Sequence) or isinstance(states, (str, bytes)):
        raise TypeError("states must be a sequence of two-item state sequences")
    return [
        _state_item_to_wire(
            item,
            gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        )
        for item in states
    ]


def _tle_set_to_wire(item: Sequence[object]) -> str:
    if not isinstance(item, (list, tuple)) or len(item) != 2:
        raise TypeError("tle_sets items must be two-item sequences of TLE strings")
    line1, line2 = item
    if not isinstance(line1, str) or not isinstance(line2, str):
        raise TypeError("tle_sets items must contain TLE strings")
    return f"{line1}\n{line2}"


def _tle_sets_to_wire(tle_sets: Sequence[Sequence[object]]) -> list[str]:
    if not isinstance(tle_sets, Sequence) or isinstance(tle_sets, (str, bytes)):
        raise TypeError("tle_sets must be a sequence of two-item TLE string sequences")
    return [_tle_set_to_wire(item) for item in tle_sets]


def hpop_rkf78(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    use_fixed_step: bool | None = None,
    initial_step_s: float | None = None,
    max_step_s: float | None = None,
    min_step_s: float | None = None,
    max_abs_error: float | None = None,
    max_rel_error: float | None = None,
    max_iterations: int | None = None,
) -> HpopIntegrator:
    """Create an HPOP RKF7(8) integrator fragment."""
    return HpopRkf78(
        name=name,
        description=description,
        user_comment=user_comment,
        use_fixed_step=use_fixed_step,
        initial_step_s=initial_step_s,
        max_step_s=max_step_s,
        min_step_s=min_step_s,
        max_abs_error=max_abs_error,
        max_rel_error=max_rel_error,
        max_iterations=max_iterations,
    )


def hpop_two_body_gravity(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
) -> HpopGravity:
    """Create an HPOP two-body gravity fragment.

    ASTROX owns the two-body gravity constants for this branch; use
    ``hpop(...)`` top-level scalar arguments for spacecraft and central-body
    propagation knobs exposed by the curated SDK.
    """
    return HpopTwoBodyGravity(
        name=name,
        description=description,
        user_comment=user_comment,
    )


def hpop_gravity_field(
    *,
    gravity_file_name: str,
    degree: int,
    order: int,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    use_secular_variations: bool | None = None,
    solid_tide_type: str | None = None,
    eop_file_path: str | None = None,
) -> HpopGravity:
    """Create an HPOP gravity-field fragment."""
    return HpopGravityField(
        gravity_file_name=gravity_file_name,
        degree=degree,
        order=order,
        name=name,
        description=description,
        user_comment=user_comment,
        use_secular_variations=use_secular_variations,
        solid_tide_type=solid_tide_type,
        eop_file_path=eop_file_path,
    )


def hpop_jacchia_roberts(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    drag_model_type: str | None = None,
    atmos_data_source: str | None = None,
    f10p7: float | None = None,
    f10p7_avg: float | None = None,
    kp: float | None = None,
) -> HpopAtmosphere:
    """Create an HPOP Jacchia-Roberts atmosphere fragment."""
    return HpopJacchiaRoberts(
        name=name,
        description=description,
        user_comment=user_comment,
        drag_model_type=drag_model_type,
        atmos_data_source=atmos_data_source,
        f10p7=f10p7,
        f10p7_avg=f10p7_avg,
        kp=kp,
    )


def hpop_srp_spherical(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    shadow_model: str | None = None,
    sun_position: str | None = None,
    eclipsing_bodies: Sequence[str] | None = None,
) -> HpopSrp:
    """Create an HPOP spherical solar-radiation-pressure fragment."""
    bodies = None
    if eclipsing_bodies is not None:
        bodies = tuple(
            _sequence_to_list(
                eclipsing_bodies,
                parameter="eclipsing_bodies",
            )
        )
    return HpopSrpSpherical(
        name=name,
        description=description,
        user_comment=user_comment,
        shadow_model=shadow_model,
        sun_position=sun_position,
        eclipsing_bodies=bodies,
    )


def hpop_third_body(
    third_body_name: str,
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    mode_type: str | None = None,
    ephem_source: str | None = None,
    grav_source: str | None = None,
    mu_m3_s2: float | None = None,
) -> HpopThirdBody:
    """Create an HPOP third-body force fragment."""
    return HpopThirdBody(
        third_body_name=third_body_name,
        name=name,
        description=description,
        user_comment=user_comment,
        mode_type=mode_type,
        ephem_source=ephem_source,
        grav_source=grav_source,
        mu_m3_s2=mu_m3_s2,
    )


def hpop_config(
    *,
    name: str | None = None,
    description: str | None = None,
    user_comment: str | None = None,
    central_body: str | None = None,
    integrator: HpopIntegrator | None = None,
    gravity: HpopGravity | None = None,
    atmosphere: HpopAtmosphere | None = None,
    srp: HpopSrp | None = None,
    third_bodies: Sequence[HpopThirdBody] | None = None,
) -> HpopConfig:
    """Create an HPOP propagator configuration fragment."""
    if integrator is not None:
        _hpop_value_to_wire(
            integrator,
            expected_type=HpopRkf78,
            parameter="integrator",
        )
    if gravity is not None:
        _hpop_value_to_wire(
            gravity,
            expected_type=(HpopTwoBodyGravity, HpopGravityField),
            parameter="gravity",
        )
    if atmosphere is not None:
        _hpop_value_to_wire(
            atmosphere,
            expected_type=HpopJacchiaRoberts,
            parameter="atmosphere",
        )
    if srp is not None:
        _hpop_value_to_wire(
            srp,
            expected_type=HpopSrpSpherical,
            parameter="srp",
        )
    body_values = None
    if third_bodies is not None:
        if isinstance(third_bodies, (str, bytes)) or not isinstance(
            third_bodies,
            Sequence,
        ):
            raise TypeError("third_bodies must be a sequence of HPOP config values")
        body_values = tuple(third_bodies)
        if not all(isinstance(body, HpopThirdBody) for body in body_values):
            raise TypeError("third_bodies must be a sequence of HPOP config values")
    return HpopConfig(
        name=name,
        description=description,
        user_comment=user_comment,
        central_body=central_body,
        integrator=integrator,
        gravity=gravity,
        atmosphere=atmosphere,
        srp=srp,
        third_bodies=body_values,
    )


def hpop(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements | None = None,
    state: CartesianState | None = None,
    config: HpopConfig | Mapping[str, Any] | None = None,
    coord_system: str | None = None,
    coord_epoch: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coefficient_of_drag: float | None = None,
    area_mass_ratio_drag_m2_kg: float | None = None,
    coefficient_of_srp: float | None = None,
    area_mass_ratio_srp_m2_kg: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate Classical or Cartesian state with ASTROX HPOP."""
    if (orbit is None) == (state is None):
        raise ValueError("exactly one of orbit or state must be provided")
    if orbit is not None:
        if not isinstance(orbit, KeplerianElements):
            raise TypeError("orbit must be a KeplerianElements instance")
        coord_type = "Classical"
        orbital_elements = orbit.to_wire()
    else:
        if not isinstance(state, CartesianState):
            raise TypeError("state must be a CartesianState instance")
        coord_type = "Cartesian"
        orbital_elements = state.to_wire()

    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "OrbitEpoch": orbit_epoch,
        "CoordType": coord_type,
        "OrbitalElements": orbital_elements,
    }
    _include_if_supplied(payload, "CoordSystem", coord_system)
    _include_if_supplied(payload, "CoordEpoch", coord_epoch)
    _include_if_supplied(payload, "GravitationalParameter", gravitational_parameter_m3_s2)
    _include_if_supplied(payload, "CoefficientOfDrag", coefficient_of_drag)
    _include_if_supplied(payload, "AreaMassRatioDrag", area_mass_ratio_drag_m2_kg)
    _include_if_supplied(payload, "CoefficientOfSRP", coefficient_of_srp)
    _include_if_supplied(payload, "AreaMassRatioSRP", area_mass_ratio_srp_m2_kg)
    if config is not None:
        if isinstance(config, HpopConfig):
            payload["HpopPropagator"] = config.to_wire()
        elif isinstance(config, Mapping):
            payload["HpopPropagator"] = dict(config)
        else:
            raise TypeError("config must be an HpopConfig value or mapping fragment")

    result = raw.post("/Propagator/HPOP", json=payload)
    return _success_path(result)


def two_body(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate Classical Keplerian elements using two-body dynamics."""
    if not isinstance(orbit, KeplerianElements):
        raise TypeError("orbit must be a KeplerianElements instance")

    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "OrbitEpoch": orbit_epoch,
        "CoordType": "Classical",
        "OrbitalElements": orbit.to_wire(),
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if coord_system is not None:
        payload["CoordSystem"] = coord_system

    result = raw.post("/Propagator/TwoBody", json=payload)
    return _success_path(result)


def j2(
    *,
    start: str,
    stop: str,
    orbit_epoch: str,
    orbit: KeplerianElements,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    coord_system: str | None = None,
    j2_normalized_value: float | None = None,
    ref_distance_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate Classical Keplerian elements using the J2 model."""
    if not isinstance(orbit, KeplerianElements):
        raise TypeError("orbit must be a KeplerianElements instance")

    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "OrbitEpoch": orbit_epoch,
        "CoordType": "Classical",
        "OrbitalElements": orbit.to_wire(),
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if coord_system is not None:
        payload["CoordSystem"] = coord_system
    if j2_normalized_value is not None:
        payload["J2NormalizedValue"] = j2_normalized_value
    if ref_distance_m is not None:
        payload["RefDistance"] = ref_distance_m

    result = raw.post("/Propagator/J2", json=payload)
    return _success_path(result)


def multi_two_body(
    *,
    epoch: str,
    states: Sequence[tuple[str, KeplerianElements]],
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[KeplerianElements, ...]:
    """Propagate multiple Classical states to one target epoch using two-body dynamics.

    ASTROX raw batch responses include ``GravitationalParameter`` on each returned
    element. The curated return intentionally omits it because live behavior shows
    that field is not a reliable echo of the propagation parameter used for the
    result; use ``astrox.raw`` for the full raw envelope.
    """
    payload = {
        "Epoch": epoch,
        "AllSateElements": _states_to_wire(
            states,
            gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        ),
    }

    result = raw.post("/Propagator/MultiTwoBody", json=payload)
    return _batch_success_path(result)


def multi_j2(
    *,
    epoch: str,
    states: Sequence[tuple[str, KeplerianElements]],
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[KeplerianElements, ...]:
    """Propagate multiple Classical states to one target epoch using ASTROX J2.

    The batch ASTROX route owns its J2 constants; the curated SDK does not expose
    J2 constants for this function because live behavior does not show those
    inputs affecting the endpoint. ASTROX raw batch responses include
    ``GravitationalParameter`` on each returned element. The curated return
    intentionally omits it because live behavior shows that field is not a
    reliable echo of the propagation parameter used for the result; use
    ``astrox.raw`` for the full raw envelope.
    """
    payload = {
        "Epoch": epoch,
        "AllSateElements": _states_to_wire(
            states,
            gravitational_parameter_m3_s2=gravitational_parameter_m3_s2,
        ),
    }

    result = raw.post("/Propagator/MultiJ2", json=payload)
    return _batch_success_path(result)


def multi_sgp4(
    *,
    epoch: str,
    tle_sets: Sequence[tuple[str, str]],
) -> tuple[KeplerianElements, ...]:
    """Propagate multiple TLEs to one target epoch using SGP4.

    Each public ``tle_sets`` item is a two-line TLE sequence. The SDK lowers it
    to the ASTROX batch route's newline-joined string format. ASTROX raw batch
    responses include ``GravitationalParameter`` on each returned element. The
    curated return intentionally omits it because live behavior shows that field
    is not a reliable echo of the propagation parameter used for the result; use
    ``astrox.raw`` for the full raw envelope.
    """
    payload = {
        "Epoch": epoch,
        "TLEs": _tle_sets_to_wire(tle_sets),
    }

    result = raw.post("/Propagator/MultiSgp4", json=payload)
    return _batch_success_path(result)


def sgp4(
    *,
    start: str,
    stop: str,
    tle_lines: tuple[str, str] | list[str],
    step_s: float | None = None,
    satellite_number: str | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a satellite from two-line element data using SGP4."""
    if (
        not isinstance(tle_lines, (list, tuple))
        or len(tle_lines) != 2
        or not all(isinstance(line, str) for line in tle_lines)
    ):
        raise TypeError("tle_lines must be a two-item sequence of TLE strings")

    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "TLEs": list(tle_lines),
    }
    if step_s is not None:
        payload["Step"] = step_s
    if satellite_number is not None:
        payload["SatelliteNumber"] = satellite_number

    result = raw.post("/Propagator/sgp4", json=payload)
    return _success_path(result)


def simple_ascent(
    *,
    start: str,
    stop: str,
    launch_latitude_deg: float,
    launch_longitude_deg: float,
    launch_altitude_m: float,
    burnout_velocity_m_s: float,
    burnout_latitude_deg: float,
    burnout_longitude_deg: float,
    burnout_altitude_m: float,
    step_s: float | None = None,
    central_body: str | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a simple ascent from launch point to burnout point."""
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "LaunchLatitude": launch_latitude_deg,
        "LaunchLongitude": launch_longitude_deg,
        "LaunchAltitude": launch_altitude_m,
        "BurnoutVelocity": burnout_velocity_m_s,
        "BurnoutLatitude": burnout_latitude_deg,
        "BurnoutLongitude": burnout_longitude_deg,
        "BurnoutAltitude": burnout_altitude_m,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body

    result = raw.post("/Propagator/SimpleAscent", json=payload)
    return _success_path(result)


def ballistic(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate the verified nominal ballistic trajectory shape."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    return _success_path(result)


def ballistic_delta_v(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    delta_v_m_s: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a ballistic trajectory using the DeltaV branch."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
        "BallisticType": "DeltaV",
        "BallisticTypeValue": delta_v_m_s,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    return _success_path(result)


def ballistic_delta_v_min_ecc(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    delta_v_m_s: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a ballistic trajectory using the DeltaV_MinEcc branch."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
        "BallisticType": "DeltaV_MinEcc",
        "BallisticTypeValue": delta_v_m_s,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    return _success_path(result)


def ballistic_apogee_altitude(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    apogee_altitude_m: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a ballistic trajectory using the ApogeeAlt branch."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
        "BallisticType": "ApogeeAlt",
        "BallisticTypeValue": apogee_altitude_m,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    return _success_path(result)


def ballistic_time_of_flight(
    *,
    start: str,
    impact_latitude_deg: float,
    impact_longitude_deg: float,
    time_of_flight_s: float,
    stop: str | None = None,
    step_s: float | None = None,
    central_body: str | None = None,
    gravitational_parameter_m3_s2: float | None = None,
    launch_latitude_deg: float | None = None,
    launch_longitude_deg: float | None = None,
    launch_altitude_m: float | None = None,
    impact_altitude_m: float | None = None,
) -> tuple[float, PropagatorPosition]:
    """Propagate a ballistic trajectory using the TimeOfFlight branch."""
    payload: dict[str, Any] = {
        "Start": start,
        "ImpactLatitude": impact_latitude_deg,
        "ImpactLongitude": impact_longitude_deg,
        "BallisticType": "TimeOfFlight",
        "BallisticTypeValue": time_of_flight_s,
    }
    if step_s is not None:
        payload["Step"] = step_s
    if central_body is not None:
        payload["CentralBody"] = central_body
    if gravitational_parameter_m3_s2 is not None:
        payload["GravitationalParameter"] = gravitational_parameter_m3_s2
    if launch_latitude_deg is not None:
        payload["LaunchLatitude"] = launch_latitude_deg
    if launch_longitude_deg is not None:
        payload["LaunchLongitude"] = launch_longitude_deg
    if launch_altitude_m is not None:
        payload["LaunchAltitude"] = launch_altitude_m
    if impact_altitude_m is not None:
        payload["ImpactAltitude"] = impact_altitude_m
    if stop is not None:
        payload["Stop"] = stop

    result = raw.post("/Propagator/Ballistic", json=payload)
    return _success_path(result)
