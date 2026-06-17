from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.validation._support import contracts


def test_normalize_for_snapshot_converts_dataclasses_and_samples_long_lists() -> None:
    @dataclass(frozen=True)
    class Value:
        vector: tuple[int, ...]

    snapshot = contracts.normalize_for_snapshot(
        {
            "short": [1, 2, 3],
            "long": list(range(25)),
            "nested": Value(vector=tuple(range(22))),
        }
    )

    assert snapshot["short"] == [1, 2, 3]
    assert snapshot["long"] == {"length": 25, "first": list(range(10)), "last": list(range(15, 25))}
    assert snapshot["nested"]["vector"] == {"length": 22, "first": list(range(10)), "last": list(range(12, 22))}


def test_canonical_snapshot_io_round_trips_sorted_json(tmp_path: Path) -> None:
    path = tmp_path / "sample.snap.json"
    snapshot = {
        "cases": [{"return": {"b": 2, "a": 1}, "id": "case"}],
        "metadata": {"astrox_base_url": "http://example.test"},
    }

    contracts.write_snapshot(path, snapshot)

    assert path.read_text(encoding="utf-8").startswith('{\n  "cases": [')
    assert contracts.read_snapshot(path) == snapshot


def test_read_snapshot_rejects_missing_return(tmp_path: Path) -> None:
    path = tmp_path / "broken.snap.json"
    path.write_text('{"cases":[{"id":"case"}]}', encoding="utf-8")

    with pytest.raises(contracts.SnapshotError, match="return is required"):
        contracts.read_snapshot(path)


def test_check_snapshot_reports_case_and_first_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "sample.snap.json"
    contracts.write_snapshot(
        path,
        {
            "cases": [
                {
                    "id": "case",
                    "return": {"value": 1.0},
                }
            ]
        },
    )

    with pytest.raises(contracts.SnapshotMismatch) as exc_info:
        contracts.check_snapshot(
            cases=[
                contracts.LiveSnapshotCase(
                    id="case",
                    run=lambda: {"value": 2.0},
                )
            ],
            snapshot_path=path,
        )

    message = str(exc_info.value)
    assert "case=case" in message
    assert "path=$.value" in message
    assert "max_numeric_error=1" in message


def test_check_snapshot_uses_exact_canonical_json_by_default(tmp_path: Path) -> None:
    path = tmp_path / "sample.snap.json"
    contracts.write_snapshot(
        path,
        {
            "cases": [
                {
                    "id": "case",
                    "return": {"value": 0},
                }
            ]
        },
    )

    with pytest.raises(contracts.SnapshotMismatch, match="category=type"):
        contracts.check_snapshot(
            cases=[
                contracts.LiveSnapshotCase(
                    id="case",
                    run=lambda: {"value": 0.0},
                )
            ],
            snapshot_path=path,
        )


def test_check_snapshot_allows_explicit_approximate_numeric_tolerance(tmp_path: Path) -> None:
    path = tmp_path / "sample.snap.json"
    contracts.write_snapshot(
        path,
        {
            "cases": [
                {
                    "id": "case",
                    "return": {"value": 1.0},
                }
            ]
        },
    )

    contracts.check_snapshot(
        cases=[
            contracts.LiveSnapshotCase(
                id="case",
                run=lambda: {"value": 1.000001},
            )
        ],
        snapshot_path=path,
        abs_tol=1.0e-5,
    )


def test_check_snapshot_allows_explicit_approximate_datetime_tolerance(tmp_path: Path) -> None:
    path = tmp_path / "sample.snap.json"
    contracts.write_snapshot(
        path,
        {
            "cases": [
                {
                    "id": "case",
                    "return": {"start": "2024-01-01T00:00:27.275Z"},
                }
            ]
        },
    )

    contracts.check_snapshot(
        cases=[
            contracts.LiveSnapshotCase(
                id="case",
                run=lambda: {"start": "2024-01-01T00:00:27.276Z"},
            )
        ],
        snapshot_path=path,
        datetime_abs_tol_s=0.002,
    )


def test_check_snapshot_rejects_case_id_drift(tmp_path: Path) -> None:
    path = tmp_path / "sample.snap.json"
    contracts.write_snapshot(path, {"cases": [{"id": "expected", "return": True}]})

    with pytest.raises(contracts.SnapshotMismatch, match="case id mismatch"):
        contracts.check_snapshot(
            cases=[contracts.LiveSnapshotCase(id="actual", run=lambda: True)],
            snapshot_path=path,
        )


def test_main_check_and_refresh_without_live_network(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "sample.snap.json"
    cases = [
        contracts.LiveSnapshotCase(
            id="case",
            run=lambda: {"value": 1},
        )
    ]

    assert contracts.main(
        cases=cases,
        snapshot_path=path,
        argv=["--refresh"],
        configure_live=False,
        env={"ASTROX_BASE_URL": "http://example.test"},
    ) == 0
    assert "LIVE_SNAPSHOT_REFRESHED=1" in capsys.readouterr().out

    assert contracts.main(
        cases=cases,
        snapshot_path=path,
        argv=["--check"],
        configure_live=False,
    ) == 0
    assert "LIVE_SNAPSHOT_CHECKED=1" in capsys.readouterr().out
