#!/usr/bin/env python3
"""Normalize OpenAPI fixture YAML into the checked-in deterministic format."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts.openapi_drift.verify import iter_fixture_paths, validate_fixture
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from verify import iter_fixture_paths, validate_fixture


DEFAULT_FIXTURE_DIR = Path("openapi/fixtures")
TOP_LEVEL_KEYS = (
    "schema_version",
    "endpoint",
    "method",
    "openapi_operation_id",
    "openapi_request_schema",
    "openapi_response_schema",
    "branches",
)
BRANCH_KEYS = ("state", "request", "expect", "blocked")
BLOCKED_KEYS = (
    "reason",
    "observed_status",
    "observed_content_type",
    "observed_shape",
    "last_seen",
    "note",
)


class FixtureDumper(yaml.SafeDumper):
    """YAML dumper that expands repeated objects instead of emitting anchors."""

    def ignore_aliases(self, data: Any) -> bool:
        return True

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> Any:
        return super().increase_indent(flow=flow, indentless=False)


def plain_copy(value: Any) -> Any:
    """Return a JSON/YAML-compatible deep copy without shared references."""
    if isinstance(value, dict):
        return {str(key): plain_copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plain_copy(item) for item in value]
    return value


def ordered_subset(mapping: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in keys:
        if key in mapping:
            ordered[key] = plain_copy(mapping[key])
    for key in sorted(set(mapping) - set(keys)):
        ordered[key] = plain_copy(mapping[key])
    return ordered


def inferred_branch_state(branch: dict[str, Any]) -> str:
    state = branch.get("state")
    if isinstance(state, str):
        return state
    if "blocked" in branch and "expect" not in branch:
        return "blocked"
    return "verified"


def normalize_branch(branch: dict[str, Any]) -> dict[str, Any]:
    state = inferred_branch_state(branch)
    normalized: dict[str, Any] = {"state": state}
    if "request" in branch:
        normalized["request"] = plain_copy(branch["request"])
    if state == "blocked":
        normalized["blocked"] = ordered_subset(plain_copy(branch["blocked"]), BLOCKED_KEYS)
    else:
        normalized["expect"] = plain_copy(branch["expect"])
    return ordered_subset(normalized, BRANCH_KEYS)


def normalize_fixture_data(fixture: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key in TOP_LEVEL_KEYS:
        if key == "branches":
            branches = fixture["branches"]
            normalized["branches"] = {
                branch_id: normalize_branch(branch)
                for branch_id, branch in branches.items()
            }
        else:
            normalized[key] = plain_copy(fixture[key])
    return normalized


def dump_fixture(fixture: dict[str, Any]) -> str:
    text = yaml.dump(
        normalize_fixture_data(fixture),
        Dumper=FixtureDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )
    return text if text.endswith("\n") else f"{text}\n"


def normalize_fixture_file(path: Path, *, check: bool = False) -> bool:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} did not load as an object")
    fixture = normalize_fixture_data(loaded)
    validate_fixture(fixture, path=path)
    normalized = dump_fixture(fixture)
    current = path.read_text(encoding="utf-8")
    changed = current != normalized
    if changed and not check:
        path.write_text(normalized, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--check", action="store_true", help="fail if any fixture would change")
    args = parser.parse_args()

    changed_paths = [
        path
        for path in iter_fixture_paths(args.fixture_dir)
        if normalize_fixture_file(path, check=args.check)
    ]
    if changed_paths:
        for path in changed_paths:
            print(path)
        if args.check:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
