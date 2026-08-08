"""Deterministic behavior tests for conjunction-analysis surfaces."""

from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction
from inspect import signature
from typing import Any

import pytest

from astrox import components, conjunction, exceptions, orbits
from tests.sdk.helpers import assert_canonical_equal


LINE1 = "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995"
LINE2 = "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456"
START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T00:10:00.000Z"
PRIMARY = orbits.tle(line1=LINE1, line2=LINE2, name="ISS", catalog_number="25544")
TARGET = orbits.tle(line1=LINE1, line2=LINE2, name="Target", catalog_number="12345")


V3_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "TotalNumber": 2,
    "AfterApoPeriFilterNumber": 1,
    "AfterCrossPlaneNumber": 1,
    "CA_Results": [
        {
            "SAT1_Name": "ISS",
            "SAT2_Name": "Target",
            "SAT1_Number": "25544",
            "SAT2_Number": "12345",
            "SAT1_TLE_Line1": LINE1,
            "SAT1_TLE_Line2": LINE2,
            "SAT2_TLE_Line1": LINE1,
            "SAT2_TLE_Line2": LINE2,
            "CA_MinRange_Time": START,
            "CA_MinRange": 1.25,
            "CA_Theta": 2.5,
            "CA_DeltaV": 7.5,
            "CA_Probability": 0.01,
        }
    ],
}

V4_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "TotalNumber": 1,
    "AfterApoPeriFilterNumber": 1,
    "AfterCrossPlaneNumber": 1,
    "CA_Results": [
        {
            "SAT2_Name": "Target",
            "SAT2_Number": "12345",
            "SAT2_TLE_Line1": LINE1,
            "SAT2_TLE_Line2": LINE2,
            "CA_MinRange_Time": STOP,
            "CA_MinRange": 2.25,
            "CA_Theta": 3.5,
            "CA_DeltaV": 8.5,
            "CA_Probability": 0.02,
        }
    ],
}


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, Any],
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_post(endpoint: str, *, json: object) -> dict[str, Any]:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(conjunction.raw, "post", fake_post)
    return calls


def position() -> components.CzmlPosition:
    return components.czml_position(
        epoch=START,
        central_body="Earth",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=5,
        reference_frame="INERTIAL",
        cartesian_velocity=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    )


def test_public_modules_exports_and_signatures_are_curated() -> None:
    import astrox

    assert astrox.conjunction is conjunction
    assert "conjunction" in astrox.__all__
    assert "find_tle_close_approaches" in conjunction.__all__
    assert "find_czml_close_approaches" in conjunction.__all__
    params = signature(conjunction.find_tle_close_approaches).parameters
    assert params["targets"].default is None
    assert params["tol_max_distance_km"].default is None
    assert params["tol_cross_dt_s"].default is None
    assert params["tol_theta_deg"].default is None
    assert params["tol_dh_km"].default is None


def test_find_tle_close_approaches_lowers_complete_payload_and_parses_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, V3_RESPONSE)

    result = conjunction.find_tle_close_approaches(
        start=START,
        stop=STOP,
        tle=PRIMARY,
        targets=[TARGET],
        tol_max_distance_km=5.0,
        tol_cross_dt_s=10.0,
        tol_theta_deg=1.0,
        tol_dh_km=30.0,
    )

    assert isinstance(result, conjunction.CloseApproachesResult)
    assert isinstance(result.results[0], conjunction.TleCloseApproach)
    assert result.results[0].primary == PRIMARY
    assert result.results[0].target == TARGET
    assert_canonical_equal(
        asdict(result),
        {
            "is_success": True,
            "message": "OK",
            "total_number": 2,
            "after_apo_peri_filter_number": 1,
            "after_cross_plane_number": 1,
            "results": [
                {
                    "primary": {
                        "line1": LINE1,
                        "line2": LINE2,
                        "name": "ISS",
                        "catalog_number": "25544",
                    },
                    "target": {
                        "line1": LINE1,
                        "line2": LINE2,
                        "name": "Target",
                        "catalog_number": "12345",
                    },
                    "min_range_time": START,
                    "min_range_km": 1.25,
                    "orbital_plane_angle_deg": 2.5,
                    "relative_speed_km_s": 7.5,
                    "collision_probability": 0.01,
                }
            ],
        },
    )
    assert calls[0]["endpoint"] == "/CAT/CA_ComputeV3"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start_UTCG": START,
            "Stop_UTCG": STOP,
            "TolMaxDistance": 5.0,
            "TolCrossDt": 10.0,
            "TolTheta": 1.0,
            "TolDh": 30.0,
            "SAT1": PRIMARY.to_tle_info_wire(),
            "Targets": [TARGET.to_tle_info_wire()],
        },
    )


def test_find_tle_close_approaches_omits_optional_server_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, {**V3_RESPONSE, "CA_Results": []})

    conjunction.find_tle_close_approaches(start=START, stop=STOP, tle=PRIMARY)

    assert_canonical_equal(
        calls[0]["json"],
        {"Start_UTCG": START, "Stop_UTCG": STOP, "SAT1": PRIMARY.to_tle_info_wire()},
    )


@pytest.mark.parametrize(
    "function_name",
    ["find_tle_close_approaches", "find_czml_close_approaches"],
)
def test_conjunction_validates_times_and_normalizes_numeric_options(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
) -> None:
    response = {
        **(V3_RESPONSE if function_name == "find_tle_close_approaches" else V4_RESPONSE),
        "CA_Results": [],
    }
    calls = record_raw_post(monkeypatch, response)
    function = getattr(conjunction, function_name)
    primary = (
        {"tle": PRIMARY}
        if function_name == "find_tle_close_approaches"
        else {"position": position()}
    )

    with pytest.raises(TypeError, match="start must be a string"):
        function(start=1, stop=STOP, **primary)
    with pytest.raises(TypeError, match="stop must be a string"):
        function(start=START, stop=1, **primary)

    function(
        start=START,
        stop=STOP,
        tol_max_distance_km=Fraction(5, 2),
        **primary,
    )
    assert calls[0]["json"]["TolMaxDistance"] == 2.5


def test_find_czml_close_approaches_preserves_position_type_discriminator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, V4_RESPONSE)

    result = conjunction.find_czml_close_approaches(
        start=START,
        stop=STOP,
        position=position(),
        targets=[TARGET],
    )

    assert isinstance(result.results[0], conjunction.CzmlCloseApproach)
    assert result.results[0].target == TARGET
    assert_canonical_equal(
        asdict(result),
        {
            "is_success": True,
            "message": "OK",
            "total_number": 1,
            "after_apo_peri_filter_number": 1,
            "after_cross_plane_number": 1,
            "results": [
                {
                    "target": {
                        "line1": LINE1,
                        "line2": LINE2,
                        "name": "Target",
                        "catalog_number": "12345",
                    },
                    "min_range_time": STOP,
                    "min_range_km": 2.25,
                    "orbital_plane_angle_deg": 3.5,
                    "relative_speed_km_s": 8.5,
                    "collision_probability": 0.02,
                }
            ],
        },
    )
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Start_UTCG": START,
            "Stop_UTCG": STOP,
            "SAT1": position().to_wire(),
            "Targets": [TARGET.to_tle_info_wire()],
        },
    )


@pytest.mark.parametrize("primary", [{"epoch": START}, PRIMARY.to_tle_info_wire()])
def test_conjunction_rejects_raw_or_wrong_primary_values(
    monkeypatch: pytest.MonkeyPatch,
    primary: object,
) -> None:
    record_raw_post(monkeypatch, {**V3_RESPONSE, "CA_Results": []})
    with pytest.raises(TypeError):
        conjunction.find_tle_close_approaches(
            start=START,
            stop=STOP,
            tle=primary,
        )


def test_v4_rejects_raw_position_dict() -> None:
    with pytest.raises(TypeError):
        conjunction.find_czml_close_approaches(
            start=START,
            stop=STOP,
            position=position().to_wire(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "field_path",
    [
        ("IsSuccess",),
        ("Message",),
        ("TotalNumber",),
        ("AfterApoPeriFilterNumber",),
        ("AfterCrossPlaneNumber",),
        ("CA_Results",),
    ],
)
def test_ca_parser_fails_loudly_for_missing_envelope_fields(
    monkeypatch: pytest.MonkeyPatch,
    field_path: tuple[str, ...],
) -> None:
    response = dict(V3_RESPONSE)
    del response[field_path[0]]
    record_raw_post(monkeypatch, response)
    with pytest.raises(KeyError):
        conjunction.find_tle_close_approaches(start=START, stop=STOP, tle=PRIMARY)


@pytest.mark.parametrize(
    ("field", "value"),
    [("IsSuccess", "true"), ("TotalNumber", 1.0), ("CA_Results", {})],
)
def test_ca_parser_rejects_mistyped_envelope_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    response = dict(V3_RESPONSE)
    response[field] = value
    record_raw_post(monkeypatch, response)
    with pytest.raises(TypeError):
        conjunction.find_tle_close_approaches(start=START, stop=STOP, tle=PRIMARY)


@pytest.mark.parametrize(
    "field",
    [
        "SAT1_Name",
        "SAT1_Number",
        "SAT1_TLE_Line1",
        "SAT1_TLE_Line2",
        "SAT2_Name",
        "SAT2_Number",
        "SAT2_TLE_Line1",
        "SAT2_TLE_Line2",
        "CA_MinRange_Time",
        "CA_MinRange",
        "CA_Theta",
        "CA_DeltaV",
        "CA_Probability",
    ],
)
def test_v3_parser_fails_on_each_nested_result_field(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    response = dict(V3_RESPONSE)
    response["CA_Results"] = [dict(V3_RESPONSE["CA_Results"][0])]
    del response["CA_Results"][0][field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        conjunction.find_tle_close_approaches(start=START, stop=STOP, tle=PRIMARY)


@pytest.mark.parametrize(
    "field",
    [
        "SAT2_Name",
        "SAT2_Number",
        "SAT2_TLE_Line1",
        "SAT2_TLE_Line2",
        "CA_MinRange_Time",
        "CA_MinRange",
        "CA_Theta",
        "CA_DeltaV",
        "CA_Probability",
    ],
)
def test_v4_parser_fails_on_each_nested_result_field(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    response = dict(V4_RESPONSE)
    response["CA_Results"] = [dict(V4_RESPONSE["CA_Results"][0])]
    del response["CA_Results"][0][field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        conjunction.find_czml_close_approaches(
            start=START,
            stop=STOP,
            position=position(),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("SAT1_Name", 1),
        ("SAT1_Number", 25544),
        ("SAT1_TLE_Line1", []),
        ("SAT1_TLE_Line2", {}),
        ("SAT2_Name", 1),
        ("SAT2_Number", 12345),
        ("SAT2_TLE_Line1", []),
        ("SAT2_TLE_Line2", {}),
        ("CA_MinRange_Time", 1),
        ("CA_MinRange", "1.25"),
        ("CA_Theta", True),
        ("CA_DeltaV", []),
        ("CA_Probability", {}),
    ],
)
def test_v3_parser_rejects_mistyped_nested_result_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    response = dict(V3_RESPONSE)
    response["CA_Results"] = [dict(V3_RESPONSE["CA_Results"][0])]
    response["CA_Results"][0][field] = value
    record_raw_post(monkeypatch, response)

    with pytest.raises(TypeError):
        conjunction.find_tle_close_approaches(start=START, stop=STOP, tle=PRIMARY)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("SAT2_Name", 1),
        ("SAT2_Number", 12345),
        ("SAT2_TLE_Line1", []),
        ("SAT2_TLE_Line2", {}),
        ("CA_MinRange_Time", 1),
        ("CA_MinRange", "2.25"),
        ("CA_Theta", True),
        ("CA_DeltaV", []),
        ("CA_Probability", {}),
    ],
)
def test_v4_parser_rejects_mistyped_nested_result_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    response = dict(V4_RESPONSE)
    response["CA_Results"] = [dict(V4_RESPONSE["CA_Results"][0])]
    response["CA_Results"][0][field] = value
    record_raw_post(monkeypatch, response)

    with pytest.raises(TypeError):
        conjunction.find_czml_close_approaches(
            start=START,
            stop=STOP,
            position=position(),
        )


@pytest.mark.parametrize("function_name", ["find_tle_close_approaches", "find_czml_close_approaches"])
def test_conjunction_propagates_astrox_api_error_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
) -> None:
    error = exceptions.AstroxAPIError("upstream failure", "/CAT/CA", response=None)

    def fake_post(endpoint: str, *, json: object) -> object:
        raise error

    monkeypatch.setattr(conjunction.raw, "post", fake_post)
    function = getattr(conjunction, function_name)
    kwargs: dict[str, object] = {"start": START, "stop": STOP}
    kwargs["tle" if function_name.startswith("find_tle") else "position"] = (
        PRIMARY if function_name.startswith("find_tle") else position()
    )

    with pytest.raises(exceptions.AstroxAPIError) as raised:
        function(**kwargs)
    assert raised.value is error
