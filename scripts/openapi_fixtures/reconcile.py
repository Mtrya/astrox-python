#!/usr/bin/env python3
"""Conservatively reconcile existing OpenAPI fixture branches against ASTROX."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import requests

try:
    from scripts.openapi_fixtures.normalize import dump_fixture
    from scripts.openapi_fixtures.shapes import response_kind
    from scripts.openapi_fixtures.verify import (
        DEFAULT_BASE_URL,
        DEFAULT_FIXTURE_DIR,
        iter_fixture_paths,
        load_fixture,
        request_kwargs,
        validate_fixture,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from normalize import dump_fixture
    from shapes import response_kind
    from verify import (
        DEFAULT_BASE_URL,
        DEFAULT_FIXTURE_DIR,
        iter_fixture_paths,
        load_fixture,
        request_kwargs,
        validate_fixture,
    )


JSON_MEDIA_TYPES = {"application/json"}
DEFAULT_OPENAPI = Path("openapi/astrox.openapi.yaml")
DEFAULT_OUTPUT = Path("openapi/fixtures/STATUS.md")


def media_type(value: str) -> str:
    """Return a normalized media type without parameters."""
    return value.split(";", 1)[0].strip().lower()


def is_json_media_type(value: str) -> bool:
    normalized = media_type(value)
    return normalized in JSON_MEDIA_TYPES or normalized.endswith("+json")


def is_text_media_type(value: str) -> bool:
    return media_type(value).startswith("text/")


def unique_shapes(shapes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {json.dumps(shape, sort_keys=True): shape for shape in shapes}
    return [by_key[key] for key in sorted(by_key)]


def shape_from_value(value: Any, previous_shape: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a fixture-safe structural response shape from a decoded JSON value."""
    kind = response_kind(value)
    shape: dict[str, Any] = {"kind": kind}
    if (
        previous_shape
        and previous_shape.get("kind") == kind
        and "const" in previous_shape
        and previous_shape["const"] == value
        and kind != "json_number"
    ):
        shape["const"] = previous_shape["const"]

    if isinstance(value, list):
        shape["length"] = len(value)
        if value:
            previous_item_shape = None
            if isinstance(previous_shape, dict):
                previous_item_shape = previous_shape.get("items")
            item_shapes = [
                shape_from_value(
                    item,
                    previous_item_shape if isinstance(previous_item_shape, dict) else None,
                )
                for item in value
            ]
            alternatives = unique_shapes(item_shapes)
            shape["items"] = alternatives[0] if len(alternatives) == 1 else {"any_of": alternatives}
    elif isinstance(value, dict):
        previous_fields = previous_shape.get("fields", {}) if isinstance(previous_shape, dict) else {}
        if not isinstance(previous_fields, dict):
            previous_fields = {}
        keys = sorted(value)
        shape["required_fields"] = keys
        shape["fields"] = {
            key: shape_from_value(
                value[key],
                previous_fields.get(key) if isinstance(previous_fields.get(key), dict) else None,
            )
            for key in keys
        }
    return shape


def text_shape(value: str) -> dict[str, Any]:
    return {"kind": "text", "min_length": 1 if value else 0}


def blocked_record(
    *,
    reason: str,
    status: int | None,
    content_type: str,
    observed_shape: Any,
    today: str,
    note: str,
) -> dict[str, Any]:
    return {
        "reason": reason,
        "observed_status": status,
        "observed_content_type": content_type,
        "observed_shape": observed_shape,
        "last_seen": today,
        "note": note,
    }


def request_live_branch(
    *,
    session: requests.Session,
    base_url: str,
    timeout: float,
    endpoint: str,
    method: str,
    branch: dict[str, Any],
) -> tuple[requests.Response | None, dict[str, Any] | None]:
    try:
        response = session.request(
            method,
            f"{base_url.rstrip('/')}{endpoint}",
            timeout=timeout,
            **request_kwargs(method, branch.get("request")),
        )
    except requests.RequestException as exc:
        return None, {
            "action": "report",
            "classification": "ambiguous_request_failed",
            "changed": False,
            "error": f"request failed: {exc}",
        }
    return response, None


def expect_from_response(
    response: requests.Response,
    *,
    previous_expect: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    actual_content_type = media_type(response.headers.get("content-type", ""))
    if not actual_content_type:
        return None, {
            "action": "report",
            "classification": "ambiguous_missing_content_type",
            "changed": False,
            "status": response.status_code,
            "actual_content_type": "",
            "error": "response did not include a Content-Type header",
        }

    previous_response_shape = None
    if isinstance(previous_expect, dict) and isinstance(previous_expect.get("response"), dict):
        previous_response_shape = previous_expect["response"]

    if is_json_media_type(actual_content_type):
        try:
            body = response.json()
        except ValueError as exc:
            return None, {
                "action": "report",
                "classification": "ambiguous_non_json_response",
                "changed": False,
                "status": response.status_code,
                "actual_content_type": actual_content_type,
                "error": f"response was not JSON: {exc}",
            }
        response_shape = shape_from_value(body, previous_response_shape)
    elif is_text_media_type(actual_content_type):
        response_shape = text_shape(response.text)
    else:
        return None, {
            "action": "report",
            "classification": "ambiguous_unsupported_content_type",
            "changed": False,
            "status": response.status_code,
            "actual_content_type": actual_content_type,
            "error": f"unsupported content type for automatic fixture reconciliation: {actual_content_type}",
        }

    return {
        "status": response.status_code,
        "content_type": actual_content_type,
        "response": response_shape,
    }, None


def is_empty_http_500(response: requests.Response) -> bool:
    return (
        response.status_code == 500
        and not response.headers.get("content-type", "")
        and response.text == ""
    )


def classify_verified_branch(
    *,
    response: requests.Response,
    branch: dict[str, Any],
    apply: bool,
    today: str,
) -> dict[str, Any]:
    if is_empty_http_500(response):
        new_blocked = blocked_record(
            reason="empty_http_500",
            status=500,
            content_type="",
            observed_shape=None,
            today=today,
            note="Existing verified payload now returns an empty HTTP 500.",
        )
        if apply:
            has_request = "request" in branch
            request_payload = branch.get("request")
            branch.clear()
            branch["state"] = "blocked"
            if has_request:
                branch["request"] = request_payload
            branch["blocked"] = new_blocked
        return {
            "action": "mark_blocked",
            "classification": "verified_now_empty_http_500",
            "changed": True,
            "status": 500,
            "actual_content_type": "",
            "new_blocked": new_blocked,
        }

    previous_expect = branch.get("expect")
    if not isinstance(previous_expect, dict):
        return {
            "action": "report",
            "classification": "ambiguous_missing_expect",
            "changed": False,
            "status": response.status_code,
            "error": "verified branch did not contain an expect object",
        }

    new_expect, failure = expect_from_response(response, previous_expect=previous_expect)
    if failure is not None:
        return failure

    if previous_expect == new_expect:
        return {
            "action": "none",
            "classification": "verified_unchanged",
            "changed": False,
            "status": response.status_code,
            "actual_content_type": new_expect["content_type"],
        }

    if apply:
        branch["expect"] = new_expect
    return {
        "action": "refresh_expect",
        "classification": "verified_expect_refreshed",
        "changed": True,
        "status": response.status_code,
        "actual_content_type": new_expect["content_type"],
        "old_expect": previous_expect,
        "new_expect": new_expect,
    }


def classify_blocked_branch(response: requests.Response) -> dict[str, Any]:
    if is_empty_http_500(response):
        return {
            "action": "none",
            "classification": "blocked_still_empty_http_500",
            "changed": False,
            "status": 500,
            "actual_content_type": "",
        }

    new_expect, failure = expect_from_response(response)
    if failure is not None:
        failure["classification"] = "blocked_still_ambiguous"
        return failure

    return {
        "action": "report",
        "classification": "previously_blocked_now_reachable",
        "changed": False,
        "status": response.status_code,
        "actual_content_type": new_expect["content_type"],
        "observed_expect": new_expect,
    }


def reconcile_branch(
    *,
    session: requests.Session,
    base_url: str,
    timeout: float,
    fixture_path: Path,
    fixture: dict[str, Any],
    branch_id: str,
    branch: dict[str, Any],
    apply: bool,
    today: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "fixture": str(fixture_path),
        "endpoint": fixture["endpoint"],
        "method": fixture["method"].upper(),
        "branch": branch_id,
        "state": branch.get("state"),
    }
    response, failure = request_live_branch(
        session=session,
        base_url=base_url,
        timeout=timeout,
        endpoint=fixture["endpoint"],
        method=fixture["method"].upper(),
        branch=branch,
    )
    if failure is not None:
        result.update(failure)
        return result
    assert response is not None

    if branch.get("state") == "blocked":
        result.update(classify_blocked_branch(response))
        return result

    result.update(
        classify_verified_branch(
            response=response,
            branch=branch,
            apply=apply,
            today=today,
        )
    )
    return result


def reconcile_fixture_file(
    path: Path,
    *,
    session: requests.Session,
    base_url: str,
    timeout: float,
    apply: bool,
    today: str,
) -> tuple[list[dict[str, Any]], bool]:
    fixture = load_fixture(path)
    changed = False
    results = []
    for branch_id, branch in fixture["branches"].items():
        result = reconcile_branch(
            session=session,
            base_url=base_url,
            timeout=timeout,
            fixture_path=path,
            fixture=fixture,
            branch_id=branch_id,
            branch=branch,
            apply=apply,
            today=today,
        )
        changed = changed or bool(result.get("changed"))
        results.append(result)

    if changed and apply:
        validate_fixture(fixture, path=path)
        path.write_text(dump_fixture(fixture), encoding="utf-8")
    return results, changed


def build_report(
    *,
    base_url: str,
    fixture_dir: Path,
    mode: str,
    fixture_count: int,
    results: list[dict[str, Any]],
    changed_fixture_paths: list[Path],
    status_updated: bool,
) -> dict[str, Any]:
    classifications = Counter(result["classification"] for result in results)
    actions = Counter(result["action"] for result in results)
    return {
        "base_url": base_url,
        "fixture_dir": str(fixture_dir),
        "mode": mode,
        "fixture_count": fixture_count,
        "branch_count": len(results),
        "changed_count": sum(1 for result in results if result.get("changed")),
        "changed_fixture_paths": [str(path) for path in changed_fixture_paths],
        "status_updated": status_updated,
        "classification_counts": dict(sorted(classifications.items())),
        "action_counts": dict(sorted(actions.items())),
        "results": results,
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# OpenAPI Fixture Reconciliation Report",
        "",
        f"- mode: `{report['mode']}`",
        f"- base URL: `{report['base_url']}`",
        f"- fixture directory: `{report['fixture_dir']}`",
        f"- fixture files scanned: {report['fixture_count']}",
        f"- branches scanned: {report['branch_count']}",
        f"- changed branches: {report['changed_count']}",
        f"- status updated: {str(report['status_updated']).lower()}",
        "",
        "## Classifications",
        "",
    ]
    if report["classification_counts"]:
        for classification, count in report["classification_counts"].items():
            lines.append(f"- `{classification}`: {count}")
    else:
        lines.append("- none")

    changed = [result for result in report["results"] if result.get("changed")]
    reported = [
        result
        for result in report["results"]
        if result.get("action") == "report" or result.get("classification") == "previously_blocked_now_reachable"
    ]
    lines.extend(["", "## Changed Branches", ""])
    if changed:
        for result in changed:
            lines.append(
                f"- `{result['endpoint']}` `{result['branch']}`: "
                f"{result['classification']} ({result['fixture']})"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Report-Only Branches", ""])
    if reported:
        for result in reported:
            status = result.get("status")
            status_text = "no status" if status is None else f"HTTP {status}"
            lines.append(
                f"- `{result['endpoint']}` `{result['branch']}`: "
                f"{result['classification']} ({status_text}, {result['fixture']})"
            )
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def write_report_outputs(
    *,
    report: dict[str, Any],
    json_output: Path | None,
    markdown_output: Path | None,
) -> None:
    if json_output is not None:
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if markdown_output is not None:
        markdown_output.write_text(markdown_report(report), encoding="utf-8")


def reconcile_fixture_dir(
    *,
    fixture_dir: Path,
    base_url: str,
    timeout: float,
    apply: bool,
    openapi: Path = DEFAULT_OPENAPI,
    status_output: Path = DEFAULT_OUTPUT,
    today: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    today = today or date.today().isoformat()
    paths = iter_fixture_paths(fixture_dir)
    changed_fixture_paths: list[Path] = []
    results: list[dict[str, Any]] = []
    status_updated = False

    owns_session = session is None
    if session is None:
        session = requests.Session()
    try:
        for path in paths:
            fixture_results, changed = reconcile_fixture_file(
                path,
                session=session,
                base_url=base_url,
                timeout=timeout,
                apply=apply,
                today=today,
            )
            results.extend(fixture_results)
            if changed:
                changed_fixture_paths.append(path)
    finally:
        if owns_session:
            session.close()

    if apply and changed_fixture_paths:
        try:
            from scripts.openapi_fixtures.generate_status import generate_status_text
        except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
            from generate_status import generate_status_text

        status_text = generate_status_text(openapi=openapi, fixture_dir=fixture_dir)
        current = status_output.read_text(encoding="utf-8") if status_output.exists() else None
        if current != status_text:
            status_output.write_text(status_text, encoding="utf-8")
            status_updated = True

    return build_report(
        base_url=base_url,
        fixture_dir=fixture_dir,
        mode="apply" if apply else "dry-run",
        fixture_count=len(paths),
        results=results,
        changed_fixture_paths=changed_fixture_paths,
        status_updated=status_updated,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--base-url", default=os.environ.get("ASTROX_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--openapi", type=Path, default=DEFAULT_OPENAPI)
    parser.add_argument("--status-output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="probe and report without editing files")
    mode.add_argument("--apply", action="store_true", help="apply safe fixture rewrites")
    args = parser.parse_args()

    report = reconcile_fixture_dir(
        fixture_dir=args.fixture_dir,
        base_url=args.base_url,
        timeout=args.timeout,
        apply=args.apply,
        openapi=args.openapi,
        status_output=args.status_output,
    )
    write_report_outputs(
        report=report,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
    )
    print("OPENAPI_FIXTURE_RECONCILE_JSON=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"OPENAPI_FIXTURE_RECONCILE_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        raise
