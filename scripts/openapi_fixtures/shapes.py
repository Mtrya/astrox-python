"""Response-shape checks for ASTROX OpenAPI fixtures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class ShapeMismatch(AssertionError):
    """Raised when a response does not match a fixture shape."""


def response_kind(value: Any) -> str:
    """Return the fixture kind name for a decoded JSON value."""
    if value is None:
        return "json_null"
    if isinstance(value, bool):
        return "json_boolean"
    if isinstance(value, int | float):
        return "json_number"
    if isinstance(value, str):
        return "json_string"
    if isinstance(value, list):
        return "json_array"
    if isinstance(value, dict):
        return "json_object"
    return type(value).__name__


def assert_shape(value: Any, shape: Mapping[str, Any], *, path: str = "$") -> None:
    """Assert that a decoded JSON value matches a fixture response shape."""
    alternatives = shape.get("any_of")
    if alternatives is not None:
        _assert_any_of_shape(value, alternatives, path=path)
        return

    expected_kind = shape.get("kind")
    if expected_kind == "text":
        if not isinstance(value, str):
            raise ShapeMismatch(f"{path} expected text, got {response_kind(value)}")
        _assert_text_shape(value, shape, path=path)
        return

    actual_kind = response_kind(value)
    if expected_kind != actual_kind:
        raise ShapeMismatch(f"{path} expected {expected_kind}, got {actual_kind}")

    if actual_kind == "json_array":
        _assert_array_shape(value, shape, path=path)
    elif actual_kind == "json_object":
        _assert_object_shape(value, shape, path=path)


def _assert_any_of_shape(value: Any, alternatives: Any, *, path: str) -> None:
    messages = []
    for alternative in alternatives:
        try:
            assert_shape(value, alternative, path=path)
        except ShapeMismatch as exc:
            messages.append(str(exc))
        else:
            return
    raise ShapeMismatch(f"{path} did not match any_of alternatives: {'; '.join(messages)}")


def _assert_array_shape(value: Sequence[Any], shape: Mapping[str, Any], *, path: str) -> None:
    expected_length = shape.get("length")
    if expected_length is not None and len(value) != expected_length:
        raise ShapeMismatch(f"{path} expected length {expected_length}, got {len(value)}")

    min_length = shape.get("min_length")
    if min_length is not None and len(value) < min_length:
        raise ShapeMismatch(f"{path} expected length >= {min_length}, got {len(value)}")

    item_shape = shape.get("items")
    if item_shape is not None:
        for index, item in enumerate(value):
            assert_shape(item, item_shape, path=f"{path}[{index}]")


def _assert_object_shape(value: Mapping[str, Any], shape: Mapping[str, Any], *, path: str) -> None:
    required_fields = shape.get("required_fields", [])
    for field in required_fields:
        if field not in value:
            raise ShapeMismatch(f"{path} missing required field {field!r}")

    field_shapes = shape.get("fields", {})
    for field, field_shape in field_shapes.items():
        if field not in value:
            raise ShapeMismatch(f"{path} missing shaped field {field!r}")
        assert_shape(value[field], field_shape, path=f"{path}.{field}")


def _assert_text_shape(value: str, shape: Mapping[str, Any], *, path: str) -> None:
    min_length = shape.get("min_length")
    if min_length is not None and len(value) < min_length:
        raise ShapeMismatch(f"{path} expected text length >= {min_length}, got {len(value)}")


def fingerprint_shape(value: Any) -> Any:
    """Build a compact shape fingerprint for reporting unexpected responses."""
    if isinstance(value, str):
        return {"kind": "text", "length": len(value)}

    kind = response_kind(value)
    if kind == "json_array":
        item_fingerprints = [fingerprint_shape(item) for item in value[:5]]
        return {
            "kind": kind,
            "length": len(value),
            "sample_items": item_fingerprints,
        }
    if kind == "json_object":
        return {
            "kind": kind,
            "fields": {key: fingerprint_shape(value[key]) for key in sorted(value)},
        }
    return {"kind": kind}
