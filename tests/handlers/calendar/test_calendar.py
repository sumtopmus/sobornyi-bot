"""Tests for the calendar module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from handlers.calendar.calendar import (
    create_handlers,
    on_edit_event,
    on_edit_image,
    edit_image,
    on_agenda_preview,
    on_agenda_publish,
    on_cleanup,
    on_find_event,
    find_event,
    back,
    cancel,
    timeout,
    exit,
)
from handlers.calendar.menu import State


class TestCalendar:
    """Tests for the calendar module."""

    def test_create_handlers(self):
        """Test the create_handlers function."""
        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 1
        assert handlers[0].name == "calendar_menu"
        assert handlers[0].persistent is True
        assert handlers[0].conversation_timeout is not None

        # Check entry points
        assert len(handlers[0].entry_points) == 1
        # The commands attribute is a frozenset, not a list
        assert "calendar" in handlers[0].entry_points[0].commands

        # Check states
        assert State.CALENDAR_MENU in handlers[0].states
        assert State.EVENT_PICKING in handlers[0].states
        assert State.EVENT_FINDING in handlers[0].states
        assert State.EVENT_NOT_FOUND in handlers[0].states
        assert State.AGENDA_EDITING_IMAGE in handlers[0].states
        assert State.AGENDA_PREVIEW in handlers[0].states
        assert ConversationHandler.TIMEOUT in handlers[0].states

        # Check fallbacks
        assert len(handlers[0].fallbacks) == 4

    @pytest.mark.asyncio
    async def test_on_edit_event(self, mock_update, mock_context):
        """Test the on_edit_event function."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()

        context.bot_data = {
            "calendar": MagicMock(),
        }
        context.bot_data["calendar"].items.return_value = []

        # Mock the events_menu function to avoid PythonCalendar.get_this_week call
        with patch("handlers.calendar.calendar.events_menu") as mock_events_menu:
            mock_events_menu.return_value = {
                "text": "Events menu",
                "reply_markup": MagicMock(),
            }

            # Call the function
            result = await on_edit_event(update, context)

            # Assertions
            assert result == State.EVENT_PICKING
            update.callback_query.answer.assert_called_once()
            update.callback_query.edit_message_text.assert_called_once()
            mock_events_menu.assert_called_once_with(
                context.bot_data["calendar"].items()
            )

    @pytest.mark.asyncio
    async def test_on_edit_image(self, mock_update, mock_context):
        """Test the on_edit_image function."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()

        # Call the function
        result = await on_edit_image(update, context)

        # Assertions
        assert result == State.AGENDA_EDITING_IMAGE
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once_with(
            "Будь ласка, завантажте фото (картинкою)."
        )

    @pytest.mark.asyncio
    async def test_edit_image(self, mock_update, mock_context):
        """Test the edit_image function."""
        # Setup
        update = mock_update
        context = mock_context

        # Mock the photo
        update.message = MagicMock()
        update.message.photo = [MagicMock(), MagicMock()]
        update.message.photo[-1].file_id = "test_file_id"

        context.bot_data = {
            "agenda": {},
            "calendar": MagicMock(),
        }

        # Mock the calendar_menu function
        with patch(
            "handlers.calendar.calendar.calendar_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.CALENDAR_MENU

            # Call the function
            result = await edit_image(update, context)

            # Assertions
            assert result == State.CALENDAR_MENU
            assert context.bot_data["agenda"]["image"] == "test_file_id"
            mock_menu.assert_called_once_with(update, context)

    @pytest.mark.asyncio
    async def test_on_agenda_preview(self, mock_update, mock_context, mock_settings):
        """Test the on_agenda_preview function with a custom image."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {"image": "custom_image_id"},
        }
        context.bot_data["calendar"].get_agenda.return_value = "Agenda text"

        # Call the function
        result = await on_agenda_preview(update, context)

        # Assertions
        assert result == State.AGENDA_PREVIEW
        update.callback_query.answer.assert_called_once()
        update.effective_user.send_photo.assert_called_once_with(
            "custom_image_id", "Agenda text"
        )

        # Check that the message with buttons was sent
        update.effective_user.send_message.assert_called_once()
        call_args = update.effective_user.send_message.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert "reply_markup" in kwargs
        assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)

        # Check for Publish button
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert any(
            button.text == "📺 Publish"
            and button.callback_data == State.AGENDA_PUBLISHING.name
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_on_agenda_preview_with_default_image(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the on_agenda_preview function with the default image."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {"image": None},
        }
        context.bot_data["calendar"].get_agenda.return_value = "Agenda text"

        # Call the function
        result = await on_agenda_preview(update, context)

        # Assertions
        assert result == State.AGENDA_PREVIEW
        update.effective_user.send_photo.assert_called_once_with(
            mock_settings.DEFAULT_AGENDA_IMAGE, "Agenda text"
        )

    @pytest.mark.asyncio
    async def test_on_agenda_publish(self, mock_update, mock_context):
        """Test the on_agenda_publish function."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()

        # Mock the publish_agenda_on_demand function
        with patch(
            "handlers.calendar.calendar.publish_agenda_on_demand", new=AsyncMock()
        ) as mock_publish:
            # Mock the calendar_menu function
            with patch(
                "handlers.calendar.calendar.calendar_menu", new=AsyncMock()
            ) as mock_menu:
                mock_menu.return_value = State.CALENDAR_MENU

                # Call the function
                result = await on_agenda_publish(update, context)

                # Assertions
                assert result == State.CALENDAR_MENU
                update.callback_query.answer.assert_called_once()
                mock_publish.assert_called_once_with(update, context)
                mock_menu.assert_called_once_with(
                    update, context, prefix_text="Порядок тижневий було опубліковано."
                )

    @pytest.mark.asyncio
    async def test_on_cleanup(self, mock_update, mock_context):
        """Test the on_cleanup function."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()

        context.bot_data = {
            "calendar": MagicMock(),
        }

        # Mock the sync_agenda function
        with patch(
            "handlers.calendar.calendar.sync_agenda", new=AsyncMock()
        ) as mock_sync:
            # Mock the calendar_menu function
            with patch(
                "handlers.calendar.calendar.calendar_menu", new=AsyncMock()
            ) as mock_menu:
                mock_menu.return_value = State.CALENDAR_MENU

                # Call the function
                result = await on_cleanup(update, context)

                # Assertions
                assert result == State.CALENDAR_MENU
                context.bot_data["calendar"].remove_past_events.assert_called_once()
                mock_sync.assert_called_once_with(context)
                mock_menu.assert_called_once_with(
                    update,
                    context,
                    prefix_text="Минулі події було видалено та порядок оновлено.",
                )

    @pytest.mark.asyncio
    async def test_on_find_event(self, mock_update, mock_context):
        """Test the on_find_event function."""
        # Setup
        update = mock_update
        context = mock_context

        # Mock the update_menu function
        with patch(
            "handlers.calendar.calendar.update_menu", new=AsyncMock()
        ) as mock_update_menu:
            # Call the function
            result = await on_find_event(update, context)

            # Assertions
            assert result == State.EVENT_FINDING
            mock_update_menu.assert_called_once()
            args = mock_update_menu.call_args[0]
            assert args[0] == update
            assert "text" in args[1]
            assert "Введіть назву події" in args[1]["text"]

    @pytest.mark.asyncio
    async def test_find_event_with_results(self, mock_update, mock_context):
        """Test the find_event function with matching events."""
        # Setup
        update = mock_update
        context = mock_context
        update.message = MagicMock()
        update.message.text = "test event"
        update.effective_user = AsyncMock()

        # Create mock events
        event1 = MagicMock()
        event1.title = "Test Event 1"

        event2 = MagicMock()
        event2.title = "Another Test Event"

        event3 = MagicMock()
        event3.title = "Unrelated Event"

        context.bot_data = {
            "calendar": MagicMock(),
        }
        context.bot_data["calendar"].items.return_value = [
            (1, event1),
            (2, event2),
            (3, event3),
        ]

        # Mock the events_menu function to avoid PythonCalendar.get_this_week call
        with patch("handlers.calendar.calendar.events_menu") as mock_events_menu:
            mock_events_menu.return_value = {
                "text": "Events menu",
                "reply_markup": MagicMock(),
            }

            # Call the function
            result = await find_event(update, context)

            # Assertions
            assert result == State.EVENT_PICKING
            update.effective_user.send_message.assert_called_once()

            # Check that events_menu was called with the correct events (containing "test" in title)
            mock_events_menu.assert_called_once()
            # Get the first argument (events) passed to events_menu
            events_arg = mock_events_menu.call_args[0][0]
            # Convert to dict for easier testing
            events_dict = dict(events_arg)
            assert len(events_dict) == 2
            assert 1 in events_dict  # event1 has "Test" in title
            assert 2 in events_dict  # event2 has "Test" in title
            assert 3 not in events_dict  # event3 doesn't have "test" in title

    @pytest.mark.asyncio
    async def test_find_event_without_results(self, mock_update, mock_context):
        """Test the find_event function without matching events."""
        # Setup
        update = mock_update
        context = mock_context
        update.message = MagicMock()
        update.message.text = "nonexistent event"
        update.effective_user = AsyncMock()

        context.bot_data = {
            "calendar": MagicMock(),
        }
        context.bot_data["calendar"].items.return_value = [
            (1, MagicMock(title="Unrelated Event")),
        ]

        # Mock the construct_back_button function
        with patch("handlers.calendar.calendar.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await find_event(update, context)

            # Assertions
            assert result == State.EVENT_NOT_FOUND
            update.effective_user.send_message.assert_called_once()
            assert (
                "Подій не знайдено"
                in update.effective_user.send_message.call_args[0][0]
            )
            mock_back.assert_called_once_with(State.EVENT_EDITING)

    @pytest.mark.asyncio
    async def test_back(self, mock_update, mock_context):
        """Test the back function."""
        # Setup
        update = mock_update
        context = mock_context

        # Mock the calendar_menu function
        with patch(
            "handlers.calendar.calendar.calendar_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.CALENDAR_MENU

            # Call the function
            result = await back(update, context)

            # Assertions
            assert result == State.CALENDAR_MENU
            mock_menu.assert_called_once_with(update, context)

    @pytest.mark.asyncio
    async def test_cancel(self, mock_update, mock_context):
        """Test the cancel function."""
        # Setup
        update = mock_update
        context = mock_context

        # Mock the calendar_menu function
        with patch(
            "handlers.calendar.calendar.calendar_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.CALENDAR_MENU

            # Call the function
            result = await cancel(update, context)

            # Assertions
            assert result == State.CALENDAR_MENU
            mock_menu.assert_called_once_with(update, context, "Операцію скасовано.")

    @pytest.mark.asyncio
    async def test_timeout_with_callback_query(self, mock_update, mock_context):
        """Test the timeout function with a callback query."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        context.user_data = {}

        # Mock the sync_agenda function
        with patch(
            "handlers.calendar.calendar.sync_agenda", new=AsyncMock()
        ) as mock_sync:
            # Call the function
            result = await timeout(update, context)

            # Assertions
            assert result == ConversationHandler.END
            mock_sync.assert_called_once_with(context)
            update.callback_query.edit_message_text.assert_called_once()
            # Check that the text contains the expected message
            text = update.callback_query.edit_message_text.call_args[1]["text"]
            assert "неактивні протягом" in text
            assert context.user_data["state"] is None

    @pytest.mark.asyncio
    async def test_timeout_without_callback_query(self, mock_update, mock_context):
        """Test the timeout function without a callback query."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = None
        update.effective_user = AsyncMock()
        context.user_data = {}

        # Set up the send_message mock to return a value
        update.effective_user.send_message.return_value = MagicMock()

        # Mock the sync_agenda function
        with patch(
            "handlers.calendar.calendar.sync_agenda", new=AsyncMock()
        ) as mock_sync:
            # Call the function
            result = await timeout(update, context)

            # Assertions
            assert result == ConversationHandler.END
            mock_sync.assert_called_once_with(context)
            update.effective_user.send_message.assert_called_once()

            # Check that the text contains the expected message
            # The call_args structure might be different than expected, so let's check the kwargs
            call_args = update.effective_user.send_message.call_args
            assert call_args is not None

            # Check if the text is in the first positional argument
            if len(call_args[0]) > 0:
                assert "неактивні протягом" in call_args[0][0]
            # Or check if it's in the keyword arguments
            elif "text" in call_args[1]:
                assert "неактивні протягом" in call_args[1]["text"]

            assert context.user_data["state"] is None

    @pytest.mark.asyncio
    async def test_exit(self, mock_update, mock_context):
        """Test the exit function."""
        # Setup
        update = mock_update
        context = mock_context
        context.user_data = {}

        # Mock the sync_agenda function
        with patch(
            "handlers.calendar.calendar.sync_agenda", new=AsyncMock()
        ) as mock_sync:
            # Mock the update_menu function
            with patch(
                "handlers.calendar.calendar.update_menu", new=AsyncMock()
            ) as mock_update_menu:
                # Call the function
                result = await exit(update, context)

                # Assertions
                assert result == ConversationHandler.END
                mock_sync.assert_called_once_with(context)
                mock_update_menu.assert_called_once()
                assert (
                    "Роботу з календарем завершено"
                    in mock_update_menu.call_args[0][1]["text"]
                )
                assert context.user_data["state"] is None
