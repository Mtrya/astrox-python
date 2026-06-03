from __future__ import annotations

from pathlib import Path

from tests.validation.sdk_contract import check_all


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def test_discover_scripts_skips_runner_tests_and_private_helpers(tmp_path: Path) -> None:
    touch(tmp_path / "propagator" / "j2.py")
    touch(tmp_path / "propagator" / "_common.py")
    touch(tmp_path / "propagator" / "test_j2.py")
    touch(tmp_path / "check_all.py")

    assert [path.relative_to(tmp_path).as_posix() for path in check_all.discover_scripts(tmp_path)] == [
        "propagator/j2.py"
    ]
