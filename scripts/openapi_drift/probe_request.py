#!/usr/bin/env python3
"""Probe one candidate fixture request and write branch evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

import requests
import yaml

try:
    from scripts.openapi_drift.discover import DEFAULT_OPENAPI, discover, load_spec
    from scripts.openapi_drift.generate_status import generate_status_text
    from scripts.openapi_drift.normalize import dump_fixture
    from scripts.openapi_drift.reconcile import (
        blocked_record,
        expect_from_response,
        is_empty_http_500,
        request_live_branch,
    )
    from scripts.openapi_drift.verify import (
        DEFAULT_BASE_URL,
        DEFAULT_FIXTURE_DIR,
        load_fixture,
        validate_fixture,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from discover import DEFAULT_OPENAPI, discover, load_spec
    from generate_status import generate_status_text
    from normalize import dump_fixture
    from reconcile import (
        blocked_record,
        expect_from_response,
        is_empty_http_500,
        request_live_branch,
    )
    from verify import DEFAULT_BASE_URL, DEFAULT_FIXTURE_DIR, load_fixture, validate_fixture


DEFAULT_STATUS_OUTPUT = Path("openapi/fixtures/STATUS.md")


def load_request_payload(
    *,
    request_file: Path | None,
    request_json: str | None,
    null_request: bool,
) -> tuple[bool, Any]:
    provided = [request_file is not None, request_json is not None, null_request]
    if sum(provided) > 1:
        raise ValueError("provide at most one of --request-file, --request-json, or --null-request")
    if request_file is not None:
        payload = yaml.safe_load(request_file.read_text(encoding="utf-8"))
        return True, payload
    if request_json is not None:
        return True, json.loads(request_json)
    if null_request:
        return True, None
    return False, None


def endpoint_metadata(*, openapi: Path, endpoint: str, method: str) -> dict[str, Any]:
    method = method.upper()
    matches = [
        item
        for item in discover(load_spec(openapi))
        if item["endpoint"] == endpoint and item["method"].upper() == method
    ]
    if not matches:
        raise ValueError(f"{openapi}: endpoint {method} {endpoint} was not found")
    match = matches[0]
    return {
        "schema_version": 1,
        "endpoint": match["endpoint"],
        "method": match["method"],
        "openapi_operation_id": match.get("operation_id"),
        "openapi_request_schema": match.get("request_schema"),
        "openapi_response_schema": match.get("response_schema") or "unknown",
        "branches": {},
    }


def load_or_create_fixture(
    *,
    fixture_path: Path,
    openapi: Path,
    endpoint: str | None,
    method: str | None,
) -> dict[str, Any]:
    if fixture_path.exists():
        fixture = load_fixture(fixture_path)
        if endpoint is not None and fixture["endpoint"] != endpoint:
            raise ValueError(f"{fixture_path}: endpoint is {fixture['endpoint']!r}, not {endpoint!r}")
        if method is not None and fixture["method"].upper() != method.upper():
            raise ValueError(f"{fixture_path}: method is {fixture['method']!r}, not {method!r}")
        return fixture
    if endpoint is None or method is None:
        raise ValueError("creating a new fixture requires --endpoint and --method")
    return endpoint_metadata(openapi=openapi, endpoint=endpoint, method=method)


def branch_from_response(
    *,
    response: requests.Response,
    request_present: bool,
    request_payload: Any,
    today: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if is_empty_http_500(response):
        blocked = blocked_record(
            reason="empty_http_500",
            status=500,
            content_type="",
            observed_shape=None,
            today=today,
            note="Candidate request returned an empty HTTP 500.",
        )
        branch: dict[str, Any] = {"state": "blocked"}
        if request_present:
            branch["request"] = request_payload
        branch["blocked"] = blocked
        return branch, {
            "action": "write_blocked",
            "classification": "candidate_empty_http_500",
            "changed": True,
            "status": 500,
            "actual_content_type": "",
            "new_blocked": blocked,
        }

    expect, failure = expect_from_response(response)
    if failure is not None:
        return None, failure

    branch = {"state": "verified"}
    if request_present:
        branch["request"] = request_payload
    branch["expect"] = expect
    return branch, {
        "action": "write_verified",
        "classification": "candidate_verified",
        "changed": True,
        "status": response.status_code,
        "actual_content_type": expect["content_type"],
        "new_expect": expect,
    }


def build_probe_report(
    *,
    fixture_path: Path,
    fixture: dict[str, Any],
    branch_id: str,
    mode: str,
    result: dict[str, Any],
    status_updated: bool,
) -> dict[str, Any]:
    return {
        "mode": mode,
        "fixture": str(fixture_path),
        "endpoint": fixture["endpoint"],
        "method": fixture["method"].upper(),
        "branch": branch_id,
        "changed": bool(result.get("changed")),
        "status_updated": status_updated,
        **result,
    }


def probe_request_branch(
    *,
    fixture_path: Path,
    branch_id: str,
    request_present: bool,
    request_payload: Any,
    base_url: str,
    timeout: float,
    apply: bool,
    replace: bool,
    openapi: Path = DEFAULT_OPENAPI,
    fixture_dir: Path = DEFAULT_FIXTURE_DIR,
    status_output: Path = DEFAULT_STATUS_OUTPUT,
    endpoint: str | None = None,
    method: str | None = None,
    today: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    today = today or date.today().isoformat()
    fixture = load_or_create_fixture(
        fixture_path=fixture_path,
        openapi=openapi,
        endpoint=endpoint,
        method=method,
    )
    branches = fixture["branches"]
    if branch_id in branches and not replace:
        raise ValueError(f"{fixture_path}: branch {branch_id!r} already exists; pass --replace to overwrite it")

    candidate = {}
    if request_present:
        candidate["request"] = request_payload

    owns_session = session is None
    if session is None:
        session = requests.Session()
    try:
        response, failure = request_live_branch(
            session=session,
            base_url=base_url,
            timeout=timeout,
            endpoint=fixture["endpoint"],
            method=fixture["method"].upper(),
            branch=candidate,
        )
    finally:
        if owns_session:
            session.close()

    status_updated = False
    if failure is not None:
        result = failure
    else:
        assert response is not None
        new_branch, result = branch_from_response(
            response=response,
            request_present=request_present,
            request_payload=request_payload,
            today=today,
        )
        if new_branch is not None and apply:
            branches[branch_id] = new_branch
            validate_fixture(fixture, path=fixture_path)
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")
            status_text = generate_status_text(openapi=openapi, fixture_dir=fixture_dir)
            current = status_output.read_text(encoding="utf-8") if status_output.exists() else None
            if current != status_text:
                status_output.write_text(status_text, encoding="utf-8")
                status_updated = True

    return build_probe_report(
        fixture_path=fixture_path,
        fixture=fixture,
        branch_id=branch_id,
        mode="apply" if apply else "dry-run",
        result=result,
        status_updated=status_updated,
    )


def write_outputs(*, report: dict[str, Any], json_output: Path | None) -> None:
    if json_output is not None:
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True, help="Fixture YAML path to create or update")
    parser.add_argument("--branch", required=True, help="Branch name to write")
    parser.add_argument("--endpoint", help="Endpoint path, required when creating a new fixture")
    parser.add_argument("--method", help="HTTP method, required when creating a new fixture")
    parser.add_argument("--request-file", type=Path, help="YAML or JSON request payload file")
    parser.add_argument("--request-json", help="Inline JSON request payload")
    parser.add_argument("--null-request", action="store_true", help="Write an explicit null request")
    parser.add_argument("--replace", action="store_true", help="Allow overwriting an existing branch")
    parser.add_argument("--base-url", default=os.environ.get("ASTROX_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--openapi", type=Path, default=DEFAULT_OPENAPI)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--status-output", type=Path, default=DEFAULT_STATUS_OUTPUT)
    parser.add_argument("--json-output", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="probe and report without editing files")
    mode.add_argument("--apply", action="store_true", help="write verified or blocked branch evidence")
    args = parser.parse_args()

    request_present, request_payload = load_request_payload(
        request_file=args.request_file,
        request_json=args.request_json,
        null_request=args.null_request,
    )
    report = probe_request_branch(
        fixture_path=args.fixture,
        branch_id=args.branch,
        request_present=request_present,
        request_payload=request_payload,
        base_url=args.base_url,
        timeout=args.timeout,
        apply=args.apply,
        replace=args.replace,
        openapi=args.openapi,
        fixture_dir=args.fixture_dir,
        status_output=args.status_output,
        endpoint=args.endpoint,
        method=args.method,
    )
    write_outputs(report=report, json_output=args.json_output)
    print("OPENAPI_FIXTURE_PROBE_JSON=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"OPENAPI_FIXTURE_PROBE_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        raise
