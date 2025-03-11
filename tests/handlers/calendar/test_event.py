"""Tests for the event module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
)

from handlers.calendar.event import (
    create_handlers,
    on_pick_event,
    on_add_event,
    add_event,
    on_edit_title,
    edit_title,
    on_edit_emoji,
    edit_emoji,
    on_edit_description,
    edit_description,
    on_preview,
    on_publish,
    on_delete_event,
    delete_event,
    back,
    cancel,
    exit,
    construct_picker_keyboard,
    sync_agenda,
)
from handlers.calendar.menu import State


class TestEventHandlers:
    """Tests for the event handlers."""

    def test_create_handlers(self):
        """Test the create_handlers function returns a list with handlers."""
        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) > 0

        # Check the first handler is a ConversationHandler
        assert isinstance(handlers[0], ConversationHandler)

        # Check entry points
        entry_points = handlers[0].entry_points
        assert len(entry_points) == 2

        # Check for specific entry points
        add_event_handler = next(
            (
                h
                for h in entry_points
                if isinstance(h, CallbackQueryHandler)
                and h.pattern.pattern == "^" + State.EVENT_ADDING.name + "$"
            ),
            None,
        )
        assert add_event_handler is not None

        pick_event_handler = next(
            (
                h
                for h in entry_points
                if isinstance(h, CallbackQueryHandler)
                and h.pattern.pattern == "^" + State.EVENT.name + ":"
            ),
            None,
        )
        assert pick_event_handler is not None

        # Check states
        states = handlers[0].states
        assert State.EVENT_MENU in states

        # Check EVENT_MENU handlers
        event_menu_handlers = states[State.EVENT_MENU]
        assert len(event_menu_handlers) > 0

        # Check for specific handlers in EVENT_MENU
        edit_title_handler = next(
            (
                h
                for h in event_menu_handlers
                if isinstance(h, CallbackQueryHandler)
                and h.pattern.pattern == "^" + State.EVENT_EDITING_TITLE.name + "$"
            ),
            None,
        )
        assert edit_title_handler is not None

    @pytest.mark.asyncio
    async def test_on_pick_event(self, mock_update, mock_context):
        """Test the on_pick_event function."""
        # Setup
        mock_update.callback_query.data = (
            f"{State.EVENT.name}:123"  # Use a valid integer ID
        )
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.effective_user.send_message = AsyncMock()

        mock_context.bot_data = {
            "calendar": MagicMock(),
        }

        mock_event = MagicMock()
        mock_context.bot_data["calendar"].get_event.return_value = mock_event
        mock_context.bot_data["calendar"].__getitem__.return_value = mock_event
        mock_event.get_full_repr.return_value = "Event details"

        # Call the function
        result = await on_pick_event(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_MENU
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()
        assert mock_context.user_data["current_event"] == mock_event

    @pytest.mark.asyncio
    async def test_on_add_event(self, mock_update, mock_context):
        """Test the on_add_event function."""
        # Setup
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.effective_message.reply_text = AsyncMock()

        # Call the function
        result = await on_add_event(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_WAITING_FOR_TITLE
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_event(self, mock_update, mock_context):
        """Test the add_event function."""
        # Setup
        mock_update.message.text = "Test Event"
        mock_update.callback_query = None
        mock_update.effective_user.send_message = AsyncMock()
        mock_context.bot_data = {
            "calendar": MagicMock(),
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu") as mock_event_menu:
            mock_event_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await add_event(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            mock_context.bot_data["calendar"].add_event.assert_called_once()
            # The add_event function creates a new Event with the title and assigns it to current_event
            assert mock_context.user_data["current_event"] is not None
            # Check that the event has the correct title
            assert mock_context.user_data["current_event"].title == "Test Event"

    @pytest.mark.asyncio
    async def test_on_edit_title(self, mock_update, mock_context):
        """Test the on_edit_title function."""
        # Setup
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }
        mock_context.user_data["current_event"].title = "Current Title"

        # Call the function
        result = await on_edit_title(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_EDITING_TITLE
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_title(self, mock_update, mock_context):
        """Test the edit_title function."""
        # Setup
        mock_update.message.text = "New Title"
        mock_update.callback_query = None
        mock_update.effective_user.send_message = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu") as mock_event_menu:
            mock_event_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await edit_title(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            assert mock_context.user_data["current_event"].title == "New Title"
            mock_event_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_edit_emoji(self, mock_update, mock_context):
        """Test the on_edit_emoji function."""
        # Setup
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }
        mock_context.user_data["current_event"].emoji = "🎉"

        # Call the function
        result = await on_edit_emoji(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_EDITING_EMOJI
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_emoji(self, mock_update, mock_context):
        """Test the edit_emoji function."""
        # Setup
        mock_update.message.text = "🎯"
        mock_update.callback_query = None
        mock_update.effective_user.send_message = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu") as mock_event_menu:
            mock_event_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await edit_emoji(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            assert mock_context.user_data["current_event"].emoji == "🎯"
            mock_event_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_edit_description(self, mock_update, mock_context):
        """Test the on_edit_description function."""
        # Setup
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }
        mock_context.user_data["current_event"].description = "Current Description"

        # Call the function
        result = await on_edit_description(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_EDITING_DESCRIPTION
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_description(self, mock_update, mock_context):
        """Test the edit_description function."""
        # Setup
        mock_update.message.text = "New Description"
        mock_update.callback_query = None
        mock_update.effective_user.send_message = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu") as mock_event_menu:
            mock_event_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await edit_description(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            assert (
                mock_context.user_data["current_event"].description == "New Description"
            )
            mock_event_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_preview(self, mock_update, mock_context, mock_settings):
        """Test the on_preview function."""
        # Setup
        mock_context.user_data = {
            "current_event": MagicMock(),
        }
        mock_context.user_data["current_event"].to_message.return_value = (
            "Event Preview"
        )

        # Mock the callback_query.answer method
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_context.bot.send_message = AsyncMock()
        mock_update.effective_chat.id = 12345

        # Call the function
        result = await on_preview(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_PREVIEW
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_publish(self, mock_update, mock_context, mock_settings):
        """Test the on_publish function."""
        # Setup
        mock_context.user_data = {
            "current_event": MagicMock(),
        }
        mock_context.user_data["current_event"].image = None
        mock_context.user_data["current_event"].post.return_value = {
            "text": "Event Message"
        }

        # Mock the callback_query.answer method
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the bot methods
        mock_context.bot.send_message = AsyncMock()
        mock_message = MagicMock()
        mock_message.link = "https://t.me/channel/123"
        mock_context.bot.send_message.return_value = mock_message

        # Mock the cross_post function
        with patch("handlers.calendar.event.cross_post") as mock_cross_post:
            mock_cross_post.return_value = None

            # Call the function
            result = await on_publish(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_PUBLISHING
            mock_update.callback_query.answer.assert_called_once()
            mock_context.bot.send_message.assert_called_once()
            mock_cross_post.assert_called_once_with(mock_message, mock_context)
            assert (
                mock_context.user_data["current_event"].tg_url
                == "https://t.me/channel/123"
            )
            mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_delete_event(self, mock_update, mock_context):
        """Test the on_delete_event function."""
        # Setup
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }
        mock_context.user_data["current_event"].title = "Test Event"

        # Call the function
        result = await on_delete_event(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_DELETING_CONFIRMATION
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        # Verify that the keyboard contains the delete confirmation buttons
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert "reply_markup" in kwargs
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert len(keyboard) > 0
        assert len(keyboard[0]) > 1
        assert keyboard[0][0].callback_data == State.EVENT_DELETING_CONFIRMATION.name
        assert keyboard[0][1].callback_data == State.EVENT_MENU.name

    @pytest.mark.asyncio
    async def test_delete_event(self, mock_update, mock_context):
        """Test the delete_event function."""
        # Setup
        mock_update.callback_query.data = "yes"
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.effective_user.send_message = AsyncMock()

        mock_context.user_data = {
            "current_event": MagicMock(),
        }
        mock_context.bot_data = {
            "calendar": MagicMock(),
            "agenda": {"date": "2023-01-01", "hash": "hash"},
        }

        # Mock the calendar_menu function
        with patch("handlers.calendar.event.calendar_menu") as mock_calendar_menu:
            mock_calendar_menu.return_value = State.CALENDAR_MENU

            # Call the function
            result = await delete_event(mock_update, mock_context)

            # Assertions
            assert result == State.CALENDAR_MENU
            mock_update.callback_query.answer.assert_called_once()
            mock_context.bot_data["calendar"].delete_event.assert_called_once_with(
                mock_context.user_data["current_event"]
            )
            mock_calendar_menu.assert_called_once_with(
                mock_update, mock_context, "Захід було видалено з календаря."
            )

    @pytest.mark.asyncio
    async def test_delete_event_cancel(self, mock_update, mock_context):
        """Test the on_delete_event function which provides the cancel option."""
        # Setup
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }

        # Call the function
        result = await on_delete_event(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_DELETING_CONFIRMATION
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        # Verify that the keyboard contains the cancel button with the correct callback data
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert "reply_markup" in kwargs
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert len(keyboard) > 0
        assert len(keyboard[0]) > 1
        assert keyboard[0][1].callback_data == State.EVENT_MENU.name

    @pytest.mark.asyncio
    async def test_back(self, mock_update, mock_context):
        """Test the back function."""
        # Setup
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.effective_user.send_message = AsyncMock()

        with patch("handlers.calendar.event.calendar_menu") as mock_calendar_menu:
            mock_calendar_menu.return_value = State.CALENDAR_MENU

            # Call the function
            result = await back(mock_update, mock_context)

            # Assertions
            assert result == State.CALENDAR_MENU
            mock_update.callback_query.answer.assert_called_once()
            mock_calendar_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_cancel(self, mock_update, mock_context):
        """Test the cancel function."""
        # Setup
        mock_update.callback_query = None
        mock_update.effective_user.send_message = AsyncMock()
        mock_context.user_data = {
            "current_event": MagicMock(),
        }
        mock_context.user_data["current_event"].get_full_repr.return_value = (
            "Event details"
        )

        # Call the function
        result = await cancel(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_MENU
        mock_update.effective_user.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_exit(self, mock_update, mock_context):
        """Test the exit function."""
        # Setup
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Call the function
        result = await exit(mock_update, mock_context)

        # Assertions
        assert result == ConversationHandler.END
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

    def test_construct_picker_keyboard(self):
        """Test the construct_picker_keyboard function."""
        # Setup
        value = "test"
        prefix = "prefix:"
        buttons = [
            ("Button 1", MagicMock(name="value1")),
            ("Button 2", MagicMock(name="value2")),
            ("Button 3", MagicMock(name="value3")),
            ("Button 4", MagicMock(name="value4")),
            ("Button 5", MagicMock(name="value5")),
        ]

        # Call the function
        keyboard = construct_picker_keyboard(value, prefix, buttons)

        # Assertions
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0
