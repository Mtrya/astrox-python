"""Shared Orekit data setup for live cross-validation scripts."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from urllib.request import urlopen


OREKIT_DATA_REVISION = "baf158744d38ec76cf94e2d396280d545b9f0ba2"
OREKIT_DATA_URL = (
    "https://gitlab.orekit.org/orekit/orekit-data/-/archive/"
    f"{OREKIT_DATA_REVISION}/orekit-data-{OREKIT_DATA_REVISION}.zip"
)
OREKIT_DATA_SHA256 = "ecd3a084b2caec90753023d6023268809a317c3b2e409f7b77d7038c8311e403"
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_orekit_data() -> Path:
    """Return the verified Orekit data archive, downloading it when needed."""
    if (
        OREKIT_DATA_PATH.exists()
        and _sha256(OREKIT_DATA_PATH) == OREKIT_DATA_SHA256
    ):
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
        actual_sha256 = _sha256(temporary_path)
        if actual_sha256 != OREKIT_DATA_SHA256:
            raise RuntimeError(
                "Orekit data checksum mismatch: "
                f"expected {OREKIT_DATA_SHA256}, got {actual_sha256}"
            )
        temporary_path.replace(OREKIT_DATA_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)
    return OREKIT_DATA_PATH
