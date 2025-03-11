import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from telegram import Bot, Chat, Message, Update, User
from telegram.ext import Application, ContextTypes
import sys

from model.calendar import Calendar


# Create a function to set up mock modules when needed
def setup_mock_modules():
    """Set up mock modules for tests that need them."""
    # Mock handlers
    error = MagicMock()
    all = []

    # Mock war module
    class War:
        war_on = MagicMock()

    war = War()

    # Mock calendar module
    class CalendarModule:
        agenda_on = MagicMock()

    calendar = CalendarModule()

    # Store original modules if they exist
    original_handlers = sys.modules.get("handlers", None)
    original_model = sys.modules.get("model", None)

    # Add mock modules to sys.modules
    sys.modules["handlers"] = type(
        "handlers", (), {"error": error, "all": all, "war": war, "calendar": calendar}
    )

    # Use the real Calendar class instead of a mock
    sys.modules["model"] = type("model", (), {"Calendar": Calendar})

    # Return a function to restore original modules
    def restore_modules():
        if original_handlers:
            sys.modules["handlers"] = original_handlers
        else:
            sys.modules.pop("handlers", None)

        if original_model:
            sys.modules["model"] = original_model
        else:
            sys.modules.pop("model", None)

    return restore_modules


# Fixture to set up and tear down mock modules for specific tests
@pytest.fixture
def mock_modules():
    """Set up mock modules for tests that need them."""
    restore_fn = setup_mock_modules()
    yield
    restore_fn()


# Disable logging during tests
@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


# Mock settings fixture
@pytest.fixture(autouse=True)
def mock_settings():
    with (
        patch("config.settings") as mock_settings,
        patch("utils.settings", new=mock_settings),
        patch("init.settings", new=mock_settings),
    ):
        # Set default values for commonly used settings
        mock_settings.DEBUG = False
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.CLEANUP_PERIOD = 60
        mock_settings.WAR_MODE = False
        mock_settings.AGENDA_MODE = False
        mock_settings.CHANNEL_USERNAME = "channel"
        mock_settings.ADMINS = ["admin1", "admin2"]
        mock_settings.MODERATORS = ["moderator1", "moderator2"]
        mock_settings.LOG_PATH = "test_log.log"
        mock_settings.MAX_BYTES = 1024
        mock_settings.BACKUP_COUNT = 3
        mock_settings.MORNING_TIME = "08:00:00"
        mock_settings.AGENDA_TIME = "09:00:00"
        mock_settings.DEFAULT_AGENDA_IMAGE = "default_image.jpg"
        mock_settings.current_env = "dev"
        yield mock_settings


# Mock telegram user
@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 123456789
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    user.is_bot = False
    user.language_code = "en"
    user.name = "Test User"
    user.mention_markdown = MagicMock(
        side_effect=lambda name=None: f"[{name or user.name}](tg://user?id={user.id})"
    )
    return user


# Mock telegram chat
@pytest.fixture
def mock_chat():
    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "supergroup"
    chat.title = "Test Chat"
    chat.username = "testchat"
    return chat


# Mock telegram message
@pytest.fixture
def mock_message(mock_user, mock_chat):
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = mock_user
    message.chat = mock_chat
    message.date = datetime.now()
    message.text = "Test message"
    return message


# Mock telegram update
@pytest.fixture
def mock_update(mock_message):
    update = MagicMock(spec=Update)
    update.update_id = 1
    update.message = mock_message
    update.effective_chat = mock_message.chat
    update.effective_user = mock_message.from_user
    return update


# Mock telegram context
@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock(spec=Bot)
    context.bot.delete_message = AsyncMock()
    context.application = MagicMock(spec=Application)
    context.application.bot_data = {"jobs": {}}
    context.application.job_queue = MagicMock()
    context.application.job_queue.run_once = MagicMock()
    context.application.job_queue.get_jobs_by_name = MagicMock(return_value=[])
    context.user_data = {}
    # Mock job
    context.job = MagicMock()
    context.job.data = 1

    return context
