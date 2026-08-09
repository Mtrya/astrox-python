"""Deterministic behavior tests for catalog query functions."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from astrox import catalog, exceptions
from tests.sdk.helpers import assert_canonical_equal


CITY_RESPONSE = {
    "IsSuccess": True,
    "Message": "Success",
    "Cities": [{"CityName": "Beijing", "Latitude": 0.6969}],
}
FACILITY_RESPONSE = {
    "IsSuccess": True,
    "Message": "Success",
    "Facilities": [{"FacilityName": "Goldstone", "Latitude": 0.6177}],
}
SATELLITE_RESPONSE = {
    "IsSuccess": True,
    "Message": "Success",
    "TotalCount": 1,
    "TLEs": [{"CommonName": "FENGYUN 3A", "Inclination": 1.72}],
}


def record_raw_get(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_get(endpoint: str, *, params: dict[str, Any]) -> object:
        calls.append({"endpoint": endpoint, "params": params})
        return response

    monkeypatch.setattr(catalog.raw, "get", fake_get)
    return calls


def test_catalog_public_exports() -> None:
    import astrox

    assert astrox.catalog is catalog
    assert "catalog" in astrox.__all__
    assert set(catalog.__all__) == {
        "query_cities",
        "query_facilities",
        "query_satellites",
    }


def test_query_cities_lowers_complete_params_and_returns_raw_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_get(monkeypatch, CITY_RESPONSE)

    response = catalog.query_cities(
        city_name="Beijing",
        province_name="Beijing",
        country_name="China",
        city_type="NationalCapital",
    )

    assert response == {"Cities": [{"CityName": "Beijing", "Latitude": 0.6969}]}
    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/city",
            "params": {
                "cityName": "Beijing",
                "provinceName": "Beijing",
                "countryName": "China",
                "typeOfCity": "NationalCapital",
            },
        },
    )


def test_query_facilities_omits_unsupplied_filters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_get(monkeypatch, FACILITY_RESPONSE)

    response = catalog.query_facilities(facility_name="Goldstone")

    assert response == {"Facilities": [{"FacilityName": "Goldstone", "Latitude": 0.6177}]}
    assert_canonical_equal(
        calls[0],
        {"endpoint": "/facility", "params": {"facilityName": "Goldstone"}},
    )


def test_query_satellites_lowers_units_and_server_spelling_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_get(monkeypatch, SATELLITE_RESPONSE)

    response = catalog.query_satellites(
        name="FENGYUN",
        catalog_number="12345",
        mission="Comm",
        owner="PRC",
        active=True,
        minimum_perigee_m=Fraction(800_000),
        maximum_perigee_m=900_000,
        minimum_apogee_m=Fraction(1_000_000),
        maximum_apogee_m=1_100_000,
        minimum_inclination_deg=10,
        maximum_inclination_deg=80,
    )

    assert response == {
        "TotalCount": 1,
        "TLEs": [{"CommonName": "FENGYUN 3A", "Inclination": 1.72}],
    }
    assert_canonical_equal(
        calls[0],
        {
            "endpoint": "/ssc",
            "params": {
                "sscName": "FENGYUN",
                "sscNumber": "12345",
                "mission": "Comm",
                "owner": "PRC",
                "active": "true",
                "minimumPerigee": 800_000.0,
                "maximumPerigee": 900_000.0,
                "minmumApogee": 1_000_000.0,
                "maximumApogee": 1_100_000.0,
                "minimumInclination": 10.0,
                "maximumInclination": 80.0,
            },
        },
    )


def test_query_satellites_omits_all_optional_filters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = record_raw_get(monkeypatch, SATELLITE_RESPONSE)

    catalog.query_satellites()

    assert_canonical_equal(calls[0], {"endpoint": "/ssc", "params": {}})


@pytest.mark.parametrize(
    ("kwargs", "parameter"),
    [
        ({"city_name": 1}, "city_name"),
        ({"facility_name": 1}, "facility_name"),
        ({"active": "true"}, "active"),
        ({"minimum_apogee_m": True}, "minimum_apogee_m"),
    ],
)
def test_catalog_rejects_mistyped_filters(
    kwargs: dict[str, Any],
    parameter: str,
) -> None:
    function = (
        catalog.query_cities
        if "city_name" in kwargs
        else catalog.query_facilities
        if "facility_name" in kwargs
        else catalog.query_satellites
    )
    with pytest.raises(TypeError, match=parameter):
        function(**kwargs)


def test_catalog_propagates_api_errors_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = exceptions.AstroxAPIError("catalog failed", "/city", response=None)

    def fake_get(endpoint: str, *, params: dict[str, Any]) -> object:
        assert endpoint == "/city"
        assert params == {"cityName": "Beijing"}
        raise error

    monkeypatch.setattr(catalog.raw, "get", fake_get)

    with pytest.raises(exceptions.AstroxAPIError) as exc_info:
        catalog.query_cities(city_name="Beijing")

    assert exc_info.value is error
