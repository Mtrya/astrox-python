from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

from astrox import orbits
from scripts.sdk_contract import core


def write_fixture(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def minimal_fixture(*, expected_return: Any = 1.0) -> dict[str, Any]:
    return {
        "area": "propagator",
        "function": "astrox.propagator.j2",
        "scenario": "nominal",
        "compare": {"mode": "approximate_json", "abs_tol": 1.0e-9, "rel_tol": 1.0e-9},
        "cases": [
            {
                "id": "sso",
                "inputs": {"value": 1},
                "expected": {"return": expected_return},
            }
        ],
    }


def test_iter_fixture_paths_discovers_yaml_and_applies_glob(tmp_path: Path) -> None:
    root = tmp_path / "contracts"
    write_fixture(root / "propagator" / "j2" / "nominal.yaml", minimal_fixture())
    write_fixture(root / "propagator" / "two_body" / "nominal.yml", minimal_fixture())
    (root / "README.md").write_text("# docs\n", encoding="utf-8")

    assert [
        path.relative_to(root).as_posix()
        for path in core.iter_fixture_paths(root)
    ] == [
        "propagator/j2/nominal.yaml",
        "propagator/two_body/nominal.yml",
    ]
    assert [
        path.relative_to(root).as_posix()
        for path in core.iter_fixture_paths(root, glob_pattern="propagator/j2/*.yaml")
    ] == ["propagator/j2/nominal.yaml"]


def test_constructor_whitelist_builds_one_level_public_input() -> None:
    inputs = core.build_call_inputs(
        {
            "orbit": {
                "constructor": "astrox.orbits.keplerian",
                "kwargs": {
                    "semi_major_axis_m": 6778137.0,
                    "eccentricity": 0.001,
                    "inclination_deg": 28.5,
                    "argument_of_periapsis_deg": 0.0,
                    "raan_deg": 0.0,
                    "true_anomaly_deg": 0.0,
                },
            }
        }
    )

    assert isinstance(inputs["orbit"], orbits.KeplerianElements)
    assert inputs["orbit"].to_wire() == [6778137.0, 0.001, 28.5, 0.0, 0.0, 0.0]


def test_constructor_whitelist_rejects_unknown_and_nested_constructors() -> None:
    with pytest.raises(core.FixtureError, match="constructor must be one of"):
        core.build_call_inputs(
            {
                "orbit": {
                    "constructor": "astrox.not_real.value",
                    "kwargs": {},
                }
            }
        )

    with pytest.raises(core.FixtureError, match="only supported at one input level"):
        core.build_call_inputs(
            {
                "outer": {
                    "inner": {
                        "constructor": "astrox.orbits.keplerian",
                        "kwargs": {},
                    }
                }
            }
        )


def test_snapshot_return_converts_dataclasses_tuples_and_samples_long_arrays() -> None:
    @dataclass(frozen=True)
    class Value:
        vector: tuple[int, ...]
        label: str

    snapshot = core.snapshot_return(
        {
            "short": [1, 2, 3],
            "long": list(range(25)),
            "nested": Value(vector=tuple(range(22)), label="ok"),
        }
    )

    assert snapshot["short"] == [1, 2, 3]
    assert snapshot["long"] == {"length": 25, "first": list(range(10)), "last": list(range(15, 25))}
    assert snapshot["nested"]["vector"] == {"length": 22, "first": list(range(10)), "last": list(range(12, 22))}
    assert snapshot["nested"]["label"] == "ok"


def test_exact_and_approximate_comparisons_are_strict_about_shape_and_values() -> None:
    core.compare_snapshot(
        expected={"value": 1.0},
        actual={"value": 1.0 + 1.0e-10},
        compare={"mode": "approximate_json", "abs_tol": 1.0e-9, "rel_tol": 0.0},
    )

    with pytest.raises(core.ComparisonError, match="path=\\$.value"):
        core.compare_snapshot(
            expected={"value": 1.0},
            actual={"value": 1.1},
            compare={"mode": "approximate_json", "abs_tol": 1.0e-9, "rel_tol": 0.0},
        )

    with pytest.raises(core.ComparisonError, match="category=keys"):
        core.compare_snapshot(
            expected={"value": 1.0},
            actual={"value": 1.0, "extra": True},
            compare={"mode": "approximate_json", "abs_tol": 1.0e-9, "rel_tol": 0.0},
        )

    with pytest.raises(core.ComparisonError):
        core.compare_snapshot(
            expected={"value": 1.0},
            actual={"value": 1.0 + 1.0e-10},
            compare={"mode": "exact_json"},
        )


def test_mismatch_format_includes_case_function_path_and_numeric_error() -> None:
    fixture = minimal_fixture(expected_return={"value": 1.0})
    fixture["cases"][0]["inputs"] = {}

    failures = core.check_fixture(
        fixture,
        callable_resolver=lambda path: lambda: {"value": 1.5},
    )

    assert len(failures) == 1
    assert "case=sso" in failures[0]
    assert "function=astrox.propagator.j2" in failures[0]
    assert "path=$.value" in failures[0]
    assert "max_numeric_error=0.5" in failures[0]


def test_refresh_fixture_updates_expected_without_live_network() -> None:
    fixture = minimal_fixture(expected_return={"old": True})
    fixture["cases"][0]["inputs"] = {"value": 41}

    refreshed = core.refresh_fixture(
        fixture,
        callable_resolver=lambda path: lambda *, value: {"value": value + 1},
    )

    expected = refreshed["cases"][0]["expected"]
    assert expected["return"] == {"value": 42}
    assert expected["refreshed_at"].endswith("Z")


def test_lint_fixture_tree_validates_checked_in_contract_fixtures(tmp_path: Path) -> None:
    root = tmp_path / "contracts"
    write_fixture(root / "propagator" / "j2" / "nominal.yaml", minimal_fixture())

    assert core.lint_fixture_tree(root) == [root / "propagator" / "j2" / "nominal.yaml"]

    broken = minimal_fixture()
    del broken["cases"][0]["expected"]
    write_fixture(root / "propagator" / "j2" / "broken.yaml", broken)

    with pytest.raises(core.FixtureError, match="expected.return is required"):
        core.lint_fixture_tree(root)


def test_default_fixture_tree_lint_accepts_current_checked_in_tree() -> None:
    core.lint_fixture_tree(core.DEFAULT_FIXTURE_ROOT)
