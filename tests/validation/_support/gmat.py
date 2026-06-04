"""Docker-backed GMAT execution support for validation scripts."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tests.validation._support.contracts import LiveConfigError
from tests.validation._support.external_tools import run_json_tool

GMAT_VALIDATION_IMAGE_ENV = "GMAT_VALIDATION_IMAGE"
EXTERNAL_VALIDATION_MODE_ENV = "ASTROX_EXTERNAL_VALIDATION"
STRICT_EXTERNAL_VALIDATION_VALUE = "strict"


def is_external_validation_strict(env: Mapping[str, str] | None = None) -> bool:
    """Return whether external-tool validation must run rather than skip."""
    env = os.environ if env is None else env
    return env.get(EXTERNAL_VALIDATION_MODE_ENV, "").strip().lower() == STRICT_EXTERNAL_VALIDATION_VALUE


def require_gmat_image(env: Mapping[str, str] | None = None) -> str:
    """Return the configured GMAT validation image or raise a live-config error."""
    env = os.environ if env is None else env
    image = env.get(GMAT_VALIDATION_IMAGE_ENV, "").strip()
    if not image:
        raise LiveConfigError(f"{GMAT_VALIDATION_IMAGE_ENV} is required for GMAT-backed validation")
    return image


def run_gmat_driver(
    driver_path: str | Path,
    payload: Any,
    *,
    image: str | None = None,
    repo_root: str | Path | None = None,
    timeout_s: float = 300.0,
    env: Mapping[str, str] | None = None,
) -> Any:
    """Run a repo-side GMAT driver inside the configured validation image."""
    env = os.environ if env is None else env
    image = require_gmat_image(env) if image is None else image
    root = _resolve_repo_root(repo_root)
    driver_relpath = _driver_relpath(driver_path, root)
    driver_abspath = root / driver_relpath
    if not driver_abspath.is_file():
        raise LiveConfigError(f"GMAT driver does not exist: {driver_relpath.as_posix()}")

    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "-i",
        "-e",
        "GMAT_ROOT=/opt/gmat",
        "-v",
        f"{root}:/workspace:ro",
        "-w",
        "/workspace",
        image,
        "python3",
        f"/workspace/{driver_relpath.as_posix()}",
    ]
    return run_json_tool(command, payload, timeout_s=timeout_s)


def _resolve_repo_root(repo_root: str | Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "astrox").is_dir():
            return candidate
    raise LiveConfigError("could not locate repository root for GMAT validation")


def _driver_relpath(driver_path: str | Path, repo_root: Path) -> Path:
    driver = Path(driver_path)
    if driver.is_absolute():
        resolved = driver.resolve()
    else:
        resolved = (repo_root / driver).resolve()
    try:
        return resolved.relative_to(repo_root)
    except ValueError as exc:
        raise LiveConfigError(f"GMAT driver must live under repository root: {driver}") from exc
