#!/usr/bin/env python3
"""Build CI-facing reports for the unified OpenAPI drift workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ISSUE_TITLE = "ASTROX fixture blocked branches now reachable"
PR_TITLE = "Refresh ASTROX upstream drift data"


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} did not contain valid JSON: {exc.msg}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return loaded


def parse_porcelain_status(text: str) -> list[str]:
    paths = []
    for line in text.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:].strip())
    return paths


def changed_categories(paths: list[str]) -> dict[str, bool]:
    return {
        "openapi_baseline": "openapi/astrox.openapi.yaml" in paths,
        "openapi_archive": any(path.startswith("openapi/archive/") for path in paths),
        "fixture_yaml": any(path.startswith("openapi/fixtures/") and path.endswith(".yaml") for path in paths),
        "fixture_status": "openapi/fixtures/STATUS.md" in paths,
    }


def test_failed(outcomes: dict[str, str]) -> bool:
    return any(value not in {"0", "success", "skipped", ""} for value in outcomes.values())


DRIFT_CHECK_LABELS = {
    "fixture_verification": "fixture replay (`verify.py`)",
    "focused": "drift consistency checks (`normalize.py`, `generate_status.py --check`, fixture tests)",
    "pytest": "full test suite inside drift workflow (`pytest tests`)",
}

CLASSIFICATION_LABELS = {
    "previously_blocked_now_reachable": "previously blocked fixture branch now returns a response",
    "verified_expect_refreshed": "verified fixture expectation refreshed",
    "verified_now_empty_http_500": "verified fixture now returns empty HTTP 500",
    "verified_unchanged": "verified fixture unchanged",
    "workflow_test_failure": "drift workflow check failure",
}


def top_items(items: list[Any], *, limit: int = 20) -> list[Any]:
    return items[:limit]


def reconcile_changed_results(reconcile_report: dict[str, Any]) -> list[dict[str, Any]]:
    results = reconcile_report.get("results", [])
    if not isinstance(results, list):
        return []
    return [
        result
        for result in results
        if isinstance(result, dict) and result.get("changed")
    ]


def reconcile_report_only_results(reconcile_report: dict[str, Any]) -> list[dict[str, Any]]:
    results = reconcile_report.get("results", [])
    if not isinstance(results, list):
        return []
    return [
        result
        for result in results
        if isinstance(result, dict) and result.get("action") == "report"
    ]


def blocked_now_reachable_results(
    reconcile_report: dict[str, Any],
    discovery_report: dict[str, Any],
) -> list[dict[str, Any]]:
    discovery_results = discovery_report.get("previously_blocked_now_reachable", [])
    if not isinstance(discovery_results, list):
        discovery_results = []
    reconcile_results = [
        result
        for result in reconcile_report_only_results(reconcile_report)
        if result.get("classification") == "previously_blocked_now_reachable"
    ]
    by_key = {
        json.dumps(
            {
                "fixture": item.get("fixture"),
                "endpoint": item.get("endpoint"),
                "branch": item.get("branch"),
            },
            sort_keys=True,
        ): item
        for item in [*discovery_results, *reconcile_results]
        if isinstance(item, dict)
    }
    return [by_key[key] for key in sorted(by_key)]


def build_pipeline_report(
    *,
    tracked_paths: list[str],
    reconcile_report: dict[str, Any],
    discovery_report: dict[str, Any],
    test_outcomes: dict[str, str],
) -> dict[str, Any]:
    blocked_now_reachable = blocked_now_reachable_results(reconcile_report, discovery_report)
    changed = bool(tracked_paths)
    pr_required = changed
    issue_required = (not pr_required) and bool(blocked_now_reachable)
    hard_cases = reconcile_report_only_results(reconcile_report)
    if test_failed(test_outcomes):
        hard_cases.append(
            {
                "classification": "workflow_test_failure",
                "error": "one or more drift workflow checks failed; inspect report artifacts",
            }
        )

    return {
        "tracked_diff_expected": changed,
        "pr_required": pr_required,
        "issue_required": issue_required,
        "issue_title": ISSUE_TITLE,
        "pr_title": PR_TITLE,
        "tracked_paths": tracked_paths,
        "changed_categories": changed_categories(tracked_paths),
        "test_outcomes": test_outcomes,
        "test_failed": test_failed(test_outcomes),
        "reconcile": {
            "changed_count": reconcile_report.get("changed_count", 0),
            "changed_fixture_paths": reconcile_report.get("changed_fixture_paths", []),
            "classification_counts": reconcile_report.get("classification_counts", {}),
            "action_counts": reconcile_report.get("action_counts", {}),
            "changed_results": reconcile_changed_results(reconcile_report),
            "report_only_results": reconcile_report_only_results(reconcile_report),
        },
        "discovery": {
            "missing_endpoint_count": discovery_report.get("missing_endpoint_count", 0),
            "missing_endpoints": discovery_report.get("missing_endpoints", []),
            "axis_count": discovery_report.get("axis_count", 0),
            "axis_value_count": discovery_report.get("axis_value_count", 0),
            "covered_axis_value_count": discovery_report.get("covered_axis_value_count", 0),
            "uncovered_axis_value_count": discovery_report.get("uncovered_axis_value_count", 0),
            "uncovered_axis_values": discovery_report.get("uncovered_axis_values", []),
            "previously_blocked_now_reachable_count": len(blocked_now_reachable),
            "previously_blocked_now_reachable": blocked_now_reachable,
        },
        "unresolved_hard_cases": hard_cases,
    }


def format_bool(value: bool) -> str:
    return "yes" if value else "no"


def format_count(noun: str, count: int) -> str:
    suffix = "" if count == 1 else "s"
    return f"{count} {noun}{suffix}"


def changed_categories_markdown(categories: dict[str, bool]) -> list[str]:
    labels = {
        "openapi_baseline": "OpenAPI description",
        "openapi_archive": "dated OpenAPI archive copy",
        "fixture_yaml": "fixture files",
        "fixture_status": "fixture coverage tracker",
    }
    return [f"- {label}: {format_bool(categories[key])}" for key, label in labels.items()]


def human_classification(name: str) -> str:
    return CLASSIFICATION_LABELS.get(name, name.replace("_", " "))


def classification_counts_markdown(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none recorded"]
    lines = []
    for name, count in sorted(counts.items()):
        lines.append(f"- {human_classification(name)}: {count}")
    return lines


def check_outcome_line(name: str, outcome: str) -> str:
    label = DRIFT_CHECK_LABELS.get(name)
    if label is not None:
        return f"- {label}: `{outcome}`"
    return f"- `{name}`: `{outcome}`"


def endpoint_line(item: dict[str, Any]) -> str:
    return (
        f"- `{item.get('endpoint')}` {item.get('method')} "
        f"(request `{item.get('request_schema')}`, response `{item.get('response_schema')}`)"
    )


def axis_value_line(item: dict[str, Any]) -> str:
    property_text = f", property `{item.get('axis_property')}`" if item.get("axis_property") else ""
    return (
        f"- `{item.get('endpoint')}` `{item.get('axis_path')}` "
        f"({item.get('axis_kind')}{property_text}) value `{item.get('value')}`"
    )


def changed_branch_line(item: dict[str, Any]) -> str:
    return (
        f"- `{item.get('endpoint')}` `{item.get('branch')}`: "
        f"{human_classification(str(item.get('classification', 'unknown')))} ({item.get('fixture')})"
    )


def blocked_reachable_line(item: dict[str, Any]) -> str:
    return (
        f"- `{item.get('endpoint')}` `{item.get('branch')}` "
        f"({item.get('fixture')}, HTTP {item.get('status')})"
    )


def summary_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Unified OpenAPI Drift Summary",
        "",
        f"- PR required: {format_bool(report['pr_required'])}",
        f"- issue required: {format_bool(report['issue_required'])}",
        f"- tracked files changed: {len(report['tracked_paths'])}",
        f"- workflow checks failed: {format_bool(report['test_failed'])}",
        "",
        "## Changed Categories",
        "",
        *changed_categories_markdown(report["changed_categories"]),
        "",
        "## Test Outcomes",
        "",
    ]
    if report["test_outcomes"]:
        lines.extend(
            check_outcome_line(name, outcome)
            for name, outcome in sorted(report["test_outcomes"].items())
        )
    else:
        lines.append("- none recorded")

    lines.extend(
        [
            "",
            "## Fixture Reconciliation",
            "",
            f"- changed branches: {report['reconcile']['changed_count']}",
            f"- classification counts: `{json.dumps(report['reconcile']['classification_counts'], sort_keys=True)}`",
            "",
            "## Discovery",
            "",
            f"- missing endpoint fixtures: {report['discovery']['missing_endpoint_count']}",
            f"- discovered branch axes: {report['discovery']['axis_count']}",
            f"- discovered branch axis values: {report['discovery']['axis_value_count']}",
            f"- covered discovered axis values: {report['discovery']['covered_axis_value_count']}",
            f"- uncovered discovered axis values: {report['discovery']['uncovered_axis_value_count']}",
            f"- previously blocked now reachable: {report['discovery']['previously_blocked_now_reachable_count']}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def merge_recommendation(report: dict[str, Any]) -> tuple[str, list[str]]:
    reasons = []
    categories = report["changed_categories"]
    if report["test_failed"]:
        reasons.append("one or more drift workflow checks failed")
    if report["unresolved_hard_cases"]:
        reasons.append("the drift workflow reported cases that need human review")
    if categories["fixture_yaml"]:
        reasons.append("fixture files changed")
    if categories["fixture_status"]:
        reasons.append("the fixture coverage tracker changed")
    if report["reconcile"]["changed_count"]:
        reasons.append(
            f"{format_count('existing fixture branch', report['reconcile']['changed_count'])} changed"
        )
    reachable_count = report["discovery"]["previously_blocked_now_reachable_count"]
    if reachable_count:
        reasons.append(
        reasons.append(
            f"{format_count('previously blocked fixture branch', reachable_count)} now {'returns' if reachable_count == 1 else 'return'} a response"
        )
        )

    if reasons:
        return "Do not auto-merge yet.", reasons

    return (
        "Ready to merge after normal PR CI is green.",
        [
            "the changed files are limited to the OpenAPI description and its dated archive copy",
            "all existing fixture records replayed without requiring fixture updates",
            "the drift workflow checks passed",
        ],
    )


def pr_body_markdown(report: dict[str, Any]) -> str:
    recommendation, recommendation_reasons = merge_recommendation(report)
    lines = [
        "Automated refresh of ASTROX upstream drift data.",
        "",
        "This PR was opened by the scheduled OpenAPI drift workflow. It does not auto-merge.",
        "",
        "## Merge Recommendation",
        "",
        f"**{recommendation}**",
        "",
        "Reasons:",
        *[f"- {reason}" for reason in recommendation_reasons],
        "",
        "Because this PR is created by GitHub Actions, normal PR CI may not appear automatically. If no PR CI check is shown, run CI manually on this branch before merging.",
        "",
        "## What Changed",
        "",
        *changed_categories_markdown(report["changed_categories"]),
        "",
        "## Existing Fixture Results",
        "",
        f"- existing fixture branches changed: {report['reconcile']['changed_count']}",
        f"- fixture files changed: {len(report['reconcile']['changed_fixture_paths'])}",
        "",
        "Fixture replay outcomes:",
        *classification_counts_markdown(report["reconcile"]["classification_counts"]),
    ]

    changed_results = top_items(report["reconcile"]["changed_results"])
    if changed_results:
        lines.extend(["", "Changed existing branches:"])
        lines.extend(changed_branch_line(item) for item in changed_results)

    lines.extend(
        [
            "",
            "## Newly Seen Or Still Uncovered API Surface",
            "",
            "These items are discovery backlog, not merge blockers for this OpenAPI refresh unless they also changed existing fixture files.",
            "",
            f"- endpoints without fixture coverage: {report['discovery']['missing_endpoint_count']}",
            f"- uncovered request/response variants: {report['discovery']['uncovered_axis_value_count']}",
        ]
    )
    missing = top_items(report["discovery"]["missing_endpoints"])
    if missing:
        lines.extend(["", "Missing endpoint fixture examples:"])
        lines.extend(endpoint_line(item) for item in missing)

    uncovered = top_items(report["discovery"]["uncovered_axis_values"])
    if uncovered:
        lines.extend(["", "Uncovered branch value examples:"])
        lines.extend(axis_value_line(item) for item in uncovered)

    reachable = report["discovery"]["previously_blocked_now_reachable"]
    lines.extend(["", "## Previously Blocked Fixture Cases", ""])
    if reachable:
        lines.append("These need human fixture review before being promoted to verified coverage.")
        lines.append("")
        lines.extend(blocked_reachable_line(item) for item in reachable)
    else:
        lines.append("- none reported")

    lines.extend(
        [
            "",
            "## Drift Workflow Checks",
            "",
            "These ran inside the scheduled/manual drift workflow before this PR body was written. They are separate from later `pull_request` CI or manually dispatched CI on this branch.",
            "",
        ]
    )
    if report["test_outcomes"]:
        lines.extend(
            check_outcome_line(name, outcome)
            for name, outcome in sorted(report["test_outcomes"].items())
        )
    else:
        lines.append("- none recorded")

    hard_cases = report["unresolved_hard_cases"]
    lines.extend(["", "## Human Review Needed", ""])
    if hard_cases:
        for item in top_items(hard_cases):
            description = item.get("error") or item.get("classification")
            classification = human_classification(str(item.get("classification", "unknown")))
            lines.append(f"- {classification}: {description}")
    else:
        lines.append("- none reported")

    lines.extend(
        [
            "",
            "Full JSON and Markdown reports are attached as the `openapi-drift-reports` workflow artifact.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def issue_body_markdown(report: dict[str, Any]) -> str:
    lines = [
        "The unified OpenAPI drift workflow found saved blocked fixture branches that now return a usable response, with no tracked drift file changes to place in a PR.",
        "",
        "These branches were not automatically promoted to `verified`; they need human fixture review.",
        "",
        "## Branches",
        "",
    ]
    reachable = report["discovery"]["previously_blocked_now_reachable"]
    if reachable:
        lines.extend(blocked_reachable_line(item) for item in reachable)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- no new endpoint fixture was generated",
            "- no blocked branch was automatically unblocked",
            "- no drift PR was opened because no tracked files changed",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(path: Path | None, report: dict[str, Any]) -> None:
    if path is None:
        return
    lines = [
        f"pr_required={str(report['pr_required']).lower()}",
        f"issue_required={str(report['issue_required']).lower()}",
        f"issue_title={report['issue_title']}",
        f"pr_title={report['pr_title']}",
    ]
    with path.open("a", encoding="utf-8") as file:
        for line in lines:
            file.write(line + "\n")


def parse_test_outcomes(values: list[str]) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"test outcome must be NAME=VALUE, got {value!r}")
        name, outcome = value.split("=", 1)
        outcomes[name] = outcome
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconcile-json", type=Path)
    parser.add_argument("--discovery-json", type=Path)
    parser.add_argument("--tracked-status", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--pr-body-output", type=Path, required=True)
    parser.add_argument("--issue-body-output", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--test-outcome", action="append", default=[])
    args = parser.parse_args()

    report = build_pipeline_report(
        tracked_paths=parse_porcelain_status(args.tracked_status.read_text(encoding="utf-8")),
        reconcile_report=load_json(args.reconcile_json),
        discovery_report=load_json(args.discovery_json),
        test_outcomes=parse_test_outcomes(args.test_outcome),
    )
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary_output.write_text(summary_markdown(report), encoding="utf-8")
    args.pr_body_output.write_text(pr_body_markdown(report), encoding="utf-8")
    args.issue_body_output.write_text(issue_body_markdown(report), encoding="utf-8")
    write_outputs(args.github_output, report)
    print("OPENAPI_FIXTURE_DRIFT_PIPELINE_JSON=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
