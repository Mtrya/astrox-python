"""Shared Orekit data setup for live cross-validation scripts."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from urllib.request import urlopen
from zipfile import BadZipFile, ZipFile, ZipInfo


OREKIT_DATA_REVISION = "baf158744d38ec76cf94e2d396280d545b9f0ba2"
OREKIT_DATA_URL = (
    "https://gitlab.orekit.org/orekit/orekit-data/-/archive/"
    f"{OREKIT_DATA_REVISION}/orekit-data-{OREKIT_DATA_REVISION}.zip"
)
OREKIT_DATA_CONTENT_SHA256 = "b32e7f8d2a64563e60b6455d346281745084dc823786d7a7373d4e1fd3cb17c7"
_OREKIT_DATA_ARCHIVE_ROOT = f"orekit-data-{OREKIT_DATA_REVISION}/"
_CACHE_HOME = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
OREKIT_DATA_PATH = Path(
    os.environ.get(
        "OREKIT_DATA_PATH",
        str(
            _CACHE_HOME
            / "astrox-python"
            / f"orekit-data-{OREKIT_DATA_REVISION}.zip"
        ),
    )
)


def _archive_content_sha256(path: Path) -> str:
    """Hash member paths and contents independently of ZIP container metadata."""
    digest = hashlib.sha256()
    with ZipFile(path) as archive:
        files: dict[str, ZipInfo] = {}
        for member in archive.infolist():
            if member.is_dir():
                continue
            if not member.filename.startswith(_OREKIT_DATA_ARCHIVE_ROOT):
                raise RuntimeError(
                    "Orekit data archive member is outside the expected root: "
                    f"{member.filename!r}"
                )
            relative_name = member.filename.removeprefix(_OREKIT_DATA_ARCHIVE_ROOT)
            if relative_name in files:
                raise RuntimeError(
                    f"Orekit data archive contains a duplicate member: {relative_name!r}"
                )
            files[relative_name] = member
        if not files:
            raise RuntimeError("Orekit data archive contains no files")

        for relative_name in sorted(files):
            member = files[relative_name]
            name_bytes = relative_name.encode("utf-8")
            digest.update(len(name_bytes).to_bytes(8, "big"))
            digest.update(name_bytes)
            digest.update(member.file_size.to_bytes(8, "big"))
            with archive.open(member) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def _has_expected_content(path: Path) -> bool:
    try:
        return _archive_content_sha256(path) == OREKIT_DATA_CONTENT_SHA256
    except (BadZipFile, OSError, RuntimeError):
        return False


def ensure_orekit_data() -> Path:
    """Return the verified Orekit data archive, downloading it when needed."""
    if OREKIT_DATA_PATH.exists() and _has_expected_content(OREKIT_DATA_PATH):
        return OREKIT_DATA_PATH

    OREKIT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=OREKIT_DATA_PATH.parent,
        prefix=f".{OREKIT_DATA_PATH.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            with urlopen(OREKIT_DATA_URL, timeout=60) as response:
                shutil.copyfileobj(response, output)
        actual_sha256 = _archive_content_sha256(temporary_path)
        if actual_sha256 != OREKIT_DATA_CONTENT_SHA256:
            raise RuntimeError(
                "Orekit data content checksum mismatch: "
                f"expected {OREKIT_DATA_CONTENT_SHA256}, got {actual_sha256}"
            )
        temporary_path.replace(OREKIT_DATA_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)
    return OREKIT_DATA_PATH
