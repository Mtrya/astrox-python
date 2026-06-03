"""Support mechanics for runnable live SDK contract scripts."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Sequence


@dataclass(frozen=True, kw_only=True)
class ContractCase:
    """One public-SDK-input validation case."""

    id: str
    run: Callable[[], Any]
    description: str | None = None


@dataclass(frozen=True, kw_only=True)
class _Mismatch:
    path: str
    category: str
    expected: Any
    actual: Any
    max_numeric_error: float | None = None

    def format(self) -> str:
        parts = [
            f"path={self.path}",
            f"category={self.category}",
            f"expected={_short_json(self.expected)}",
            f"actual={_short_json(self.actual)}",
        ]
        if self.max_numeric_error is not None:
            parts.append(f"max_numeric_error={self.max_numeric_error:.12g}")
        return "snapshot mismatch: " + "; ".join(parts)


class SnapshotError(Exception):
    """Base error for validation snapshot failures."""


class SnapshotMismatch(SnapshotError):
    """Raised when a live SDK return does not match the sidecar snapshot."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class LiveConfigError(SnapshotError):
    """Raised when required live ASTROX configuration is missing or invalid."""


def configure_astrox_from_env(env: dict[str, str] | None = None) -> None:
    env = os.environ if env is None else env
    base_url = env.get("ASTROX_BASE_URL")
    if not base_url:
        raise LiveConfigError("ASTROX_BASE_URL is required for live validation scripts")

    import astrox

    astrox.configure(
        base_url=base_url,
        timeout=_float_env(env, "ASTROX_TIMEOUT", 30.0),
        max_retries=_int_env(env, "ASTROX_MAX_RETRIES", 3),
        retry_delay=_float_env(env, "ASTROX_RETRY_DELAY", 1.0),
    )


def to_json_compatible(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return to_json_compatible(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): to_json_compatible(item)
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0]))
        }
    if isinstance(value, (list, tuple)):
        return [to_json_compatible(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    raise TypeError(f"value of type {type(value).__name__} is not JSON-compatible")


def normalize_for_snapshot(value: Any) -> Any:
    return _normalize_arrays(to_json_compatible(value))


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def read_snapshot(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        snapshot = json.load(stream)
    if not isinstance(snapshot, dict):
        raise SnapshotError(f"{path}: snapshot must be a JSON object")
    cases = snapshot.get("cases")
    if not isinstance(cases, list):
        raise SnapshotError(f"{path}: snapshot.cases must be a list")
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise SnapshotError(f"{path}: cases[{index}] must be an object")
        if not isinstance(case.get("id"), str) or not case["id"]:
            raise SnapshotError(f"{path}: cases[{index}].id must be a non-empty string")
        if "return" not in case:
            raise SnapshotError(f"{path}: cases[{index}].return is required")
    return snapshot


def write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(snapshot) + "\n", encoding="utf-8")


def refresh_snapshot(
    *,
    cases: Sequence[ContractCase],
    snapshot_path: Path,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = os.environ if env is None else env
    snapshot = {
        "metadata": {
            "refreshed_at": _utc_timestamp(),
            "astrox_base_url": env.get("ASTROX_BASE_URL", ""),
        },
        "cases": _run_cases(cases),
    }
    write_snapshot(snapshot_path, snapshot)
    return snapshot


def check_snapshot(
    *,
    cases: Sequence[ContractCase],
    snapshot_path: Path,
    abs_tol: float = 0.0,
    rel_tol: float = 0.0,
) -> None:
    expected = read_snapshot(snapshot_path)
    actual_cases = _run_cases(cases)
    _check_case_ids(expected_cases=expected["cases"], actual_cases=actual_cases)

    expected_by_id = {case["id"]: case for case in expected["cases"]}
    failures: list[str] = []
    for actual in actual_cases:
        case_id = actual["id"]
        mismatch = compare_values(
            expected_by_id[case_id]["return"],
            actual["return"],
            abs_tol=abs_tol,
            rel_tol=rel_tol,
        )
        if mismatch is not None:
            failures.append(f"case={case_id}; {mismatch.format()}")
    if failures:
        raise SnapshotMismatch("\n".join(failures))


def compare_values(
    expected: Any,
    actual: Any,
    *,
    abs_tol: float = 0.0,
    rel_tol: float = 0.0,
) -> _Mismatch | None:
    if abs_tol == 0.0 and rel_tol == 0.0:
        if canonical_bytes(expected) == canonical_bytes(actual):
            return None
        return _first_structural_mismatch(expected, actual)
    return _compare_at(expected, actual, path="$", abs_tol=abs_tol, rel_tol=rel_tol)


def main(
    *,
    cases: Sequence[ContractCase],
    snapshot_path: Path,
    argv: Sequence[str] | None = None,
    configure_live: bool = True,
    env: dict[str, str] | None = None,
    abs_tol: float = 0.0,
    rel_tol: float = 0.0,
) -> int:
    parser = argparse.ArgumentParser(description="Check or refresh a live SDK contract snapshot.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="Compare live SDK returns with the sidecar snapshot.")
    action.add_argument("--refresh", action="store_true", help="Rewrite the sidecar snapshot from live SDK returns.")
    args = parser.parse_args(argv)

    try:
        if configure_live:
            configure_astrox_from_env(env)
        if args.refresh:
            snapshot = refresh_snapshot(cases=cases, snapshot_path=snapshot_path, env=env)
            print(f"SDK_CONTRACT_REFRESHED={len(snapshot['cases'])}")
        else:
            check_snapshot(
                cases=cases,
                snapshot_path=snapshot_path,
                abs_tol=abs_tol,
                rel_tol=rel_tol,
            )
            print(f"SDK_CONTRACT_CHECKED={len(cases)}")
    except SnapshotError as exc:
        print(f"SDK_CONTRACT_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


def _run_cases(cases: Sequence[ContractCase]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for case in cases:
        if case.id in seen:
            raise SnapshotError(f"duplicate case id {case.id!r}")
        seen.add(case.id)
        result = {
            "id": case.id,
            "return": normalize_for_snapshot(case.run()),
        }
        if case.description is not None:
            result["description"] = case.description
        results.append(result)
    return results


def _check_case_ids(
    *,
    expected_cases: list[dict[str, Any]],
    actual_cases: list[dict[str, Any]],
) -> None:
    expected_ids = [case["id"] for case in expected_cases]
    actual_ids = [case["id"] for case in actual_cases]
    if expected_ids != actual_ids:
        raise SnapshotMismatch(
            "case id mismatch: "
            f"expected={json.dumps(expected_ids, ensure_ascii=False)}; "
            f"actual={json.dumps(actual_ids, ensure_ascii=False)}"
        )


def _compare_at(
    expected: Any,
    actual: Any,
    *,
    path: str,
    abs_tol: float,
    rel_tol: float,
) -> _Mismatch | None:
    if isinstance(expected, bool) or isinstance(actual, bool):
        if expected == actual:
            return None
        return _Mismatch(path=path, category="value", expected=expected, actual=actual)
    if isinstance(expected, int | float) and isinstance(actual, int | float):
        if math.isclose(actual, expected, abs_tol=abs_tol, rel_tol=rel_tol):
            return None
        return _Mismatch(
            path=path,
            category="numeric",
            expected=expected,
            actual=actual,
            max_numeric_error=abs(float(actual) - float(expected)),
        )
    if type(expected) is not type(actual):
        return _Mismatch(
            path=path,
            category="type",
            expected=type(expected).__name__,
            actual=type(actual).__name__,
        )
    if isinstance(expected, dict):
        if set(expected) != set(actual):
            return _Mismatch(
                path=path,
                category="keys",
                expected=sorted(expected),
                actual=sorted(actual),
            )
        for key in sorted(expected):
            mismatch = _compare_at(
                expected[key],
                actual[key],
                path=f"{path}.{key}",
                abs_tol=abs_tol,
                rel_tol=rel_tol,
            )
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return _Mismatch(
                path=path,
                category="length",
                expected=len(expected),
                actual=len(actual),
            )
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            mismatch = _compare_at(
                expected_item,
                actual_item,
                path=f"{path}[{index}]",
                abs_tol=abs_tol,
                rel_tol=rel_tol,
            )
            if mismatch is not None:
                return mismatch
        return None
    if expected != actual:
        return _Mismatch(path=path, category="value", expected=expected, actual=actual)
    return None


def _first_structural_mismatch(expected: Any, actual: Any, path: str = "$") -> _Mismatch:
    if type(expected) is not type(actual):
        return _Mismatch(
            path=path,
            category="type",
            expected=type(expected).__name__,
            actual=type(actual).__name__,
        )
    if isinstance(expected, dict):
        if set(expected) != set(actual):
            return _Mismatch(
                path=path,
                category="keys",
                expected=sorted(expected),
                actual=sorted(actual),
            )
        for key in sorted(expected):
            if canonical_bytes(expected[key]) != canonical_bytes(actual[key]):
                return _first_structural_mismatch(expected[key], actual[key], f"{path}.{key}")
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return _Mismatch(
                path=path,
                category="length",
                expected=len(expected),
                actual=len(actual),
            )
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            if canonical_bytes(expected_item) != canonical_bytes(actual_item):
                return _first_structural_mismatch(expected_item, actual_item, f"{path}[{index}]")
    if isinstance(expected, int | float) and isinstance(actual, int | float):
        return _Mismatch(
            path=path,
            category="value",
            expected=expected,
            actual=actual,
            max_numeric_error=abs(float(actual) - float(expected)),
        )
    return _Mismatch(path=path, category="value", expected=expected, actual=actual)


def _normalize_arrays(value: Any) -> Any:
    if isinstance(value, list):
        normalized = [_normalize_arrays(item) for item in value]
        if len(normalized) <= 20:
            return normalized
        return {
            "length": len(normalized),
            "first": normalized[:10],
            "last": normalized[-10:],
        }
    if isinstance(value, dict):
        return {key: _normalize_arrays(item) for key, item in value.items()}
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )


def _short_json(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    if len(text) <= 240:
        return text
    return text[:237] + "..."


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _float_env(env: dict[str, str], key: str, default: float) -> float:
    value = env.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise LiveConfigError(f"{key} must be a float") from exc


def _int_env(env: dict[str, str], key: str, default: int) -> int:
    value = env.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise LiveConfigError(f"{key} must be an integer") from exc
