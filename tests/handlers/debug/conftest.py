"""Fixtures for handlers tests."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def patch_settings(mock_settings):
    """Patch the settings module for all tests in this class."""
    with (
        patch("config.settings") as mock_settings,
        patch("handlers.debug.debug.settings", mock_settings),
        patch("handlers.debug.info.settings", mock_settings),
        patch("handlers.debug.upload.settings", mock_settings),
    ):
        yield
