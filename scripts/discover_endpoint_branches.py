#!/usr/bin/env python3
"""
Discover branch axes for an endpoint from the local OpenAPI YAML.

Usage:
    python scripts/discover_endpoint_branches.py /access/AccessComputeV2
    python scripts/discover_endpoint_branches.py /Propagator/Ballistic
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_SPEC = Path("openapi/astrox.openapi.yaml")
PRIMARY_NESTED_BRANCH_FIELDS = {"Position", "Grid"}
PRIMARY_SCALAR_BRANCH_FIELDS = {
    "BallisticType",
    "ComputeAER",
    "UseLightTimeDelay",
    "ContainAssetAccessResults",
    "ContainCoveragePoints",
    "FilterType",
    "Output",
    "Method",
    "Version",
    "CoordType",
    "CoordSystem",
}


def load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def find_block(lines: list[str], header: str, indent: int) -> list[str]:
    prefix = " " * indent
    target = f"{prefix}{header}:"

    start = None
    for index, line in enumerate(lines):
        if line == target:
            start = index
            break

    if start is None:
        raise KeyError(f"Could not find block for {header!r}")

    block: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith(prefix) and not line.startswith(prefix + " ") and line.endswith(":"):
            break
        block.append(line)
    return block


def find_endpoint_request_schema(lines: list[str], endpoint: str) -> str:
    block = find_block(lines, endpoint, indent=2)
    pattern = re.compile(r"#/components/schemas/([^']+)")
    for line in block:
        match = pattern.search(line)
        if match:
            return match.group(1)
    raise KeyError(f"Could not find request schema for endpoint {endpoint}")


def parse_property_blocks(schema_block: list[str]) -> dict[str, list[str]]:
    properties: dict[str, list[str]] = {}
    in_properties = False
    current_name: str | None = None
    current_block: list[str] = []

    for line in schema_block:
        if not in_properties:
            if line.strip() == "properties:":
                in_properties = True
            continue

        if re.match(r"^\s{8}[A-Za-z0-9_$]+:$", line):
            if current_name is not None:
                properties[current_name] = current_block
            current_name = line.strip()[:-1]
            current_block = []
            continue

        if line.startswith("    ") and not line.startswith("      "):
            break

        if current_name is not None:
            current_block.append(line)

    if current_name is not None:
        properties[current_name] = current_block

    return properties


def extract_ref(block: list[str]) -> str | None:
    pattern = re.compile(r"#/components/schemas/([^']+)")
    for line in block:
        match = pattern.search(line)
        if match:
            return match.group(1)
    return None


def extract_enum_values(block: list[str]) -> list[str]:
    values: list[str] = []
    in_enum = False

    for line in block:
        stripped = line.strip()
        if stripped == "enum:":
            in_enum = True
            continue
        if in_enum:
            if stripped.startswith("- "):
                values.append(stripped[2:])
                continue
            break

    if values:
        return values

    for line in block:
        stripped = line.strip()
        if not stripped.startswith("description:"):
            continue

        text = stripped.split(":", 1)[1]

        for pattern in (
            r"取值:\s*([^'<>]+)",
            r"\(([A-Za-z0-9_,+\-]+)\)",
        ):
            match = re.search(pattern, text)
            if not match:
                continue
            raw_values = match.group(1)
            if "," not in raw_values and "取值" not in text:
                continue
            values = [value.strip() for value in raw_values.split(",") if value.strip()]
            if values:
                return values

    return []


def is_boolean_property(block: list[str]) -> bool:
    for line in block:
        if line.strip() == "type: boolean":
            return True
    return False


def extract_discriminator_values(schema_block: list[str]) -> list[str]:
    values: list[str] = []
    in_discriminator = False
    in_mapping = False

    for line in schema_block:
        if line == "      discriminator:":
            in_discriminator = True
            continue
        if in_discriminator and line == "        mapping:":
            in_mapping = True
            continue
        if in_mapping:
            if re.match(r"^\s{10}[A-Za-z0-9_]+:", line):
                values.append(line.strip().split(":", 1)[0])
                continue
            break

    return values


def extract_property_discriminator_values(block: list[str]) -> list[str]:
    values: list[str] = []
    in_discriminator = False
    in_mapping = False
    skip_keys = {"description", "nullable", "discriminator", "propertyName", "mapping"}

    for line in block:
        stripped = line.strip()
        if stripped == "discriminator:":
            in_discriminator = True
            continue
        if in_discriminator and stripped == "mapping:":
            in_mapping = True
            continue
        if in_mapping:
            if re.match(r"^\s+[A-Za-z0-9_]+:", line):
                key = stripped.split(":", 1)[0]
                if key not in skip_keys:
                    values.append(key)
                continue
            break

    return values


def unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def discover_from_schema(
    lines: list[str],
    schema_name: str,
    prefix: str = "",
    depth: int = 0,
) -> list[str]:
    if depth > 2:
        return []

    schema_block = find_block(lines, schema_name, indent=4)
    property_blocks = parse_property_blocks(schema_block)
    branches: list[str] = []

    discriminator_values = extract_discriminator_values(schema_block)
    if discriminator_values and prefix:
        branches.extend(f"{prefix}.$type={value}" for value in discriminator_values)

    for property_name, property_block in property_blocks.items():
        property_prefix = f"{prefix}.{property_name}" if prefix else property_name
        should_follow_nested_ref = depth == 0 or property_name in PRIMARY_NESTED_BRANCH_FIELDS
        should_keep_property = (
            depth == 0
            or property_name in PRIMARY_NESTED_BRANCH_FIELDS
            or property_name in PRIMARY_SCALAR_BRANCH_FIELDS
        )

        if not should_keep_property:
            continue

        if is_boolean_property(property_block):
            branches.append(f"{property_prefix}=true")
            continue

        property_discriminator_values = extract_property_discriminator_values(property_block)
        if property_discriminator_values:
            branches.extend(
                f"{property_prefix}.$type={value}"
                for value in property_discriminator_values
            )

        enum_values = extract_enum_values(property_block)
        if enum_values and property_name != "$type":
            branches.extend(f"{property_prefix}={value}" for value in enum_values)

        ref_name = extract_ref(property_block)
        if ref_name is None:
            continue

        if not should_follow_nested_ref:
            continue

        branches.extend(
            discover_from_schema(lines, ref_name, prefix=property_prefix, depth=depth + 1)
        )

    return unique_keep_order(branches)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("endpoint", help="Endpoint path, for example /access/AccessComputeV2")
    parser.add_argument(
        "--spec",
        type=Path,
        default=DEFAULT_SPEC,
        help=f"OpenAPI YAML to inspect (default: {DEFAULT_SPEC})",
    )
    args = parser.parse_args()

    if not args.spec.exists():
        print(f"Spec file not found: {args.spec}", file=sys.stderr)
        return 1

    lines = load_lines(args.spec)

    try:
        request_schema = find_endpoint_request_schema(lines, args.endpoint)
        branches = discover_from_schema(lines, request_schema)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"## `{args.endpoint}`")
    for branch in branches:
        print(f"- [ ] `{branch}`")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
