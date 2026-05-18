"""Generated model public-surface tests."""

from __future__ import annotations

import importlib

import pytest

import astrox
from astrox import _models


def test_generated_models_remain_available_as_internal_transport_models() -> None:
    assert hasattr(_models, "KeplerElements")
    assert hasattr(_models, "KeplerElementsWithEpoch")
    assert hasattr(_models, "Propagator")


def test_generated_model_alias_module_is_not_publicly_importable() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("astrox.models")


def test_root_package_does_not_export_generated_model_aliases() -> None:
    assert "models" not in astrox.__all__
    assert not hasattr(astrox, "models")
