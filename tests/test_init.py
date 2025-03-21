"""Tests for the init module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Import the module to test with patched settings
from init import add_handlers, post_init, setup_logging

# Import the real Calendar class
from model.calendar import Calendar
from utils import MESSAGE_CLEANUP_JOB, message_cleanup


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

    def test_setup_logging_debug_mode(self, mock_settings):
        """Test setup_logging with DEBUG=True."""
        with (
            patch("logging.handlers.RotatingFileHandler") as mock_handler_class,
            patch("logging.Formatter") as mock_formatter_class,
            patch("logging.getLogger") as mock_get_logger,
            patch("init.debug_mode_on") as mock_debug_mode_on,
            patch("init.debug_mode_off") as mock_debug_mode_off,
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

    def test_setup_logging_production_mode(self, mock_settings):
        """Test setup_logging with DEBUG=False."""
        with (
            patch("logging.handlers.RotatingFileHandler") as mock_handler_class,
            patch("logging.Formatter") as mock_formatter_class,
            patch("logging.getLogger") as mock_get_logger,
            patch("init.debug_mode_on") as mock_debug_mode_on,
            patch("init.debug_mode_off") as mock_debug_mode_off,
        ):
            # Configure mocks
            mock_settings.DEBUG = False
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

            # Verify that debug_mode_off was called and debug_mode_on was not
            mock_debug_mode_off.assert_called_once()
            mock_debug_mode_on.assert_not_called()


class TestPostInit:
    """Tests for the post_init function."""

    @pytest.fixture
    def mock_application(self):
        """Create a mock application for testing."""
        app = MagicMock()
        app.bot_data = {}
        return app

    @pytest.mark.asyncio
    @patch("init.handlers.war.enable_war_mode")
    @patch("init.handlers.calendar.agenda_on")
    @patch("init.handlers.calendar.reminder_on")
    async def test_bot_data_initialization(
        self,
        mock_reminder_on,
        mock_agenda_on,
        mock_enable_war_mode,
        mock_application,
        mock_settings,
    ):
        """Test that bot_data is properly initialized."""
        mock_settings.WAR_MODE = False
        mock_settings.AGENDA_MODE = False

        await post_init(mock_application)

        # Check that bot_data was initialized with the expected values
        assert "calendar" in mock_application.bot_data
        assert isinstance(mock_application.bot_data["calendar"], Calendar)
        assert mock_application.bot_data["agenda"] == {"image": None}
        assert mock_application.bot_data["subscribers"] == set(mock_settings.MODERATORS)
        assert mock_application.bot_data["jobs"] == {}
        assert mock_application.bot_data["cross-posts"] == {}

        # Check that enable_war_mode and agenda_on were not called
        mock_enable_war_mode.assert_not_called()
        mock_agenda_on.assert_not_called()
        mock_reminder_on.assert_called_once_with(mock_application)

    @pytest.mark.asyncio
    @patch("init.handlers.war.enable_war_mode")
    @patch("init.handlers.calendar.agenda_on")
    async def test_war_mode_activation(
        self, mock_agenda_on, mock_enable_war_mode, mock_application, mock_settings
    ):
        """Test that war mode is activated when WAR_MODE is True."""
        mock_settings.WAR_MODE = True
        mock_settings.AGENDA_MODE = False

        await post_init(mock_application)

        # Check that war_on was called and agenda_on was not
        mock_enable_war_mode.assert_called_once_with(mock_application)
        mock_agenda_on.assert_not_called()

    @pytest.mark.asyncio
    @patch("init.handlers.war.enable_war_mode")
    @patch("init.handlers.calendar.agenda_on")
    async def test_agenda_mode_activation(
        self, mock_agenda_on, mock_enable_war_mode, mock_application, mock_settings
    ):
        """Test that agenda mode is activated when AGENDA_MODE is True."""
        mock_settings.WAR_MODE = False
        mock_settings.AGENDA_MODE = True

        await post_init(mock_application)

        # Check that agenda_on was called and war_on was not
        mock_agenda_on.assert_called_once_with(mock_application)
        mock_enable_war_mode.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_existing_message_cleanup_jobs(self, mock_application):
        """Test that existing message_cleanup jobs are processed correctly."""
        # Create a job in bot_data
        job_name = f"{MESSAGE_CLEANUP_JOB}:12345"
        job_time = datetime.now() + timedelta(minutes=5)
        job_data = 12345

        mock_application.bot_data = {
            "jobs": {job_name: {"time": job_time, "data": job_data}}
        }

        # Patch utils.add_job to verify it's called correctly
        with (
            patch("init.utils.add_job") as mock_add_job,
            patch("init.datetime") as mock_datetime,
        ):
            # Set up datetime.now() to return a fixed time
            current_time = datetime.now()
            mock_datetime.now.return_value = current_time

            # Expected delay calculation
            expected_delay = max(timedelta(seconds=0), job_time - current_time)

            await post_init(mock_application)

            # Verify add_job was called with correct parameters
            mock_add_job.assert_called_once_with(
                message_cleanup,
                expected_delay,
                mock_application,
                MESSAGE_CLEANUP_JOB,
                job_data,
            )

            # Verify jobs dict was reset
            assert mock_application.bot_data["jobs"] == {}

    @pytest.mark.asyncio
    async def test_process_existing_jobs_with_past_time(self, mock_application):
        """Test that jobs with past times are processed with zero delay."""
        # Create a job in bot_data with a time in the past
        job_name = f"{MESSAGE_CLEANUP_JOB}:12345"
        job_time = datetime.now() - timedelta(minutes=5)  # 5 minutes in the past
        job_data = 12345

        mock_application.bot_data = {
            "jobs": {job_name: {"time": job_time, "data": job_data}}
        }

        # Patch utils.add_job to verify it's called correctly
        with (
            patch("init.utils.add_job") as mock_add_job,
            patch("init.datetime") as mock_datetime,
        ):
            # Set up datetime.now() to return a fixed time
            current_time = datetime.now()
            mock_datetime.now.return_value = current_time

            # For past times, delay should be 0
            expected_delay = timedelta(seconds=0)

            await post_init(mock_application)

            # Verify add_job was called with zero delay
            mock_add_job.assert_called_once_with(
                message_cleanup,
                expected_delay,
                mock_application,
                MESSAGE_CLEANUP_JOB,
                job_data,
            )

    @pytest.mark.asyncio
    async def test_process_multiple_existing_jobs(self, mock_application):
        """Test processing multiple existing jobs of different types."""
        # Create multiple jobs in bot_data
        current_time = datetime.now()

        # Message cleanup job
        cleanup_job_name = f"{MESSAGE_CLEANUP_JOB}:12345"
        cleanup_job_time = current_time + timedelta(minutes=5)
        cleanup_job_data = 12345

        # Unknown job type that should be ignored
        unknown_job_name = "unknown_job:67890"
        unknown_job_time = current_time + timedelta(minutes=10)
        unknown_job_data = 67890

        mock_application.bot_data = {
            "jobs": {
                cleanup_job_name: {"time": cleanup_job_time, "data": cleanup_job_data},
                unknown_job_name: {"time": unknown_job_time, "data": unknown_job_data},
            }
        }

        # Patch utils.add_job to verify it's called correctly
        with (
            patch("init.utils.add_job") as mock_add_job,
            patch("init.datetime") as mock_datetime,
        ):
            # Set up datetime.now() to return a fixed time
            mock_datetime.now.return_value = current_time

            # Expected delay calculation for cleanup job
            expected_delay = timedelta(minutes=5)

            await post_init(mock_application)

            # Verify add_job was called only for the message_cleanup job
            mock_add_job.assert_called_once_with(
                message_cleanup,
                expected_delay,
                mock_application,
                MESSAGE_CLEANUP_JOB,
                cleanup_job_data,
            )

            # Verify jobs dict was reset
            assert mock_application.bot_data["jobs"] == {}

    @pytest.mark.asyncio
    async def test_empty_jobs_dict(self, mock_application):
        """Test that post_init handles an empty jobs dict correctly."""
        mock_application.bot_data = {"jobs": {}}

        # Patch utils.add_job to verify it's not called
        with patch("init.utils.add_job") as mock_add_job:
            await post_init(mock_application)

            # Verify add_job was not called
            mock_add_job.assert_not_called()

            # Verify jobs dict is still empty
            assert mock_application.bot_data["jobs"] == {}


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
