#!/usr/bin/env python3
"""Run every SDK contract validation script in check mode."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


DEFAULT_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True, kw_only=True)
class ScriptResult:
    path: Path
    returncode: int
    stdout: str
    stderr: str


def discover_scripts(root: Path = DEFAULT_ROOT) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if path.is_file()
        and path.name != "check_all.py"
        and not path.name.startswith("_")
        and not path.name.startswith("test_")
        and "__pycache__" not in path.parts
    )


def run_scripts(
    scripts: Sequence[Path],
    *,
    env: dict[str, str] | None = None,
) -> list[ScriptResult]:
    run_env = os.environ.copy()
    if env is not None:
        run_env.update(env)

    results: list[ScriptResult] = []
    for script in scripts:
        completed = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=Path.cwd(),
            env=run_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        results.append(
            ScriptResult(
                path=script,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        )
    return results


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)

    scripts = discover_scripts(args.root)
    results = run_scripts(scripts)
    failed = [result for result in results if result.returncode != 0]

    for result in results:
        print(f"SDK_CONTRACT_SCRIPT={result.path.relative_to(args.root)}")
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)

    print(f"SDK_CONTRACT_SCRIPTS_CHECKED={len(results)}")
    print(f"SDK_CONTRACT_SCRIPTS_FAILED={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
