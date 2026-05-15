#!/usr/bin/env python3
"""Verify checked-in OpenAPI fixtures against the live ASTROX server."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import requests
import yaml

try:
    from scripts.openapi_drift.shapes import ShapeMismatch, assert_shape, fingerprint_shape
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from shapes import ShapeMismatch, assert_shape, fingerprint_shape


DEFAULT_BASE_URL = "http://astrox.cn:8765"
DEFAULT_FIXTURE_DIR = Path("openapi/fixtures")
SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
SUPPORTED_RESPONSE_KINDS = {
    "json_null",
    "json_boolean",
    "json_number",
    "json_string",
    "json_array",
    "json_object",
    "text",
}
SUPPORTED_BRANCH_STATES = {"verified", "blocked"}
BRANCH_KEYS = {"state", "request", "expect", "blocked"}
VERIFIED_BRANCH_KEYS = {"state", "request", "expect"}
BLOCKED_BRANCH_KEYS = {"state", "request", "blocked"}
MISSING = object()


def load_fixture(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} did not load as an object")
    validate_fixture(loaded, path=path)
    return loaded


def _validation_error(path: Path, field_path: str, message: str) -> ValueError:
    return ValueError(f"{path}: {field_path} {message}")


def _required_value(
    fixture: dict[str, Any],
    key: str,
    *,
    path: Path,
    field_path: str | None = None,
) -> Any:
    value = fixture.get(key, MISSING)
    if value is MISSING:
        raise _validation_error(path, field_path or key, "is required")
    return value


def _require_object(value: Any, *, path: Path, field_path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _validation_error(path, field_path, "must be an object")
    return value


def _require_non_empty_string(value: Any, *, path: Path, field_path: str) -> str:
    if not isinstance(value, str) or not value:
        raise _validation_error(path, field_path, "must be a non-empty string")
    return value


def _require_null_or_non_empty_string(value: Any, *, path: Path, field_path: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_string(value, path=path, field_path=field_path)


def _require_int(value: Any, *, path: Path, field_path: str) -> int:
    if type(value) is not int:
        raise _validation_error(path, field_path, "must be an integer")
    return value


def _require_json_value(value: Any, *, path: Path, field_path: str, depth: int = 0) -> None:
    if depth > 100:
        raise _validation_error(path, field_path, "is nested too deeply")
    if value is None or isinstance(value, str | int | bool):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _validation_error(path, field_path, "must be a finite JSON number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_json_value(
                item,
                path=path,
                field_path=f"{field_path}[{index}]",
                depth=depth + 1,
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise _validation_error(path, field_path, "must contain only string object keys")
            _require_json_value(
                item,
                path=path,
                field_path=f"{field_path}.{key}",
                depth=depth + 1,
            )
        return
    raise _validation_error(path, field_path, "must be JSON-compatible")


def validate_fixture(fixture: dict[str, Any], *, path: Path) -> None:
    """Validate a fixture file before making live server requests."""
    schema_version = _require_int(
        _required_value(fixture, "schema_version", path=path),
        path=path,
        field_path="schema_version",
    )
    if schema_version != 1:
        raise _validation_error(path, "schema_version", "must be 1")

    _require_non_empty_string(
        _required_value(fixture, "endpoint", path=path),
        path=path,
        field_path="endpoint",
    )
    method = _require_non_empty_string(
        _required_value(fixture, "method", path=path),
        path=path,
        field_path="method",
    )
    method = method.upper()
    if method not in SUPPORTED_METHODS:
        raise _validation_error(path, "method", f"must be one of {sorted(SUPPORTED_METHODS)}")

    operation_id = _required_value(fixture, "openapi_operation_id", path=path)
    if operation_id is not None and (not isinstance(operation_id, str) or not operation_id):
        raise _validation_error(path, "openapi_operation_id", "must be null or a non-empty string")
    _require_null_or_non_empty_string(
        _required_value(fixture, "openapi_request_schema", path=path),
        path=path,
        field_path="openapi_request_schema",
    )
    _require_non_empty_string(
        _required_value(fixture, "openapi_response_schema", path=path),
        path=path,
        field_path="openapi_response_schema",
    )

    branches = _require_object(
        _required_value(fixture, "branches", path=path),
        path=path,
        field_path="branches",
    )
    if not branches:
        raise _validation_error(path, "branches", "must contain at least one branch")
    for branch_id, branch in branches.items():
        if not isinstance(branch_id, str) or not branch_id:
            raise _validation_error(path, "branches", "keys must be non-empty strings")
        branch_path = f"branches.{branch_id}"
        _validate_branch(branch, method=method, path=path, field_path=branch_path)


def _validate_branch(value: Any, *, method: str, path: Path, field_path: str) -> None:
    branch = _require_object(value, path=path, field_path=field_path)
    state = _require_non_empty_string(
        _required_value(branch, "state", path=path, field_path=f"{field_path}.state"),
        path=path,
        field_path=f"{field_path}.state",
    )
    if state not in SUPPORTED_BRANCH_STATES:
        raise _validation_error(
            path,
            f"{field_path}.state",
            f"must be one of {sorted(SUPPORTED_BRANCH_STATES)}",
        )

    expected_keys = VERIFIED_BRANCH_KEYS if state == "verified" else BLOCKED_BRANCH_KEYS
    unknown_keys = sorted(set(branch) - expected_keys)
    if unknown_keys:
        raise _validation_error(path, field_path, f"contains unknown keys {unknown_keys}")
    if "request" in branch:
        _validate_request_payload(
            branch["request"],
            method=method,
            path=path,
            field_path=f"{field_path}.request",
        )
    if state == "blocked":
        blocked = _require_object(
            _required_value(branch, "blocked", path=path, field_path=f"{field_path}.blocked"),
            path=path,
            field_path=f"{field_path}.blocked",
        )
        _validate_blocked(blocked, path=path, field_path=f"{field_path}.blocked")
        return

    expect = _require_object(
        _required_value(branch, "expect", path=path, field_path=f"{field_path}.expect"),
        path=path,
        field_path=f"{field_path}.expect",
    )
    _validate_expect(expect, path=path, field_path=f"{field_path}.expect")


def _validate_blocked(value: dict[str, Any], *, path: Path, field_path: str) -> None:
    _require_non_empty_string(
        _required_value(value, "reason", path=path, field_path=f"{field_path}.reason"),
        path=path,
        field_path=f"{field_path}.reason",
    )
    observed_status = _required_value(
        value,
        "observed_status",
        path=path,
        field_path=f"{field_path}.observed_status",
    )
    if observed_status is not None:
        status = _require_int(
            observed_status,
            path=path,
            field_path=f"{field_path}.observed_status",
        )
        if status < 100 or status > 599:
            raise _validation_error(
                path,
                f"{field_path}.observed_status",
                "must be null or an HTTP status code",
            )
    observed_content_type = _required_value(
        value,
        "observed_content_type",
        path=path,
        field_path=f"{field_path}.observed_content_type",
    )
    if not isinstance(observed_content_type, str):
        raise _validation_error(path, f"{field_path}.observed_content_type", "must be a string")
    observed_shape = _required_value(
        value,
        "observed_shape",
        path=path,
        field_path=f"{field_path}.observed_shape",
    )
    _require_json_value(observed_shape, path=path, field_path=f"{field_path}.observed_shape")
    _require_non_empty_string(
        _required_value(value, "last_seen", path=path, field_path=f"{field_path}.last_seen"),
        path=path,
        field_path=f"{field_path}.last_seen",
    )
    note = _required_value(value, "note", path=path, field_path=f"{field_path}.note")
    if not isinstance(note, str):
        raise _validation_error(path, f"{field_path}.note", "must be a string")


def _validate_request_payload(value: Any, *, method: str, path: Path, field_path: str) -> None:
    if method == "GET" and value is not None and not isinstance(value, dict):
        raise _validation_error(
            path,
            field_path,
            "must be null or an object for GET query parameters",
        )
    _require_json_value(value, path=path, field_path=field_path)


def _validate_expect(value: dict[str, Any], *, path: Path, field_path: str) -> None:
    status = _require_int(
        _required_value(value, "status", path=path, field_path=f"{field_path}.status"),
        path=path,
        field_path=f"{field_path}.status",
    )
    if status < 100 or status > 599:
        raise _validation_error(path, f"{field_path}.status", "must be an HTTP status code")

    content_type = _required_value(
        value,
        "content_type",
        path=path,
        field_path=f"{field_path}.content_type",
    )
    if status == 204:
        if not isinstance(content_type, str):
            raise _validation_error(path, f"{field_path}.content_type", "must be a string")
    else:
        _require_non_empty_string(
            content_type,
            path=path,
            field_path=f"{field_path}.content_type",
        )
    response = _require_object(
        _required_value(value, "response", path=path, field_path=f"{field_path}.response"),
        path=path,
        field_path=f"{field_path}.response",
    )
    _validate_response_shape(response, path=path, field_path=f"{field_path}.response")


def _validate_response_shape(value: dict[str, Any], *, path: Path, field_path: str) -> None:
    if "any_of" in value:
        if set(value) != {"any_of"}:
            raise _validation_error(path, field_path, "must not combine any_of with other shape keys")
        alternatives = value["any_of"]
        if not isinstance(alternatives, list) or not alternatives:
            raise _validation_error(path, f"{field_path}.any_of", "must be a non-empty list")
        for index, alternative in enumerate(alternatives):
            alternative_shape = _require_object(
                alternative,
                path=path,
                field_path=f"{field_path}.any_of[{index}]",
            )
            _validate_response_shape(
                alternative_shape,
                path=path,
                field_path=f"{field_path}.any_of[{index}]",
            )
        text_expectations = [response_shape_expects_text(alternative) for alternative in alternatives]
        if any(text_expectations) and not all(text_expectations):
            raise _validation_error(
                path,
                f"{field_path}.any_of",
                "must not mix text and JSON response shapes",
            )
        return

    kind = _require_non_empty_string(
        _required_value(value, "kind", path=path, field_path=f"{field_path}.kind"),
        path=path,
        field_path=f"{field_path}.kind",
    )
    if kind not in SUPPORTED_RESPONSE_KINDS:
        raise _validation_error(
            path,
            f"{field_path}.kind",
            f"must be one of {sorted(SUPPORTED_RESPONSE_KINDS)}",
        )

    if "const" in value:
        _validate_const(value["const"], kind=kind, path=path, field_path=f"{field_path}.const")

    if kind == "json_array":
        _validate_array_shape(value, path=path, field_path=field_path)
    elif kind == "json_object":
        _validate_object_shape(value, path=path, field_path=field_path)
    elif kind == "text":
        _validate_text_shape(value, path=path, field_path=field_path)


def _validate_const(value: Any, *, kind: str, path: Path, field_path: str) -> None:
    if kind in {"json_array", "json_object"}:
        raise _validation_error(path, field_path, "is only supported for primitive shapes")
    if kind == "json_null":
        if value is not None:
            raise _validation_error(path, field_path, "must be null for json_null")
    elif kind == "json_boolean":
        if type(value) is not bool:
            raise _validation_error(path, field_path, "must be a boolean for json_boolean")
    elif kind == "json_number":
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise _validation_error(path, field_path, "must be a number for json_number")
        if isinstance(value, float) and not math.isfinite(value):
            raise _validation_error(path, field_path, "must be a finite number for json_number")
    elif kind in {"json_string", "text"} and not isinstance(value, str):
        raise _validation_error(path, field_path, f"must be a string for {kind}")


def _validate_array_shape(value: dict[str, Any], *, path: Path, field_path: str) -> None:
    if "length" in value:
        length = _require_int(value["length"], path=path, field_path=f"{field_path}.length")
        if length < 0:
            raise _validation_error(path, f"{field_path}.length", "must be >= 0")
    if "min_length" in value:
        min_length = _require_int(
            value["min_length"],
            path=path,
            field_path=f"{field_path}.min_length",
        )
        if min_length < 0:
            raise _validation_error(path, f"{field_path}.min_length", "must be >= 0")
    if "items" in value:
        items = _require_object(value["items"], path=path, field_path=f"{field_path}.items")
        _validate_response_shape(items, path=path, field_path=f"{field_path}.items")


def _validate_object_shape(value: dict[str, Any], *, path: Path, field_path: str) -> None:
    required_fields = value.get("required_fields", [])
    if not isinstance(required_fields, list) or not all(
        isinstance(field, str) and field for field in required_fields
    ):
        raise _validation_error(
            path,
            f"{field_path}.required_fields",
            "must be a list of non-empty strings",
        )

    fields = value.get("fields", {})
    if not isinstance(fields, dict) or not all(
        isinstance(field, str) and field for field in fields
    ):
        raise _validation_error(
            path,
            f"{field_path}.fields",
            "must be an object with non-empty string keys",
        )
    for field, field_shape in fields.items():
        field_shape_object = _require_object(
            field_shape,
            path=path,
            field_path=f"{field_path}.fields.{field}",
        )
        _validate_response_shape(
            field_shape_object,
            path=path,
            field_path=f"{field_path}.fields.{field}",
        )


def _validate_text_shape(value: dict[str, Any], *, path: Path, field_path: str) -> None:
    if "min_length" in value:
        min_length = _require_int(
            value["min_length"],
            path=path,
            field_path=f"{field_path}.min_length",
        )
        if min_length < 0:
            raise _validation_error(path, f"{field_path}.min_length", "must be >= 0")


def iter_fixture_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.yaml") if path.is_file())


def content_type_matches(actual: str, expected_media_type: str) -> bool:
    """Return whether a response Content-Type matches an expected media type."""
    actual_media_type = actual.split(";", 1)[0].strip().lower()
    return actual_media_type == expected_media_type.lower()


def request_kwargs(method: str, request_payload: Any) -> dict[str, Any]:
    """Build method-appropriate request keyword arguments for a fixture branch."""
    if request_payload is None:
        return {}
    if method.upper() == "GET":
        return {"params": request_payload}
    return {"json": request_payload}


def response_shape_expects_text(shape: Any) -> bool:
    """Return whether a response shape should be matched against raw text."""
    if not isinstance(shape, dict):
        return False
    if shape.get("kind") == "text":
        return True
    alternatives = shape.get("any_of")
    if isinstance(alternatives, list):
        text_expectations = [response_shape_expects_text(alternative) for alternative in alternatives]
        if any(text_expectations) and not all(text_expectations):
            raise ValueError("any_of must not mix text and JSON response shapes")
        return all(text_expectations)
    return False


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
    if branch.get("state") == "blocked":
        blocked = branch.get("blocked", {})
        return {
            "endpoint": endpoint,
            "method": method,
            "branch": branch_id,
            "state": "blocked",
            "status": None,
            "ok": True,
            "skipped": True,
            "blocked_reason": blocked.get("reason") if isinstance(blocked, dict) else None,
        }

    expected = branch.get("expect", {})
    expected_status = expected.get("status")
    expected_response = expected.get("response")
    request_payload = branch.get("request")

    try:
        response = session.request(
            method,
            f"{base_url.rstrip('/')}{endpoint}",
            timeout=timeout,
            **request_kwargs(method, request_payload),
        )
    except requests.RequestException as exc:
        return {
            "endpoint": endpoint,
            "method": method,
            "branch": branch_id,
            "status": None,
            "ok": False,
            "failure_kind": "request_failed",
            "error": f"request failed: {exc}",
        }

    result: dict[str, Any] = {
        "endpoint": endpoint,
        "method": method,
        "branch": branch_id,
        "state": branch.get("state", "verified"),
        "status": response.status_code,
        "ok": True,
    }

    if expected_status is not None and response.status_code != expected_status:
        result["ok"] = False
        result["failure_kind"] = "status_mismatch"
        result["expected_status"] = expected_status
        result["actual_status"] = response.status_code
        result["error"] = f"expected status {expected_status}, got {response.status_code}"
        return result

    expected_content_type = expected.get("content_type")
    if expected_content_type is not None:
        actual_content_type = response.headers.get("content-type", "")
        if not content_type_matches(actual_content_type, expected_content_type):
            result["ok"] = False
            result["failure_kind"] = "content_type_mismatch"
            result["expected_content_type"] = expected_content_type
            result["actual_content_type"] = actual_content_type
            result["error"] = f"expected content type {expected_content_type}, got {actual_content_type!r}"
            return result

    if expected_response is None:
        return result

    if response_shape_expects_text(expected_response):
        body = response.text
    else:
        try:
            body = response.json()
        except ValueError as exc:
            result["ok"] = False
            result["failure_kind"] = "non_json_response"
            result["error"] = f"response was not JSON: {exc}"
            return result

    try:
        assert_shape(body, expected_response)
    except ShapeMismatch as exc:
        result["ok"] = False
        result["failure_kind"] = "shape_mismatch"
        result["error"] = str(exc)
        result["actual_shape"] = fingerprint_shape(body)
    return result


def verify_fixture(path: Path, *, session: requests.Session, base_url: str, timeout: float) -> list[dict[str, Any]]:
    fixture = load_fixture(path)
    endpoint = fixture["endpoint"]
    method = fixture["method"].upper()
    branches = fixture["branches"]

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


def build_report(*, base_url: str, fixture_count: int, results: list[dict[str, Any]]) -> dict[str, Any]:
    failed_results = [result for result in results if not result["ok"]]
    skipped_results = [result for result in results if result.get("skipped")]
    failure_kinds: dict[str, int] = {}
    for result in failed_results:
        failure_kind = result.get("failure_kind", "unknown_failure")
        failure_kinds[failure_kind] = failure_kinds.get(failure_kind, 0) + 1

    return {
        "base_url": base_url,
        "fixture_count": fixture_count,
        "branch_count": len(results),
        "ok_count": len(results) - len(failed_results),
        "skipped_count": len(skipped_results),
        "failed_count": len(failed_results),
        "failure_kinds": failure_kinds,
        "failed_results": failed_results,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--base-url", default=os.environ.get("ASTROX_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    paths = iter_fixture_paths(args.fixture_dir)
    results: list[dict[str, Any]] = []
    with requests.Session() as session:
        for path in paths:
            results.extend(verify_fixture(path, session=session, base_url=args.base_url, timeout=args.timeout))

    report = build_report(base_url=args.base_url, fixture_count=len(paths), results=results)
    print("OPENAPI_FIXTURE_RESULT_JSON=" + json.dumps(report, sort_keys=True))
    return 1 if report["failed_count"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"OPENAPI_FIXTURE_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        raise
