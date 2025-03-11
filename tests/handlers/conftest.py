"""Fixtures for calendar handlers tests."""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def patch_settings(mock_settings):
    """Patch the settings module for all tests in this class."""
    with (patch("handlers.channel.settings", mock_settings),):
        yield
