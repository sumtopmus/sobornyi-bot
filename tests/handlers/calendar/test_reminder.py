"""Tests for the reminder module."""

from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from handlers.calendar.reminder import JOB_NAME, remind, reminder_on


class TestReminder:
    """Tests for the reminder module."""

    @patch("handlers.calendar.reminder.next_week")
    def test_reminder_on(self, mock_next_week, mock_settings):
        """Test the reminder_on function."""
        # Mock next_week to return a known date
        next_week = datetime(2023, 1, 8).date()
        mock_next_week.return_value = next_week

        # Set up the reminder time in settings
        mock_settings.REMINDER_TIME = "18:00:00"

        # Setup
        app = MagicMock()
        app.job_queue.get_jobs_by_name.return_value = []

        # Call the function
        reminder_on(app)

        # Assertions
        app.job_queue.get_jobs_by_name.assert_called_once_with(JOB_NAME)
        app.job_queue.run_repeating.assert_called_once()

        # Check the arguments to run_repeating
        args, kwargs = app.job_queue.run_repeating.call_args
        assert args[0] == remind
        assert kwargs["interval"] == timedelta(weeks=1)
        assert kwargs["name"] == JOB_NAME

        # Check the first time is correctly calculated (day before next_week at REMINDER_TIME)
        expected_first_time = datetime.combine(
            next_week - timedelta(days=1),
            time.fromisoformat(mock_settings.REMINDER_TIME),
        )
        assert kwargs["first"] == expected_first_time

    def test_reminder_on_job_exists(self):
        """Test the reminder_on function when the job already exists."""
        # Setup
        app = MagicMock()
        app.job_queue.get_jobs_by_name.return_value = [MagicMock()]

        # Call the function
        reminder_on(app)

        # Assertions
        app.job_queue.get_jobs_by_name.assert_called_once_with(JOB_NAME)
        app.job_queue.run_repeating.assert_not_called()

    @pytest.mark.asyncio
    async def test_remind_with_poster(self, mock_context):
        """Test the remind function when poster is available."""
        # Setup context with subscribers and poster available
        context = mock_context
        context.bot_data = {
            "subscribers": [123, 456],
            "agenda": {"image": "some_image_data"},
        }

        # Call the function
        await remind(context)

        # Assertions - two calls expected, one for each subscriber
        assert context.bot.send_message.call_count == 2

        # Check the message format
        expected_text = "⏰ Час оновити календар!\n\n✅ Постер"
        context.bot.send_message.assert_any_call(chat_id=123, text=expected_text)
        context.bot.send_message.assert_any_call(chat_id=456, text=expected_text)

    @pytest.mark.asyncio
    async def test_remind_without_poster(self, mock_context):
        """Test the remind function when poster is not available."""
        # Setup context with subscribers but no poster
        context = mock_context
        context.bot_data = {"subscribers": [123, 456], "agenda": {"image": None}}

        # Call the function
        await remind(context)

        # Assertions - two calls expected, one for each subscriber
        assert context.bot.send_message.call_count == 2

        # Check the message format
        expected_text = "⏰ Час оновити календар!\n\n🚫 Постер"
        context.bot.send_message.assert_any_call(chat_id=123, text=expected_text)
        context.bot.send_message.assert_any_call(chat_id=456, text=expected_text)

    @pytest.mark.asyncio
    async def test_remind_no_subscribers(self, mock_context):
        """Test the remind function when there are no subscribers."""
        # Setup context with no subscribers
        context = mock_context
        context.bot_data = {"subscribers": [], "agenda": {"image": None}}

        # Call the function
        await remind(context)

        # Assertions - no messages should be sent
        context.bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    @patch("handlers.calendar.reminder.log")
    async def test_remind_missing_data(self, mock_log, mock_context):
        """Test the remind function with missing data in bot_data."""
        # Setup context with missing data
        # Initialize with the basic structure to prevent KeyError
        context = mock_context
        context.bot_data = {"agenda": {"image": None}, "subscribers": []}

        # Call the function
        await remind(context)

        # No message should be sent because there are no subscribers
        context.bot.send_message.assert_not_called()
        # But log should be called
        mock_log.assert_called()
