#!/usr/bin/env python3
"""List OpenAPI endpoints and obvious branch axes for fixture planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


DEFAULT_OPENAPI = Path("openapi/astrox.openapi.yaml")


def load_spec(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} did not load as an object")
    return loaded


def operation_id(operation: dict[str, Any]) -> str | None:
    value = operation.get("operationId")
    return value if isinstance(value, str) else None


def schema_ref_name(schema: dict[str, Any]) -> str | None:
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        return ref.rsplit("/", 1)[-1]
    return None


def request_schema(operation: dict[str, Any]) -> str | None:
    content = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
    )
    schema = content.get("schema", {})
    if isinstance(schema, dict):
        return schema_ref_name(schema)
    return None


def response_schema(operation: dict[str, Any]) -> str | None:
    content = (
        operation.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
    )
    schema = content.get("schema", {})
    if isinstance(schema, dict):
        return schema_ref_name(schema) or schema.get("type")
    return None


def find_branch_axes(schema: Any, *, path: str = "$") -> list[dict[str, Any]]:
    axes: list[dict[str, Any]] = []
    if isinstance(schema, dict):
        enum = schema.get("enum")
        if isinstance(enum, list) and enum:
            axes.append({"path": path, "kind": "enum", "values": enum})

        discriminator = schema.get("discriminator")
        if isinstance(discriminator, dict):
            property_name = discriminator.get("propertyName")
            mapping = discriminator.get("mapping")
            axis: dict[str, Any] = {"path": path, "kind": "discriminator"}
            if isinstance(property_name, str):
                axis["property"] = property_name
            if isinstance(mapping, dict):
                axis["values"] = sorted(mapping)
            axes.append(axis)

        for key, value in schema.items():
            next_path = f"{path}.{key}" if path else key
            axes.extend(find_branch_axes(value, path=next_path))
    elif isinstance(schema, list):
        for index, item in enumerate(schema):
            axes.extend(find_branch_axes(item, path=f"{path}[{index}]"))
    return axes


def discover(spec: dict[str, Any]) -> list[dict[str, Any]]:
    schemas = spec.get("components", {}).get("schemas", {})
    results: list[dict[str, Any]] = []

    for endpoint, methods in sorted(spec.get("paths", {}).items()):
        if not isinstance(methods, dict):
            continue
        for method, operation in sorted(methods.items()):
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            request_name = request_schema(operation)
            request_shape = schemas.get(request_name, {}) if request_name else {}
            results.append(
                {
                    "endpoint": endpoint,
                    "method": method.upper(),
                    "operation_id": operation_id(operation),
                    "request_schema": request_name,
                    "response_schema": response_schema(operation),
                    "branch_axes": find_branch_axes(request_shape),
                }
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, default=DEFAULT_OPENAPI)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    endpoints = discover(load_spec(args.openapi))
    indent = 2 if args.pretty else None
    print(json.dumps({"endpoint_count": len(endpoints), "endpoints": endpoints}, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

