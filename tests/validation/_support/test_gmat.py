from __future__ import annotations

from pathlib import Path

import pytest

from tests.validation._support import gmat
from tests.validation._support.contracts import LiveConfigError


def test_external_validation_strict_mode_is_explicit() -> None:
    assert not gmat.is_external_validation_strict({})
    assert not gmat.is_external_validation_strict({"ASTROX_EXTERNAL_VALIDATION": "optional"})
    assert gmat.is_external_validation_strict({"ASTROX_EXTERNAL_VALIDATION": "strict"})
    assert gmat.is_external_validation_strict({"ASTROX_EXTERNAL_VALIDATION": " STRICT "})


def test_require_gmat_image_raises_when_missing() -> None:
    with pytest.raises(LiveConfigError, match="GMAT_VALIDATION_IMAGE"):
        gmat.require_gmat_image({})


def test_run_gmat_driver_mounts_repo_readonly_and_executes_repo_driver(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    driver = root / "tests" / "validation" / "cross_validation" / "propagator" / "test_hpop_gmat.py"
    driver.parent.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    (root / "astrox").mkdir()
    driver.write_text("print('{}')\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run_json_tool(command: list[str], payload: object, *, timeout_s: float) -> dict[str, str]:
        captured["command"] = command
        captured["payload"] = payload
        captured["timeout_s"] = timeout_s
        return {"ok": "yes"}

    monkeypatch.setattr(gmat, "run_json_tool", fake_run_json_tool)

    result = gmat.run_gmat_driver(
        driver,
        {"case": "nominal"},
        image="ghcr.io/example/gmat:gmat-r2026a",
        repo_root=root,
        timeout_s=42.0,
    )

    assert result == {"ok": "yes"}
    assert captured["payload"] == {"case": "nominal"}
    assert captured["timeout_s"] == 42.0
    command = captured["command"]
    assert command == [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "-i",
        "-e",
        "GMAT_ROOT=/opt/gmat",
        "-v",
        f"{root.resolve()}:/workspace:ro",
        "-w",
        "/workspace",
        "ghcr.io/example/gmat:gmat-r2026a",
        "python3",
        "/workspace/tests/validation/cross_validation/propagator/test_hpop_gmat.py",
    ]


def test_run_gmat_driver_rejects_driver_outside_repo(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "driver.py"
    outside.write_text("print('{}')\n", encoding="utf-8")

    with pytest.raises(LiveConfigError, match="under repository root"):
        gmat.run_gmat_driver(outside, {}, image="image", repo_root=root)


def test_run_gmat_driver_rejects_relative_driver_escape(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "driver.py"
    outside.write_text("print('{}')\n", encoding="utf-8")

    with pytest.raises(LiveConfigError, match="under repository root"):
        gmat.run_gmat_driver("../driver.py", {}, image="image", repo_root=root)
