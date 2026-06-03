"""Shared mechanics for runnable validation scripts."""

from tests.validation._support.contracts import (
    ContractCase,
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

__all__ = [
    "ContractCase",
    "LiveConfigError",
    "SnapshotError",
    "SnapshotMismatch",
    "canonical_bytes",
    "check_snapshot",
    "compare_values",
    "configure_astrox_from_env",
    "main",
    "normalize_for_snapshot",
    "read_snapshot",
    "refresh_snapshot",
    "to_json_compatible",
    "write_snapshot",
]
