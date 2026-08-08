"""Behavior tests for the public TLE value object."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from astrox import orbits
from tests.sdk.helpers import assert_canonical_equal


LINE1 = "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995"
LINE2 = "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456"


def test_tle_constructor_returns_frozen_kw_only_dataclass() -> None:
    value = orbits.tle(
        line1=LINE1,
        line2=LINE2,
        name="ISS",
        catalog_number="25544",
    )

    assert isinstance(value, orbits.Tle)
    assert is_dataclass(value)
    assert [field.name for field in fields(orbits.Tle)] == [
        "line1",
        "line2",
        "name",
        "catalog_number",
    ]
    with pytest.raises(FrozenInstanceError):
        value.line1 = "changed"


def test_tle_lowering_emits_complete_tle_info_and_lines_payloads() -> None:
    value = orbits.tle(
        line1=LINE1,
        line2=LINE2,
        name="ISS",
        catalog_number="25544",
    )

    assert_canonical_equal(
        value.to_tle_info_wire(),
        {
            "SAT_Name": "ISS",
            "SAT_Number": "25544",
            "TLE_Line1": LINE1,
            "TLE_Line2": LINE2,
        },
    )
    assert_canonical_equal(value.to_lines_wire(), [LINE1, LINE2])


def test_tle_omits_optional_metadata_without_server_defaults() -> None:
    value = orbits.tle(line1=LINE1, line2=LINE2)

    assert_canonical_equal(
        value.to_tle_info_wire(),
        {"TLE_Line1": LINE1, "TLE_Line2": LINE2},
    )
    assert_canonical_equal(value.to_lines_wire(), [LINE1, LINE2])


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"line1": 1, "line2": LINE2}, "line1 must be a string"),
        ({"line1": LINE1, "line2": 2}, "line2 must be a string"),
        ({"line1": LINE1, "line2": LINE2, "name": 1}, "name must be a string"),
        (
            {"line1": LINE1, "line2": LINE2, "catalog_number": 1},
            "catalog_number must be a string",
        ),
    ],
)
def test_tle_rejects_mistyped_fields(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(TypeError, match=message):
        orbits.tle(**kwargs)  # type: ignore[arg-type]


def test_tle_requires_keyword_arguments_and_is_public() -> None:
    with pytest.raises(TypeError):
        orbits.tle(LINE1, LINE2)  # type: ignore[call-arg]

    assert "Tle" in orbits.__all__
    assert "tle" in orbits.__all__


def test_tle_from_tle_info_wire_reuses_complete_and_prefixed_shapes() -> None:
    complete = {
        "SAT_Name": "ISS",
        "SAT_Number": "25544",
        "TLE_Line1": LINE1,
        "TLE_Line2": LINE2,
    }
    prefixed = {
        "SAT1_Name": "ISS",
        "SAT1_Number": "25544",
        "SAT1_TLE_Line1": LINE1,
        "SAT1_TLE_Line2": LINE2,
    }
    expected = orbits.tle(
        line1=LINE1,
        line2=LINE2,
        name="ISS",
        catalog_number="25544",
    )

    assert orbits.Tle.from_tle_info_wire(complete) == expected
    assert orbits.Tle.from_tle_info_wire(prefixed, prefix="SAT1") == expected


@pytest.mark.parametrize(
    "missing_field",
    ["SAT_Name", "SAT_Number", "TLE_Line1", "TLE_Line2"],
)
def test_tle_from_tle_info_wire_fails_on_missing_fields(missing_field: str) -> None:
    payload = {
        "SAT_Name": "ISS",
        "SAT_Number": "25544",
        "TLE_Line1": LINE1,
        "TLE_Line2": LINE2,
    }
    del payload[missing_field]

    with pytest.raises(KeyError):
        orbits.Tle.from_tle_info_wire(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("SAT_Name", 1),
        ("SAT_Number", 25544),
        ("TLE_Line1", []),
        ("TLE_Line2", {}),
    ],
)
def test_tle_from_tle_info_wire_fails_on_mistyped_fields(
    field: str,
    value: object,
) -> None:
    payload: dict[str, object] = {
        "SAT_Name": "ISS",
        "SAT_Number": "25544",
        "TLE_Line1": LINE1,
        "TLE_Line2": LINE2,
    }
    payload[field] = value

    with pytest.raises(TypeError):
        orbits.Tle.from_tle_info_wire(payload)


def test_tle_from_tle_info_wire_requires_mapping() -> None:
    with pytest.raises(TypeError):
        orbits.Tle.from_tle_info_wire([LINE1, LINE2])  # type: ignore[arg-type]
