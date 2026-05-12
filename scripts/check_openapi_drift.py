#!/usr/bin/env python3
"""Detect live OpenAPI and generated-model drift against checked-in baselines."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from fetch_openapi import fetch_openapi, stable_yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO_ROOT / "openapi" / "astrox.openapi.yaml"
DEFAULT_MODELS = REPO_ROOT / "astrox" / "_models.py"
DEFAULT_BASE_URL = "http://astrox.cn:8765"


def load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} did not load as an object")
    return loaded


def describe_spec_delta(baseline: dict[str, Any], live: dict[str, Any]) -> dict[str, Any]:
    baseline_paths = set(baseline["paths"])
    live_paths = set(live["paths"])
    baseline_schemas = set(baseline["components"]["schemas"])
    live_schemas = set(live["components"]["schemas"])
    return {
        "baseline_version": baseline["info"].get("version"),
        "live_version": live["info"].get("version"),
        "added_paths": sorted(live_paths - baseline_paths),
        "removed_paths": sorted(baseline_paths - live_paths),
        "added_schemas_count": len(live_schemas - baseline_schemas),
        "removed_schemas_count": len(baseline_schemas - live_schemas),
    }


def normalize_generated_model_text(text: str) -> str:
    lines = [
        line
        for line in text.splitlines()
        if not line.startswith("# Generated at:")
    ]
    return "\n".join(lines).rstrip() + "\n"


def generate_models_from_spec(spec_path: Path, output_path: Path, source: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "generate_models.py"),
            "--input",
            str(spec_path),
            "--output",
            str(output_path),
            "--source",
            source,
            "--deterministic-header",
        ],
        check=True,
        cwd=REPO_ROOT,
    )


def unified_diff(left: str, right: str, left_name: str, right_name: str) -> str:
    return "".join(
        difflib.unified_diff(
            left.splitlines(keepends=True),
            right.splitlines(keepends=True),
            fromfile=left_name,
            tofile=right_name,
            n=3,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("ASTROX_BASE_URL", DEFAULT_BASE_URL),
        help="ASTROX server base URL",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--models", type=Path, default=DEFAULT_MODELS)
    args = parser.parse_args()

    baseline_spec = load_yaml(args.baseline)
    live_spec = fetch_openapi(args.base_url, args.timeout)

    baseline_text = stable_yaml(baseline_spec)
    live_text = stable_yaml(live_spec)
    spec_drifted = baseline_text != live_text

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        live_spec_path = tmp / "astrox.live.openapi.yaml"
        generated_models_path = tmp / "_models.py"
        live_spec_path.write_text(live_text, encoding="utf-8")

        generate_models_from_spec(
            live_spec_path,
            generated_models_path,
            f"{args.base_url.rstrip('/')}/openapi/v1.json",
        )

        expected_models = normalize_generated_model_text(args.models.read_text(encoding="utf-8"))
        generated_models = normalize_generated_model_text(
            generated_models_path.read_text(encoding="utf-8")
        )
        model_drifted = expected_models != generated_models

        result = {
            "base_url": args.base_url,
            "spec_drifted": spec_drifted,
            "model_drifted": model_drifted,
            "spec_delta": describe_spec_delta(baseline_spec, live_spec),
        }
        print("OPENAPI_DRIFT_RESULT_JSON=" + json.dumps(result, sort_keys=True))

        if spec_drifted:
            print(
                unified_diff(
                    baseline_text,
                    live_text,
                    str(args.baseline),
                    str(live_spec_path),
                )[:20000],
                file=sys.stderr,
            )
        if model_drifted:
            print(
                unified_diff(
                    expected_models,
                    generated_models,
                    str(args.models),
                    str(generated_models_path),
                )[:20000],
                file=sys.stderr,
            )

    return 1 if spec_drifted or model_drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
