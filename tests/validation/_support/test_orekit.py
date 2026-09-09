from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

import pytest

from tests.validation._support import orekit


def _write_archive(
    path: Path,
    *,
    files: dict[str, bytes],
    compression: int,
    date_time: tuple[int, int, int, int, int, int],
) -> None:
    with ZipFile(path, "w") as archive:
        for relative_name, content in files.items():
            member = ZipInfo(
                f"{orekit._OREKIT_DATA_ARCHIVE_ROOT}{relative_name}",
                date_time=date_time,
            )
            member.compress_type = compression
            archive.writestr(member, content)


def test_archive_content_checksum_ignores_zip_container_metadata(tmp_path: Path) -> None:
    files = {"tai-utc.dat": b"time data\n", "itrf-versions.conf": b"frame data\n"}
    stored = tmp_path / "stored.zip"
    deflated = tmp_path / "deflated.zip"
    _write_archive(
        stored,
        files=files,
        compression=ZIP_STORED,
        date_time=(2024, 1, 2, 3, 4, 6),
    )
    _write_archive(
        deflated,
        files=files,
        compression=ZIP_DEFLATED,
        date_time=(2026, 7, 8, 9, 10, 12),
    )

    assert stored.read_bytes() != deflated.read_bytes()
    assert orekit._archive_content_sha256(stored) == orekit._archive_content_sha256(
        deflated
    )


def test_archive_content_checksum_detects_member_changes(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.zip"
    changed_content = tmp_path / "changed-content.zip"
    changed_path = tmp_path / "changed-path.zip"
    common = {"compression": ZIP_DEFLATED, "date_time": (2026, 1, 2, 3, 4, 6)}
    _write_archive(baseline, files={"data.txt": b"baseline"}, **common)
    _write_archive(changed_content, files={"data.txt": b"changed"}, **common)
    _write_archive(changed_path, files={"renamed.txt": b"baseline"}, **common)

    baseline_checksum = orekit._archive_content_sha256(baseline)
    assert orekit._archive_content_sha256(changed_content) != baseline_checksum
    assert orekit._archive_content_sha256(changed_path) != baseline_checksum


def test_archive_content_checksum_rejects_unexpected_root(tmp_path: Path) -> None:
    archive_path = tmp_path / "unexpected-root.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("other/data.txt", b"data")

    with pytest.raises(RuntimeError, match="outside the expected root"):
        orekit._archive_content_sha256(archive_path)
