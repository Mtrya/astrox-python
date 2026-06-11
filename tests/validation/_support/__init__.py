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

__all__ = [
    "LiveSnapshotCase",
    "EXTERNAL_VALIDATION_MODE_ENV",
    "ExternalToolError",
    "GMAT_VALIDATION_IMAGE_ENV",
    "LiveConfigError",
    "STRICT_EXTERNAL_VALIDATION_VALUE",
    "SnapshotError",
    "SnapshotMismatch",
    "canonical_bytes",
    "check_snapshot",
    "compare_values",
    "configure_astrox_from_env",
    "is_external_validation_strict",
    "main",
    "normalize_for_snapshot",
    "read_snapshot",
    "require_gmat_image",
    "refresh_snapshot",
    "run_gmat_driver",
    "run_json_tool",
    "to_json_compatible",
    "write_snapshot",
]
