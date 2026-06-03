#!/usr/bin/env python3
"""Check optional SDK oracle fixtures against checked-in SDK contract snapshots."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.sdk_contract.core import DEFAULT_FIXTURE_ROOT as DEFAULT_CONTRACT_ROOT
from scripts.sdk_contract.core import FixtureError, load_fixture

DEFAULT_ORACLE_ROOT = Path("tests/fixtures/oracles")


@dataclass(frozen=True)
class OracleFailure:
    """Single oracle mismatch."""

    path: Path
    case_id: str
    message: str

    def format(self) -> str:
        return f"{self.path}: case={self.case_id}: {self.message}"


def iter_oracle_paths(oracle_root: Path = DEFAULT_ORACLE_ROOT) -> list[Path]:
    if not oracle_root.exists():
        return []
    return sorted(
        path
        for path in oracle_root.rglob("*")
        if path.is_file() and path.suffix in {".yaml", ".yml"}
    )


def load_oracle(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as exc:
        raise FixtureError(f"{path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FixtureError(f"{path}: oracle fixture must be a mapping")
    return data


def check_tree(
    *,
    oracle_root: Path = DEFAULT_ORACLE_ROOT,
    contract_root: Path = DEFAULT_CONTRACT_ROOT,
) -> tuple[int, list[OracleFailure]]:
    failures: list[OracleFailure] = []
    paths = iter_oracle_paths(oracle_root)
    for path in paths:
        failures.extend(
            check_oracle_fixture(
                path,
                contract_root=contract_root,
            )
        )
    return len(paths), failures


def check_oracle_fixture(
    path: Path,
    *,
    contract_root: Path = DEFAULT_CONTRACT_ROOT,
) -> list[OracleFailure]:
    fixture = load_oracle(path)
    _require_mapping(fixture, "source", path)
    _require_str(fixture, "scope", path)
    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        raise FixtureError(f"{path}: cases must be a non-empty list")

    failures: list[OracleFailure] = []
    for index, case in enumerate(cases):
        case_id = _require_str(case, "id", path, index=index)
        kind = _require_str(case, "kind", path, index=index)
        contract_ref = _require_mapping(case, "astrox_contract", path, index=index)
        contract_path = contract_root / _require_str(
            contract_ref,
            "path",
            path,
            index=index,
        )
        contract_case_id = _require_str(contract_ref, "case", path, index=index)
        expected_return = _load_contract_return(contract_path, contract_case_id)
        if kind == "sgp4_state_samples":
            failures.extend(_check_sgp4_case(path, case_id, case, expected_return))
        else:
            raise FixtureError(f"{path}: case={case_id}: unsupported oracle kind {kind!r}")
    return failures


def _check_sgp4_case(
    path: Path,
    case_id: str,
    case: dict[str, Any],
    expected_return: Any,
) -> list[OracleFailure]:
    if (
        not isinstance(expected_return, list)
        or len(expected_return) != 2
        or not isinstance(expected_return[1], dict)
    ):
        raise FixtureError(f"{path}: case={case_id}: ASTROX return must be [period_s, position]")

    tolerance = _require_mapping(case, "tolerance", path)
    period_abs_s = _require_number(tolerance, "period_abs_s", path)
    position_abs_m = _require_number(tolerance, "position_abs_m", path)
    velocity_abs_m_s = _require_number(tolerance, "velocity_abs_m_s", path)
    oracle = _require_mapping(case, "oracle", path)
    oracle_period_s = _require_number(oracle, "period_s", path)
    astrox_period_s = _require_number_from_value(expected_return[0], path, "period_s")

    failures: list[OracleFailure] = []
    period_error = abs(astrox_period_s - oracle_period_s)
    if period_error > period_abs_s:
        failures.append(
            OracleFailure(
                path=path,
                case_id=case_id,
                message=(
                    f"period_s error {period_error:.12g} exceeds tolerance "
                    f"{period_abs_s:.12g}"
                ),
            )
        )

    samples = _contract_samples(expected_return[1], path, case_id)
    oracle_samples = oracle.get("samples")
    if not isinstance(oracle_samples, list) or not oracle_samples:
        raise FixtureError(f"{path}: case={case_id}: oracle.samples must be a non-empty list")
    for sample in oracle_samples:
        if not isinstance(sample, dict):
            raise FixtureError(f"{path}: case={case_id}: oracle sample must be a mapping")
        offset_s = _require_number(sample, "offset_s", path)
        astrox_sample = samples.get(offset_s)
        if astrox_sample is None:
            failures.append(
                OracleFailure(
                    path=path,
                    case_id=case_id,
                    message=f"missing ASTROX sample at offset_s={offset_s:g}",
                )
            )
            continue

        oracle_position = _require_number_list(sample, "position_m", path, length=3)
        oracle_velocity = _require_number_list(sample, "velocity_m_s", path, length=3)
        position_error = max(abs(a - b) for a, b in zip(astrox_sample[:3], oracle_position))
        velocity_error = max(abs(a - b) for a, b in zip(astrox_sample[3:], oracle_velocity))
        if position_error > position_abs_m:
            failures.append(
                OracleFailure(
                    path=path,
                    case_id=case_id,
                    message=(
                        f"position error at offset_s={offset_s:g} is "
                        f"{position_error:.12g}, tolerance {position_abs_m:.12g}"
                    ),
                )
            )
        if velocity_error > velocity_abs_m_s:
            failures.append(
                OracleFailure(
                    path=path,
                    case_id=case_id,
                    message=(
                        f"velocity error at offset_s={offset_s:g} is "
                        f"{velocity_error:.12g}, tolerance {velocity_abs_m_s:.12g}"
                    ),
                )
            )
    return failures


def _contract_samples(
    position: dict[str, Any],
    path: Path,
    case_id: str,
) -> dict[float, tuple[float, float, float, float, float, float]]:
    cartesian_velocity = position.get("cartesian_velocity")
    if not isinstance(cartesian_velocity, list) or len(cartesian_velocity) % 7 != 0:
        raise FixtureError(
            f"{path}: case={case_id}: ASTROX cartesian_velocity must be a flat 7-value sample list"
        )
    samples: dict[float, tuple[float, float, float, float, float, float]] = {}
    for index in range(0, len(cartesian_velocity), 7):
        chunk = cartesian_velocity[index : index + 7]
        if not all(isinstance(value, int | float) for value in chunk):
            raise FixtureError(f"{path}: case={case_id}: cartesian_velocity values must be numeric")
        samples[float(chunk[0])] = tuple(float(value) for value in chunk[1:7])
    return samples


def _load_contract_return(contract_path: Path, case_id: str) -> Any:
    try:
        contract = load_fixture(contract_path)
    except (OSError, yaml.YAMLError) as exc:
        raise FixtureError(f"{contract_path}: {exc}") from exc
    cases = contract.get("cases")
    if not isinstance(cases, list):
        raise FixtureError(f"{contract_path}: cases must be a list")
    for case in cases:
        if isinstance(case, dict) and case.get("id") == case_id:
            expected = case.get("expected")
            if not isinstance(expected, dict) or "return" not in expected:
                raise FixtureError(f"{contract_path}: case={case_id}: expected.return is required")
            return expected["return"]
    raise FixtureError(f"{contract_path}: case={case_id}: not found")


def _require_mapping(
    data: dict[str, Any],
    key: str,
    path: Path,
    *,
    index: int | None = None,
) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        label = _label(path, index)
        raise FixtureError(f"{label}: {key} must be a mapping")
    return value


def _require_str(
    data: dict[str, Any],
    key: str,
    path: Path,
    *,
    index: int | None = None,
) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        label = _label(path, index)
        raise FixtureError(f"{label}: {key} must be a non-empty string")
    return value


def _require_number(data: dict[str, Any], key: str, path: Path) -> float:
    value = data.get(key)
    return _require_number_from_value(value, path, key)


def _require_number_from_value(value: Any, path: Path, key: str) -> float:
    if not isinstance(value, int | float):
        raise FixtureError(f"{path}: {key} must be numeric")
    return float(value)


def _require_number_list(
    data: dict[str, Any],
    key: str,
    path: Path,
    *,
    length: int,
) -> list[float]:
    value = data.get(key)
    if (
        not isinstance(value, list)
        or len(value) != length
        or not all(isinstance(item, int | float) for item in value)
    ):
        raise FixtureError(f"{path}: {key} must be a {length}-item numeric list")
    return [float(item) for item in value]


def _label(path: Path, index: int | None) -> str:
    if index is None:
        return str(path)
    return f"{path}: cases[{index}]"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-root", type=Path, default=DEFAULT_ORACLE_ROOT)
    parser.add_argument("--contract-root", type=Path, default=DEFAULT_CONTRACT_ROOT)
    args = parser.parse_args()

    checked, failures = check_tree(
        oracle_root=args.oracle_root,
        contract_root=args.contract_root,
    )
    for failure in failures:
        print(failure.format(), file=sys.stderr)
    print(f"SDK_ORACLE_CHECKED={checked}")
    print(f"SDK_ORACLE_FAILED={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FixtureError as exc:
        print(f"SDK_ORACLE_CHECK_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
