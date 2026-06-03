"""Shared helpers for live ASTROX SDK contract snapshots."""

from __future__ import annotations

import fnmatch
import importlib
import json
import math
import os
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import yaml


DEFAULT_FIXTURE_ROOT = Path("tests/fixtures/astrox_sdk_contract")
SUPPORTED_COMPARE_MODES = {"exact_json", "approximate_json"}
CONSTRUCTOR_WHITELIST = {"astrox.orbits.keplerian"}


class ContractError(Exception):
    """Base error for SDK contract harness failures."""


class FixtureError(ContractError):
    """Raised when a fixture is malformed."""


class ComparisonError(ContractError):
    """Raised when a live SDK return does not match a fixture snapshot."""

    def __init__(self, mismatch: "Mismatch") -> None:
        self.mismatch = mismatch
        super().__init__(mismatch.format())


class LiveConfigError(ContractError):
    """Raised when required live ASTROX configuration is missing or invalid."""


class Mismatch:
    """Concise mismatch summary."""

    def __init__(
        self,
        *,
        path: str,
        category: str,
        expected: Any,
        actual: Any,
        max_numeric_error: float | None = None,
    ) -> None:
        self.path = path
        self.category = category
        self.expected = expected
        self.actual = actual
        self.max_numeric_error = max_numeric_error

    def format(self, *, case_id: str | None = None, function: str | None = None) -> str:
        parts = []
        if case_id is not None:
            parts.append(f"case={case_id}")
        if function is not None:
            parts.append(f"function={function}")
        parts.append(f"path={self.path}")
        parts.append(f"category={self.category}")
        parts.append(f"expected={_short_repr(self.expected)}")
        parts.append(f"actual={_short_repr(self.actual)}")
        if self.max_numeric_error is not None:
            parts.append(f"max_numeric_error={self.max_numeric_error:.12g}")
        return "SDK contract mismatch: " + "; ".join(parts)


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iter_fixture_paths(
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    *,
    glob_pattern: str | None = None,
) -> list[Path]:
    if not fixture_root.exists():
        return []
    paths = sorted(
        path
        for path in fixture_root.rglob("*")
        if path.is_file() and path.suffix in {".yaml", ".yml"}
    )
    if glob_pattern is None:
        return paths
    return [
        path
        for path in paths
        if fnmatch.fnmatch(path.relative_to(fixture_root).as_posix(), glob_pattern)
    ]


def load_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise FixtureError(f"{path}: fixture must be a mapping")
    return data


def dump_fixture(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(
            order_fixture(data),
            stream,
            allow_unicode=True,
            sort_keys=False,
            width=10_000,
        )


def order_fixture(data: dict[str, Any]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in ("area", "function", "scenario", "compare", "cases", "notes"):
        if key in data:
            ordered[key] = data[key]
    for key in data:
        if key not in ordered:
            ordered[key] = data[key]
    return ordered


def validate_fixture(
    data: dict[str, Any],
    *,
    path: Path | None = None,
    require_expected: bool,
) -> None:
    label = str(path) if path is not None else "fixture"
    _require_str(data, "area", label)
    function_path = _require_str(data, "function", label)
    if not function_path.startswith("astrox."):
        raise FixtureError(f"{label}: function must be an astrox.* import path")
    _require_str(data, "scenario", label)

    compare = data.get("compare")
    if not isinstance(compare, dict):
        raise FixtureError(f"{label}: compare must be a mapping")
    mode = compare.get("mode")
    if mode not in SUPPORTED_COMPARE_MODES:
        modes = ", ".join(sorted(SUPPORTED_COMPARE_MODES))
        raise FixtureError(f"{label}: compare.mode must be one of {modes}")
    for key in ("abs_tol", "rel_tol"):
        if key in compare and not isinstance(compare[key], int | float):
            raise FixtureError(f"{label}: compare.{key} must be numeric")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise FixtureError(f"{label}: cases must be a non-empty list")
    seen_case_ids: set[str] = set()
    for index, case in enumerate(cases):
        case_label = f"{label}: cases[{index}]"
        if not isinstance(case, dict):
            raise FixtureError(f"{case_label} must be a mapping")
        case_id = _require_str(case, "id", case_label)
        if case_id in seen_case_ids:
            raise FixtureError(f"{case_label}: duplicate case id {case_id!r}")
        seen_case_ids.add(case_id)
        inputs = case.get("inputs")
        if not isinstance(inputs, dict):
            raise FixtureError(f"{case_label}: inputs must be a mapping")
        _validate_constructor_markers(inputs, case_label)
        if require_expected:
            expected = case.get("expected")
            if not isinstance(expected, dict) or "return" not in expected:
                raise FixtureError(f"{case_label}: expected.return is required")


def lint_fixture_tree(
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    *,
    glob_pattern: str | None = None,
    require_expected: bool = True,
) -> list[Path]:
    paths = iter_fixture_paths(fixture_root, glob_pattern=glob_pattern)
    for path in paths:
        validate_fixture(load_fixture(path), path=path, require_expected=require_expected)
    return paths


def configure_astrox_from_env(env: dict[str, str] | None = None) -> None:
    env = os.environ if env is None else env
    base_url = env.get("ASTROX_BASE_URL")
    if not base_url:
        raise LiveConfigError("ASTROX_BASE_URL is required for live SDK contract checks")

    import astrox

    astrox.configure(
        base_url=base_url,
        timeout=_float_env(env, "ASTROX_TIMEOUT", 30.0),
        max_retries=_int_env(env, "ASTROX_MAX_RETRIES", 3),
        retry_delay=_float_env(env, "ASTROX_RETRY_DELAY", 1.0),
    )


def resolve_import_path(path: str) -> Callable[..., Any]:
    module_name, _, attr_name = path.rpartition(".")
    if not module_name or not attr_name:
        raise FixtureError(f"invalid import path {path!r}")
    module = importlib.import_module(module_name)
    value = getattr(module, attr_name)
    if not callable(value):
        raise FixtureError(f"import path {path!r} is not callable")
    return value


def build_call_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    built: dict[str, Any] = {}
    for name, value in inputs.items():
        if _is_constructor_value(value):
            built[name] = build_constructor_value(value, f"inputs.{name}")
        else:
            if _contains_constructor_marker(value):
                raise FixtureError(
                    f"inputs.{name}: constructor values are only supported at one input level"
                )
            built[name] = value
    return built


def build_constructor_value(value: dict[str, Any], context: str) -> Any:
    constructor_path = value.get("constructor")
    if constructor_path not in CONSTRUCTOR_WHITELIST:
        allowed = ", ".join(sorted(CONSTRUCTOR_WHITELIST))
        raise FixtureError(f"{context}: constructor must be one of {allowed}")
    kwargs = value.get("kwargs")
    if not isinstance(kwargs, dict):
        raise FixtureError(f"{context}: constructor kwargs must be a mapping")
    if _contains_constructor_marker(kwargs):
        raise FixtureError(f"{context}: nested constructors are not supported")
    constructor = resolve_import_path(constructor_path)
    return constructor(**kwargs)


def execute_case(
    fixture: dict[str, Any],
    case: dict[str, Any],
    *,
    callable_resolver: Callable[[str], Callable[..., Any]] = resolve_import_path,
) -> Any:
    function_path = fixture["function"]
    function = callable_resolver(function_path)
    inputs = build_call_inputs(case["inputs"])
    return function(**inputs)


def snapshot_return(value: Any) -> Any:
    return normalize_arrays(to_json_compatible(value))


def to_json_compatible(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return to_json_compatible(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): to_json_compatible(val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [to_json_compatible(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    raise TypeError(f"value of type {type(value).__name__} is not JSON-compatible")


def normalize_arrays(value: Any) -> Any:
    if isinstance(value, list):
        normalized = [normalize_arrays(item) for item in value]
        if len(normalized) <= 20:
            return normalized
        return {
            "length": len(normalized),
            "first": normalized[:10],
            "last": normalized[-10:],
        }
    if isinstance(value, dict):
        return {key: normalize_arrays(val) for key, val in value.items()}
    return value


def compare_snapshot(
    *,
    expected: Any,
    actual: Any,
    compare: dict[str, Any],
    case_id: str | None = None,
    function: str | None = None,
) -> None:
    mode = compare["mode"]
    if mode == "exact_json":
        mismatch = _compare_exact(expected, actual)
    elif mode == "approximate_json":
        mismatch = _compare_approx(
            expected,
            actual,
            abs_tol=float(compare.get("abs_tol", 0.0)),
            rel_tol=float(compare.get("rel_tol", 0.0)),
        )
    else:
        raise FixtureError(f"unsupported compare mode {mode!r}")
    if mismatch is not None:
        if case_id is not None or function is not None:
            raise ComparisonError(
                Mismatch(
                    path=mismatch.path,
                    category=mismatch.category,
                    expected=mismatch.expected,
                    actual=mismatch.actual,
                    max_numeric_error=mismatch.max_numeric_error,
                )
            ) from None
        raise ComparisonError(mismatch)


def check_fixture(
    fixture: dict[str, Any],
    *,
    callable_resolver: Callable[[str], Callable[..., Any]] = resolve_import_path,
) -> list[str]:
    failures: list[str] = []
    for case in fixture["cases"]:
        try:
            actual = snapshot_return(
                execute_case(fixture, case, callable_resolver=callable_resolver)
            )
            compare_snapshot(
                expected=case["expected"]["return"],
                actual=actual,
                compare=fixture["compare"],
            )
        except Exception as exc:
            failures.append(_format_case_failure(fixture, case, exc))
    return failures


def refresh_fixture(
    fixture: dict[str, Any],
    *,
    callable_resolver: Callable[[str], Callable[..., Any]] = resolve_import_path,
) -> dict[str, Any]:
    refreshed = dict(fixture)
    refreshed_cases: list[dict[str, Any]] = []
    for case in fixture["cases"]:
        refreshed_case = dict(case)
        actual = snapshot_return(
            execute_case(fixture, case, callable_resolver=callable_resolver)
        )
        existing_expected = refreshed_case.get("expected")
        expected = dict(existing_expected) if isinstance(existing_expected, dict) else {}
        expected["refreshed_at"] = utc_timestamp()
        expected["return"] = actual
        refreshed_case["expected"] = expected
        refreshed_cases.append(refreshed_case)
    refreshed["cases"] = refreshed_cases
    return refreshed


def _compare_exact(expected: Any, actual: Any) -> Mismatch | None:
    if _canonical_bytes(expected) == _canonical_bytes(actual):
        return None
    return _first_structural_mismatch(expected, actual)


def _compare_approx(
    expected: Any,
    actual: Any,
    *,
    abs_tol: float,
    rel_tol: float,
) -> Mismatch | None:
    return _compare_approx_at(
        expected,
        actual,
        path="$",
        abs_tol=abs_tol,
        rel_tol=rel_tol,
    )


def _compare_approx_at(
    expected: Any,
    actual: Any,
    *,
    path: str,
    abs_tol: float,
    rel_tol: float,
) -> Mismatch | None:
    if isinstance(expected, bool) or isinstance(actual, bool):
        if expected == actual:
            return None
        return Mismatch(path=path, category="value", expected=expected, actual=actual)
    if isinstance(expected, int | float) and isinstance(actual, int | float):
        if math.isclose(actual, expected, abs_tol=abs_tol, rel_tol=rel_tol):
            return None
        return Mismatch(
            path=path,
            category="numeric",
            expected=expected,
            actual=actual,
            max_numeric_error=abs(float(actual) - float(expected)),
        )
    if type(expected) is not type(actual):
        return Mismatch(
            path=path,
            category="type",
            expected=type(expected).__name__,
            actual=type(actual).__name__,
        )
    if isinstance(expected, dict):
        if set(expected) != set(actual):
            return Mismatch(
                path=path,
                category="keys",
                expected=sorted(expected),
                actual=sorted(actual),
            )
        for key in sorted(expected):
            mismatch = _compare_approx_at(
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
            return Mismatch(
                path=path,
                category="length",
                expected=len(expected),
                actual=len(actual),
            )
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            mismatch = _compare_approx_at(
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
        return Mismatch(path=path, category="value", expected=expected, actual=actual)
    return None


def _first_structural_mismatch(expected: Any, actual: Any, path: str = "$") -> Mismatch:
    if type(expected) is not type(actual):
        return Mismatch(
            path=path,
            category="type",
            expected=type(expected).__name__,
            actual=type(actual).__name__,
        )
    if isinstance(expected, dict):
        if set(expected) != set(actual):
            return Mismatch(
                path=path,
                category="keys",
                expected=sorted(expected),
                actual=sorted(actual),
            )
        for key in sorted(expected):
            if _canonical_bytes(expected[key]) != _canonical_bytes(actual[key]):
                return _first_structural_mismatch(
                    expected[key],
                    actual[key],
                    f"{path}.{key}",
                )
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            return Mismatch(
                path=path,
                category="length",
                expected=len(expected),
                actual=len(actual),
            )
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            if _canonical_bytes(expected_item) != _canonical_bytes(actual_item):
                return _first_structural_mismatch(
                    expected_item,
                    actual_item,
                    f"{path}[{index}]",
                )
    return Mismatch(path=path, category="value", expected=expected, actual=actual)


def _format_case_failure(
    fixture: dict[str, Any],
    case: dict[str, Any],
    exc: Exception,
) -> str:
    case_id = str(case.get("id", "<unknown>"))
    function = str(fixture.get("function", "<unknown>"))
    if isinstance(exc, ComparisonError):
        return exc.mismatch.format(case_id=case_id, function=function)
    return f"SDK contract failure: case={case_id}; function={function}; error={type(exc).__name__}: {exc}"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _short_repr(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    if len(text) <= 240:
        return text
    return text[:237] + "..."


def _require_str(mapping: dict[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise FixtureError(f"{context}: {key} must be a non-empty string")
    return value


def _validate_constructor_markers(inputs: dict[str, Any], context: str) -> None:
    for name, value in inputs.items():
        if _is_constructor_value(value):
            constructor = value.get("constructor")
            if constructor not in CONSTRUCTOR_WHITELIST:
                allowed = ", ".join(sorted(CONSTRUCTOR_WHITELIST))
                raise FixtureError(f"{context}.inputs.{name}: constructor must be one of {allowed}")
            if not isinstance(value.get("kwargs"), dict):
                raise FixtureError(f"{context}.inputs.{name}: constructor kwargs must be a mapping")
            if _contains_constructor_marker(value["kwargs"]):
                raise FixtureError(f"{context}.inputs.{name}: nested constructors are not supported")
        elif _contains_constructor_marker(value):
            raise FixtureError(
                f"{context}.inputs.{name}: constructor values are only supported at one input level"
            )


def _is_constructor_value(value: Any) -> bool:
    return isinstance(value, dict) and set(value) >= {"constructor", "kwargs"}


def _contains_constructor_marker(value: Any) -> bool:
    if isinstance(value, dict):
        if "constructor" in value:
            return True
        return any(_contains_constructor_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_constructor_marker(item) for item in value)
    return False


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
