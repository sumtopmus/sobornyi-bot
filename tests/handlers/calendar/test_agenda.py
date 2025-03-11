"""Tests for the agenda module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime, time, timedelta

from handlers.calendar.agenda import (
    agenda_on,
    publish_agenda,
    sync_agenda,
    publish_agenda_on_demand,
)
from utils import calculate_hash


class TestAgenda:
    """Tests for the agenda module."""

    def test_agenda_on(self, mock_settings):
        """Test the agenda_on function."""
        # Setup
        app = MagicMock()
        app.job_queue.get_jobs_by_name.return_value = []

        # Mock Calendar.get_next_week to return a known date
        next_week = date(2023, 1, 8)
        with patch("handlers.calendar.agenda.next_week", return_value=next_week):
            # Call the function
            agenda_on(app)

            # Assertions
            app.job_queue.get_jobs_by_name.assert_called_once_with("weekly_agenda")
            app.job_queue.run_repeating.assert_called_once()

            # Check the arguments to run_repeating
            args, kwargs = app.job_queue.run_repeating.call_args
            assert args[0] == publish_agenda
            assert kwargs["interval"] == timedelta(weeks=1)
            assert kwargs["name"] == "weekly_agenda"

            # Check the first time is correctly calculated
            expected_first_time = datetime.combine(
                next_week, time.fromisoformat(mock_settings.AGENDA_TIME)
            )
            assert kwargs["first"] == expected_first_time

    def test_agenda_on_job_exists(self):
        """Test the agenda_on function when the job already exists."""
        # Setup
        app = MagicMock()
        app.job_queue.get_jobs_by_name.return_value = [MagicMock()]

        # Call the function
        agenda_on(app)

        # Assertions
        app.job_queue.get_jobs_by_name.assert_called_once_with("weekly_agenda")
        app.job_queue.run_repeating.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_agenda_with_image(self, mock_context, mock_settings):
        """Test the publish_agenda function with a custom image."""
        # Setup
        context = mock_context
        context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {"image": "custom_image_data"},
        }
        context.bot_data["calendar"].get_agenda.return_value = "Agenda text"

        # Mock the current week date
        this_week = date(2023, 1, 1)
        with (
            patch("handlers.calendar.agenda.this_week", return_value=this_week),
            patch("handlers.calendar.agenda.cross_post", new=AsyncMock()),
        ):
            # Call the function
            await publish_agenda(context)

            # Assertions
            context.bot.send_photo.assert_called_once_with(
                chat_id=mock_settings.CHANNEL_USERNAME,
                photo="custom_image_data",
                caption="Agenda text",
            )

            # Check that the bot data was updated correctly
            assert (
                context.bot_data["agenda"]["message_id"]
                == context.bot.send_photo.return_value.message_id
            )
            assert context.bot_data["agenda"]["date"] == this_week.isoformat()
            assert context.bot_data["agenda"]["hash"] == calculate_hash("Agenda text")
            assert context.bot_data["agenda"]["image"] is None

    @pytest.mark.asyncio
    async def test_publish_agenda_with_default_image(self, mock_context, mock_settings):
        """Test the publish_agenda function with the default image."""
        # Setup
        context = mock_context
        context.bot_data = {"calendar": MagicMock(), "agenda": {"image": None}}
        context.bot_data["calendar"].get_agenda.return_value = "Agenda text"

        # Mock the current week date
        this_week = date(2023, 1, 1)
        with (
            patch("handlers.calendar.agenda.this_week", return_value=this_week),
            patch("handlers.calendar.agenda.cross_post", new=AsyncMock()),
        ):
            # Call the function
            await publish_agenda(context)

            # Assertions
            context.bot.send_photo.assert_called_once_with(
                chat_id=mock_settings.CHANNEL_USERNAME,
                photo=mock_settings.DEFAULT_AGENDA_IMAGE,
                caption="Agenda text",
            )

            # Check that the bot data was updated correctly
            assert (
                context.bot_data["agenda"]["message_id"]
                == context.bot.send_photo.return_value.message_id
            )
            assert context.bot_data["agenda"]["date"] == this_week.isoformat()
            assert context.bot_data["agenda"]["hash"] == calculate_hash("Agenda text")
            assert context.bot_data["agenda"]["image"] is None

    @pytest.mark.asyncio
    async def test_sync_agenda_no_change(self, mock_context):
        """Test the sync_agenda function when there's no change in the agenda."""
        # Setup
        context = mock_context
        agenda_text = "Agenda text"
        agenda_hash = calculate_hash(agenda_text)
        this_week = date(2023, 1, 1)

        context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {
                "date": this_week.isoformat(),
                "hash": agenda_hash,
                "message_id": 12345,
            },
        }
        context.bot_data["calendar"].get_agenda.return_value = agenda_text

        # Mock the current week date
        with patch("model.this_week", return_value=this_week):
            # Call the function
            await sync_agenda(context)

            # Assertions - should not edit the message
            context.bot.edit_message_caption.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_agenda_with_change(self, mock_context, mock_settings):
        """Test the sync_agenda function when there's a change in the agenda."""
        # Setup
        context = mock_context
        old_agenda_text = "Old agenda text"
        old_agenda_hash = calculate_hash(old_agenda_text)
        new_agenda_text = "New agenda text"
        this_week = date(2023, 1, 1)

        context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {
                "date": this_week.isoformat(),
                "hash": old_agenda_hash,
                "message_id": 12345,
            },
        }
        context.bot_data["calendar"].get_agenda.return_value = new_agenda_text

        # Mock the current week date
        with patch("handlers.calendar.agenda.this_week", return_value=this_week):
            # Call the function
            await sync_agenda(context)

            # Assertions - should edit the message
            context.bot.edit_message_caption.assert_called_once_with(
                chat_id=mock_settings.CHANNEL_USERNAME,
                message_id=12345,
                caption=new_agenda_text,
            )

            # Check that the hash was updated
            assert context.bot_data["agenda"]["hash"] == calculate_hash(new_agenda_text)

    @pytest.mark.asyncio
    async def test_sync_agenda_different_week(self, mock_context):
        """Test the sync_agenda function when it's a different week."""
        # Setup
        context = mock_context
        agenda_text = "Agenda text"
        agenda_hash = calculate_hash(agenda_text)
        last_week = date(2022, 12, 25)
        this_week = date(2023, 1, 1)

        context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {
                "date": last_week.isoformat(),
                "hash": agenda_hash,
                "message_id": 12345,
            },
        }
        context.bot_data["calendar"].get_agenda.return_value = agenda_text

        # Mock the current week date
        with patch("model.this_week", return_value=this_week):
            # Call the function
            await sync_agenda(context)

            # Assertions - should not edit the message since it's a different week
            context.bot.edit_message_caption.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_agenda_missing_data(self, mock_context):
        """Test the sync_agenda function when agenda data is missing."""
        # Setup
        context = mock_context
        context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {},  # Missing date and hash
        }

        # Call the function
        await sync_agenda(context)

        # Assertions - should return early without errors
        context.bot.edit_message_caption.assert_not_called()
        context.bot_data["calendar"].get_agenda.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_agenda_on_demand(self, mock_update, mock_context):
        """Test the publish_agenda_on_demand function."""
        # Setup
        update = mock_update
        context = mock_context

        # Mock the publish_agenda function
        with patch(
            "handlers.calendar.agenda.publish_agenda", new=AsyncMock()
        ) as mock_publish:
            # Call the function
            await publish_agenda_on_demand(update, context)

            # Assertions
            mock_publish.assert_called_once_with(context)
