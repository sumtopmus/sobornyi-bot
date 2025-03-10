import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import logging
from datetime import datetime, timedelta

# Now import the module to test
from init import setup_logging, post_init, add_handlers
from utils import message_cleanup, MESSAGE_CLEANUP_JOB


class TestSetupLogging:
    def test_setup_logging_debug_mode(self, mock_settings):
        # Test setup_logging with DEBUG=True
        mock_settings.DEBUG = True
        mock_settings.LOG_PATH = "test_log.log"
        mock_settings.MAX_BYTES = 1024
        mock_settings.BACKUP_COUNT = 3

        with patch("init.logging") as mock_logging:
            # Mock the logging levels
            mock_logging.DEBUG = logging.DEBUG
            mock_logging.INFO = logging.INFO
            mock_logging.WARNING = logging.WARNING

            mock_handler = MagicMock()
            mock_handler_class = MagicMock()
            mock_handler_class.return_value = mock_handler
            mock_logging.handlers.RotatingFileHandler = mock_handler_class

            mock_formatter = MagicMock()
            mock_logging.Formatter.return_value = mock_formatter

            # Call the function
            setup_logging()

            # Check that the handler was created with the correct parameters
            mock_handler_class.assert_called_once_with(
                filename=mock_settings.LOG_PATH,
                maxBytes=mock_settings.MAX_BYTES,
                backupCount=mock_settings.BACKUP_COUNT,
            )

            # Check that the formatter was set
            mock_handler.setFormatter.assert_called_once_with(mock_formatter)

            # Check that the handler was added to the root logger
            mock_logging.getLogger.return_value.addHandler.assert_called_once_with(
                mock_handler
            )

            # Check that the log level was set to DEBUG
            mock_logging.getLogger.return_value.setLevel.assert_any_call(
                mock_logging.DEBUG
            )

            # Check that the apscheduler and httpx loggers were set to WARNING
            mock_logging.getLogger.assert_any_call("apscheduler")
            mock_logging.getLogger.assert_any_call("httpx")

    def test_setup_logging_production_mode(self, mock_settings):
        # Test setup_logging with DEBUG=False
        mock_settings.DEBUG = False
        mock_settings.LOG_PATH = "test_log.log"
        mock_settings.MAX_BYTES = 1024
        mock_settings.BACKUP_COUNT = 3

        with patch("init.logging") as mock_logging:
            # Mock the logging levels
            mock_logging.DEBUG = logging.DEBUG
            mock_logging.INFO = logging.INFO
            mock_logging.WARNING = logging.WARNING

            mock_handler = MagicMock()
            mock_handler_class = MagicMock()
            mock_handler_class.return_value = mock_handler
            mock_logging.handlers.RotatingFileHandler = mock_handler_class

            # Call the function
            setup_logging()

            # Check that the log level was set to INFO
            mock_logging.getLogger.return_value.setLevel.assert_any_call(
                mock_logging.INFO
            )


class TestPostInit:
    @pytest.mark.asyncio
    async def test_post_init_with_war_mode(self, mock_settings):
        # Test post_init with WAR_MODE=True
        mock_settings.WAR_MODE = True
        mock_settings.AGENDA_MODE = False

        app = MagicMock()
        app.bot_data = {}

        with patch("init.handlers.war.war_on") as mock_war_on, patch(
            "init.handlers.calendar.agenda_on"
        ) as mock_agenda_on, patch("init.Calendar") as mock_calendar_class:

            mock_calendar = MagicMock()
            mock_calendar_class.return_value = mock_calendar

            # Call the function
            await post_init(app)

            # Check that war_on was called
            mock_war_on.assert_called_once_with(app)

            # Check that agenda_on was not called
            mock_agenda_on.assert_not_called()

            # Check that the calendar was initialized
            assert app.bot_data["calendar"] == mock_calendar
            assert app.bot_data["agenda"] == {"image": None}
            assert app.bot_data["jobs"] == {}
            assert app.bot_data["cross-posts"] == {}

    @pytest.mark.asyncio
    async def test_post_init_with_agenda_mode(self, mock_settings):
        # Test post_init with AGENDA_MODE=True
        mock_settings.WAR_MODE = False
        mock_settings.AGENDA_MODE = True

        app = MagicMock()
        app.bot_data = {}

        with patch("init.handlers.war.war_on") as mock_war_on, patch(
            "init.handlers.calendar.agenda_on"
        ) as mock_agenda_on, patch("init.Calendar") as mock_calendar_class:

            # Call the function
            await post_init(app)

            # Check that agenda_on was called
            mock_agenda_on.assert_called_once_with(app)

            # Check that war_on was not called
            mock_war_on.assert_not_called()

    @pytest.mark.asyncio
    async def test_post_init_with_existing_jobs(self, mock_settings):
        # Test post_init with existing jobs
        mock_settings.WAR_MODE = False
        mock_settings.AGENDA_MODE = False

        app = MagicMock()
        app.bot_data = {
            "jobs": {
                "message_cleanup:123": {
                    "time": datetime.now() + timedelta(seconds=60),
                    "data": 123,
                }
            }
        }

        with patch("init.utils") as mock_utils, patch(
            "init.datetime"
        ) as mock_datetime, patch("init.Calendar") as mock_calendar_class:

            # Set up the mock for MESSAGE_CLEANUP_JOB
            mock_utils.MESSAGE_CLEANUP_JOB = MESSAGE_CLEANUP_JOB

            mock_datetime.now.return_value = datetime.now()

            # Call the function
            await post_init(app)

            # Check that add_job was called for the message_cleanup job
            mock_utils.add_job.assert_called_once()
            # Check the job_family parameter
            assert mock_utils.add_job.call_args[0][3] == MESSAGE_CLEANUP_JOB
            # Check the job_data parameter
            assert mock_utils.add_job.call_args[0][4] == 123


class TestAddHandlers:
    def test_add_handlers(self):
        # Test add_handlers
        app = MagicMock()

        with patch("init.handlers.error") as mock_error_handler, patch(
            "init.handlers.all"
        ) as mock_all_handlers:

            # Call the function
            add_handlers(app)

            # Check that the error handler was added
            app.add_error_handler.assert_called_once_with(mock_error_handler)

            # Check that all handlers were added
            app.add_handlers.assert_called_once_with(mock_all_handlers)
