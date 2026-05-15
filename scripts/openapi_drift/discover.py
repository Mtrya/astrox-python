#!/usr/bin/env python3
"""List OpenAPI endpoints and obvious branch axes for fixture planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


DEFAULT_OPENAPI = Path("openapi/astrox.openapi.yaml")
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
COMBINATORS = ("anyOf", "oneOf", "allOf")


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


def resolve_ref_name(ref: str) -> str | None:
    if ref.startswith("#/components/schemas/"):
        return ref.rsplit("/", 1)[-1]
    return None


class SchemaResolver:
    """Resolve local component schema references in an OpenAPI document."""

    def __init__(self, spec: dict[str, Any]) -> None:
        schemas = spec.get("components", {}).get("schemas", {})
        self.schemas = schemas if isinstance(schemas, dict) else {}

    def resolve_ref(self, ref: str) -> tuple[str, dict[str, Any]] | None:
        name = resolve_ref_name(ref)
        if name is None:
            return None
        schema = self.schemas.get(name)
        if not isinstance(schema, dict):
            return None
        return name, schema


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


def request_schema_object(operation: dict[str, Any]) -> dict[str, Any]:
    content = operation.get("requestBody", {}).get("content", {})
    if not isinstance(content, dict):
        return {}
    for media_type in ("application/json", "text/json", "application/*+json"):
        media = content.get(media_type, {})
        if isinstance(media, dict) and isinstance(media.get("schema"), dict):
            return media["schema"]
    return {}


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


def axis_provenance(*, source_ref: str | None, source_schema: str | None) -> dict[str, str]:
    provenance: dict[str, str] = {}
    if source_ref is not None:
        provenance["ref"] = source_ref
    if source_schema is not None:
        provenance["schema"] = source_schema
    return provenance


def is_discriminator_tag_enum(path: str, enum: list[Any]) -> bool:
    return path.endswith(".$type") and len(enum) == 1


def dedupe_axes(axes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped = []
    for axis in axes:
        key = json.dumps(axis, sort_keys=True)
        if key not in seen:
            seen.add(key)
            deduped.append(axis)
    return deduped


def find_branch_axes(
    schema: Any,
    *,
    resolver: SchemaResolver | None = None,
    path: str = "$",
    source_ref: str | None = None,
    source_schema: str | None = None,
    seen_refs: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    axes: list[dict[str, Any]] = []
    if isinstance(schema, dict):
        ref = schema.get("$ref")
        if isinstance(ref, str) and resolver is not None:
            resolved = resolver.resolve_ref(ref)
            if resolved is None or ref in seen_refs:
                return axes
            resolved_name, resolved_schema = resolved
            return find_branch_axes(
                resolved_schema,
                resolver=resolver,
                path=path,
                source_ref=ref,
                source_schema=resolved_name,
                seen_refs=seen_refs | {ref},
            )

        enum = schema.get("enum")
        if isinstance(enum, list) and enum:
            if not is_discriminator_tag_enum(path, enum):
                axes.append(
                    {
                        "path": path,
                        "kind": "enum",
                        "values": enum,
                        "provenance": axis_provenance(source_ref=source_ref, source_schema=source_schema),
                    }
                )

        discriminator = schema.get("discriminator")
        if isinstance(discriminator, dict):
            property_name = discriminator.get("propertyName")
            mapping = discriminator.get("mapping")
            axis: dict[str, Any] = {
                "path": path,
                "kind": "discriminator",
                "provenance": axis_provenance(source_ref=source_ref, source_schema=source_schema),
            }
            if isinstance(property_name, str):
                axis["property"] = property_name
            if isinstance(mapping, dict):
                axis["values"] = sorted(mapping)
            axes.append(axis)

        properties = schema.get("properties")
        if isinstance(properties, dict):
            for key, value in properties.items():
                next_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                axes.extend(
                    find_branch_axes(
                        value,
                        resolver=resolver,
                        path=next_path,
                        source_ref=source_ref,
                        source_schema=source_schema,
                        seen_refs=seen_refs,
                    )
                )

        items = schema.get("items")
        if items is not None:
            axes.extend(
                find_branch_axes(
                    items,
                    resolver=resolver,
                    path=f"{path}[]",
                    source_ref=source_ref,
                    source_schema=source_schema,
                    seen_refs=seen_refs,
                )
            )

        for key in COMBINATORS:
            values = schema.get(key)
            if isinstance(values, list):
                for item in values:
                    axes.extend(
                        find_branch_axes(
                            item,
                            resolver=resolver,
                            path=path,
                            source_ref=source_ref,
                            source_schema=source_schema,
                            seen_refs=seen_refs,
                        )
                    )
    elif isinstance(schema, list):
        for item in schema:
            axes.extend(
                find_branch_axes(
                    item,
                    resolver=resolver,
                    path=path,
                    source_ref=source_ref,
                    source_schema=source_schema,
                    seen_refs=seen_refs,
                )
            )
    return axes


def discover(spec: dict[str, Any]) -> list[dict[str, Any]]:
    resolver = SchemaResolver(spec)
    results: list[dict[str, Any]] = []

    for endpoint, methods in sorted(spec.get("paths", {}).items()):
        if not isinstance(methods, dict):
            continue
        for method, operation in sorted(methods.items()):
            if method.lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue
            request_name = request_schema(operation)
            request_shape = request_schema_object(operation)
            results.append(
                {
                    "endpoint": endpoint,
                    "method": method.upper(),
                    "operation_id": operation_id(operation),
                    "request_schema": request_name,
                    "response_schema": response_schema(operation),
                    "branch_axes": dedupe_axes(find_branch_axes(request_shape, resolver=resolver)),
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
    payload = {"endpoint_count": len(endpoints), "endpoints": endpoints}
    print(json.dumps(payload, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
