from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
import yaml

from scripts.openapi_drift.discover import discover, load_spec
from scripts.openapi_drift.discovery_report import (
    axis_observed_values,
    discovery_fixture_report,
    markdown_report as discovery_markdown_report,
    path_tokens,
)
from scripts.openapi_drift.drift_pipeline_report import (
    build_pipeline_report,
    load_json,
    parse_porcelain_status,
    pr_body_markdown,
    summary_markdown,
)
from scripts.openapi_drift.generate_status import generate_status_text
from scripts.openapi_drift.normalize import dump_fixture, normalize_fixture_data, normalize_fixture_file
from scripts.openapi_drift.probe_request import probe_request_branch
from scripts.openapi_drift.reconcile import (
    expect_from_response,
    markdown_report as reconcile_markdown_report,
    reconcile_fixture_dir,
    shape_from_value,
)
from scripts.openapi_drift.shapes import ShapeMismatch, assert_shape, fingerprint_shape
from scripts.openapi_drift.verify import (
    build_report,
    content_type_matches,
    iter_fixture_paths,
    load_fixture,
    request_kwargs,
    response_shape_expects_text,
    validate_fixture,
    verify_branch,
    verify_fixture,
)


class StubResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        body: Any = None,
        text: str = "",
        json_error: ValueError | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = headers if headers is not None else {"content-type": "application/json"}
        self.body = body if body is not None else {}
        self.text = text
        self.json_error = json_error

    def json(self) -> Any:
        if self.json_error is not None:
            raise self.json_error
        return self.body


class StubSession:
    def __init__(self, response: StubResponse) -> None:
        self.response = response

    def request(self, *args: Any, **kwargs: Any) -> StubResponse:
        return self.response

    def close(self) -> None:
        pass


class FailingStubSession:
    def request(self, *args: Any, **kwargs: Any) -> Any:
        raise requests.Timeout("slow upstream")

    def close(self) -> None:
        pass


def valid_fixture_data() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "endpoint": "/Example",
        "method": "POST",
        "openapi_operation_id": None,
        "openapi_request_schema": "ExampleInput",
        "openapi_response_schema": "ExampleOutput",
        "branches": {
            "nominal": {
                "state": "verified",
                "request": {},
                "expect": {
                    "status": 200,
                    "content_type": "application/json",
                    "response": {"kind": "json_object"},
                },
            }
        },
    }


def write_minimal_openapi(path: Path, endpoint: str = "/Example") -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    endpoint: {
                        "post": {
                            "requestBody": {
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            },
                            "responses": {
                                "200": {"content": {"application/json": {"schema": {"type": "object"}}}}
                            },
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_shape_accepts_state_vector() -> None:
    assert_shape(
        [1.0, 2.0, 3.0],
        {"kind": "json_array", "length": 3, "items": {"kind": "json_number"}},
    )


def test_shape_rejects_wrong_array_length() -> None:
    try:
        assert_shape([1.0], {"kind": "json_array", "length": 3, "items": {"kind": "json_number"}})
    except ShapeMismatch as exc:
        assert "expected length 3" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ShapeMismatch")


def test_shape_any_of_accepts_nullable_array() -> None:
    shape = {
        "any_of": [
            {"kind": "json_null"},
            {"kind": "json_array", "items": {"kind": "json_number"}},
        ]
    }

    assert_shape(None, shape)
    assert_shape([1.0, 2.0], shape)


def test_shape_any_of_reports_alternative_mismatches() -> None:
    try:
        assert_shape(
            {"Cities": []},
            {
                "any_of": [
                    {"kind": "json_null"},
                    {"kind": "json_array"},
                ]
            },
        )
    except ShapeMismatch as exc:
        message = str(exc)
        assert "did not match any_of alternatives" in message
        assert "expected json_null" in message
        assert "expected json_array" in message
    else:  # pragma: no cover
        raise AssertionError("expected ShapeMismatch")


def test_shape_accepts_text_min_length() -> None:
    assert_shape("satcat rows\n", {"kind": "text", "min_length": 1})


def test_shape_accepts_primitive_const() -> None:
    assert_shape(False, {"kind": "json_boolean", "const": False})
    assert_shape("OK", {"kind": "json_string", "const": "OK"})


def test_shape_rejects_primitive_const_mismatch() -> None:
    try:
        assert_shape(True, {"kind": "json_boolean", "const": False})
    except ShapeMismatch as exc:
        assert "expected const False" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ShapeMismatch")


def test_shape_rejects_short_text() -> None:
    try:
        assert_shape("", {"kind": "text", "min_length": 1})
    except ShapeMismatch as exc:
        assert "expected text length >= 1" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ShapeMismatch")


def test_shape_fingerprint_reports_object_fields() -> None:
    assert fingerprint_shape({"b": [1], "a": None}) == {
        "kind": "json_object",
        "fields": {
            "a": {"kind": "json_null"},
            "b": {"kind": "json_array", "length": 1, "sample_items": [{"kind": "json_number"}]},
        },
    }


def test_shape_fingerprint_reports_text_length() -> None:
    assert fingerprint_shape("abc") == {"kind": "text", "length": 3}


def test_iter_fixture_paths_ignores_readme(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "README.md").write_text("# docs\n", encoding="utf-8")
    (fixture_dir / "one.yaml").write_text("schema_version: 1\n", encoding="utf-8")

    assert iter_fixture_paths(fixture_dir) == [fixture_dir / "one.yaml"]


def test_content_type_matches_ignores_parameters() -> None:
    assert content_type_matches("application/json; charset=utf-8", "application/json")
    assert not content_type_matches("text/plain; charset=utf-8", "application/json")


def test_request_kwargs_sends_get_payload_as_params() -> None:
    assert request_kwargs("GET", {"cityName": "Beijing"}) == {"params": {"cityName": "Beijing"}}
    assert request_kwargs("get", {"cityName": "Beijing"}) == {"params": {"cityName": "Beijing"}}
    assert request_kwargs("POST", {"SemimajorAxis": 1.0}) == {"json": {"SemimajorAxis": 1.0}}
    assert request_kwargs("GET", None) == {}
    assert request_kwargs("POST", None) == {}


def test_verify_branch_sends_get_payload_as_query_params() -> None:
    class Response:
        status_code = 200
        headers = {"content-type": "application/json"}

    class RecordingSession:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def request(self, method: str, url: str, **kwargs: Any) -> Response:
            self.calls.append({"method": method, "url": url, "kwargs": kwargs})
            return Response()

    session = RecordingSession()

    result = verify_branch(
        session=session,  # type: ignore[arg-type]
        base_url="http://example.test/",
        timeout=2.0,
        endpoint="/city",
        method="GET",
        branch_id="by_city",
        branch={"request": {"cityName": "Beijing"}, "expect": {"status": 200}},
    )

    assert result["ok"] is True
    assert session.calls == [
        {
            "method": "GET",
            "url": "http://example.test/city",
            "kwargs": {"timeout": 2.0, "params": {"cityName": "Beijing"}},
        }
    ]


def test_verify_branch_omits_payload_for_no_body_request() -> None:
    class Response:
        status_code = 200
        headers = {"content-type": "application/json"}

    class RecordingSession:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def request(self, method: str, url: str, **kwargs: Any) -> Response:
            self.calls.append({"method": method, "url": url, "kwargs": kwargs})
            return Response()

    session = RecordingSession()

    result = verify_branch(
        session=session,  # type: ignore[arg-type]
        base_url="http://example.test",
        timeout=2.0,
        endpoint="/WeatherForecast",
        method="GET",
        branch_id="nominal",
        branch={"expect": {"status": 200}},
    )

    assert result["ok"] is True
    assert session.calls == [
        {
            "method": "GET",
            "url": "http://example.test/WeatherForecast",
            "kwargs": {"timeout": 2.0},
        }
    ]


def test_verify_branch_reports_request_exception() -> None:
    class FailingSession:
        def request(self, *args: Any, **kwargs: Any) -> Any:
            raise requests.Timeout("slow upstream")

    result = verify_branch(
        session=FailingSession(),  # type: ignore[arg-type]
        base_url="http://example.test",
        timeout=1.0,
        endpoint="/Example",
        method="GET",
        branch_id="nominal",
        branch={"expect": {"status": 200}},
    )

    assert result["ok"] is False
    assert result["status"] is None
    assert result["failure_kind"] == "request_failed"
    assert "slow upstream" in result["error"]


def test_verify_branch_classifies_status_mismatch() -> None:
    result = verify_branch(
        session=StubSession(StubResponse(status_code=500)),  # type: ignore[arg-type]
        base_url="http://example.test",
        timeout=1.0,
        endpoint="/Example",
        method="GET",
        branch_id="nominal",
        branch={"expect": {"status": 200}},
    )

    assert result["ok"] is False
    assert result["failure_kind"] == "status_mismatch"
    assert result["expected_status"] == 200
    assert result["actual_status"] == 500


def test_verify_branch_classifies_content_type_mismatch() -> None:
    result = verify_branch(
        session=StubSession(StubResponse(headers={"content-type": "text/plain"})),  # type: ignore[arg-type]
        base_url="http://example.test",
        timeout=1.0,
        endpoint="/Example",
        method="GET",
        branch_id="nominal",
        branch={"expect": {"status": 200, "content_type": "application/json"}},
    )

    assert result["ok"] is False
    assert result["failure_kind"] == "content_type_mismatch"
    assert result["expected_content_type"] == "application/json"
    assert result["actual_content_type"] == "text/plain"


def test_verify_branch_classifies_non_json_response() -> None:
    result = verify_branch(
        session=StubSession(StubResponse(json_error=ValueError("no json"))),  # type: ignore[arg-type]
        base_url="http://example.test",
        timeout=1.0,
        endpoint="/Example",
        method="GET",
        branch_id="nominal",
        branch={"expect": {"status": 200, "response": {"kind": "json_object"}}},
    )

    assert result["ok"] is False
    assert result["failure_kind"] == "non_json_response"
    assert "no json" in result["error"]


def test_verify_branch_accepts_text_response_without_json_parse() -> None:
    result = verify_branch(
        session=StubSession(
            StubResponse(
                headers={"content-type": "text/plain; charset=utf-8"},
                text="satcat rows\n",
                json_error=ValueError("should not parse json"),
            )
        ),  # type: ignore[arg-type]
        base_url="http://example.test",
        timeout=1.0,
        endpoint="/satcat",
        method="GET",
        branch_id="nominal",
        branch={
            "expect": {
                "status": 200,
                "content_type": "text/plain",
                "response": {"kind": "text", "min_length": 1},
            }
        },
    )

    assert result["ok"] is True


def test_response_shape_expects_text_rejects_mixed_any_of() -> None:
    try:
        response_shape_expects_text({"any_of": [{"kind": "json_object"}, {"kind": "text"}]})
    except ValueError as exc:
        assert "must not mix text and JSON" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_verify_branch_classifies_shape_mismatch() -> None:
    result = verify_branch(
        session=StubSession(StubResponse(body={"Answer": []})),  # type: ignore[arg-type]
        base_url="http://example.test",
        timeout=1.0,
        endpoint="/Example",
        method="GET",
        branch_id="nominal",
        branch={"expect": {"status": 200, "response": {"kind": "json_array"}}},
    )

    assert result["ok"] is False
    assert result["failure_kind"] == "shape_mismatch"
    assert result["actual_shape"] == {
        "kind": "json_object",
        "fields": {"Answer": {"kind": "json_array", "length": 0, "sample_items": []}},
    }


def test_build_report_summarizes_failed_results_for_stdout_triage() -> None:
    results = [
        {"endpoint": "/ok", "branch": "nominal", "ok": True},
        {
            "endpoint": "/bad",
            "branch": "nominal",
            "ok": False,
            "failure_kind": "status_mismatch",
            "error": "expected status 200, got 500",
        },
    ]

    report = build_report(base_url="http://example.test", fixture_count=2, results=results)

    assert report["branch_count"] == 2
    assert report["ok_count"] == 1
    assert report["skipped_count"] == 0
    assert report["failed_count"] == 1
    assert report["failure_kinds"] == {"status_mismatch": 1}
    assert report["failed_results"] == [results[1]]


def test_verify_fixture_reports_missing_endpoint_with_path(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.yaml"
    fixture.write_text("schema_version: 1\nbranches: {}\n", encoding="utf-8")

    class UnusedSession:
        def request(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
            raise AssertionError("should not request")

    try:
        verify_fixture(
            fixture,
            session=UnusedSession(),  # type: ignore[arg-type]
            base_url="http://example.test",
            timeout=1.0,
        )
    except ValueError as exc:
        assert str(fixture) in str(exc)
        assert "endpoint" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_load_fixture_validates_before_live_requests(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    del data["branches"]["nominal"]["expect"]["response"]
    fixture.write_text(yaml.safe_dump(data), encoding="utf-8")

    class UnusedSession:
        def request(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
            raise AssertionError("should not request")

    try:
        verify_fixture(
            fixture,
            session=UnusedSession(),  # type: ignore[arg-type]
            base_url="http://example.test",
            timeout=1.0,
        )
    except ValueError as exc:
        message = str(exc)
        assert str(fixture) in message
        assert "branches.nominal.expect.response" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_requires_top_level_fields(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"

    try:
        validate_fixture({"schema_version": 1}, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "endpoint" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_rejects_invalid_expect_status(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["status"] = True

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.expect.status" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_requires_explicit_branch_state(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    del data["branches"]["nominal"]["state"]

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.state" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_accepts_blocked_branch(tmp_path: Path) -> None:
    fixture_path = tmp_path / "blocked.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"] = {
        "state": "blocked",
        "request": {"Example": "payload"},
        "blocked": {
            "reason": "empty_http_500",
            "observed_status": 500,
            "observed_content_type": "",
            "observed_shape": None,
            "last_seen": "2026-05-15",
            "note": "Endpoint execution returns an empty HTTP 500.",
        },
    }

    validate_fixture(data, path=fixture_path)


def test_verify_branch_skips_blocked_branch_without_request() -> None:
    class UnusedSession:
        def request(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
            raise AssertionError("should not request blocked branch")

    result = verify_branch(
        session=UnusedSession(),  # type: ignore[arg-type]
        base_url="http://example.test",
        timeout=1.0,
        endpoint="/Example",
        method="POST",
        branch_id="nominal",
        branch={
            "state": "blocked",
            "blocked": {
                "reason": "empty_http_500",
                "observed_status": 500,
                "observed_content_type": "",
                "observed_shape": None,
                "last_seen": "2026-05-15",
                "note": "",
            },
        },
    )

    assert result["ok"] is True
    assert result["skipped"] is True
    assert result["state"] == "blocked"


def test_validate_fixture_rejects_invalid_response_shape(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["response"] = {
        "kind": "json_object",
        "fields": {"Answer": {"kind": "json_float"}},
    }

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.expect.response.fields.Answer.kind" in message
        assert "must be one of" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_accepts_any_of_response_shape(tmp_path: Path) -> None:
    fixture_path = tmp_path / "city.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["response"] = {
        "kind": "json_object",
        "required_fields": ["Cities"],
        "fields": {
            "Cities": {
                "any_of": [
                    {"kind": "json_null"},
                    {"kind": "json_array", "items": {"kind": "json_object"}},
                ]
            }
        },
    }

    validate_fixture(data, path=fixture_path)


def test_validate_fixture_accepts_text_response_shape(tmp_path: Path) -> None:
    fixture_path = tmp_path / "satcat.yaml"
    data = valid_fixture_data()
    data["endpoint"] = "/satcat"
    data["method"] = "GET"
    data["openapi_request_schema"] = None
    data["openapi_response_schema"] = "text/plain"
    data["branches"]["nominal"]["expect"] = {
        "status": 200,
        "content_type": "text/plain",
        "response": {"kind": "text", "min_length": 1},
    }
    del data["branches"]["nominal"]["request"]

    validate_fixture(data, path=fixture_path)


def test_validate_fixture_accepts_empty_content_type_for_204(tmp_path: Path) -> None:
    fixture_path = tmp_path / "no_content.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"] = {
        "status": 204,
        "content_type": "",
        "response": {"kind": "text", "min_length": 0},
    }

    validate_fixture(data, path=fixture_path)


def test_validate_fixture_accepts_primitive_const_shape(tmp_path: Path) -> None:
    fixture_path = tmp_path / "failure.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["response"] = {
        "kind": "json_object",
        "fields": {"IsSuccess": {"kind": "json_boolean", "const": False}},
    }

    validate_fixture(data, path=fixture_path)


def test_validate_fixture_rejects_object_const_shape(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["response"] = {
        "kind": "json_object",
        "const": {},
    }

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.expect.response.const" in message
        assert "primitive" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_rejects_wrong_const_kind(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["response"] = {
        "kind": "json_boolean",
        "const": "false",
    }

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.expect.response.const" in message
        assert "boolean" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_rejects_non_finite_json_numbers(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["request"] = {"Bad": float("nan")}

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "finite JSON number" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_rejects_deeply_nested_json_values(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    value: Any = "leaf"
    for _ in range(101):
        value = [value]
    data["branches"]["nominal"]["request"] = value

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "nested too deeply" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_rejects_mixed_text_and_json_any_of(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["response"] = {
        "any_of": [
            {"kind": "json_object"},
            {"kind": "text"},
        ]
    }

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.expect.response.any_of" in message
        assert "must not mix text and JSON" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_rejects_empty_any_of(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["response"] = {"any_of": []}

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.expect.response.any_of" in message
        assert "non-empty list" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_rejects_mixed_any_of_shape_keys(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["expect"]["response"] = {
        "kind": "json_null",
        "any_of": [{"kind": "json_null"}],
    }

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.expect.response" in message
        assert "must not combine any_of" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_allows_missing_request_for_no_body_branch(tmp_path: Path) -> None:
    fixture_path = tmp_path / "weather.yaml"
    data = valid_fixture_data()
    data["endpoint"] = "/WeatherForecast"
    data["method"] = "GET"
    data["openapi_request_schema"] = None
    del data["branches"]["nominal"]["request"]

    validate_fixture(data, path=fixture_path)


def test_validate_fixture_rejects_non_object_get_query_request(tmp_path: Path) -> None:
    fixture_path = tmp_path / "city.yaml"
    data = valid_fixture_data()
    data["endpoint"] = "/city"
    data["method"] = "GET"
    data["branches"]["nominal"]["request"] = ["cityName", "Beijing"]

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal.request" in message
        assert "GET query parameters" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_validate_fixture_rejects_unknown_branch_keys(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad.yaml"
    data = valid_fixture_data()
    data["branches"]["nominal"]["requests"] = {}

    try:
        validate_fixture(data, path=fixture_path)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "branches.nominal" in message
        assert "unknown keys" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_normalize_fixture_data_adds_state_and_expands_shared_expect() -> None:
    shared_expect = {
        "status": 200,
        "content_type": "application/json",
        "response": {"kind": "json_object"},
    }
    fixture = valid_fixture_data()
    del fixture["branches"]["nominal"]["state"]
    fixture["branches"]["alternate"] = {
        "request": {"Mode": "A"},
        "expect": shared_expect,
    }
    fixture["branches"]["nominal"]["expect"] = shared_expect

    normalized = normalize_fixture_data(fixture)
    dumped = dump_fixture(fixture)

    assert normalized["branches"]["nominal"]["state"] == "verified"
    assert normalized["branches"]["alternate"]["state"] == "verified"
    assert "&" not in dumped
    assert "*" not in dumped
    assert "state: verified" in dumped


def test_normalize_fixture_file_reports_missing_key_with_path(tmp_path: Path) -> None:
    fixture_path = tmp_path / "partial.yaml"
    fixture = valid_fixture_data()
    del fixture["endpoint"]
    fixture_path.write_text(yaml.safe_dump(fixture), encoding="utf-8")

    try:
        normalize_fixture_file(fixture_path, check=True)
    except ValueError as exc:
        message = str(exc)
        assert str(fixture_path) in message
        assert "missing required key 'endpoint'" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_current_fixture_files_pass_schema_validation() -> None:
    for fixture_path in iter_fixture_paths(Path("openapi/fixtures")):
        load_fixture(fixture_path)


def axis_by_path(endpoint: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {axis["path"]: axis for axis in endpoint["branch_axes"]}


def test_discover_lists_endpoint_branch_axes(tmp_path: Path) -> None:
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "/Example": {
                        "post": {
                            "operationId": "Example_Post",
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ExampleInput"}
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "array"}
                                        }
                                    }
                                }
                            },
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "ExampleInput": {
                            "type": "object",
                            "properties": {
                                "Mode": {
                                    "type": "string",
                                    "enum": ["A", "B"],
                                }
                            },
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    endpoints = discover(load_spec(spec_path))

    assert endpoints == [
        {
            "endpoint": "/Example",
            "method": "POST",
            "operation_id": "Example_Post",
            "request_schema": "ExampleInput",
            "response_schema": "array",
            "branch_axes": [
                {
                    "path": "$.Mode",
                    "kind": "enum",
                    "values": ["A", "B"],
                    "provenance": {
                        "ref": "#/components/schemas/ExampleInput",
                        "schema": "ExampleInput",
                    },
                }
            ],
        }
    ]


def test_generate_status_reports_verified_blocked_and_uncovered(tmp_path: Path) -> None:
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "/Example": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ExampleInput"}
                                    }
                                }
                            },
                            "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}},
                        }
                    },
                    "/Missing": {"get": {"responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}}},
                },
                "components": {
                    "schemas": {
                        "ExampleInput": {
                            "type": "object",
                            "properties": {"Mode": {"type": "string", "enum": ["A", "B"]}},
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture["endpoint"] = "/Example"
    fixture["branches"]["blocked_case"] = {
        "state": "blocked",
        "request": {"Mode": "B"},
        "blocked": {
            "reason": "empty_http_500",
            "observed_status": 500,
            "observed_content_type": "",
            "observed_shape": None,
            "last_seen": "2026-05-15",
            "note": "",
        },
    }
    (fixture_dir / "example.yaml").write_text(dump_fixture(fixture), encoding="utf-8")

    status = generate_status_text(openapi=spec_path, fixture_dir=fixture_dir)

    assert "Generated by scripts/openapi_drift/generate_status.py" in status
    assert "- verified fixture branches: 1" in status
    assert "- blocked fixture branches: 1" in status
    assert "- covered discovered branch axis values: 1" in status
    assert "- uncovered discovered branch axis values: 1" in status
    assert "- [x] `/Example` nominal" in status
    assert "- [ ] `/Missing` nominal" in status
    assert "- [!] `blocked_case` (blocked)" in status
    assert "- [~] `$.Mode` (enum)" in status
    assert "  - [ ] `A`" in status
    assert "  - [!] `B`" in status


def test_axis_observed_values_reads_nested_array_discriminator_values() -> None:
    request = {
        "Items": [
            {"Position": {"$type": "J2"}},
            {"Position": {"$type": "SitePosition"}},
        ]
    }
    axis = {
        "path": "$.Items[].Position",
        "kind": "discriminator",
        "property": "$type",
        "values": ["J2", "SitePosition"],
    }

    assert axis_observed_values(request, axis) == ["J2", "SitePosition"]


def test_path_tokens_handles_quoted_properties_with_dots() -> None:
    assert path_tokens('$["my.property"][].Mode') == [
        ("my.property", True),
        ("Mode", False),
    ]
    assert axis_observed_values(
        {"my.property": [{"Mode": "A"}]},
        {"path": '$["my.property"][].Mode'},
    ) == ["A"]


def test_discover_quotes_branch_axis_paths_for_complex_property_names(tmp_path: Path) -> None:
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "/Example": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ExampleInput"}
                                    }
                                }
                            },
                            "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}},
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "ExampleInput": {
                            "type": "object",
                            "properties": {
                                "my.property": {
                                    "type": "object",
                                    "properties": {"Mode": {"type": "string", "enum": ["A"]}},
                                }
                            },
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    endpoints = discover(load_spec(spec_path))

    assert endpoints[0]["branch_axes"][0]["path"] == '$["my.property"].Mode'


def test_discovery_report_finds_missing_endpoint_and_axis_values(tmp_path: Path) -> None:
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "/Example": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ExampleInput"}
                                    }
                                }
                            },
                            "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}},
                        }
                    },
                    "/Missing": {
                        "post": {
                            "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}
                        }
                    },
                },
                "components": {
                    "schemas": {
                        "ExampleInput": {
                            "type": "object",
                            "properties": {"Mode": {"type": "string", "enum": ["A", "B"]}},
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture["endpoint"] = "/Example"
    fixture["branches"]["nominal"]["request"] = {"Mode": "A"}
    (fixture_dir / "example.yaml").write_text(dump_fixture(fixture), encoding="utf-8")

    report = discovery_fixture_report(openapi=spec_path, fixture_dir=fixture_dir)

    assert report["missing_endpoint_count"] == 1
    assert report["missing_endpoints"][0]["endpoint"] == "/Missing"
    assert report["axis_value_count"] == 2
    assert report["covered_axis_value_count"] == 1
    assert report["uncovered_axis_value_count"] == 1
    assert report["axis_reports"][0]["state"] == "partial"
    values = {value_report["value"]: value_report for value_report in report["axis_reports"][0]["values"]}
    assert values["A"]["state"] == "verified"
    assert values["A"]["fixture_evidence"][0]["branch"] == "nominal"
    assert values["B"]["state"] == "uncovered"


def test_discovery_report_tracks_blocked_axis_value_as_covered(tmp_path: Path) -> None:
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "/Example": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ExampleInput"}
                                    }
                                }
                            },
                            "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}},
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "ExampleInput": {
                            "type": "object",
                            "properties": {"Mode": {"type": "string", "enum": ["A", "B"]}},
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture["endpoint"] = "/Example"
    fixture["branches"]["nominal"]["request"] = {"Mode": "A"}
    fixture["branches"]["mode_b_blocked"] = {
        "state": "blocked",
        "request": {"Mode": "B"},
        "blocked": {
            "reason": "empty_http_500",
            "observed_status": 500,
            "observed_content_type": "",
            "observed_shape": None,
            "last_seen": "2026-05-15",
            "note": "",
        },
    }
    (fixture_dir / "example.yaml").write_text(dump_fixture(fixture), encoding="utf-8")

    report = discovery_fixture_report(openapi=spec_path, fixture_dir=fixture_dir)

    assert report["covered_axis_value_count"] == 2
    assert report["uncovered_axis_value_count"] == 0
    assert report["axis_reports"][0]["state"] == "partial"
    values = {value_report["value"]: value_report for value_report in report["axis_reports"][0]["values"]}
    assert values["A"]["state"] == "verified"
    assert values["B"]["state"] == "blocked"


def test_discovery_report_probes_previously_blocked_now_reachable(tmp_path: Path) -> None:
    spec_path = tmp_path / "openapi.yaml"
    write_minimal_openapi(spec_path)
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture["branches"]["nominal"] = {
        "state": "blocked",
        "request": {"Example": "payload"},
        "blocked": {
            "reason": "empty_http_500",
            "observed_status": 500,
            "observed_content_type": "",
            "observed_shape": None,
            "last_seen": "2026-05-15",
            "note": "",
        },
    }
    (fixture_dir / "example.yaml").write_text(dump_fixture(fixture), encoding="utf-8")

    report = discovery_fixture_report(
        openapi=spec_path,
        fixture_dir=fixture_dir,
        probe_blocked=True,
        session=StubSession(StubResponse(body={"Answer": []})),  # type: ignore[arg-type]
    )

    assert report["previously_blocked_now_reachable_count"] == 1
    reachable = report["previously_blocked_now_reachable"][0]
    assert reachable["classification"] == "previously_blocked_now_reachable"
    assert reachable["endpoint"] == "/Example"
    assert reachable["branch"] == "nominal"


def test_discovery_report_markdown_summarizes_uncovered_contracts(tmp_path: Path) -> None:
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "/Example": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ExampleInput"}
                                    }
                                }
                            },
                            "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}},
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "ExampleInput": {
                            "type": "object",
                            "properties": {"Mode": {"type": "string", "enum": ["A"]}},
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()

    markdown = discovery_markdown_report(
        discovery_fixture_report(openapi=spec_path, fixture_dir=fixture_dir)
    )

    assert "missing endpoint fixtures: 1" in markdown
    assert "`/Example` POST" in markdown
    assert "`/Example` `$.Mode` (enum) value `A`" in markdown


def test_drift_pipeline_report_requires_pr_for_expected_tracked_changes() -> None:
    tracked_paths = parse_porcelain_status(
        " M openapi/astrox.openapi.yaml\n"
        " M openapi/fixtures/STATUS.md\n"
    )

    report = build_pipeline_report(
        tracked_paths=tracked_paths,
        previous_openapi_version="2026-05-18",
        current_openapi_version="2026-06-02",
    )
    body = pr_body_markdown(report)

    assert report["pr_required"] is True
    assert report["refresh_valid"] is True
    assert report["changed_categories"]["openapi_baseline"] is True
    assert report["changed_categories"]["fixture_status"] is True
    assert report["unexpected_paths"] == []
    assert "previous version" in body
    assert "fixture inventory remains in the repository" in body


def test_drift_pipeline_report_no_pr_for_no_diff() -> None:
    report = build_pipeline_report(
        tracked_paths=[],
        previous_openapi_version="2026-06-02",
        current_openapi_version="2026-06-02",
    )
    summary = summary_markdown(report)

    assert report["pr_required"] is False
    assert report["tracked_diff_expected"] is False
    assert report["refresh_valid"] is True
    assert report["changed_categories"]["openapi_baseline"] is False
    assert "PR required: no" in summary


def test_drift_pipeline_report_rejects_unexpected_tracked_paths() -> None:
    report = build_pipeline_report(
        tracked_paths=["openapi/fixtures/example.yaml"],
        previous_openapi_version="2026-05-18",
        current_openapi_version="2026-06-02",
    )
    summary = summary_markdown(report)

    assert report["pr_required"] is False
    assert report["refresh_valid"] is False
    assert report["unexpected_paths"] == ["openapi/fixtures/example.yaml"]
    assert "Unexpected Files" in summary


def test_load_json_reports_empty_files_with_context(tmp_path: Path) -> None:
    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")

    try:
        load_json(path)
    except ValueError as exc:
        message = str(exc)
        assert str(path) in message
        assert "did not contain valid JSON" in message
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_shape_from_value_uses_min_length_for_new_arrays() -> None:
    assert shape_from_value([1, 2]) == {
        "kind": "json_array",
        "min_length": 1,
        "items": {"kind": "json_number"},
    }


def test_shape_from_value_preserves_existing_exact_array_length_contract() -> None:
    assert shape_from_value([1, 2], previous_shape={"kind": "json_array", "length": 3}) == {
        "kind": "json_array",
        "length": 2,
        "items": {"kind": "json_number"},
    }


def test_shape_from_value_preserves_existing_broad_array_contract() -> None:
    assert shape_from_value([1, 2], previous_shape={"kind": "json_array"}) == {
        "kind": "json_array",
        "items": {"kind": "json_number"},
    }


def test_shape_from_value_preserves_existing_required_field_order() -> None:
    assert shape_from_value(
        {"A": True, "B": True},
        previous_shape={"kind": "json_object", "required_fields": ["B", "A"]},
    ) == {
        "kind": "json_object",
        "required_fields": ["B", "A"],
        "fields": {
            "A": {"kind": "json_boolean"},
            "B": {"kind": "json_boolean"},
        },
    }


def test_shape_from_value_preserves_required_field_order_inside_any_of() -> None:
    assert shape_from_value(
        {"X": 1, "Y": 2, "Z": 3, "Vx": 4, "Vy": 5, "Vz": 6},
        previous_shape={
            "any_of": [
                {"kind": "json_string"},
                {
                    "kind": "json_object",
                    "required_fields": ["X", "Y", "Z", "Vx", "Vy", "Vz"],
                    "fields": {
                        "X": {"kind": "json_number"},
                        "Y": {"kind": "json_number"},
                        "Z": {"kind": "json_number"},
                        "Vx": {"kind": "json_number"},
                        "Vy": {"kind": "json_number"},
                        "Vz": {"kind": "json_number"},
                    },
                },
            ]
        },
    )["required_fields"] == ["X", "Y", "Z", "Vx", "Vy", "Vz"]


def test_shape_from_value_preserves_array_length_hint_inside_any_of() -> None:
    assert shape_from_value(
        [[{"Start": "2026-05-15T00:00:00Z", "Stop": "2026-05-15T00:01:00Z"}]],
        previous_shape={
            "any_of": [
                {
                    "kind": "json_array",
                    "min_length": 1,
                    "items": {
                        "kind": "json_array",
                        "items": {
                            "kind": "json_object",
                            "required_fields": ["Start", "Stop"],
                            "fields": {
                                "Start": {"kind": "json_string"},
                                "Stop": {"kind": "json_string"},
                            },
                        },
                    },
                },
                {
                    "kind": "json_array",
                    "min_length": 1,
                    "items": {
                        "kind": "json_array",
                        "items": {"kind": "json_array"},
                    },
                },
            ]
        },
    ) == {
        "kind": "json_array",
        "min_length": 1,
        "items": {
            "kind": "json_array",
            "items": {
                "kind": "json_object",
                "required_fields": ["Start", "Stop"],
                "fields": {
                    "Start": {"kind": "json_string"},
                    "Stop": {"kind": "json_string"},
                },
            },
        },
    }


def test_reconcile_reports_const_mismatch_without_broadening(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture["branches"]["nominal"]["expect"]["response"] = {
        "kind": "json_object",
        "required_fields": ["IsSuccess"],
        "fields": {"IsSuccess": {"kind": "json_boolean", "const": False}},
    }
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")

    report = reconcile_fixture_dir(
        fixture_dir=fixture_dir,
        base_url="http://example.test",
        timeout=1.0,
        apply=True,
        session=StubSession(StubResponse(body={"IsSuccess": True})),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    loaded = load_fixture(fixture_path)
    assert loaded["branches"]["nominal"]["expect"]["response"]["fields"]["IsSuccess"] == {
        "kind": "json_boolean",
        "const": False,
    }
    assert report["changed_count"] == 0
    result = report["results"][0]
    assert result["action"] == "report"
    assert result["classification"] == "verified_const_mismatch"
    assert result["const_mismatches"] == [{"path": "$.IsSuccess", "expected": False, "actual": True}]


def test_expect_from_response_accepts_empty_204_without_content_type() -> None:
    expect, failure = expect_from_response(
        StubResponse(status_code=204, headers={}, text="")
    )

    assert failure is None
    assert expect == {
        "status": 204,
        "content_type": "",
        "response": {"kind": "text", "min_length": 0},
    }


def test_reconcile_dry_run_reports_expect_refresh_without_writing(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")
    before = fixture_path.read_text(encoding="utf-8")

    report = reconcile_fixture_dir(
        fixture_dir=fixture_dir,
        base_url="http://example.test",
        timeout=1.0,
        apply=False,
        session=StubSession(StubResponse(body={"Answer": [1, 2]})),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    assert fixture_path.read_text(encoding="utf-8") == before
    assert report["mode"] == "dry-run"
    assert report["changed_count"] == 1
    assert report["classification_counts"] == {"verified_expect_refreshed": 1}
    result = report["results"][0]
    assert result["action"] == "refresh_expect"
    assert result["new_expect"]["response"] == {
        "kind": "json_object",
        "required_fields": ["Answer"],
        "fields": {
            "Answer": {
                "kind": "json_array",
                "min_length": 1,
                "items": {"kind": "json_number"},
            }
        },
    }


def test_reconcile_apply_refreshes_expect_and_regenerates_status(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")
    openapi_path = tmp_path / "openapi.yaml"
    status_path = fixture_dir / "STATUS.md"
    write_minimal_openapi(openapi_path)

    report = reconcile_fixture_dir(
        fixture_dir=fixture_dir,
        base_url="http://example.test",
        timeout=1.0,
        apply=True,
        openapi=openapi_path,
        status_output=status_path,
        session=StubSession(StubResponse(body={"Answer": True})),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    loaded = load_fixture(fixture_path)
    assert loaded["branches"]["nominal"]["expect"]["response"] == {
        "kind": "json_object",
        "required_fields": ["Answer"],
        "fields": {"Answer": {"kind": "json_boolean"}},
    }
    assert report["mode"] == "apply"
    assert report["changed_fixture_paths"] == [str(fixture_path)]
    assert report["status_updated"] is True
    assert "Generated by scripts/openapi_drift/generate_status.py" in status_path.read_text(
        encoding="utf-8"
    )


def test_reconcile_apply_marks_verified_empty_http_500_blocked(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")
    openapi_path = tmp_path / "openapi.yaml"
    write_minimal_openapi(openapi_path)

    report = reconcile_fixture_dir(
        fixture_dir=fixture_dir,
        base_url="http://example.test",
        timeout=1.0,
        apply=True,
        openapi=openapi_path,
        status_output=fixture_dir / "STATUS.md",
        session=StubSession(StubResponse(status_code=500, headers={}, text="")),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    branch = load_fixture(fixture_path)["branches"]["nominal"]
    assert branch["state"] == "blocked"
    assert branch["blocked"] == {
        "reason": "empty_http_500",
        "observed_status": 500,
        "observed_content_type": "",
        "observed_shape": None,
        "last_seen": "2026-05-15",
        "note": "Existing verified payload now returns an empty HTTP 500.",
    }
    assert "expect" not in branch
    assert report["classification_counts"] == {"verified_now_empty_http_500": 1}


def test_reconcile_reports_previously_blocked_now_reachable_without_unblocking(
    tmp_path: Path,
) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture["branches"]["nominal"] = {
        "state": "blocked",
        "request": {"Example": "payload"},
        "blocked": {
            "reason": "empty_http_500",
            "observed_status": 500,
            "observed_content_type": "",
            "observed_shape": None,
            "last_seen": "2026-05-15",
            "note": "",
        },
    }
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")

    report = reconcile_fixture_dir(
        fixture_dir=fixture_dir,
        base_url="http://example.test",
        timeout=1.0,
        apply=True,
        session=StubSession(StubResponse(body={"Answer": []})),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    branch = load_fixture(fixture_path)["branches"]["nominal"]
    assert branch["state"] == "blocked"
    assert report["changed_count"] == 0
    assert report["classification_counts"] == {"previously_blocked_now_reachable": 1}
    assert report["results"][0]["observed_expect"]["status"] == 200


def test_reconcile_reports_ambiguous_request_failure_without_change(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")

    report = reconcile_fixture_dir(
        fixture_dir=fixture_dir,
        base_url="http://example.test",
        timeout=1.0,
        apply=True,
        session=FailingStubSession(),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    assert load_fixture(fixture_path)["branches"]["nominal"]["state"] == "verified"
    assert report["changed_count"] == 0
    assert report["classification_counts"] == {"ambiguous_request_failed": 1}
    assert "slow upstream" in report["results"][0]["error"]


def test_reconcile_markdown_report_lists_changed_and_report_only_branches() -> None:
    report = {
        "mode": "dry-run",
        "base_url": "http://example.test",
        "fixture_dir": "fixtures",
        "fixture_count": 1,
        "branch_count": 2,
        "changed_count": 1,
        "status_updated": False,
        "classification_counts": {
            "previously_blocked_now_reachable": 1,
            "verified_expect_refreshed": 1,
        },
        "results": [
            {
                "fixture": "fixtures/example.yaml",
                "endpoint": "/Example",
                "branch": "nominal",
                "action": "refresh_expect",
                "classification": "verified_expect_refreshed",
                "changed": True,
            },
            {
                "fixture": "fixtures/example.yaml",
                "endpoint": "/Example",
                "branch": "blocked_case",
                "action": "report",
                "classification": "previously_blocked_now_reachable",
                "changed": False,
                "status": 200,
            },
        ],
    }

    markdown = reconcile_markdown_report(report)

    assert "`verified_expect_refreshed`: 1" in markdown
    assert "`/Example` `nominal`: verified_expect_refreshed" in markdown
    assert "`/Example` `blocked_case`: previously_blocked_now_reachable" in markdown


def test_probe_request_dry_run_reports_verified_branch_without_writing(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")
    before = fixture_path.read_text(encoding="utf-8")

    report = probe_request_branch(
        fixture_path=fixture_path,
        branch_id="mode_b",
        request_present=True,
        request_payload={"Mode": "B"},
        base_url="http://example.test",
        timeout=1.0,
        apply=False,
        replace=False,
        session=StubSession(StubResponse(body={"Answer": [1]})),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    assert fixture_path.read_text(encoding="utf-8") == before
    assert report["mode"] == "dry-run"
    assert report["classification"] == "candidate_verified"
    assert report["action"] == "write_verified"
    assert report["new_expect"]["response"] == {
        "kind": "json_object",
        "required_fields": ["Answer"],
        "fields": {
            "Answer": {
                "kind": "json_array",
                "min_length": 1,
                "items": {"kind": "json_number"},
            }
        },
    }


def test_probe_request_apply_adds_verified_branch_and_regenerates_status(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    openapi_path = tmp_path / "openapi.yaml"
    status_path = fixture_dir / "STATUS.md"
    write_minimal_openapi(openapi_path)
    fixture_path = fixture_dir / "example.yaml"

    report = probe_request_branch(
        fixture_path=fixture_path,
        branch_id="nominal",
        request_present=True,
        request_payload={"Example": "payload"},
        base_url="http://example.test",
        timeout=1.0,
        apply=True,
        replace=False,
        openapi=openapi_path,
        fixture_dir=fixture_dir,
        status_output=status_path,
        endpoint="/Example",
        method="POST",
        session=StubSession(StubResponse(body={"Answer": True})),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    fixture = load_fixture(fixture_path)
    branch = fixture["branches"]["nominal"]
    assert branch["state"] == "verified"
    assert branch["request"] == {"Example": "payload"}
    assert branch["expect"]["response"] == {
        "kind": "json_object",
        "required_fields": ["Answer"],
        "fields": {"Answer": {"kind": "json_boolean"}},
    }
    assert report["mode"] == "apply"
    assert report["status_updated"] is True
    assert "- [x] `/Example` nominal" in status_path.read_text(encoding="utf-8")


def test_probe_request_apply_adds_blocked_branch_for_empty_http_500(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")

    report = probe_request_branch(
        fixture_path=fixture_path,
        branch_id="bad_case",
        request_present=True,
        request_payload={"Mode": "bad"},
        base_url="http://example.test",
        timeout=1.0,
        apply=True,
        replace=False,
        fixture_dir=fixture_dir,
        status_output=fixture_dir / "STATUS.md",
        session=StubSession(StubResponse(status_code=500, headers={}, text="")),  # type: ignore[arg-type]
        today="2026-05-15",
    )

    branch = load_fixture(fixture_path)["branches"]["bad_case"]
    assert branch["state"] == "blocked"
    assert branch["request"] == {"Mode": "bad"}
    assert branch["blocked"] == {
        "reason": "empty_http_500",
        "observed_status": 500,
        "observed_content_type": "",
        "observed_shape": None,
        "last_seen": "2026-05-15",
        "note": "Candidate request returned an empty HTTP 500.",
    }
    assert report["classification"] == "candidate_empty_http_500"


def test_probe_request_requires_replace_for_existing_branch(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture = valid_fixture_data()
    fixture_path = fixture_dir / "example.yaml"
    fixture_path.write_text(dump_fixture(fixture), encoding="utf-8")

    try:
        probe_request_branch(
            fixture_path=fixture_path,
            branch_id="nominal",
            request_present=True,
            request_payload={},
            base_url="http://example.test",
            timeout=1.0,
            apply=False,
            replace=False,
            session=StubSession(StubResponse()),  # type: ignore[arg-type]
        )
    except ValueError as exc:
        assert "pass --replace" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_discover_resolves_refs_items_combinators_and_discriminators(tmp_path: Path) -> None:
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "/Example": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ExampleInput"}
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "content": {
                                        "application/json": {"schema": {"type": "object"}}
                                    }
                                }
                            },
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "ExampleInput": {
                            "type": "object",
                            "allOf": [{"$ref": "#/components/schemas/BaseOptions"}],
                            "properties": {
                                "Grid": {"$ref": "#/components/schemas/Grid"},
                                "Assets": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Asset"},
                                },
                            },
                        },
                        "BaseOptions": {
                            "type": "object",
                            "properties": {
                                "CoordType": {"type": "string", "enum": ["Cartesian", "Spherical"]}
                            },
                        },
                        "Grid": {
                            "type": "object",
                            "oneOf": [
                                {"$ref": "#/components/schemas/GridGlobal"},
                                {"$ref": "#/components/schemas/GridLatLon"},
                            ],
                            "discriminator": {
                                "propertyName": "$type",
                                "mapping": {
                                    "Global": "#/components/schemas/GridGlobal",
                                    "LatLonBounds": "#/components/schemas/GridLatLon",
                                },
                            },
                        },
                        "GridGlobal": {
                            "type": "object",
                            "properties": {"$type": {"type": "string", "enum": ["Global"]}},
                        },
                        "GridLatLon": {
                            "type": "object",
                            "properties": {"$type": {"type": "string", "enum": ["LatLonBounds"]}},
                        },
                        "Asset": {
                            "type": "object",
                            "properties": {"Position": {"$ref": "#/components/schemas/EntityPosition"}},
                        },
                        "EntityPosition": {
                            "type": "object",
                            "anyOf": [
                                {"$ref": "#/components/schemas/EntityPositionJ2"},
                                {"$ref": "#/components/schemas/EntityPositionSite"},
                            ],
                            "discriminator": {
                                "propertyName": "$type",
                                "mapping": {
                                    "J2": "#/components/schemas/EntityPositionJ2",
                                    "SitePosition": "#/components/schemas/EntityPositionSite",
                                },
                            },
                        },
                        "EntityPositionJ2": {
                            "type": "object",
                            "properties": {"$type": {"type": "string", "enum": ["J2"]}},
                        },
                        "EntityPositionSite": {
                            "type": "object",
                            "properties": {"$type": {"type": "string", "enum": ["SitePosition"]}},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    endpoint = discover(load_spec(spec_path))[0]
    axes = axis_by_path(endpoint)

    assert axes["$.Grid"] == {
        "path": "$.Grid",
        "kind": "discriminator",
        "property": "$type",
        "values": ["Global", "LatLonBounds"],
        "provenance": {"ref": "#/components/schemas/Grid", "schema": "Grid"},
    }
    assert axes["$.Assets[].Position"] == {
        "path": "$.Assets[].Position",
        "kind": "discriminator",
        "property": "$type",
        "values": ["J2", "SitePosition"],
        "provenance": {"ref": "#/components/schemas/EntityPosition", "schema": "EntityPosition"},
    }
    assert axes["$.CoordType"] == {
        "path": "$.CoordType",
        "kind": "enum",
        "values": ["Cartesian", "Spherical"],
        "provenance": {"ref": "#/components/schemas/BaseOptions", "schema": "BaseOptions"},
    }
    assert "$.Grid.$type" not in axes


def test_discover_real_spec_known_branch_axes() -> None:
    endpoints = {
        endpoint["endpoint"]: endpoint
        for endpoint in discover(load_spec(Path("openapi/astrox.openapi.yaml")))
    }

    rocket_axes = axis_by_path(endpoints["/Rocket/RocketGuid"])
    assert rocket_axes["$"]["kind"] == "discriminator"
    assert rocket_axes["$"]["property"] == "$type"
    assert set(rocket_axes["$"]["values"]) == {"CZ2CD", "KZ1A", "CZ7A", "CZ3BC", "CZ4BC"}

    coverage_axes = axis_by_path(endpoints["/Coverage/GetGridPoints"])
    assert coverage_axes["$.Grid"]["kind"] == "discriminator"
    assert set(coverage_axes["$.Grid"]["values"]) == {
        "CbLatLonBounds",
        "Global",
        "LatitudeBounds",
        "LatLonBounds",
    }

    access_axes = axis_by_path(endpoints["/access/AccessComputeV2"])
    assert access_axes["$.FromObjectPath.Position"]["kind"] == "discriminator"
    assert access_axes["$.ToObjectPath.Position"]["kind"] == "discriminator"
    assert "J2" in access_axes["$.FromObjectPath.Position"]["values"]
    assert "SitePosition" in access_axes["$.ToObjectPath.Position"]["values"]

    chain_axes = axis_by_path(endpoints["/access/ChainCompute"])
    assert chain_axes["$.AllObjects[]"]["kind"] == "discriminator"
    assert set(chain_axes["$.AllObjects[]"]["values"]) == {"EntityPath", "EntityPathGroup"}
