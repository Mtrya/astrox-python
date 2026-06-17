"""Shared mechanics for runnable validation scripts."""

from tests.validation._support.contracts import (
    LiveSnapshotCase,
    LiveConfigError,
    SnapshotError,
    SnapshotMismatch,
    canonical_bytes,
    check_snapshot,
    compare_values,
    configure_astrox_from_env,
    main,
    normalize_for_snapshot,
    read_snapshot,
    refresh_snapshot,
    to_json_compatible,
    write_snapshot,
)
from tests.validation._support.external_tools import ExternalToolError, run_json_tool
from tests.validation._support.gmat import (
    EXTERNAL_VALIDATION_MODE_ENV,
    GMAT_VALIDATION_IMAGE_ENV,
    STRICT_EXTERNAL_VALIDATION_VALUE,
    is_external_validation_strict,
    require_gmat_image,
    run_gmat_driver,
)
from tests.validation._support.skyfield import (
    DEFAULT_SKYFIELD_DATA_DIR,
    MMAP_LENGTH_ERROR,
    SKYFIELD_DATA_DIR_ENV,
    load_skyfield_ephemeris,
    skyfield_loader_from_env,
)

__all__ = [
    "LiveSnapshotCase",
    "EXTERNAL_VALIDATION_MODE_ENV",
    "ExternalToolError",
    "GMAT_VALIDATION_IMAGE_ENV",
    "DEFAULT_SKYFIELD_DATA_DIR",
    "LiveConfigError",
    "MMAP_LENGTH_ERROR",
    "SKYFIELD_DATA_DIR_ENV",
    "STRICT_EXTERNAL_VALIDATION_VALUE",
    "SnapshotError",
    "SnapshotMismatch",
    "canonical_bytes",
    "check_snapshot",
    "compare_values",
    "configure_astrox_from_env",
    "is_external_validation_strict",
    "load_skyfield_ephemeris",
    "main",
    "normalize_for_snapshot",
    "read_snapshot",
    "require_gmat_image",
    "refresh_snapshot",
    "run_gmat_driver",
    "run_json_tool",
    "skyfield_loader_from_env",
    "to_json_compatible",
    "write_snapshot",
]
