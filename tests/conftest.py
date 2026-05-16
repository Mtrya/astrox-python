"""Shared pytest fixtures."""

import pytest

from astrox import Client


@pytest.fixture(scope="session")
def session():
    """Provide a shared Client session for all tests."""
    return Client(timeout=60)
