#!/usr/bin/env python3
"""Fetch the live ASTROX OpenAPI document into the repo-owned baseline."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

import requests
import yaml


DEFAULT_BASE_URL = "http://astrox.cn:8765"
DEFAULT_OUTPUT = Path("openapi/astrox.openapi.yaml")


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object")
    return value


def require_key(mapping: dict[str, Any], key: str, context: str) -> Any:
    try:
        return mapping[key]
    except KeyError as exc:
        raise ValueError(f"{context} is missing required key {key!r}") from exc


def validate_openapi_spec(spec: Any) -> dict[str, Any]:
    document = require_mapping(spec, "OpenAPI document")
    require_key(document, "openapi", "OpenAPI document")
    info = require_mapping(require_key(document, "info", "OpenAPI document"), "OpenAPI info")
    require_key(info, "version", "OpenAPI info")
    paths = require_mapping(require_key(document, "paths", "OpenAPI document"), "OpenAPI paths")
    components = require_mapping(require_key(document, "components", "OpenAPI document"), "OpenAPI components")
    require_mapping(require_key(components, "schemas", "OpenAPI components"), "OpenAPI schemas")
    if not paths:
        raise ValueError("OpenAPI paths must be non-empty")
    return document


def fetch_openapi(base_url: str, timeout: float) -> dict[str, Any]:
    response = requests.get(f"{base_url.rstrip('/')}/openapi/v1.json", timeout=timeout)
    response.raise_for_status()
    return validate_openapi_spec(response.json())


def stable_yaml(spec: dict[str, Any]) -> str:
    return yaml.safe_dump(
        spec,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


def write_yaml(path: Path, spec: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_yaml(spec), encoding="utf-8")


def archive_name(version: str) -> str:
    safe_version = re.sub(r"[^A-Za-z0-9_.-]+", "_", version).strip("._-")
    return f"astrox.openapi.{safe_version or 'unknown'}.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("ASTROX_BASE_URL", DEFAULT_BASE_URL),
        help="ASTROX server base URL",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Canonical OpenAPI baseline path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        help="Optional directory for versioned OpenAPI snapshots",
    )
    args = parser.parse_args()

    spec = fetch_openapi(args.base_url, args.timeout)
    version = spec["info"]["version"]
    write_yaml(args.output, spec)

    archive_path = None
    if args.archive_dir:
        archive_path = args.archive_dir / archive_name(version)
        if not archive_path.exists():
            write_yaml(archive_path, spec)

    result = {
        "base_url": args.base_url,
        "openapi_version": version,
        "output": str(args.output),
        "archive": str(archive_path) if archive_path else None,
        "path_count": len(spec["paths"]),
        "schema_count": len(spec["components"]["schemas"]),
    }
    print("OPENAPI_FETCH_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
