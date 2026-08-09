#!/usr/bin/env python3
"""Live snapshot validation for catalog query functions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import catalog  # noqa: E402
from tests.validation._support import (  # noqa: E402
    LiveSnapshotCase,
    SnapshotError,
    check_snapshot,
    configure_astrox_from_env,
    main as snapshot_main,
)


SNAPSHOT_PATH = Path(__file__).with_name("catalog.snap.json")


def _record_shape(value: Any, *, field: str) -> dict[str, Any]:
    if value is None:
        return {"kind": "null"}
    if not isinstance(value, list):
        raise SnapshotError(f"{field} must be a list or null")
    if not value:
        return {"kind": "array", "item_keys": []}
    if not all(isinstance(item, dict) for item in value):
        raise SnapshotError(f"{field} must contain object records")
    return {
        "kind": "array",
        "item_keys": {
            str(key): True
            for key in sorted({str(key) for item in value for key in item})
        },
    }


def _catalog_shape(response: Any, *, collection_field: str) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise SnapshotError("catalog response must be an object")
    for key in ("IsSuccess", "Message", collection_field):
        if key not in response:
            raise SnapshotError(f"catalog response missing {key}")
    if not isinstance(response["IsSuccess"], bool):
        raise SnapshotError("catalog IsSuccess must be a boolean")
    if not isinstance(response["Message"], str):
        raise SnapshotError("catalog Message must be a string")
    return {
        "response_keys": sorted(str(key) for key in response),
        "IsSuccess": response["IsSuccess"],
        "Message": response["Message"],
        collection_field: _record_shape(response[collection_field], field=collection_field),
    }


def query_city_shape() -> dict[str, Any]:
    return _catalog_shape(
        catalog.query_cities(city_name="Beijing"),
        collection_field="Cities",
    )


def query_facility_shape() -> dict[str, Any]:
    return _catalog_shape(
        catalog.query_facilities(facility_name="Goldstone"),
        collection_field="Facilities",
    )


def query_satellite_shape() -> dict[str, Any]:
    return _catalog_shape(
        catalog.query_satellites(name="FENGYUN", active=True),
        collection_field="TLEs",
    )


CASES = [
    LiveSnapshotCase(
        id="query_cities_by_name",
        description="Stable response envelope and record keys for a named city query.",
        run=query_city_shape,
    ),
    LiveSnapshotCase(
        id="query_facilities_by_name",
        description="Stable response envelope and record keys for a named facility query.",
        run=query_facility_shape,
    ),
    LiveSnapshotCase(
        id="query_satellites_by_name_active",
        description="Stable response envelope and record keys for an active satellite query; database rows are intentionally not frozen.",
        run=query_satellite_shape,
    ),
]


def test_catalog_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(cases=CASES, snapshot_path=SNAPSHOT_PATH)


def _main() -> int:
    try:
        return snapshot_main(cases=CASES, snapshot_path=SNAPSHOT_PATH)
    except Exception as exc:
        print(f"LIVE_SNAPSHOT_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
