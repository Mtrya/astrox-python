"""Shared Skyfield loading helpers for validation tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from skyfield.api import Loader


SKYFIELD_DATA_DIR_ENV = "SKYFIELD_DATA_DIR"
DEFAULT_SKYFIELD_DATA_DIR = "/tmp/astrox-python-skyfield"
MMAP_LENGTH_ERROR = "mmap length is greater than file size"


def skyfield_loader_from_env() -> Loader:
    """Return the validation Skyfield loader rooted in the configured data dir."""
    data_dir = Path(os.environ.get(SKYFIELD_DATA_DIR_ENV, DEFAULT_SKYFIELD_DATA_DIR))
    return Loader(str(data_dir))


def load_skyfield_ephemeris(loader: Any, filename: str = "de421.bsp") -> Any:
    """Load a Skyfield ephemeris, repairing a truncated local BSP cache once.

    Skyfield skips downloads when a file with the requested name already exists.
    If a previous run left a partial BSP file behind, jplephem can fail while
    memory-mapping it with ``ValueError: mmap length is greater than file size``.
    That is a cache-integrity problem, not a semantic cross-validation failure,
    so remove only the suspect BSP file and let Skyfield fetch/open it again.
    """
    try:
        ephemeris = loader(filename)
        _validate_ephemeris(ephemeris)
        return ephemeris
    except ValueError as exc:
        if MMAP_LENGTH_ERROR not in str(exc):
            raise
        path = Path(loader.path_to(filename))
        if path.exists():
            path.unlink()
        try:
            ephemeris = loader(filename)
            _validate_ephemeris(ephemeris)
            return ephemeris
        except Exception as retry_exc:
            raise ValueError(
                f"Skyfield ephemeris {filename!r} looked corrupt and could not be reloaded from {path}"
            ) from retry_exc


def _validate_ephemeris(ephemeris: Any) -> None:
    """Force jplephem's lazy mmap setup before returning a kernel to tests."""
    spk = getattr(ephemeris, "spk", None)
    if spk is None:
        return
    for segment in getattr(spk, "segments", ()):
        _ = segment._data
