"""Shared Orekit data setup for live cross-validation scripts."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from urllib.request import urlopen


OREKIT_DATA_URL = (
    "https://gitlab.orekit.org/orekit/orekit-data/-/archive/main/orekit-data-main.zip"
)
OREKIT_DATA_PATH = Path(
    os.environ.get("OREKIT_DATA_PATH", "/tmp/astrox-python-orekit-data.zip")
)


def ensure_orekit_data() -> Path:
    """Return a local Orekit data archive, downloading it when absent."""
    if OREKIT_DATA_PATH.exists() and OREKIT_DATA_PATH.stat().st_size > 0:
        return OREKIT_DATA_PATH

    OREKIT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = OREKIT_DATA_PATH.with_suffix(OREKIT_DATA_PATH.suffix + ".tmp")
    with urlopen(OREKIT_DATA_URL, timeout=60) as response, temporary_path.open(
        "wb"
    ) as output:
        shutil.copyfileobj(response, output)
    temporary_path.replace(OREKIT_DATA_PATH)
    return OREKIT_DATA_PATH
