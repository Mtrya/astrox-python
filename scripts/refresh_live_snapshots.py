#!/usr/bin/env python3
"""Refresh all maintained live snapshot sidecars."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, kw_only=True)
class SnapshotScript:
    label: str
    path: Path
    snapshot: Path


SNAPSHOT_SCRIPTS = [
    SnapshotScript(
        label="access",
        path=Path("tests/validation/live_snapshot/access/test_access.py"),
        snapshot=Path("tests/validation/live_snapshot/access/access.snap.json"),
    ),
    SnapshotScript(
        label="lighting",
        path=Path("tests/validation/live_snapshot/lighting/test_lighting.py"),
        snapshot=Path("tests/validation/live_snapshot/lighting/lighting.snap.json"),
    ),
    SnapshotScript(
        label="orbits/conversions",
        path=Path("tests/validation/live_snapshot/orbits/test_conversions.py"),
        snapshot=Path("tests/validation/live_snapshot/orbits/conversions.snap.json"),
    ),
    SnapshotScript(
        label="orbits/orbit_system",
        path=Path("tests/validation/live_snapshot/orbits/test_orbit_system.py"),
        snapshot=Path("tests/validation/live_snapshot/orbits/orbit_system.snap.json"),
    ),
    SnapshotScript(
        label="orbits/wizards",
        path=Path("tests/validation/live_snapshot/orbits/test_wizards.py"),
        snapshot=Path("tests/validation/live_snapshot/orbits/wizards.snap.json"),
    ),
    SnapshotScript(
        label="propagator/ballistic",
        path=Path("tests/validation/live_snapshot/propagator/test_ballistic.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/ballistic.snap.json"),
    ),
    SnapshotScript(
        label="propagator/hpop",
        path=Path("tests/validation/live_snapshot/propagator/test_hpop.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/hpop.snap.json"),
    ),
    SnapshotScript(
        label="propagator/j2",
        path=Path("tests/validation/live_snapshot/propagator/test_j2.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/j2.snap.json"),
    ),
    SnapshotScript(
        label="propagator/multi_j2",
        path=Path("tests/validation/live_snapshot/propagator/test_multi_j2.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/multi_j2.snap.json"),
    ),
    SnapshotScript(
        label="propagator/multi_sgp4",
        path=Path("tests/validation/live_snapshot/propagator/test_multi_sgp4.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/multi_sgp4.snap.json"),
    ),
    SnapshotScript(
        label="propagator/multi_two_body",
        path=Path("tests/validation/live_snapshot/propagator/test_multi_two_body.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/multi_two_body.snap.json"),
    ),
    SnapshotScript(
        label="propagator/sgp4",
        path=Path("tests/validation/live_snapshot/propagator/test_sgp4.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/sgp4.snap.json"),
    ),
    SnapshotScript(
        label="propagator/simple_ascent",
        path=Path("tests/validation/live_snapshot/propagator/test_simple_ascent.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/simple_ascent.snap.json"),
    ),
    SnapshotScript(
        label="propagator/two_body",
        path=Path("tests/validation/live_snapshot/propagator/test_two_body.py"),
        snapshot=Path("tests/validation/live_snapshot/propagator/two_body.snap.json"),
    ),
    SnapshotScript(
        label="rocket/landing_zone",
        path=Path("tests/validation/live_snapshot/rocket/test_landing_zone.py"),
        snapshot=Path("tests/validation/live_snapshot/rocket/landing_zone.snap.json"),
    ),
]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        help="ASTROX base URL. Defaults to ASTROX_BASE_URL from the environment.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed snapshot refresh.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List refreshable snapshot scripts and exit.",
    )
    args = parser.parse_args(argv)

    validate_manifest()
    if args.list:
        for script in SNAPSHOT_SCRIPTS:
            print(f"{script.label}\t{script.path}\t{script.snapshot}")
        return 0

    env = os.environ.copy()
    if args.base_url is not None:
        env["ASTROX_BASE_URL"] = args.base_url
    if not env.get("ASTROX_BASE_URL"):
        print(
            "LIVE_SNAPSHOT_FAILED=LiveConfigError: ASTROX_BASE_URL is required "
            "or pass --base-url",
            file=sys.stderr,
        )
        return 2

    failures: list[tuple[SnapshotScript, int]] = []
    for index, script in enumerate(SNAPSHOT_SCRIPTS, start=1):
        print(f"LIVE_SNAPSHOT_REFRESH_START={index}/{len(SNAPSHOT_SCRIPTS)} {script.label}", flush=True)
        result = subprocess.run(
            [sys.executable, str(script.path), "--refresh"],
            cwd=REPO_ROOT,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            failures.append((script, result.returncode))
            print(
                f"LIVE_SNAPSHOT_REFRESH_FAILED={script.label} exit={result.returncode}",
                file=sys.stderr,
                flush=True,
            )
            if args.fail_fast:
                break

    if failures:
        print(f"LIVE_SNAPSHOT_REFRESH_FAILED_COUNT={len(failures)}", file=sys.stderr)
        for script, returncode in failures:
            print(f"- {script.label}: {script.path} exit={returncode}", file=sys.stderr)
        return 1

    print(f"LIVE_SNAPSHOT_REFRESHED_FILES={len(SNAPSHOT_SCRIPTS)}")
    print("LIVE_SNAPSHOT_FAILED=0")
    return 0


def validate_manifest() -> None:
    missing = [
        str(path)
        for script in SNAPSHOT_SCRIPTS
        for path in (script.path, script.snapshot)
        if not (REPO_ROOT / path).exists()
    ]
    if missing:
        raise SystemExit("Snapshot refresh manifest references missing paths:\n" + "\n".join(missing))


if __name__ == "__main__":
    raise SystemExit(main())
