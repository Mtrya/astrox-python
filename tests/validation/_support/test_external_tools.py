from __future__ import annotations

import sys

import pytest

from tests.validation._support.external_tools import ExternalToolError, run_json_tool


def test_run_json_tool_round_trips_canonical_payload() -> None:
    result = run_json_tool(
        [
            sys.executable,
            "-c",
            "import json, sys; payload=json.load(sys.stdin); print(json.dumps({'seen': payload}, sort_keys=True))",
        ],
        {"b": [2, 1], "a": 3},
    )

    assert result == {"seen": {"a": 3, "b": [2, 1]}}


def test_run_json_tool_reports_nonzero_exit() -> None:
    with pytest.raises(ExternalToolError) as exc_info:
        run_json_tool(
            [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('intentional failure'); sys.exit(7)",
            ],
            {},
        )

    message = str(exc_info.value)
    assert "returncode=7" in message
    assert "intentional failure" in message


def test_run_json_tool_reports_invalid_json_stdout() -> None:
    with pytest.raises(ExternalToolError) as exc_info:
        run_json_tool(
            [
                sys.executable,
                "-c",
                "print('not json')",
            ],
            {},
        )

    message = str(exc_info.value)
    assert "invalid JSON stdout" in message
    assert "not json" in message


def test_run_json_tool_rejects_empty_command() -> None:
    with pytest.raises(ExternalToolError, match="command must not be empty"):
        run_json_tool([], {})
