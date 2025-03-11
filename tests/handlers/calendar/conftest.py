"""Fixtures for calendar handlers tests."""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def patch_settings(mock_settings):
    """Patch the settings module for all tests in this class."""
    with (
        patch("handlers.calendar.agenda.settings", mock_settings),
        patch("handlers.calendar.calendar.settings", mock_settings),
        patch("handlers.calendar.event.settings", mock_settings),
    ):
        yield
