"""Shared pytest fixtures."""

import pytest

from astrox import HTTPClient


@pytest.fixture(scope="session")
def session():
    """Provide a shared HTTPClient session for all tests."""
    return HTTPClient(timeout=60)
