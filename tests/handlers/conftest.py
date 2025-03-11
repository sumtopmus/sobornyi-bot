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
        patch("config.settings", mock_settings),
    ):
        yield


@pytest.fixture
def mock_message():
    """Create a mock message for testing."""
    message = MagicMock(spec=Message)
    message.message_id = 123
    message.text = "Test message"
    message.caption = None
    message.entities = []
    message.caption_entities = []
    message.copy = AsyncMock()
    return message


@pytest.fixture
def mock_channel_post(mock_message):
    """Create a mock channel post for testing."""
    channel_post = mock_message
    channel_post.pinned_message = None
    return channel_post


@pytest.fixture
def mock_edited_channel_post(mock_message):
    """Create a mock edited channel post for testing."""
    edited_post = mock_message
    return edited_post


@pytest.fixture
def mock_update(mock_message, mock_channel_post, mock_edited_channel_post):
    """Create a mock update for testing."""
    update = MagicMock(spec=Update)
    update.update_id = 1
    update.message = mock_message
    update.channel_post = mock_channel_post
    update.edited_channel_post = mock_edited_channel_post
    update.callback_query = AsyncMock()
    update.callback_query.data = "test_data"
    update.callback_query.message = mock_message
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.edit_message_caption = AsyncMock()
    update.effective_message = mock_message
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = -1001234567890
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456789
    update.effective_user.username = "testuser"
    return update


@pytest.fixture
def mock_context():
    """Create a mock context for testing."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    context.bot.edit_message_caption = AsyncMock()
    context.bot.pin_chat_message = AsyncMock()
    context.bot.delete_message = AsyncMock()
    context.bot_data = {"cross-posts": {}}
    context.user_data = {}
    context.chat_data = {}
    context.args = []
    context.job = MagicMock()
    return context
