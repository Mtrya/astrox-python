from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
import pytest

from scripts.sdk_oracles import check
from scripts.sdk_contract.core import FixtureError


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_current_oracle_tree_passes() -> None:
    checked, failures = check.check_tree()

    assert checked >= 1
    assert failures == []


def test_oracle_checker_reports_numeric_mismatch(tmp_path: Path) -> None:
    contract_root = tmp_path / "contracts"
    oracle_root = tmp_path / "oracles"
    write_yaml(
        contract_root / "propagator" / "sgp4" / "nominal.yaml",
        {
            "area": "propagator",
            "function": "astrox.propagator.sgp4",
            "scenario": "nominal",
            "compare": {"mode": "approximate_json", "abs_tol": 1.0e-9, "rel_tol": 1.0e-9},
            "cases": [
                {
                    "id": "iss_tle",
                    "inputs": {},
                    "expected": {
                        "return": [
                            10.0,
                            {
                                "cartesian_velocity": [
                                    0.0,
                                    100.0,
                                    200.0,
                                    300.0,
                                    1.0,
                                    2.0,
                                    3.0,
                                ]
                            },
                        ]
                    },
                }
            ],
        },
    )
    write_yaml(
        oracle_root / "sgp4" / "propagator" / "iss_tle.yaml",
        {
            "area": "propagator",
            "source": {"name": "sgp4"},
            "scope": "mismatch fixture",
            "cases": [
                {
                    "id": "iss_tle",
                    "kind": "sgp4_state_samples",
                    "astrox_contract": {
                        "path": "propagator/sgp4/nominal.yaml",
                        "case": "iss_tle",
                    },
                    "tolerance": {
                        "period_abs_s": 0.1,
                        "position_abs_m": 0.1,
                        "velocity_abs_m_s": 0.1,
                    },
                    "oracle": {
                        "period_s": 10.0,
                        "samples": [
                            {
                                "offset_s": 0.0,
                                "position_m": [101.0, 200.0, 300.0],
                                "velocity_m_s": [1.0, 2.0, 3.0],
                            }
                        ],
                    },
                }
            ],
        },
    )

    checked, failures = check.check_tree(
        oracle_root=oracle_root,
        contract_root=contract_root,
    )

    assert checked == 1
    assert len(failures) == 1
    assert "position error" in failures[0].message


def test_oracle_checker_wraps_missing_contract_snapshot(tmp_path: Path) -> None:
    oracle_root = tmp_path / "oracles"
    write_yaml(
        oracle_root / "sgp4" / "propagator" / "iss_tle.yaml",
        {
            "area": "propagator",
            "source": {"name": "sgp4"},
            "scope": "missing contract fixture",
            "cases": [
                {
                    "id": "iss_tle",
                    "kind": "sgp4_state_samples",
                    "astrox_contract": {
                        "path": "propagator/sgp4/missing.yaml",
                        "case": "iss_tle",
                    },
                    "tolerance": {
                        "period_abs_s": 0.1,
                        "position_abs_m": 0.1,
                        "velocity_abs_m_s": 0.1,
                    },
                    "oracle": {
                        "period_s": 10.0,
                        "samples": [
                            {
                                "offset_s": 0.0,
                                "position_m": [100.0, 200.0, 300.0],
                                "velocity_m_s": [1.0, 2.0, 3.0],
                            }
                        ],
                    },
                }
            ],
        },
    )

    with pytest.raises(FixtureError, match="missing.yaml"):
        check.check_tree(
            oracle_root=oracle_root,
            contract_root=tmp_path / "contracts",
        )
