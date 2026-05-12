#!/usr/bin/env python3
"""
Lightweight live smoke checks for ASTROX server reachability and schema drift.

This script is intentionally shallow. Exhaustive branch probing belongs in the
scheduled drift CI; this blocking smoke check verifies that the live OpenAPI
surface still matches the checked-in spec closely enough for normal PR work.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SPEC = REPO_ROOT / "docs" / "internal" / "astrox-web-api-260118-fixed.yaml"
GENERATED_MODELS = REPO_ROOT / "astrox" / "_models.py"
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


def extract_local_paths(spec_path: Path) -> list[str]:
    text = spec_path.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"^  (/[^:]+):$", text, flags=re.MULTILINE)))


def extract_generated_api_version(models_path: Path) -> str | None:
    text = models_path.read_text(encoding="utf-8")
    match = re.search(r"^# API Version: (.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def fetch_openapi(base_url: str, timeout: float) -> dict[str, Any]:
    response = requests.get(f"{base_url.rstrip('/')}/openapi/v1.json", timeout=timeout)
    response.raise_for_status()
    return response.json()


def check_live_paths(live_spec: dict[str, Any], local_paths: list[str]) -> dict[str, Any]:
    live_paths = live_spec["paths"]
    missing = [path for path in local_paths if path not in live_paths]
    added = sorted(path for path in live_paths if path not in set(local_paths))

    malformed_posts: list[str] = []
    for path in local_paths:
        if path not in live_paths:
            continue
        post = live_paths[path].get("post")
        if post is None:
            continue
        post["responses"]
        if "requestBody" in post:
            content = post["requestBody"]["content"]
            content["application/json"]["schema"]
        else:
            malformed_posts.append(path)

    return {
        "local_path_count": len(local_paths),
        "live_path_count": len(live_paths),
        "missing_paths": missing,
        "added_paths": added,
        "posts_without_request_body": malformed_posts,
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
    parser.add_argument(
        "--fail-on-version-drift",
        action="store_true",
        help="Fail if live OpenAPI version differs from generated local models",
    )
    args = parser.parse_args()

    local_paths = extract_local_paths(LOCAL_SPEC)
    expected_version = extract_generated_api_version(GENERATED_MODELS)
    live_spec = fetch_openapi(args.base_url, args.timeout)

    live_version = live_spec["info"]["version"]
    version_mismatch = expected_version is not None and live_version != expected_version
    if args.fail_on_version_drift and version_mismatch:
        raise AssertionError(
            f"OpenAPI version drift: generated={expected_version!r}, live={live_version!r}"
        )

    path_report = check_live_paths(live_spec, local_paths)
    if path_report["missing_paths"]:
        raise AssertionError(f"Missing live OpenAPI paths: {path_report['missing_paths']}")

    direct_report = None
    if not args.schema_only:
        direct_report = check_direct_endpoint(args.base_url, args.timeout)

    result = {
        "base_url": args.base_url,
        "generated_openapi_version": expected_version,
        "openapi_version": live_version,
        "version_mismatch": version_mismatch,
        "path_report": path_report,
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
