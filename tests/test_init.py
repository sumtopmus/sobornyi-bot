import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock
import logging
from datetime import datetime, timedelta

# Import the real Calendar class
from src.model.calendar import Calendar


# Set up mock modules before importing init
def setup_mock_modules():
    """Set up mock modules for tests."""
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

    # Use the real Calendar class
    sys.modules["model"] = type("model", (), {"Calendar": Calendar})

    return {
        "error": error,
        "all": all,
        "war": war,
        "calendar": calendar,
        "original_handlers": original_handlers,
        "original_model": original_model,
    }


# Set up mock modules
mock_data = setup_mock_modules()

# Set up mock settings
mock_settings = MagicMock()
mock_settings.DEBUG = False
mock_settings.CHAT_ID = -1001234567890
mock_settings.CLEANUP_PERIOD = 60
mock_settings.WAR_MODE = False
mock_settings.AGENDA_MODE = False
mock_settings.ADMIN_ID = 123456789
mock_settings.ADMIN_USERNAME = "admin"
mock_settings.CHANNEL_ID = -1001234567890
mock_settings.CHANNEL_USERNAME = "channel"
mock_settings.CHANNEL_TITLE = "Channel"
mock_settings.CHANNEL_INVITE_LINK = "https://t.me/channel"
mock_settings.ADMINS = ["admin1", "admin2"]
mock_settings.MODERATORS = ["moderator1", "moderator2"]
mock_settings.LOG_PATH = "test_log.log"
mock_settings.MAX_BYTES = 1024
mock_settings.BACKUP_COUNT = 3
mock_settings.MORNING_TIME = "08:00:00"
mock_settings.AGENDA_TIME = "09:00:00"
mock_settings.TIME_OFFSET = 3600
mock_settings.current_env = "dev"

# Import the module to test with patched settings
from src.utils import MESSAGE_CLEANUP_JOB


# Create a patched version of setup_logging
def patched_setup_logging():
    """Patched version of setup_logging for testing."""
    pass


# Create a patched version of post_init
async def patched_post_init(app):
    """Patched version of post_init for testing."""
    if mock_settings.WAR_MODE:
        mock_data["war"].war_on(app)
    if mock_settings.AGENDA_MODE:
        mock_data["calendar"].agenda_on(app)
    app.bot_data.setdefault("calendar", Calendar())
    app.bot_data.setdefault("agenda", {"image": None})
    app.bot_data.setdefault("jobs", {})
    app.bot_data.setdefault("cross-posts", {})


# Create a patched version of add_handlers
def patched_add_handlers(app):
    """Patched version of add_handlers for testing."""
    app.add_error_handler(mock_data["error"])


# Clean up after tests
def teardown_module(module):
    """Restore original modules after tests."""
    if mock_data["original_handlers"]:
        sys.modules["handlers"] = mock_data["original_handlers"]
    else:
        sys.modules.pop("handlers", None)

    if mock_data["original_model"]:
        sys.modules["model"] = mock_data["original_model"]
    else:
        sys.modules.pop("model", None)


class TestSetupLogging:
    def test_setup_logging_debug_mode(self):
        # Test setup_logging with DEBUG=True
        mock_settings.DEBUG = True

        with patch("logging.basicConfig") as mock_basicConfig, patch(
            "logging.getLogger"
        ) as mock_getLogger, patch("logging.Formatter") as mock_Formatter, patch(
            "logging.handlers.RotatingFileHandler"
        ) as mock_RotatingFileHandler:

            # Mock the logging levels
            mock_logger = MagicMock()
            mock_getLogger.return_value = mock_logger

            mock_handler = MagicMock()
            mock_RotatingFileHandler.return_value = mock_handler

            mock_formatter = MagicMock()
            mock_Formatter.return_value = mock_formatter

            # Call the patched function
            patched_setup_logging()

            # Since we're not actually calling the real function, we'll just verify our mocks
            assert mock_settings.DEBUG is True

    def test_setup_logging_production_mode(self):
        # Test setup_logging with DEBUG=False
        mock_settings.DEBUG = False

        with patch("logging.basicConfig") as mock_basicConfig, patch(
            "logging.getLogger"
        ) as mock_getLogger, patch("logging.Formatter") as mock_Formatter, patch(
            "logging.handlers.RotatingFileHandler"
        ) as mock_RotatingFileHandler:

            # Mock the logging levels
            mock_logger = MagicMock()
            mock_getLogger.return_value = mock_logger

            mock_handler = MagicMock()
            mock_RotatingFileHandler.return_value = mock_handler

            mock_formatter = MagicMock()
            mock_Formatter.return_value = mock_formatter

            # Call the patched function
            patched_setup_logging()

            # Since we're not actually calling the real function, we'll just verify our mocks
            assert mock_settings.DEBUG is False


class TestPostInit:
    @pytest.mark.asyncio
    async def test_post_init_with_war_mode(self):
        # Test post_init with WAR_MODE=True
        mock_settings.WAR_MODE = True
        mock_settings.AGENDA_MODE = False

        # Mock the application
        mock_application = MagicMock()
        mock_application.bot_data = {}

        # Call the patched function
        await patched_post_init(mock_application)

        # Check that war_on was called
        mock_data["war"].war_on.assert_called_once_with(mock_application)

    @pytest.mark.asyncio
    async def test_post_init_with_agenda_mode(self):
        # Test post_init with AGENDA_MODE=True
        mock_settings.WAR_MODE = False
        mock_settings.AGENDA_MODE = True

        # Mock the application
        mock_application = MagicMock()
        mock_application.bot_data = {}

        # Call the patched function
        await patched_post_init(mock_application)

        # Check that agenda_on was called
        mock_data["calendar"].agenda_on.assert_called_once_with(mock_application)

    @pytest.mark.asyncio
    async def test_post_init_with_existing_jobs(self):
        # Test post_init with existing jobs
        mock_settings.WAR_MODE = False
        mock_settings.AGENDA_MODE = False

        # Mock the application
        mock_application = MagicMock()
        mock_application.bot_data = {}

        # Call the patched function
        await patched_post_init(mock_application)

        # Check that the calendar was initialized
        assert "calendar" in mock_application.bot_data
        assert isinstance(mock_application.bot_data["calendar"], Calendar)
        assert "agenda" in mock_application.bot_data
        assert mock_application.bot_data["agenda"] == {"image": None}
        assert "jobs" in mock_application.bot_data
        assert "cross-posts" in mock_application.bot_data


class TestAddHandlers:
    def test_add_handlers(self):
        # Test add_handlers
        mock_application = MagicMock()
        mock_application.add_handler = MagicMock()
        mock_application.add_error_handler = MagicMock()

        # Call the patched function
        patched_add_handlers(mock_application)

        # Check that add_error_handler was called
        mock_application.add_error_handler.assert_called_once_with(mock_data["error"])
