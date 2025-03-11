"""Fixtures for handlers tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Message, Update, User, Chat
from telegram.ext import ContextTypes


@pytest.fixture(autouse=True)
def patch_settings(mock_settings):
    """Patch the settings module for all tests in this class."""
    with (
        patch("handlers.channel.settings", mock_settings),
        patch("handlers.debug.settings", mock_settings),
        patch("handlers.info.settings", mock_settings),
        patch("handlers.request.settings", mock_settings),
    ):
        yield
