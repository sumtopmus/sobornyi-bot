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

    @pytest.fixture
    def mock_agenda(self, mock_context):
        """Common fixture for agenda tests."""
        text = "Agenda text"
        hash = calculate_hash(text)
        this_week_date = date(2023, 1, 1)
        message_id = 12345

        # Setup default bot_data
        mock_context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {
                "date": this_week_date.isoformat(),
                "hash": hash,
                "message_id": message_id,
            },
        }
        mock_context.bot_data["calendar"].get_agenda.return_value = text

        return {
            "text": text,
            "hash": hash,
            "this_week": this_week_date,
            "message_id": message_id,
            "context": mock_context,
        }

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
    async def test_sync_agenda_no_change(self, mock_agenda):
        """Test the sync_agenda function when there's no change in the agenda."""
        # Mock the current week date
        with patch("model.this_week", return_value=mock_agenda["this_week"]):
            # Call the function
            await sync_agenda(mock_agenda["context"])

            # Assertions - should not edit the message
            mock_agenda["context"].bot.edit_message_caption.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_agenda_early_return_on_hash_match(self, mock_agenda):
        """Test that sync_agenda returns early when the hash matches."""
        # Create a spy on the calculate_hash function to verify it's called
        with (
            patch(
                "handlers.calendar.agenda.this_week",
                return_value=mock_agenda["this_week"],
            ),
            patch(
                "handlers.calendar.agenda.calculate_hash", side_effect=calculate_hash
            ) as mock_hash,
        ):
            # Call the function
            await sync_agenda(mock_agenda["context"])
            # Verify calculate_hash was called once with the agenda text
            mock_hash.assert_called_once_with(mock_agenda["text"])
            # Verify that edit_message_caption was not called (early return happened)
            mock_agenda["context"].bot.edit_message_caption.assert_not_called()
            # Verify that the hash in bot_data was not updated (early return happened)
            assert (
                mock_agenda["context"].bot_data["agenda"]["hash"] == mock_agenda["hash"]
            )

    @pytest.mark.asyncio
    async def test_sync_agenda_with_change(self, mock_settings, mock_agenda):
        """Test the sync_agenda function when there's a change in the agenda."""
        # Override with different agenda text
        old_text = "Old agenda text"
        old_hash = calculate_hash(old_text)
        new_text = "New agenda text"

        # Update bot_data for this specific test
        mock_agenda["context"].bot_data["agenda"]["hash"] = old_hash
        mock_agenda["context"].bot_data["calendar"].get_agenda.return_value = new_text

        # Mock the current week date
        with patch(
            "handlers.calendar.agenda.this_week", return_value=mock_agenda["this_week"]
        ):
            # Call the function
            await sync_agenda(mock_agenda["context"])

            # Assertions - should edit the message
            mock_agenda["context"].bot.edit_message_caption.assert_called_once_with(
                chat_id=mock_settings.CHANNEL_USERNAME,
                message_id=mock_agenda["message_id"],
                caption=new_text,
            )
            # Check that the hash was updated
            assert mock_agenda["context"].bot_data["agenda"]["hash"] == calculate_hash(
                new_text
            )

    @pytest.mark.asyncio
    async def test_sync_agenda_different_week(self, mock_agenda):
        """Test the sync_agenda function when it's a different week."""
        # Override with last week's date
        last_week = date(2022, 12, 25)
        mock_agenda["context"].bot_data["agenda"]["date"] = last_week.isoformat()

        # Mock the current week date
        with patch("model.this_week", return_value=mock_agenda["this_week"]):
            # Call the function
            await sync_agenda(mock_agenda["context"])

            # Assertions - should not edit the message since it's a different week
            mock_agenda["context"].bot.edit_message_caption.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_agenda_missing_data(self, mock_agenda):
        """Test the sync_agenda function when agenda data is missing."""
        # Override with empty agenda data
        mock_agenda["context"].bot_data["agenda"] = {}  # Missing date and hash
        # Reset the mock to clear any pre-configured return values
        mock_agenda["context"].bot_data["calendar"].get_agenda.reset_mock()

        # Call the function - should raise KeyError
        with pytest.raises(KeyError):
            await sync_agenda(mock_agenda["context"])

        # Assertions - function should raise exception before these calls
        mock_agenda["context"].bot.edit_message_caption.assert_not_called()
        mock_agenda["context"].bot_data["calendar"].get_agenda.assert_not_called()

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
