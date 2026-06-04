"""JSON subprocess support for external validation tools."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class ExternalToolError(RuntimeError):
    """Raised when an external validation tool cannot produce JSON output."""


def run_json_tool(
    command: Sequence[str | os.PathLike[str]],
    payload: Any,
    *,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    timeout_s: float = 300.0,
) -> Any:
    """Run a subprocess that accepts one JSON value and emits one JSON value."""
    command_text = _format_command(command)
    input_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    merged_env = os.environ.copy()
    if env is not None:
        merged_env.update(env)

    try:
        completed = subprocess.run(
            [os.fspath(part) for part in command],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=merged_env,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExternalToolError(
            f"external tool timed out after {timeout_s:g}s: {command_text}"
        ) from exc
    except OSError as exc:
        raise ExternalToolError(f"external tool failed to start: {command_text}: {exc}") from exc

    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    if completed.returncode != 0:
        raise ExternalToolError(
            "external tool exited nonzero: "
            f"command={command_text}; returncode={completed.returncode}; "
            f"stderr={_short(stderr)}; stdout={_short(stdout)}"
        )
    if not stdout.strip():
        raise ExternalToolError(
            f"external tool produced no JSON stdout: command={command_text}; stderr={_short(stderr)}"
        )
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ExternalToolError(
            "external tool produced invalid JSON stdout: "
            f"command={command_text}; stdout={_short(stdout)}; stderr={_short(stderr)}"
        ) from exc


def _format_command(command: Sequence[str | os.PathLike[str]]) -> str:
    return " ".join(os.fspath(part) for part in command)


def _short(text: str, limit: int = 2000) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3] + "..."
