#!/usr/bin/env python3
"""Build reports for the simplified OpenAPI drift refresh workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PR_TITLE = "Refresh ASTROX upstream drift data"
EXPECTED_DRIFT_PATHS = {
    "openapi/astrox.openapi.yaml",
    "openapi/fixtures/STATUS.md",
}
EXPECTED_DRIFT_PREFIXES = ("openapi/archive/",)


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


def load_openapi_version(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} did not load as an object")
    info = loaded.get("info")
    if not isinstance(info, dict):
        return None
    version = info.get("version")
    return version if isinstance(version, str) else None


def parse_porcelain_status(text: str) -> list[str]:
    paths = []
    for line in text.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:].strip())
    return paths


def expected_drift_path(path: str) -> bool:
    return path in EXPECTED_DRIFT_PATHS or any(
        path.startswith(prefix) for prefix in EXPECTED_DRIFT_PREFIXES
    )


def changed_categories(paths: list[str]) -> dict[str, bool]:
    return {
        "openapi_baseline": "openapi/astrox.openapi.yaml" in paths,
        "openapi_archive": any(path.startswith("openapi/archive/") for path in paths),
        "fixture_status": "openapi/fixtures/STATUS.md" in paths,
    }


def build_pipeline_report(
    *,
    tracked_paths: list[str],
    previous_openapi_version: str | None,
    current_openapi_version: str | None,
) -> dict[str, Any]:
    unexpected_paths = [path for path in tracked_paths if not expected_drift_path(path)]
    refresh_valid = not unexpected_paths
    pr_required = bool(tracked_paths) and refresh_valid
    return {
        "pr_title": PR_TITLE,
        "pr_required": pr_required,
        "refresh_valid": refresh_valid,
        "tracked_diff_expected": bool(tracked_paths),
        "tracked_paths": tracked_paths,
        "unexpected_paths": unexpected_paths,
        "changed_categories": changed_categories(tracked_paths),
        "openapi": {
            "previous_version": previous_openapi_version,
            "current_version": current_openapi_version,
            "version_changed": previous_openapi_version != current_openapi_version,
        },
    }


def format_bool(value: bool) -> str:
    return "yes" if value else "no"


def format_version(value: str | None) -> str:
    return value if value is not None else "unknown"


def changed_categories_markdown(categories: dict[str, bool]) -> list[str]:
    labels = {
        "openapi_baseline": "OpenAPI description",
        "openapi_archive": "dated OpenAPI archive copy",
        "fixture_status": "fixture coverage tracker",
    }
    return [f"- {label}: {format_bool(categories[key])}" for key, label in labels.items()]


def tracked_paths_markdown(paths: list[str]) -> list[str]:
    if not paths:
        return ["- none"]
    return [f"- `{path}`" for path in paths]


def summary_markdown(report: dict[str, Any]) -> str:
    openapi = report["openapi"]
    lines = [
        "# OpenAPI Drift Summary",
        "",
        f"- PR required: {format_bool(report['pr_required'])}",
        f"- refresh valid: {format_bool(report['refresh_valid'])}",
        f"- tracked files changed: {len(report['tracked_paths'])}",
        f"- OpenAPI version: `{format_version(openapi['previous_version'])}` -> `{format_version(openapi['current_version'])}`",
        "",
        "## Changed Categories",
        "",
        *changed_categories_markdown(report["changed_categories"]),
        "",
        "## Changed Files",
        "",
        *tracked_paths_markdown(report["tracked_paths"]),
    ]
    if report["unexpected_paths"]:
        lines.extend(["", "## Unexpected Files", "", *tracked_paths_markdown(report["unexpected_paths"])])
    return "\n".join(lines).rstrip() + "\n"


def pr_body_markdown(report: dict[str, Any]) -> str:
    openapi = report["openapi"]
    lines = [
        "Automated refresh of ASTROX upstream OpenAPI data.",
        "",
        "This PR was opened by the scheduled OpenAPI drift workflow. Native GitHub auto-merge is enabled by the workflow; repository required checks are the merge gate.",
        "",
        "## OpenAPI",
        "",
        f"- previous version: `{format_version(openapi['previous_version'])}`",
        f"- current version: `{format_version(openapi['current_version'])}`",
        "",
        "## What Changed",
        "",
        *changed_categories_markdown(report["changed_categories"]),
        "",
        "Changed files:",
        *tracked_paths_markdown(report["tracked_paths"]),
    ]
    if report["changed_categories"]["fixture_status"]:
        lines.extend(
            [
                "",
                "`openapi/fixtures/STATUS.md` is regenerated while the fixture inventory remains in the repository. It is transitional reference state, not a drift gate.",
            ]
        )
    lines.extend(
        [
            "",
            "Full JSON and Markdown reports are attached as the `openapi-drift-reports` workflow artifact.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(path: Path | None, report: dict[str, Any]) -> None:
    if path is None:
        return
    lines = [
        f"pr_required={str(report['pr_required']).lower()}",
        f"refresh_valid={str(report['refresh_valid']).lower()}",
        f"pr_title={report['pr_title']}",
    ]
    with path.open("a", encoding="utf-8") as file:
        for line in lines:
            file.write(line + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-openapi", type=Path, required=True)
    parser.add_argument("--current-openapi", type=Path, required=True)
    parser.add_argument("--tracked-status", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--pr-body-output", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    report = build_pipeline_report(
        tracked_paths=parse_porcelain_status(args.tracked_status.read_text(encoding="utf-8")),
        previous_openapi_version=load_openapi_version(args.previous_openapi),
        current_openapi_version=load_openapi_version(args.current_openapi),
    )
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary_output.write_text(summary_markdown(report), encoding="utf-8")
    args.pr_body_output.write_text(pr_body_markdown(report), encoding="utf-8")
    write_outputs(args.github_output, report)
    print("OPENAPI_DRIFT_PIPELINE_JSON=" + json.dumps(report, sort_keys=True))
    return 0 if report["refresh_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
