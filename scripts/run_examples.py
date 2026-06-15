#!/usr/bin/env python3
"""Run every discoverable example script and report pass/fail/skip/timeout.

Discovers ``examples/**/*.py``, consults ``examples/manifest.toml`` for
explicit skips, then runs each non-skipped file as a subprocess with a
per-file timeout.  Prints a summary table and exits non-zero when any
example fails unexpectedly.

Usage::

    uv run python scripts/run_examples.py [--timeout SECONDS] [--examples-dir DIR]
"""

from __future__ import annotations

import argparse
import os
import py_compile
import subprocess
import sys
import time
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        import tomllib  # type: ignore[no-redef, unused-ignore]

EXAMPLES_DIR_DEFAULT = Path(__file__).resolve().parent.parent / "examples"
MANIFEST_NAME = "manifest.toml"
DEFAULT_TIMEOUT = 120


def discover_examples(examples_dir: Path) -> list[Path]:
    found = sorted(examples_dir.rglob("*.py"))
    return [p for p in found if p.name != "__init__.py"]


def load_manifest(examples_dir: Path) -> dict[str, dict]:
    manifest_path = examples_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        return {}
    with manifest_path.open("rb") as f:
        data = tomllib.load(f)
    manifest: dict[str, dict] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            manifest[k] = v
        else:
            print(f"manifest: ignoring non-table top-level key: {k!r}", file=sys.stderr)
    return manifest


def relative_path(example: Path, examples_dir: Path) -> str:
    return example.relative_to(examples_dir).as_posix()


def run_example(
    example: Path,
    *,
    timeout: float,
) -> tuple[str, str]:
    result = subprocess.run(
        [sys.executable, str(example)],
        timeout=timeout,
        capture_output=True,
        text=True,
        env={**os.environ, "MPLBACKEND": "Agg"},
    )
    if result.returncode == 0:
        return "pass", ""
    return "fail", (result.stderr or result.stdout).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="per-example subprocess timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--examples-dir",
        type=Path,
        default=EXAMPLES_DIR_DEFAULT,
        help="root directory containing example scripts (default: %(default)s)",
    )
    args = parser.parse_args()

    examples_dir = args.examples_dir.resolve()
    if not examples_dir.is_dir():
        print(f"examples directory not found: {examples_dir}", file=sys.stderr)
        return 2

    examples = discover_examples(examples_dir)
    if not examples:
        print("no example files found", file=sys.stderr)
        return 2

    manifest = load_manifest(examples_dir)

    results: list[tuple[str, str, str, float]] = []
    unexpected_failures = 0

    for example in examples:
        rel = relative_path(example, examples_dir)
        try:
            example.resolve().relative_to(examples_dir)
        except ValueError:
            print(f"security: example resolves outside examples dir: {example}", file=sys.stderr)
            return 2

        entry = manifest.get(rel)
        if entry and entry.get("skip"):
            reason = entry.get("reason", "")
            if not reason.strip():
                print(f"manifest: {rel!r} marked skip but missing a non-empty reason", file=sys.stderr)
                return 2
            try:
                py_compile.compile(str(example), doraise=True)
            except py_compile.PyCompileError as exc:
                print(f"  FAIL  {rel}  (skipped example fails syntax check: {exc})")
                results.append((rel, "fail", str(exc), 0.0))
                unexpected_failures += 1
                continue
            print(f"  SKIP  {rel}  ({reason})")
            results.append((rel, "skip", reason, 0.0))
            continue

        t0 = time.monotonic()
        status, detail = "", ""
        try:
            status, detail = run_example(example, timeout=args.timeout)
        except subprocess.TimeoutExpired as exc:
            status = "timeout"
            output = (exc.stderr or exc.stdout or b"").strip()
            detail = f"exceeded {args.timeout}s"
            if output:
                detail += "; last output:"
                for line in output.decode("utf-8", errors="replace").splitlines()[-10:]:
                    detail += f"\n        {line}"
        elapsed = time.monotonic() - t0

        if status == "pass":
            print(f"  PASS  {rel}  ({elapsed:.1f}s)")
        elif status == "fail":
            print(f"  FAIL  {rel}  ({elapsed:.1f}s)")
            if detail:
                for line in detail.splitlines()[:20]:
                    print(f"        {line}")
            unexpected_failures += 1
        elif status == "timeout":
            print(f"  TIMEOUT  {rel}  ({elapsed:.1f}s)")
            unexpected_failures += 1

        results.append((rel, status, detail, elapsed))

    print()
    print(f"{'example':<55} {'status':<10} {'time':>6}")
    print("-" * 73)
    for rel, status, detail, elapsed in results:
        print(f"{rel:<55} {status:<10} {elapsed:5.1f}s")

    passed = sum(1 for _, s, _, _ in results if s == "pass")
    skipped = sum(1 for _, s, _, _ in results if s == "skip")
    failed = sum(1 for _, s, _, _ in results if s == "fail")
    timed_out = sum(1 for _, s, _, _ in results if s == "timeout")
    total = len(results)

    print()
    print(f"total {total}  passed {passed}  skipped {skipped}  failed {failed}  timed out {timed_out}")

    return 1 if unexpected_failures > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
