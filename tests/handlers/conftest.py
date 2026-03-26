"""Fixtures for handlers tests."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def patch_settings(mock_settings):
    """Patch the settings module for all tests in this class."""
    with (
        patch("handlers.channel.settings", mock_settings),
        patch("handlers.topic.settings", mock_settings),
        patch("handlers.war.settings", mock_settings),
        patch("handlers.welcome.settings", mock_settings),
    ):
        yield
