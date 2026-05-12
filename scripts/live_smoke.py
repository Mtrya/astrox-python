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
import time
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


def request_with_retry(
    method: str,
    url: str,
    *,
    timeout: float,
    attempts: int = 3,
    **kwargs: Any,
) -> requests.Response:
    last_exc: requests.RequestException | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            if response.status_code < 500:
                response.raise_for_status()
                return response
            response.raise_for_status()
        except requests.RequestException as exc:
            last_exc = exc
            if attempt == attempts:
                break
            time.sleep(0.5 * 2 ** (attempt - 1))
    raise AssertionError(f"{method} {url} failed after {attempts} attempts: {last_exc}") from last_exc


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AssertionError(f"{context} must be an object")
    return value


def require_key(mapping: dict[str, Any], key: str, context: str) -> Any:
    try:
        return mapping[key]
    except KeyError as exc:
        raise AssertionError(f"{context} is missing required key {key!r}") from exc


def fetch_openapi(base_url: str, timeout: float) -> dict[str, Any]:
    response = request_with_retry("GET", f"{base_url.rstrip('/')}/openapi/v1.json", timeout=timeout)
    spec = response.json()
    return require_mapping(spec, "live OpenAPI document")


def check_live_openapi(live_spec: dict[str, Any]) -> dict[str, Any]:
    openapi_version = require_key(live_spec, "openapi", "live OpenAPI document")
    info = require_mapping(require_key(live_spec, "info", "live OpenAPI document"), "live OpenAPI info")
    info_version = require_key(info, "version", "live OpenAPI info")
    paths = require_mapping(require_key(live_spec, "paths", "live OpenAPI document"), "live OpenAPI paths")
    components = require_mapping(
        require_key(live_spec, "components", "live OpenAPI document"),
        "live OpenAPI components",
    )
    schemas = require_mapping(
        require_key(components, "schemas", "live OpenAPI components"),
        "live OpenAPI schemas",
    )

    if not paths:
        raise AssertionError("live OpenAPI paths must be a non-empty object")
    if not schemas:
        raise AssertionError("live OpenAPI schemas must be a non-empty object")

    endpoint = require_mapping(
        require_key(paths, DIRECT_SMOKE_ENDPOINT, "live OpenAPI paths"),
        f"live OpenAPI path {DIRECT_SMOKE_ENDPOINT}",
    )
    route = require_mapping(
        require_key(endpoint, "post", f"live OpenAPI path {DIRECT_SMOKE_ENDPOINT}"),
        "direct smoke route",
    )
    request_body = require_mapping(
        require_key(route, "requestBody", "direct smoke route"),
        "direct smoke requestBody",
    )
    request_content = require_mapping(
        require_key(request_body, "content", "direct smoke requestBody"),
        "direct smoke request content",
    )
    request_media = require_mapping(
        require_key(request_content, "application/json", "direct smoke request content"),
        "direct smoke request JSON media",
    )
    request_schema = require_mapping(
        require_key(request_media, "schema", "direct smoke request JSON media"),
        "direct smoke request schema",
    )
    responses = require_mapping(require_key(route, "responses", "direct smoke route"), "direct smoke responses")
    response_200 = require_mapping(require_key(responses, "200", "direct smoke responses"), "direct smoke 200 response")
    response_content = require_mapping(
        require_key(response_200, "content", "direct smoke 200 response"),
        "direct smoke response content",
    )
    response_media = require_mapping(
        require_key(response_content, "application/json", "direct smoke response content"),
        "direct smoke response JSON media",
    )
    response_schema = require_mapping(
        require_key(response_media, "schema", "direct smoke response JSON media"),
        "direct smoke response schema",
    )
    require_key(request_schema, "$ref", "direct smoke request schema")
    require_key(response_schema, "type", "direct smoke response schema")

    return {
        "openapi": openapi_version,
        "version": info_version,
        "path_count": len(paths),
        "schema_count": len(schemas),
        "direct_endpoint_in_openapi": DIRECT_SMOKE_ENDPOINT,
    }


def check_direct_endpoint(base_url: str, timeout: float) -> dict[str, Any]:
    response = request_with_retry(
        "POST",
        f"{base_url.rstrip('/')}{DIRECT_SMOKE_ENDPOINT}",
        json=DIRECT_SMOKE_PAYLOAD,
        timeout=timeout,
    )
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
