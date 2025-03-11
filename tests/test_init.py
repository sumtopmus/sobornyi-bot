"""Tests for the init module."""

import pytest
import sys
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the real Calendar class
from model.calendar import Calendar

# Import the module to test with patched settings
from init import add_handlers, setup_logging, post_init
from utils import MESSAGE_CLEANUP_JOB


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


class TestWarningFilters:
    """Tests for the warning filters setup in init.py."""

    def test_warning_filters(self):
        """Test that warning filters are set up correctly."""
        with patch("warnings.filterwarnings") as mock_filterwarnings:
            # Reset the mock to clear any previous calls
            mock_filterwarnings.reset_mock()

            # Re-import init to trigger the warning filters
            import importlib
            from src import init

            importlib.reload(init)

            # Check that filterwarnings was called with the expected arguments
            # The actual number of calls may vary, so we'll just check that the specific calls we're interested in were made
            mock_filterwarnings.assert_any_call(
                action="ignore",
                message=r".*CallbackQueryHandler",
                category=init.PTBUserWarning,
            )
            mock_filterwarnings.assert_any_call(
                action="ignore",
                message=r".*nested conversations.*",
                category=init.PTBUserWarning,
            )


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_debug_mode(self):
        """Test setup_logging with DEBUG=True."""
        # Test setup_logging with DEBUG=True
        with (
            patch("logging.handlers.RotatingFileHandler") as mock_handler_class,
            patch("logging.Formatter") as mock_formatter_class,
            patch("logging.getLogger") as mock_get_logger,
            patch("init.debug_mode_on") as mock_debug_mode_on,
            patch("init.debug_mode_off") as mock_debug_mode_off,
            patch("init.settings", mock_settings),
        ):
            # Configure mocks
            mock_settings.DEBUG = True
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler
            mock_formatter = MagicMock()
            mock_formatter_class.return_value = mock_formatter
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            setup_logging()

            # Verify the handler was created with the correct parameters
            mock_handler_class.assert_called_once_with(
                filename=mock_settings.LOG_PATH,
                maxBytes=mock_settings.MAX_BYTES,
                backupCount=mock_settings.BACKUP_COUNT,
            )

            # Verify the formatter was created and set
            mock_formatter_class.assert_called_once_with(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            mock_handler.setFormatter.assert_called_once_with(mock_formatter)

            # Verify that the root logger had the handler added
            mock_root_logger.addHandler.assert_called_once_with(mock_handler)

            # Verify that debug_mode_on was called and debug_mode_off was not
            mock_debug_mode_on.assert_called_once()
            mock_debug_mode_off.assert_not_called()

    def test_setup_logging_production_mode(self):
        """Test setup_logging with DEBUG=False."""
        # Test setup_logging with DEBUG=False
        with (
            patch("logging.handlers.RotatingFileHandler") as mock_handler_class,
            patch("logging.Formatter") as mock_formatter_class,
            patch("init.debug_mode_on") as mock_debug_mode_on,
            patch("init.debug_mode_off") as mock_debug_mode_off,
        ):
            # Configure mocks
            mock_settings.DEBUG = False
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler
            mock_formatter = MagicMock()
            mock_formatter_class.return_value = mock_formatter

            setup_logging()

            # Verify the handler was created with the correct parameters
            mock_handler_class.assert_called_once_with(
                filename=mock_settings.LOG_PATH,
                maxBytes=mock_settings.MAX_BYTES,
                backupCount=mock_settings.BACKUP_COUNT,
            )

            # Verify the formatter was created and set
            mock_formatter_class.assert_called_once_with(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            mock_handler.setFormatter.assert_called_once_with(mock_formatter)

            # Verify that debug_mode_off was called and debug_mode_on was not
            mock_debug_mode_off.assert_called_once()
            mock_debug_mode_on.assert_not_called()


class TestPostInit:
    """Tests for the post_init function."""

    @pytest.mark.asyncio
    async def test_bot_data_initialization(self):
        """Test that bot_data is properly initialized."""
        # Mock the application
        mock_application = MagicMock()
        mock_application.bot_data = {}

        # Patch settings and handlers to avoid side effects
        with (
            patch("init.settings", mock_settings),
            patch("init.handlers.war.war_on") as mock_war_on,
            patch("init.handlers.calendar.agenda_on") as mock_agenda_on,
        ):
            mock_settings.WAR_MODE = False
            mock_settings.AGENDA_MODE = False

            await post_init(mock_application)

        # Check that war and agenda modes were not activated
        mock_war_on.assert_not_called()
        mock_agenda_on.assert_not_called()
        # Check that bot_data was initialized correctly
        assert "calendar" in mock_application.bot_data
        assert isinstance(mock_application.bot_data["calendar"], Calendar)
        assert "agenda" in mock_application.bot_data
        assert mock_application.bot_data["agenda"] == {"image": None}
        assert "jobs" in mock_application.bot_data
        assert mock_application.bot_data["jobs"] == {}
        assert "cross-posts" in mock_application.bot_data
        assert mock_application.bot_data["cross-posts"] == {}

    @pytest.mark.asyncio
    async def test_war_mode_activation(self):
        """Test that war_on is called when WAR_MODE is True."""
        with patch("init.handlers.war.war_on") as mock_war_on:
            # Configure settings
            mock_settings.WAR_MODE = True

            # Mock the application
            mock_application = MagicMock()
            mock_application.bot_data = {}

            # Patch settings and other functions that might be called
            with (
                patch("init.settings", mock_settings),
                patch("init.handlers.calendar.agenda_on"),
            ):
                await post_init(mock_application)

            # Verify war_on was called with the application
            mock_war_on.assert_called_once_with(mock_application)

    @pytest.mark.asyncio
    async def test_agenda_mode_activation(self):
        """Test that agenda_on is called when AGENDA_MODE is True."""
        with patch("init.handlers.calendar.agenda_on") as mock_agenda_on:
            # Configure settings
            mock_settings.AGENDA_MODE = True

            # Mock the application
            mock_application = MagicMock()
            mock_application.bot_data = {}

            # Patch settings and other functions that might be called
            with (
                patch("init.settings", mock_settings),
                patch("init.handlers.war.war_on"),
            ):
                await post_init(mock_application)

            # Verify agenda_on was called with the application
            mock_agenda_on.assert_called_once_with(mock_application)


class TestAddHandlers:
    """Tests for the add_handlers function."""

    def test_add_handlers(self):
        """Test add_handlers function."""
        # Create a mock handlers module
        mock_handlers = MagicMock()
        mock_handlers.error = MagicMock()
        mock_handlers.all = [MagicMock(), MagicMock()]

        # Test add_handlers
        with patch("init.handlers", mock_handlers):
            # Mock the application
            mock_application = MagicMock()

            add_handlers(mock_application)

            # Check that add_error_handler was called with the error handler
            mock_application.add_error_handler.assert_called_once_with(
                mock_handlers.error
            )

            # Check that add_handlers was called with all handlers
            mock_application.add_handlers.assert_called_once_with(mock_handlers.all)

    def test_add_handlers_with_custom_handlers(self):
        """Test add_handlers with custom handlers."""
        # Create a mock handlers module with custom handlers
        mock_handlers = MagicMock()
        mock_handlers.error = MagicMock()
        custom_handler1 = MagicMock()
        custom_handler2 = MagicMock()
        mock_handlers.all = [custom_handler1, custom_handler2]

        # Test add_handlers
        with patch("init.handlers", mock_handlers):
            # Mock the application
            mock_application = MagicMock()

            add_handlers(mock_application)

            # Check that add_error_handler was called with the error handler
            mock_application.add_error_handler.assert_called_once_with(
                mock_handlers.error
            )

            # Check that add_handlers was called with all handlers
            mock_application.add_handlers.assert_called_once_with(
                [custom_handler1, custom_handler2]
            )
