#!/usr/bin/env python3
"""
Lightweight live smoke checks for ASTROX server reachability and basic schema.

This script is intentionally shallow. Exhaustive branch probing belongs in the
scheduled drift CI; this blocking smoke check verifies that the live OpenAPI
surface is parseable and that one tiny direct endpoint route still works.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import requests


DEFAULT_BASE_URL = "http://astrox.cn:8765"

DIRECT_SMOKE_ENDPOINT = "/OrbitConvert/Kepler2RV"
DIRECT_SMOKE_PAYLOAD = {
    "SemimajorAxis": 6778137.0,
    "Eccentricity": 0.0,
    "Inclination": 0.0,
    "ArgumentOfPeriapsis": 0.0,
    "RightAscensionOfAscendingNode": 0.0,
    "TrueAnomaly": 0.0,
    "GravitationalParameter": 3.986004418e14,
}


def fetch_openapi(base_url: str, timeout: float) -> dict[str, Any]:
    response = requests.get(f"{base_url.rstrip('/')}/openapi/v1.json", timeout=timeout)
    response.raise_for_status()
    return response.json()


def check_live_openapi(live_spec: dict[str, Any]) -> dict[str, Any]:
    openapi_version = live_spec["openapi"]
    info_version = live_spec["info"]["version"]
    paths = live_spec["paths"]
    schemas = live_spec["components"]["schemas"]

    if not isinstance(paths, dict) or not paths:
        raise AssertionError("live OpenAPI paths must be a non-empty object")
    if not isinstance(schemas, dict) or not schemas:
        raise AssertionError("live OpenAPI schemas must be a non-empty object")

    route = paths[DIRECT_SMOKE_ENDPOINT]["post"]
    request_schema = route["requestBody"]["content"]["application/json"]["schema"]
    response_schema = route["responses"]["200"]["content"]["application/json"]["schema"]
    request_schema["$ref"]
    response_schema["type"]

    return {
        "openapi": openapi_version,
        "version": info_version,
        "path_count": len(paths),
        "schema_count": len(schemas),
        "direct_endpoint_in_openapi": DIRECT_SMOKE_ENDPOINT,
    }


def check_direct_endpoint(base_url: str, timeout: float) -> dict[str, Any]:
    response = requests.post(
        f"{base_url.rstrip('/')}{DIRECT_SMOKE_ENDPOINT}",
        json=DIRECT_SMOKE_PAYLOAD,
        timeout=timeout,
    )
    response.raise_for_status()
    body = response.json()

    if not isinstance(body, list) or len(body) != 6:
        raise AssertionError(f"{DIRECT_SMOKE_ENDPOINT} returned unexpected body: {body}")

    return {
        "endpoint": DIRECT_SMOKE_ENDPOINT,
        "state_vector_length": len(body),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("ASTROX_BASE_URL", DEFAULT_BASE_URL),
        help="ASTROX server base URL",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Skip the tiny direct endpoint probe",
    )
    args = parser.parse_args()

    live_spec = fetch_openapi(args.base_url, args.timeout)
    openapi_report = check_live_openapi(live_spec)

    direct_report = None
    if not args.schema_only:
        direct_report = check_direct_endpoint(args.base_url, args.timeout)

    result = {
        "base_url": args.base_url,
        "openapi": openapi_report,
        "direct_probe": direct_report,
    }
    print("LIVE_SMOKE_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LIVE_SMOKE_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        raise
