"""Deterministic behavior tests for CAT endpoint surfaces."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass
from fractions import Fraction
from inspect import signature
from typing import Any

import pytest

from astrox import cat, exceptions, orbits
from tests.sdk.helpers import assert_canonical_equal


LINE1 = "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995"
LINE2 = "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456"
START = "2024-01-01T00:00:00.000Z"
MOTHER = orbits.tle(line1=LINE1, line2=LINE2, name="ISS", catalog_number="25544")

GET_TLE_RESPONSE = {
    "SAT_Name": "generated",
    "SAT_Number": "25544",
    "TLE_Line1": LINE1,
    "TLE_Line2": LINE2,
}
LIFETIME_RESPONSE = {"IsSuccess": True, "Message": "OK", "LifeYears": 25}
DEBRIS_RESPONSE: dict[str, Any] = {
    "IsSuccess": True,
    "Message": "OK",
    "DebrisTLEs": [
        {
            "SAT_Name": "ISS Debris",
            "SAT_Number": "AF000",
            "TLE_Line1": LINE1,
            "TLE_Line2": LINE2,
        }
    ],
    "AzElVel": [[40.0, 0.0, 10.0, 0.002]],
    "LifeYears": [25],
    "AltitudeOfPerigee": [418.5],
    "AltitudeOfApogee": [461.2],
    "Periods": [93.3],
}


def record_raw_post(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_post(endpoint: str, *, json: object) -> object:
        calls.append({"endpoint": endpoint, "json": json})
        return response

    monkeypatch.setattr(cat.raw, "post", fake_post)
    return calls


def _generate_tle_kwargs() -> dict[str, object]:
    return {
        "name": "generated",
        "catalog_number": "25544",
        "epoch": START,
        "bstar": 0.0,
        "semi_major_axis_km": 6794.0,
        "eccentricity": 0.0,
        "inclination_deg": 0.0,
        "argument_of_perigee_deg": 0.0,
        "raan_deg": 0.0,
        "true_anomaly_deg": 0.0,
    }


def test_cat_public_exports_and_optional_signature_defaults() -> None:
    import astrox

    assert astrox.cat is cat
    assert "cat" in astrox.__all__
    assert set(cat.__all__) >= {
        "DebrisBreakupResult",
        "DebrisImpulse",
        "TleLifetimeResult",
        "estimate_tle_lifetime",
        "generate_tle",
        "simulate_debris_breakup_simple",
        "simulate_debris_breakup",
        "simulate_debris_breakup_nasa",
    }
    assert signature(cat.estimate_tle_lifetime).parameters["sm"].default is None
    assert signature(cat.estimate_tle_lifetime).parameters["mass"].default is None


def test_debris_impulse_is_frozen_and_lowers_exact_row() -> None:
    impulse = cat.DebrisImpulse(
        azimuth_deg=40.0,
        elevation_deg=0.0,
        delta_v_m_s=10.0,
        area_to_mass_ratio_m2_kg=0.002,
    )

    assert is_dataclass(impulse)
    assert [field.name for field in fields(cat.DebrisImpulse)] == [
        "azimuth_deg",
        "elevation_deg",
        "delta_v_m_s",
        "area_to_mass_ratio_m2_kg",
    ]
    assert_canonical_equal(impulse.to_wire(), [40.0, 0.0, 10.0, 0.002])
    with pytest.raises(FrozenInstanceError):
        impulse.delta_v_m_s = 11.0


def test_generate_tle_lowers_exact_payload_and_returns_tle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, GET_TLE_RESPONSE)

    result = cat.generate_tle(
        name="generated",
        catalog_number="25544",
        epoch=START,
        bstar=0.00004142,
        semi_major_axis_km=6794.0,
        eccentricity=0.0001882,
        inclination_deg=51.6461,
        argument_of_perigee_deg=64.8995,
        raan_deg=339.8014,
        true_anomaly_deg=295.2305,
        is_mean_elements=False,
    )

    assert result == orbits.tle(
        line1=LINE1,
        line2=LINE2,
        name="generated",
        catalog_number="25544",
    )
    assert calls[0]["endpoint"] == "/CAT/GetTLE"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "Name": "generated",
            "SSC": "25544",
            "Epoch": START,
            "BStar": 0.00004142,
            "Sma": 6794.0,
            "Ecc": 0.0001882,
            "Inc": 51.6461,
            "W": 64.8995,
            "RAAN": 339.8014,
            "TA": 295.2305,
            "IsMeanElements": False,
        },
    )


def test_cat_real_numbers_lower_to_json_compatible_floats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, GET_TLE_RESPONSE)

    cat.generate_tle(
        name="generated",
        catalog_number="25544",
        epoch=START,
        bstar=Fraction(1, 100),
        semi_major_axis_km=Fraction(6794),
        eccentricity=Fraction(1, 1000),
        inclination_deg=Fraction(51, 1),
        argument_of_perigee_deg=Fraction(64, 1),
        raan_deg=Fraction(339, 1),
        true_anomaly_deg=Fraction(295, 1),
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "Name": "generated",
            "SSC": "25544",
            "Epoch": START,
            "BStar": 0.01,
            "Sma": 6794.0,
            "Ecc": 0.001,
            "Inc": 51.0,
            "W": 64.0,
            "RAAN": 339.0,
            "TA": 295.0,
        },
    )
    impulse = cat.DebrisImpulse(
        azimuth_deg=Fraction(40),
        elevation_deg=Fraction(1, 2),
        delta_v_m_s=Fraction(10),
        area_to_mass_ratio_m2_kg=Fraction(1, 500),
    )
    assert impulse.to_wire() == [40.0, 0.5, 10.0, 0.002]


def test_generate_tle_omits_server_default_mean_elements_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, GET_TLE_RESPONSE)

    cat.generate_tle(
        name="generated",
        catalog_number="25544",
        epoch=START,
        bstar=0.0,
        semi_major_axis_km=6794.0,
        eccentricity=0.0,
        inclination_deg=0.0,
        argument_of_perigee_deg=0.0,
        raan_deg=0.0,
        true_anomaly_deg=0.0,
    )

    assert "IsMeanElements" not in calls[0]["json"]


@pytest.mark.parametrize("missing_field", ["SAT_Name", "SAT_Number", "TLE_Line1", "TLE_Line2"])
def test_generate_tle_parser_fails_on_missing_returned_fields(
    monkeypatch: pytest.MonkeyPatch,
    missing_field: str,
) -> None:
    response = dict(GET_TLE_RESPONSE)
    del response[missing_field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        cat.generate_tle(**_generate_tle_kwargs())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("SAT_Name", 1),
        ("SAT_Number", 25544),
        ("TLE_Line1", []),
        ("TLE_Line2", {}),
    ],
)
def test_generate_tle_parser_rejects_mistyped_returned_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    response = dict(GET_TLE_RESPONSE)
    response[field] = value
    record_raw_post(monkeypatch, response)

    with pytest.raises(TypeError):
        cat.generate_tle(**_generate_tle_kwargs())  # type: ignore[arg-type]


def test_estimate_tle_lifetime_lowers_tle_info_and_parses_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, LIFETIME_RESPONSE)

    result = cat.estimate_tle_lifetime(
        epoch=START,
        tle=MOTHER,
        sm=0.01,
        mass=100.0,
    )

    assert asdict(result) == {
        "is_success": True,
        "message": "OK",
        "life_years": 25.0,
    }
    assert_canonical_equal(
        calls[0]["json"],
        {"Epoch": START, "TLEs": MOTHER.to_tle_info_wire(), "Sm": 0.01, "Mass": 100.0},
    )


def test_estimate_tle_lifetime_omits_unknown_optional_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, LIFETIME_RESPONSE)

    cat.estimate_tle_lifetime(epoch=START, tle=MOTHER)

    assert_canonical_equal(
        calls[0]["json"],
        {"Epoch": START, "TLEs": MOTHER.to_tle_info_wire()},
    )


@pytest.mark.parametrize("missing_field", ["IsSuccess", "Message", "LifeYears"])
def test_tle_lifetime_parser_fails_on_missing_fields(
    monkeypatch: pytest.MonkeyPatch,
    missing_field: str,
) -> None:
    response = dict(LIFETIME_RESPONSE)
    del response[missing_field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        cat.estimate_tle_lifetime(epoch=START, tle=MOTHER)


@pytest.mark.parametrize(
    ("field", "value"),
    [("IsSuccess", "true"), ("Message", 1), ("LifeYears", "25")],
)
def test_tle_lifetime_parser_rejects_mistyped_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    response = dict(LIFETIME_RESPONSE)
    response[field] = value
    record_raw_post(monkeypatch, response)

    with pytest.raises(TypeError):
        cat.estimate_tle_lifetime(epoch=START, tle=MOTHER)


def test_debris_breakup_simple_lowers_exact_payload_and_parses_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, DEBRIS_RESPONSE)

    result = cat.simulate_debris_breakup_simple(
        mother_tle=MOTHER,
        epoch=START,
        count=2,
        ssc_prefix="AF",
        delta_v_m_s=10.0,
        area_to_mass_ratio_m2_kg=0.002,
        min_azimuth_deg=40.0,
        max_azimuth_deg=180.0,
        min_elevation_deg=0.0,
        max_elevation_deg=2.0,
        compute_lifetime=False,
    )

    assert isinstance(result.debris_tles[0], orbits.Tle)
    assert isinstance(result.impulses[0], cat.DebrisImpulse)
    assert_canonical_equal(
        asdict(result),
        {
            "is_success": True,
            "message": "OK",
            "debris_tles": [
                {
                    "line1": LINE1,
                    "line2": LINE2,
                    "name": "ISS Debris",
                    "catalog_number": "AF000",
                }
            ],
            "impulses": [
                {
                    "azimuth_deg": 40.0,
                    "elevation_deg": 0.0,
                    "delta_v_m_s": 10.0,
                    "area_to_mass_ratio_m2_kg": 0.002,
                }
            ],
            "life_years": [25.0],
            "altitude_of_perigee_km": [418.5],
            "altitude_of_apogee_km": [461.2],
            "periods_min": [93.3],
        },
    )
    assert calls[0]["endpoint"] == "/CAT/DebrisBreakupSimple"
    assert_canonical_equal(
        calls[0]["json"],
        {
            "MotherSate": MOTHER.to_tle_info_wire(),
            "Epoch": START,
            "Count": 2,
            "SSC_Pre": "AF",
            "DeltaV": 10.0,
            "A2M": 0.002,
            "MinAzimuth": 40.0,
            "MaxAzimuth": 180.0,
            "MinElevation": 0.0,
            "MaxElevation": 2.0,
            "ComputeLifeOfTime": False,
        },
    )


def test_debris_breakup_explicit_rows_reject_raw_nested_lists_and_lowers_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, DEBRIS_RESPONSE)
    impulse = cat.DebrisImpulse(
        azimuth_deg=0.0,
        elevation_deg=0.0,
        delta_v_m_s=10.0,
        area_to_mass_ratio_m2_kg=0.002,
    )

    cat.simulate_debris_breakup(
        mother_tle=MOTHER,
        epoch=START,
        impulses=[impulse],
        ssc_prefix="AF",
        area_to_mass_ratio_m2_kg=0.002,
        compute_lifetime=False,
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "MotherSate": MOTHER.to_tle_info_wire(),
            "Epoch": START,
            "SSC_Pre": "AF",
            "A2M": 0.002,
            "AzElVel": [[0.0, 0.0, 10.0, 0.002]],
            "ComputeLifeOfTime": False,
        },
    )

    with pytest.raises(TypeError):
        cat.simulate_debris_breakup(
            mother_tle=MOTHER,
            epoch=START,
            impulses=[[0.0, 0.0, 10.0, 0.002]],  # type: ignore[list-item]
        )


def test_debris_breakup_nasa_uses_neutral_unresolved_input_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_post(monkeypatch, DEBRIS_RESPONSE)

    cat.simulate_debris_breakup_nasa(
        mother_tle=MOTHER,
        epoch=START,
        ssc_prefix="AF",
        total_mass=100.0,
        minimum_characteristic_length=0.1,
    )

    assert_canonical_equal(
        calls[0]["json"],
        {
            "MotherSate": MOTHER.to_tle_info_wire(),
            "Epoch": START,
            "SSC_Pre": "AF",
            "MassTotal": 100.0,
            "MinLc": 0.1,
        },
    )


@pytest.mark.parametrize(
    ("function_name", "kwargs"),
    [
        ("estimate_tle_lifetime", {"epoch": START, "tle": {"TLE_Line1": LINE1}}),
        (
            "simulate_debris_breakup_simple",
            {"mother_tle": {"TLE_Line1": LINE1}, "epoch": START},
        ),
        (
            "simulate_debris_breakup_nasa",
            {"mother_tle": {"TLE_Line1": LINE1}, "epoch": START},
        ),
    ],
)
def test_cat_rejects_raw_tle_fragments(
    function_name: str,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(TypeError):
        getattr(cat, function_name)(**kwargs)


@pytest.mark.parametrize(
    "field",
    [
        "IsSuccess",
        "Message",
        "DebrisTLEs",
        "AzElVel",
        "LifeYears",
        "AltitudeOfPerigee",
        "AltitudeOfApogee",
        "Periods",
    ],
)
def test_debris_parser_fails_loudly_for_missing_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    response = dict(DEBRIS_RESPONSE)
    del response[field]
    record_raw_post(monkeypatch, response)
    with pytest.raises(KeyError):
        cat.simulate_debris_breakup_simple(mother_tle=MOTHER, epoch=START)


@pytest.mark.parametrize(
    "field",
    ["SAT_Name", "SAT_Number", "TLE_Line1", "TLE_Line2"],
)
def test_debris_parser_fails_on_nested_tle_missing_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    response = dict(DEBRIS_RESPONSE)
    response["DebrisTLEs"] = [dict(DEBRIS_RESPONSE["DebrisTLEs"][0])]
    del response["DebrisTLEs"][0][field]
    record_raw_post(monkeypatch, response)

    with pytest.raises(KeyError):
        cat.simulate_debris_breakup_simple(mother_tle=MOTHER, epoch=START)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("SAT_Name", 1),
        ("SAT_Number", 25544),
        ("TLE_Line1", []),
        ("TLE_Line2", {}),
    ],
)
def test_debris_parser_rejects_mistyped_nested_tle_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    response = dict(DEBRIS_RESPONSE)
    response["DebrisTLEs"] = [dict(DEBRIS_RESPONSE["DebrisTLEs"][0])]
    response["DebrisTLEs"][0][field] = value
    record_raw_post(monkeypatch, response)

    with pytest.raises(TypeError):
        cat.simulate_debris_breakup_simple(mother_tle=MOTHER, epoch=START)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("IsSuccess", "true"),
        ("Message", 1),
        ("DebrisTLEs", {}),
        ("AzElVel", {}),
        ("AzElVel", [[0.0, 0.0, 10.0]]),
        ("AzElVel", [[0.0, 0.0, 10.0, "0.002"]]),
        ("LifeYears", ["25"]),
        ("AltitudeOfPerigee", [True]),
        ("AltitudeOfApogee", [None]),
        ("Periods", [False]),
    ],
)
def test_debris_parser_rejects_mistyped_fields(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    response = dict(DEBRIS_RESPONSE)
    response[field] = value
    record_raw_post(monkeypatch, response)

    with pytest.raises(TypeError):
        cat.simulate_debris_breakup_simple(mother_tle=MOTHER, epoch=START)


@pytest.mark.parametrize(
    "field",
    [
        "DebrisTLEs",
        "AzElVel",
        "LifeYears",
        "AltitudeOfPerigee",
        "AltitudeOfApogee",
        "Periods",
    ],
)
def test_debris_parser_rejects_unsynchronized_output_arrays(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    response = dict(DEBRIS_RESPONSE)
    values = response[field]
    response[field] = [*values, values[0]]
    record_raw_post(monkeypatch, response)

    with pytest.raises(TypeError, match="synchronized"):
        cat.simulate_debris_breakup_simple(mother_tle=MOTHER, epoch=START)


@pytest.mark.parametrize(
    "function_name",
    [
        "generate_tle",
        "estimate_tle_lifetime",
        "simulate_debris_breakup_simple",
        "simulate_debris_breakup",
        "simulate_debris_breakup_nasa",
    ],
)
def test_cat_propagates_astrox_api_error_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
) -> None:
    error = exceptions.AstroxAPIError("upstream failure", "/CAT", response=None)

    def fake_post(endpoint: str, *, json: object) -> object:
        raise error

    monkeypatch.setattr(cat.raw, "post", fake_post)
    if function_name == "generate_tle":
        kwargs: dict[str, object] = {
            "name": "generated",
            "catalog_number": "25544",
            "epoch": START,
            "bstar": 0.0,
            "semi_major_axis_km": 6794.0,
            "eccentricity": 0.0,
            "inclination_deg": 0.0,
            "argument_of_perigee_deg": 0.0,
            "raan_deg": 0.0,
            "true_anomaly_deg": 0.0,
        }
    elif function_name == "estimate_tle_lifetime":
        kwargs = {"epoch": START, "tle": MOTHER}
    elif function_name == "simulate_debris_breakup":
        kwargs = {
            "mother_tle": MOTHER,
            "epoch": START,
            "impulses": [
                cat.DebrisImpulse(
                    azimuth_deg=0.0,
                    elevation_deg=0.0,
                    delta_v_m_s=10.0,
                    area_to_mass_ratio_m2_kg=0.002,
                )
            ],
        }
    else:
        kwargs = {"mother_tle": MOTHER, "epoch": START}

    with pytest.raises(exceptions.AstroxAPIError) as raised:
        getattr(cat, function_name)(**kwargs)
    assert raised.value is error
