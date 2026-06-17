from __future__ import annotations

from pathlib import Path

import pytest

from tests.validation._support.skyfield import (
    MMAP_LENGTH_ERROR,
    load_skyfield_ephemeris,
)


class FakeLoader:
    def __init__(self, directory: Path, *, first_error: Exception | None = None) -> None:
        self.directory = directory
        self.first_error = first_error
        self.calls = 0

    def path_to(self, filename: str) -> str:
        return str(self.directory / filename)

    def __call__(self, filename: str) -> dict[str, object]:
        self.calls += 1
        if self.calls == 1 and self.first_error is not None:
            raise self.first_error
        return {"filename": filename, "calls": self.calls}


class LazyMmapSegment:
    @property
    def _data(self) -> object:
        raise ValueError(MMAP_LENGTH_ERROR)


class LazyMmapEphemeris:
    class Spk:
        segments = (LazyMmapSegment(),)

    spk = Spk()


class LazyMmapLoader(FakeLoader):
    def __call__(self, filename: str) -> object:
        self.calls += 1
        if self.calls == 1:
            return LazyMmapEphemeris()
        return {"filename": filename, "calls": self.calls}


def test_load_skyfield_ephemeris_repairs_truncated_bsp_cache(tmp_path: Path) -> None:
    cache_file = tmp_path / "de421.bsp"
    cache_file.write_bytes(b"partial")
    loader = FakeLoader(tmp_path, first_error=ValueError(MMAP_LENGTH_ERROR))

    result = load_skyfield_ephemeris(loader)

    assert result == {"filename": "de421.bsp", "calls": 2}
    assert not cache_file.exists()


def test_load_skyfield_ephemeris_repairs_lazy_mmap_bsp_failure(tmp_path: Path) -> None:
    cache_file = tmp_path / "de421.bsp"
    cache_file.write_bytes(b"partial")
    loader = LazyMmapLoader(tmp_path)

    result = load_skyfield_ephemeris(loader)

    assert result == {"filename": "de421.bsp", "calls": 2}
    assert not cache_file.exists()


def test_load_skyfield_ephemeris_preserves_non_cache_errors(tmp_path: Path) -> None:
    cache_file = tmp_path / "de421.bsp"
    cache_file.write_bytes(b"partial")
    loader = FakeLoader(tmp_path, first_error=ValueError("different parser failure"))

    with pytest.raises(ValueError, match="different parser failure"):
        load_skyfield_ephemeris(loader)

    assert loader.calls == 1
    assert cache_file.exists()
