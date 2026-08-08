"""Behavior tests for Astrogator RunMCS response parsing."""

from __future__ import annotations

from copy import deepcopy

import pytest

from astrox import astrogator
from astrox.astrogator._results import (
    DifferentialCorrectorResult,
    InitialStateResult,
    ManeuverImpulsiveResult,
    PropagateResult,
    RunMCSResult,
    SequenceResult,
    TargetSequenceResult,
    run_mcs_result_from_wire,
)


MU = 3.986004415e14


def _state(epoch: str = "2026-01-01T00:00:00.000Z") -> dict[str, object]:
    return {
        "Epoch": epoch,
        "CoordSystemName": "Earth Inertial",
        "Cartesian": {"X": 1.0, "Y": 2.0, "Z": 3.0, "Vx": 4.0, "Vy": 5.0, "Vz": 6.0},
        "Keplerian": {
            "ElementType": "Osculating",
            "GravitationalParameter": MU,
            "SemiMajorAxis": 7_000_000.0,
            "Eccentricity": 0.3,
            "Inclination": 45.0,
            "RAAN": 30.0,
            "ArgOfPeriapsis": 60.0,
            "MeanAnomaly": 15.0,
            "TrueAnomaly": 30.0,
            "AnomalyType": "True",
            "Period": 5800.0,
        },
        "Spherical": {
            "RightAscension": 120.0,
            "Declination": 45.0,
            "RadiusMagnitude": 5_000_000.0,
            "HorizFPA": 6.0,
            "VelocityAzimuth": 90.0,
            "VelocityMagnitude": 10_000.0,
        },
        "DryMass": 500.0,
        "FuelMass": 500.0,
        "Cd": 2.2,
        "Cr": 1.0,
        "DragArea": 20.0,
        "SRPArea": 20.0,
        "Geodetic_Latitude": 45.0,
        "Geodetic_Longitude": 20.0,
        "Geodetic_Altitude": 100.0,
        "Geocentric_Latitude": 44.9,
        "Geocentric_Longitude": 20.0,
    }


def _base_result(type_name: str = "InitialState", *, wire_type: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "TypeName": type_name,
        "Name": "Segment",
        "Description": "description",
        "UserComment": "comment",
        "InitialState": _state(),
        "FinalState": _state("2026-01-01T00:00:01.000Z"),
        "DurationSec": 1.0,
        "Results": {"FinalTA": 30.1},
    }
    if wire_type is not None:
        payload["$type"] = wire_type
    return payload


def _response(*results: dict[str, object]) -> dict[str, object]:
    return {
        "IsSuccess": True,
        "Message": "Success",
        "MainSequenceResults": list(results),
    }


def test_parser_dispatches_initial_propagate_maneuver_and_preserves_unknown_fields() -> None:
    initial = _base_result()
    initial["FutureField"] = {"kept": True}
    propagate = _base_result("Propagate", wire_type="PropagateResult")
    propagate.update({"StoppedOnMaximumDuration": False, "StoppingConditionName": "Duration"})
    maneuver = _base_result("ManeuverImpulsive", wire_type="ManeuverImpulsiveResult")
    maneuver["ManeuverInformation"] = {
        "Start": "2026-01-01T00:00:00.000Z",
        "Stop": "2026-01-01T00:00:00.000Z",
        "UpdateMass": False,
        "Duration": 0.0,
        "FuelUsed": 0.0,
        "EstimatedFuelUsed": 33.4,
        "DeltaV_Mag": 100.0,
        "ManeuverAttitudeName": "Attitude",
        "DeltaV_Inertial": [1.0, 2.0, 3.0, 4.0, 5.0, 100.0],
        "DeltaV_VNC": [6.0, 7.0, 8.0, 9.0, 10.0, 100.0],
        "Quanternion": None,
    }

    result = run_mcs_result_from_wire(_response(initial, propagate, maneuver))

    assert isinstance(result, RunMCSResult)
    assert isinstance(result.main_sequence_results[0], InitialStateResult)
    assert isinstance(result.main_sequence_results[1], PropagateResult)
    assert isinstance(result.main_sequence_results[2], ManeuverImpulsiveResult)
    assert result.main_sequence_results[0].unknown_fields["FutureField"] == {"kept": True}
    assert result.main_sequence_results[1].stopping_condition_name == "Duration"
    maneuver_result = result.main_sequence_results[2]
    assert maneuver_result.maneuver_information.delta_v_inertial[-1] == 100.0
    assert maneuver_result.maneuver_information.quaternion is None


def test_parser_recurses_sequence_and_target_operator_results() -> None:
    child = _base_result("Propagate", wire_type="PropagateResult")
    child.update({"StoppedOnMaximumDuration": False, "StoppingConditionName": "Duration"})
    sequence = _base_result("Sequence", wire_type="SequenceResult")
    sequence["SegmentResults"] = [_base_result(), child]
    target = _base_result("TargetSequence", wire_type="TargetSequenceResult")
    target["SegmentResults"] = [_base_result(), child]
    target["OperatorResults"] = [
        {
            "$type": "DifferentialCorrectorResults",
            "Converged": True,
            "TotalIterations": 1,
            "ControlParameters": [
                {
                    "Enable": True,
                    "Name": "StopConditions.Duration",
                    "InitialValue": "10.0",
                    "FinalValue": "53.0",
                    "Correction": 43.0,
                    "LastUpdate": 0,
                    "Dimension": "",
                    "MaxStep": 600.0,
                    "ParentName": "Coast",
                    "Perturbation": 1.0,
                    "ScalingMethod": "NoScaling",
                    "ScalingValue": 1.0,
                    "Tolerance": 0.0001,
                    "Unit": "",
                    "Values": [53.0],
                }
            ],
            "Results": [
                {
                    "Enable": True,
                    "Name": "FinalTA",
                    "DesiredValue": "36.0",
                    "ParentName": "Coast",
                    "CurrentValue": "35.9",
                    "Unit": "",
                    "Difference": -0.1,
                    "ScalingMethod": "NoScaling",
                    "ScalingValue": 1.0,
                    "Tolerance": 0.1,
                    "Weight": 1.0,
                    "Values": [35.9],
                }
            ],
            "TypeName": "DifferentialCorrector",
            "Name": "DC1",
            "Description": "description",
            "UserComment": "comment",
        }
    ]

    result = run_mcs_result_from_wire(_response(sequence, target))
    assert isinstance(result.main_sequence_results[0], SequenceResult)
    assert [type(item) for item in result.main_sequence_results[0].segment_results] == [
        InitialStateResult,
        PropagateResult,
    ]
    assert isinstance(result.main_sequence_results[1], TargetSequenceResult)
    assert isinstance(result.main_sequence_results[1].operator_results[0], DifferentialCorrectorResult)
    assert result.main_sequence_results[1].operator_results[0].converged is True


def test_parser_builds_czml_positions_only_when_positions_are_present() -> None:
    response = _response(_base_result("Propagate", wire_type="PropagateResult"))
    response["MainSequenceResults"][0].update(  # type: ignore[union-attr]
        {"StoppedOnMaximumDuration": False, "StoppingConditionName": "Duration"}
    )
    response["Positions"] = {
        "CentralBody": "Earth",
        "CzmlPositions": [
            {
                "CentralBody": "Earth",
                "interpolationAlgorithm": "HERMITE",
                "interpolationDegree": 7,
                "referenceFrame": "INERTIAL",
                "epoch": "2026-01-01T00:00:00.000Z",
                "interval": "2026-01-01T00:00:00.000Z/2026-01-01T00:00:01.000Z",
                "cartesianVelocity": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            }
        ],
    }
    result = run_mcs_result_from_wire(response)
    assert result.positions is not None
    assert result.positions.positions[0].interpolation_degree == 7
    assert result.positions.positions[0].cartesian_velocity == (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0)


def test_parser_fails_loudly_when_required_state_field_is_missing() -> None:
    response = _response(_base_result())
    del response["MainSequenceResults"][0]["FinalState"]["Keplerian"]["Period"]  # type: ignore[index]
    with pytest.raises(KeyError):
        run_mcs_result_from_wire(response)


def test_parser_fails_loudly_when_required_result_field_is_missing() -> None:
    response = _response(_base_result("Propagate", wire_type="PropagateResult"))
    response["MainSequenceResults"][0]["StoppedOnMaximumDuration"] = False  # type: ignore[index]
    with pytest.raises(KeyError):
        run_mcs_result_from_wire(response)


def test_parser_uses_typename_fallback_for_follow_without_wire_type() -> None:
    response = _response(_base_result("Follow"))
    result = run_mcs_result_from_wire(response)
    assert isinstance(result.main_sequence_results[0], astrogator.FollowResult)
    assert result.main_sequence_results[0].wire_type is None


def test_parser_rejects_numeric_string_for_number_field() -> None:
    response = _response(_base_result())
    response["MainSequenceResults"][0]["DurationSec"] = "1.0"  # type: ignore[index]
    with pytest.raises(TypeError):
        run_mcs_result_from_wire(response)


def test_parser_rejects_boolean_string_for_bool_field() -> None:
    response = _response(_base_result("Propagate", wire_type="PropagateResult"))
    response["MainSequenceResults"][0].update(  # type: ignore[union-attr]
        {"StoppedOnMaximumDuration": "False", "StoppingConditionName": "Duration"}
    )
    with pytest.raises(TypeError):
        run_mcs_result_from_wire(response)


def test_parser_rejects_string_element_in_numeric_array() -> None:
    maneuver = _base_result("ManeuverImpulsive", wire_type="ManeuverImpulsiveResult")
    maneuver["ManeuverInformation"] = {
        "Start": "2026-01-01T00:00:00.000Z",
        "Stop": "2026-01-01T00:00:00.000Z",
        "UpdateMass": False,
        "Duration": 0.0,
        "FuelUsed": 0.0,
        "EstimatedFuelUsed": 33.4,
        "DeltaV_Mag": 100.0,
        "ManeuverAttitudeName": "Attitude",
        "DeltaV_Inertial": [1.0, "2.0", 3.0, 4.0, 5.0, 100.0],
        "DeltaV_VNC": [6.0, 7.0, 8.0, 9.0, 10.0, 100.0],
        "Quanternion": None,
    }
    with pytest.raises(TypeError):
        run_mcs_result_from_wire(_response(maneuver))
