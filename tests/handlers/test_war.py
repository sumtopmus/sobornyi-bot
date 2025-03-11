"""Tests for the war module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, time

from handlers.war import (
    create_handlers,
    war_on,
    war_off,
    enable_war_mode,
    morning_message,
    JOB_NAME,
)


class TestWar:
    """Tests for the war module."""

    def test_create_handlers(self, mock_settings):
        """Test the create_handlers function."""
        # Setup
        mock_settings.ADMINS = ["admin1", "admin2"]
        mock_settings.CHAT_ID = -1001234567890

        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 2
        assert handlers[0].callback == war_on
        assert handlers[1].callback == war_off

        # Check that the filters are applied (without checking specific attributes)
        assert handlers[0].filters is not None
        assert handlers[1].filters is not None

    def test_war_on_command(self, mock_update, mock_context):
        """Test the war_on function that handles the command."""
        # Setup
        mock_context.application = MagicMock()

        # Mock the enable_war_mode function
        with patch("handlers.war.enable_war_mode") as mock_enable_war_mode:
            # Call the function
            war_on(mock_update, mock_context)

            # Assertions
            mock_enable_war_mode.assert_called_once_with(mock_context.application)

    def test_enable_war_mode(self, mock_settings, mock_context):
        """Test the enable_war_mode function."""
        # Setup
        app = MagicMock()
        app.job_queue.get_jobs_by_name.return_value = []
        mock_settings.MORNING_TIME = "08:00:00"

        # Call the function
        with patch("handlers.war.utils.log") as mock_log:
            enable_war_mode(app)

            # Assertions
            mock_log.assert_has_calls([call("war_on"), call(f"job_added: {JOB_NAME}")])
            app.job_queue.get_jobs_by_name.assert_called_once_with(JOB_NAME)
            app.job_queue.run_daily.assert_called_once()

            # Check the arguments to run_daily
            args, kwargs = app.job_queue.run_daily.call_args
            assert args[0] == morning_message
            assert isinstance(args[1], time)
            assert args[1].hour == 8
            assert args[1].minute == 0
            assert args[1].second == 0
            assert kwargs["name"] == JOB_NAME

    def test_enable_war_mode_job_exists(self, mock_context):
        """Test the enable_war_mode function when the job already exists."""
        # Setup
        app = MagicMock()
        app.job_queue.get_jobs_by_name.return_value = [MagicMock()]

        # Call the function
        with patch("handlers.war.utils.log") as mock_log:
            enable_war_mode(app)

            # Assertions
            mock_log.assert_called_once_with("war_on")
            app.job_queue.get_jobs_by_name.assert_called_once_with(JOB_NAME)
            app.job_queue.run_daily.assert_not_called()

    def test_war_off(self, mock_update, mock_context):
        """Test the war_off function."""
        # Setup
        mock_context.application = MagicMock()

        # Call the function
        with patch("handlers.war.utils.log") as mock_log, patch(
            "handlers.war.utils.clear_jobs"
        ) as mock_clear_jobs:
            war_off(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("war_off")
            mock_clear_jobs.assert_called_once_with(mock_context.application, JOB_NAME)

    @pytest.mark.asyncio
    async def test_morning_message(self, mock_settings, mock_context):
        """Test the morning_message function."""
        # Setup
        mock_context.bot.sendMessage = AsyncMock()
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.WAR_START_DATE = "2022-02-24"
        mock_settings.DATE_FORMAT = "%Y-%m-%d"

        # Mock datetime.today to return a fixed date
        mock_today = datetime(2022, 3, 1)

        # Call the function
        with patch("handlers.war.utils.log") as mock_log, patch(
            "handlers.war.datetime"
        ) as mock_datetime:
            mock_datetime.strptime.return_value = datetime(2022, 2, 24)
            mock_datetime.today.return_value = mock_today
            mock_datetime.strptime = datetime.strptime

            await morning_message(mock_context)

            # Assertions
            mock_log.assert_called_once_with("morning_message")
            mock_context.bot.sendMessage.assert_called_once()

            # Check the arguments to sendMessage
            args, kwargs = mock_context.bot.sendMessage.call_args
            assert kwargs["chat_id"] == -1001234567890
            assert "День 6 героїчного спротиву українського народу" in kwargs["text"]
            assert "Щоденна хвилина мовчання" in kwargs["text"]
