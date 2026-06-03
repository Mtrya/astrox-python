#!/usr/bin/env python3
"""Check live ASTROX SDK returns against checked-in contract snapshots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.sdk_contract.core import (
    DEFAULT_FIXTURE_ROOT,
    ContractError,
    check_fixture,
    configure_astrox_from_env,
    iter_fixture_paths,
    load_fixture,
    validate_fixture,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURE_ROOT)
    parser.add_argument("--glob", dest="glob_pattern", help="Only check matching fixture paths under the fixture root")
    args = parser.parse_args()

    configure_astrox_from_env()
    paths = iter_fixture_paths(args.fixture_root, glob_pattern=args.glob_pattern)
    failures: list[str] = []
    for path in paths:
        fixture = load_fixture(path)
        validate_fixture(fixture, path=path, require_expected=True)
        failures.extend(check_fixture(fixture))

    for failure in failures:
        print(failure, file=sys.stderr)

    print(f"SDK_CONTRACT_CHECKED={len(paths)}")
    print(f"SDK_CONTRACT_FAILED={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"SDK_CONTRACT_CHECK_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
