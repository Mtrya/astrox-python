#!/usr/bin/env python3
"""Verify checked-in OpenAPI fixtures against the live ASTROX server."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
import yaml

try:
    from scripts.openapi_fixtures.shapes import ShapeMismatch, assert_shape, fingerprint_shape
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from shapes import ShapeMismatch, assert_shape, fingerprint_shape


DEFAULT_BASE_URL = "http://astrox.cn:8765"
DEFAULT_FIXTURE_DIR = Path("openapi/fixtures")


def load_fixture(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} did not load as an object")
    return loaded


def iter_fixture_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.yaml") if path.is_file())


def verify_branch(
    *,
    session: requests.Session,
    base_url: str,
    timeout: float,
    endpoint: str,
    method: str,
    branch_id: str,
    branch: dict[str, Any],
) -> dict[str, Any]:
    expected = branch.get("expect", {})
    expected_status = expected.get("status")
    expected_response = expected.get("response")
    request_payload = branch.get("request")

    response = session.request(
        method,
        f"{base_url.rstrip('/')}{endpoint}",
        json=request_payload,
        timeout=timeout,
    )

    result: dict[str, Any] = {
        "endpoint": endpoint,
        "method": method,
        "branch": branch_id,
        "status": response.status_code,
        "ok": True,
    }

    if expected_status is not None and response.status_code != expected_status:
        result["ok"] = False
        result["error"] = f"expected status {expected_status}, got {response.status_code}"
        return result

    if expected_response is None:
        return result

    try:
        body = response.json()
    except ValueError as exc:
        result["ok"] = False
        result["error"] = f"response was not JSON: {exc}"
        return result

    try:
        assert_shape(body, expected_response)
    except ShapeMismatch as exc:
        result["ok"] = False
        result["error"] = str(exc)
        result["actual_shape"] = fingerprint_shape(body)
    return result


def verify_fixture(path: Path, *, session: requests.Session, base_url: str, timeout: float) -> list[dict[str, Any]]:
    fixture = load_fixture(path)
    endpoint = fixture["endpoint"]
    method = fixture.get("method", "POST").upper()
    branches = fixture.get("branches", {})
    if not isinstance(branches, dict):
        raise ValueError(f"{path} branches must be an object")

    results = []
    for branch_id, branch in sorted(branches.items()):
        if not isinstance(branch, dict):
            raise ValueError(f"{path} branch {branch_id!r} must be an object")
        result = verify_branch(
            session=session,
            base_url=base_url,
            timeout=timeout,
            endpoint=endpoint,
            method=method,
            branch_id=branch_id,
            branch=branch,
        )
        result["fixture"] = str(path)
        results.append(result)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--base-url", default=os.environ.get("ASTROX_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    paths = iter_fixture_paths(args.fixture_dir)
    results: list[dict[str, Any]] = []
    with requests.Session() as session:
        for path in paths:
            results.extend(verify_fixture(path, session=session, base_url=args.base_url, timeout=args.timeout))

    report = {
        "base_url": args.base_url,
        "fixture_count": len(paths),
        "branch_count": len(results),
        "failed_count": sum(1 for result in results if not result["ok"]),
        "results": results,
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")
    print("OPENAPI_FIXTURE_RESULT_JSON=" + json.dumps(report, sort_keys=True))
    return 1 if report["failed_count"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"OPENAPI_FIXTURE_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        raise

