#!/usr/bin/env python3
"""Report discovered OpenAPI contracts that lack checked-in fixture evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

try:
    from scripts.openapi_drift.discover import DEFAULT_OPENAPI, discover, load_spec
    from scripts.openapi_drift.reconcile import reconcile_branch
    from scripts.openapi_drift.verify import (
        DEFAULT_BASE_URL,
        DEFAULT_FIXTURE_DIR,
        iter_fixture_paths,
        load_fixture,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from discover import DEFAULT_OPENAPI, discover, load_spec
    from reconcile import reconcile_branch
    from verify import DEFAULT_BASE_URL, DEFAULT_FIXTURE_DIR, iter_fixture_paths, load_fixture


def load_fixtures(fixture_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    return [(path, load_fixture(path)) for path in iter_fixture_paths(fixture_dir)]


def endpoint_fixture_index(
    fixtures: list[tuple[Path, dict[str, Any]]],
) -> dict[str, list[tuple[Path, dict[str, Any]]]]:
    by_endpoint: dict[str, list[tuple[Path, dict[str, Any]]]] = defaultdict(list)
    for path, fixture in fixtures:
        by_endpoint[fixture["endpoint"]].append((path, fixture))
    return dict(by_endpoint)


def path_tokens(path: str) -> list[tuple[str, bool]]:
    """Parse discovery JSON paths such as ``$.Items[].Position``."""
    if path == "$":
        return []
    if not path.startswith("$."):
        raise ValueError(f"unsupported discovery path {path!r}")
    tokens: list[tuple[str, bool]] = []
    for raw_part in path[2:].split("."):
        if not raw_part:
            raise ValueError(f"unsupported discovery path {path!r}")
        if raw_part.endswith("[]"):
            tokens.append((raw_part[:-2], True))
        else:
            tokens.append((raw_part, False))
    return tokens


def values_at_path(value: Any, path: str) -> list[Any]:
    values = [value]
    for key, is_array in path_tokens(path):
        next_values: list[Any] = []
        for item in values:
            if not isinstance(item, dict) or key not in item:
                continue
            child = item[key]
            if is_array:
                if isinstance(child, list):
                    next_values.extend(child)
            else:
                next_values.append(child)
        values = next_values
    return values


def axis_observed_values(request_payload: Any, axis: dict[str, Any]) -> list[Any]:
    axis_values = values_at_path(request_payload, axis["path"])
    property_name = axis.get("property")
    if isinstance(property_name, str):
        observed = []
        for value in axis_values:
            if isinstance(value, dict) and property_name in value:
                observed.append(value[property_name])
        return observed
    return axis_values


def value_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def state_priority(state: str) -> int:
    if state == "verified":
        return 2
    if state == "blocked":
        return 1
    return 0


def best_state(states: list[str]) -> str:
    if not states:
        return "uncovered"
    return max(states, key=state_priority)


def state_label(state: str) -> str:
    if state == "verified":
        return "x"
    if state == "blocked":
        return "!"
    if state == "partial":
        return "~"
    return " "


def axis_key(axis: dict[str, Any]) -> str:
    payload = {
        "path": axis.get("path"),
        "kind": axis.get("kind"),
        "property": axis.get("property"),
        "values": axis.get("values"),
        "provenance": axis.get("provenance"),
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def fixture_evidence_for_axis(
    *,
    endpoint_fixtures: list[tuple[Path, dict[str, Any]]],
    axis: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_values = axis.get("values")
    if not isinstance(candidate_values, list) or not candidate_values:
        return {}
    candidate_keys = {value_key(value): value for value in candidate_values}

    for path, fixture in endpoint_fixtures:
        for branch_id, branch in fixture["branches"].items():
            if not isinstance(branch, dict):
                continue
            state = branch.get("state")
            if state not in {"verified", "blocked"}:
                continue
            request_payload = branch.get("request")
            for observed_value in axis_observed_values(request_payload, axis):
                observed_key = value_key(observed_value)
                if observed_key not in candidate_keys:
                    continue
                evidence[observed_key].append(
                    {
                        "fixture": str(path),
                        "branch": branch_id,
                        "state": state,
                    }
                )
    return dict(evidence)


def axis_value_reports(
    *,
    endpoint: dict[str, Any],
    axis: dict[str, Any],
    endpoint_fixtures: list[tuple[Path, dict[str, Any]]],
) -> list[dict[str, Any]]:
    values = axis.get("values")
    if not isinstance(values, list):
        return []
    evidence = fixture_evidence_for_axis(endpoint_fixtures=endpoint_fixtures, axis=axis)
    reports = []
    for value in values:
        value_evidence = evidence.get(value_key(value), [])
        state = best_state([item["state"] for item in value_evidence])
        reports.append(
            {
                "endpoint": endpoint["endpoint"],
                "method": endpoint["method"],
                "request_schema": endpoint.get("request_schema"),
                "response_schema": endpoint.get("response_schema"),
                "axis_path": axis["path"],
                "axis_kind": axis["kind"],
                "axis_property": axis.get("property"),
                "value": value,
                "state": state,
                "fixture_evidence": sorted(
                    value_evidence,
                    key=lambda item: (item["state"], item["fixture"], item["branch"]),
                ),
            }
        )
    return reports


def axis_state(value_reports: list[dict[str, Any]]) -> str:
    if not value_reports:
        return "uncovered"
    states = [value["state"] for value in value_reports]
    if all(state == "verified" for state in states):
        return "verified"
    if all(state == "blocked" for state in states):
        return "blocked"
    if any(state in {"verified", "blocked"} for state in states):
        return "partial"
    return "uncovered"


def endpoint_report(endpoint: dict[str, Any], fixture_paths: list[Path]) -> dict[str, Any]:
    return {
        "endpoint": endpoint["endpoint"],
        "method": endpoint["method"],
        "operation_id": endpoint.get("operation_id"),
        "request_schema": endpoint.get("request_schema"),
        "response_schema": endpoint.get("response_schema"),
        "fixture_paths": [str(path) for path in fixture_paths],
    }


def discovery_fixture_report(
    *,
    openapi: Path,
    fixture_dir: Path,
    probe_blocked: bool = False,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 30.0,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    endpoints = discover(load_spec(openapi))
    fixtures = load_fixtures(fixture_dir)
    by_endpoint = endpoint_fixture_index(fixtures)
    endpoint_by_name = {endpoint["endpoint"]: endpoint for endpoint in endpoints}

    missing_endpoints = [
        endpoint_report(endpoint, [])
        for endpoint in endpoints
        if endpoint["endpoint"] not in by_endpoint
    ]

    axis_reports = []
    axis_value_count = 0
    covered_axis_value_count = 0
    for endpoint in endpoints:
        endpoint_fixtures = by_endpoint.get(endpoint["endpoint"], [])
        fixture_paths = [path for path, _ in endpoint_fixtures]
        for axis in endpoint["branch_axes"]:
            value_reports = axis_value_reports(
                endpoint=endpoint,
                axis=axis,
                endpoint_fixtures=endpoint_fixtures,
            )
            axis_value_count += len(value_reports)
            covered_axis_value_count += sum(
                1 for value_report in value_reports if value_report["state"] in {"verified", "blocked"}
            )
            axis_reports.append(
                {
                    "endpoint": endpoint["endpoint"],
                    "method": endpoint["method"],
                    "operation_id": endpoint.get("operation_id"),
                    "request_schema": endpoint.get("request_schema"),
                    "response_schema": endpoint.get("response_schema"),
                    "axis_path": axis["path"],
                    "axis_kind": axis["kind"],
                    "axis_property": axis.get("property"),
                    "axis_provenance": axis.get("provenance", {}),
                    "values": value_reports,
                    "state": axis_state(value_reports),
                    "fixture_paths": [str(path) for path in fixture_paths],
                    "axis_key": axis_key(axis),
                }
            )

    uncovered_axis_values = [
        value_report
        for axis in axis_reports
        for value_report in axis["values"]
        if value_report["state"] == "uncovered"
    ]
    uncovered_axes = [
        axis
        for axis in axis_reports
        if axis["state"] == "uncovered"
    ]
    previously_blocked_now_reachable = (
        probe_blocked_branches(
            fixtures=fixtures,
            base_url=base_url,
            timeout=timeout,
            session=session,
        )
        if probe_blocked
        else []
    )

    fixture_only_endpoints = [
        {
            "endpoint": endpoint,
            "fixture_paths": [str(path) for path, _ in by_endpoint[endpoint]],
        }
        for endpoint in sorted(set(by_endpoint) - set(endpoint_by_name))
    ]

    return {
        "openapi": str(openapi),
        "fixture_dir": str(fixture_dir),
        "endpoint_count": len(endpoints),
        "fixture_endpoint_count": len(by_endpoint),
        "fixture_file_count": len(fixtures),
        "missing_endpoint_count": len(missing_endpoints),
        "missing_endpoints": missing_endpoints,
        "fixture_only_endpoint_count": len(fixture_only_endpoints),
        "fixture_only_endpoints": fixture_only_endpoints,
        "axis_count": len(axis_reports),
        "axis_value_count": axis_value_count,
        "covered_axis_value_count": covered_axis_value_count,
        "uncovered_axis_count": len(uncovered_axes),
        "uncovered_axis_value_count": len(uncovered_axis_values),
        "axis_reports": sorted(
            axis_reports,
            key=lambda item: (
                item["endpoint"].lower(),
                item["axis_path"],
                item["axis_kind"],
                json.dumps(item.get("axis_property"), sort_keys=True),
                json.dumps(item.get("axis_provenance"), sort_keys=True),
            ),
        ),
        "uncovered_axes": sorted(
            uncovered_axes,
            key=lambda item: (item["endpoint"].lower(), item["axis_path"], item["axis_key"]),
        ),
        "uncovered_axis_values": sorted(
            uncovered_axis_values,
            key=lambda item: (
                item["endpoint"].lower(),
                item["axis_path"],
                json.dumps(item["value"], sort_keys=True),
            ),
        ),
        "probe_blocked": probe_blocked,
        "previously_blocked_now_reachable_count": len(previously_blocked_now_reachable),
        "previously_blocked_now_reachable": previously_blocked_now_reachable,
    }


def probe_blocked_branches(
    *,
    fixtures: list[tuple[Path, dict[str, Any]]],
    base_url: str,
    timeout: float,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    owns_session = session is None
    if session is None:
        session = requests.Session()
    try:
        for path, fixture in fixtures:
            for branch_id, branch in fixture["branches"].items():
                if not isinstance(branch, dict) or branch.get("state") != "blocked":
                    continue
                result = reconcile_branch(
                    session=session,
                    base_url=base_url,
                    timeout=timeout,
                    fixture_path=path,
                    fixture=fixture,
                    branch_id=branch_id,
                    branch=branch,
                    apply=False,
                    today="",
                )
                if result.get("classification") == "previously_blocked_now_reachable":
                    results.append(result)
    finally:
        if owns_session:
            session.close()
    return sorted(results, key=lambda item: (item["endpoint"].lower(), item["branch"], item["fixture"]))


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# OpenAPI Fixture Discovery Report",
        "",
        f"- source spec: `{report['openapi']}`",
        f"- fixture directory: `{report['fixture_dir']}`",
        f"- discovered endpoints: {report['endpoint_count']}",
        f"- fixture endpoint records: {report['fixture_endpoint_count']}",
        f"- missing endpoint fixtures: {report['missing_endpoint_count']}",
        f"- discovered branch axes: {report['axis_count']}",
        f"- discovered branch axis values: {report['axis_value_count']}",
        f"- covered discovered axis values: {report['covered_axis_value_count']}",
        f"- uncovered discovered axis values: {report['uncovered_axis_value_count']}",
        f"- previously blocked now reachable: {report['previously_blocked_now_reachable_count']}",
        "",
        "## Missing Endpoint Fixtures",
        "",
    ]
    if report["missing_endpoints"]:
        for endpoint in report["missing_endpoints"]:
            lines.append(
                f"- `{endpoint['endpoint']}` {endpoint['method']} "
                f"(request `{endpoint['request_schema']}`, response `{endpoint['response_schema']}`)"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Uncovered Branch Axis Values", ""])
    if report["uncovered_axis_values"]:
        for value in report["uncovered_axis_values"]:
            property_text = (
                f", property `{value['axis_property']}`"
                if value.get("axis_property") is not None
                else ""
            )
            lines.append(
                f"- `{value['endpoint']}` `{value['axis_path']}` "
                f"({value['axis_kind']}{property_text}) value `{value['value']}`"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Previously Blocked Now Reachable", ""])
    if report["previously_blocked_now_reachable"]:
        for result in report["previously_blocked_now_reachable"]:
            lines.append(
                f"- `{result['endpoint']}` `{result['branch']}` "
                f"({result['fixture']}, HTTP {result.get('status')})"
            )
    elif report["probe_blocked"]:
        lines.append("- none")
    else:
        lines.append("- not probed")
    return "\n".join(lines).rstrip() + "\n"


def write_report_outputs(
    *,
    report: dict[str, Any],
    json_output: Path | None,
    markdown_output: Path | None,
) -> None:
    if json_output is not None:
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if markdown_output is not None:
        markdown_output.write_text(markdown_report(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, default=DEFAULT_OPENAPI)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--probe-blocked", action="store_true")
    parser.add_argument("--base-url", default=os.environ.get("ASTROX_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    report = discovery_fixture_report(
        openapi=args.openapi,
        fixture_dir=args.fixture_dir,
        probe_blocked=args.probe_blocked,
        base_url=args.base_url,
        timeout=args.timeout,
    )
    write_report_outputs(
        report=report,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
    )
    print("OPENAPI_FIXTURE_DISCOVERY_REPORT_JSON=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"OPENAPI_FIXTURE_DISCOVERY_REPORT_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        raise
