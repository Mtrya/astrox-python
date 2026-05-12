from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
import yaml

from scripts.openapi_fixtures.discover import discover, load_spec
from scripts.openapi_fixtures.shapes import ShapeMismatch, assert_shape, fingerprint_shape
from scripts.openapi_fixtures.verify import (
    content_type_matches,
    iter_fixture_paths,
    request_kwargs,
    verify_branch,
    verify_fixture,
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


def test_shape_fingerprint_reports_object_fields() -> None:
    assert fingerprint_shape({"b": [1], "a": None}) == {
        "kind": "json_object",
        "fields": {
            "a": {"kind": "json_null"},
            "b": {"kind": "json_array", "length": 1, "sample_items": [{"kind": "json_number"}]},
        },
    }


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
    assert request_kwargs("POST", {"SemimajorAxis": 1.0}) == {"json": {"SemimajorAxis": 1.0}}
    assert request_kwargs("GET", None) == {}


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
    assert "slow upstream" in result["error"]


def test_verify_fixture_reports_missing_endpoint_with_path(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.yaml"
    fixture.write_text("schema_version: 1\nbranches: {}\n", encoding="utf-8")

    class UnusedSession:
        def request(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
            raise AssertionError("should not request")

    try:
        verify_fixture(fixture, session=UnusedSession(), base_url="http://example.test", timeout=1.0)  # type: ignore[arg-type]
    except ValueError as exc:
        assert str(fixture) in str(exc)
        assert "endpoint" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


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
            "branch_axes": [{"path": "$.properties.Mode", "kind": "enum", "values": ["A", "B"]}],
        }
    ]
