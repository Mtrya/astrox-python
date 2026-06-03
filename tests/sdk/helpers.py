"""Shared helpers for SDK contract tests."""

from __future__ import annotations

import json
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def assert_canonical_equal(actual: Any, expected: Any) -> None:
    assert canonical_bytes(actual) == canonical_bytes(expected)
