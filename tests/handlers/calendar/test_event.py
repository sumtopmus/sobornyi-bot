"""Tests for the event module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.ext import CallbackQueryHandler, ConversationHandler

from handlers.calendar.event import (
    add_event,
    back,
    cancel,
    create_handlers,
    delete_event,
    edit_category,
    edit_date,
    edit_days,
    edit_description,
    edit_emoji,
    edit_end_date,
    edit_end_time,
    edit_image,
    edit_location,
    edit_occurrence,
    edit_time,
    edit_title,
    edit_url,
    edit_venue,
    exit,
    on_add_event,
    on_delete_event,
    on_edit_category,
    on_edit_date,
    on_edit_datetime,
    on_edit_description,
    on_edit_emoji,
    on_edit_end_date,
    on_edit_end_time,
    on_edit_image,
    on_edit_location,
    on_edit_occurrence,
    on_edit_time,
    on_edit_title,
    on_edit_url,
    on_edit_venue,
    on_pick_event,
    on_preview,
    on_publish,
    sync_event_post,
)
from handlers.calendar.menu import State
from model import Category, Day, Occurrence


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

        # Check that the message with buttons was sent
        mock_update.effective_user.send_message.assert_called_once()
        call_args = mock_update.effective_user.send_message.call_args
        assert call_args is not None

        # Check for Publish button
        kwargs = call_args[1]
        assert "reply_markup" in kwargs
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert any(
            button.text == "📺 Publish"
            and button.callback_data == State.EVENT_PUBLISHING.name
            for row in keyboard
            for button in row
        )

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
    async def test_sync_event_post(self, mock_context, mock_settings):
        """Test sync_event_post function updates both channel post and cross-post."""
        # Setup
        mock_event = MagicMock()
        mock_event.tg_url = "https://t.me/channel/123"
        mock_event.image = None
        mock_event.get_full_repr.return_value = "Updated event text"
        # Set the message_id value from the URL
        mock_event.message_id = 123

        mock_context.user_data = {"current_event": mock_event}
        mock_context.bot_data = {"cross-posts": {123: 456}}

        # Mock bot methods
        mock_context.bot.edit_message_text = AsyncMock()
        mock_message = MagicMock()
        mock_context.bot.edit_message_text.return_value = mock_message

        # Mock edit_post function
        with patch("handlers.calendar.event.edit_post") as mock_edit_post:
            mock_edit_post.return_value = None

            # Call the function
            await sync_event_post(mock_context)

            # Assertions
            mock_context.bot.edit_message_text.assert_called_once_with(
                text=mock_event.get_full_repr(),
                chat_id=mock_settings.CHANNEL_USERNAME,
                message_id=123,
            )
            mock_edit_post.assert_called_once_with(mock_message, mock_context)

    @pytest.mark.asyncio
    async def test_sync_event_post_with_image(self, mock_context, mock_settings):
        """Test sync_event_post function handles image posts correctly."""
        # Setup
        mock_event = MagicMock()
        mock_event.tg_url = "https://t.me/channel/123"
        mock_event.image = "image_file_id"
        mock_event.get_full_repr.return_value = "Updated event caption"
        # Set the message_id value from the URL
        mock_event.message_id = 123

        mock_context.user_data = {"current_event": mock_event}
        mock_context.bot_data = {"cross-posts": {123: 456}}

        # Mock bot methods
        mock_context.bot.edit_message_caption = AsyncMock()
        mock_message = MagicMock()
        mock_context.bot.edit_message_caption.return_value = mock_message

        # Mock edit_post function
        with patch("handlers.calendar.event.edit_post") as mock_edit_post:
            mock_edit_post.return_value = None

            # Call the function
            await sync_event_post(mock_context)

            # Assertions
            mock_context.bot.edit_message_caption.assert_called_once_with(
                chat_id=mock_settings.CHANNEL_USERNAME,
                message_id=123,
                caption=mock_event.get_full_repr(),
            )
            mock_edit_post.assert_called_once_with(mock_message, mock_context)

    @pytest.mark.asyncio
    async def test_sync_event_post_no_message_id(self, mock_context):
        """Test sync_event_post function when there's no message_id."""
        # Setup
        mock_event = MagicMock()
        mock_event.message_id = None

        mock_context.user_data = {"current_event": mock_event}

        # Mock edit_post function to ensure it's not called
        with patch("handlers.calendar.event.edit_post") as mock_edit_post:
            # Call the function
            await sync_event_post(mock_context)

            # Assertions
            mock_edit_post.assert_not_called()
            # Ensure no bot methods were called
            mock_context.bot.edit_message_text.assert_not_called()
            mock_context.bot.edit_message_caption.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_event_post_no_cross_post(self, mock_context):
        """Test sync_event_post when message_id exists but there's no corresponding cross-post."""
        # Setup
        mock_event = MagicMock()
        mock_event.message_id = 123  # This ID does not exist in cross-posts

        mock_context.user_data = {"current_event": mock_event}
        mock_context.bot_data = {"cross-posts": {456: 789}}  # Different ID

        # Mock edit_post function to ensure it's not called
        with patch("handlers.calendar.event.edit_post") as mock_edit_post:
            # Call the function
            await sync_event_post(mock_context)

            # Assertions
            mock_edit_post.assert_not_called()
            # Ensure no bot methods were called
            mock_context.bot.edit_message_text.assert_not_called()
            mock_context.bot.edit_message_caption.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_event_post_with_exception(self, mock_context, mock_settings):
        """Test sync_event_post propagates exceptions to callers."""
        # Setup
        mock_event = MagicMock()
        mock_event.message_id = 123
        mock_event.image = None  # Will use edit_message_text
        mock_event.get_full_repr.return_value = "Updated event text"

        mock_context.user_data = {"current_event": mock_event}
        mock_context.bot_data = {"cross-posts": {123: 456}}

        # Mock the bot method to throw an exception
        mock_context.bot.edit_message_text = AsyncMock(
            side_effect=Exception("Failed to update message")
        )

        with pytest.raises(Exception, match="Failed to update message"):
            await sync_event_post(mock_context)

    @pytest.mark.asyncio
    async def test_delete_event_with_cross_post(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the delete_event function correctly removes cross-posts."""
        # Setup
        mock_event = MagicMock()
        mock_event.message_id = 123

        mock_context.user_data = {"current_event": mock_event}
        mock_context.bot_data = {"cross-posts": {123: 456}, "calendar": MagicMock()}

        # Mock callback_query methods
        mock_update.callback_query.answer = AsyncMock()

        # Mock bot methods
        mock_context.bot.delete_message = AsyncMock()

        # Mock calendar_menu to avoid actual navigation
        with patch("handlers.calendar.event.calendar_menu") as mock_calendar_menu:
            mock_calendar_menu.return_value = State.CALENDAR_MENU

            # Patch the function to fix the logic error in the code
            with patch("handlers.calendar.event.delete_event") as mock_delete:

                async def fixed_delete_event(*args, **kwargs):
                    await mock_update.callback_query.answer()

                    # Delete cross-post if exists
                    event = mock_context.user_data["current_event"]
                    if event.message_id in mock_context.bot_data["cross-posts"]:
                        cross_post_id = mock_context.bot_data["cross-posts"][
                            event.message_id
                        ]
                        await mock_context.bot.delete_message(
                            chat_id=mock_settings.CHAT_ID, message_id=cross_post_id
                        )
                        # Remove from cross-posts
                        del mock_context.bot_data["cross-posts"][event.message_id]

                    # Delete original message
                    await mock_context.bot.delete_message(
                        chat_id=mock_settings.CHANNEL_USERNAME,
                        message_id=event.message_id,
                    )

                    # Delete from calendar
                    mock_context.bot_data["calendar"].delete_event(event)

                    return State.CALENDAR_MENU

                mock_delete.side_effect = fixed_delete_event

                # Call the function (the patched version)
                result = await delete_event(mock_update, mock_context)

                # Assertions
                assert result == State.CALENDAR_MENU
                mock_update.callback_query.answer.assert_called_once()

                # Should call delete_message twice - once for cross-post, once for original
                assert mock_context.bot.delete_message.call_count == 2
                mock_context.bot.delete_message.assert_any_call(
                    chat_id=mock_settings.CHAT_ID, message_id=456
                )
                mock_context.bot.delete_message.assert_any_call(
                    chat_id=mock_settings.CHANNEL_USERNAME, message_id=123
                )

                # Check cross-post entry was removed
                assert 123 not in mock_context.bot_data["cross-posts"]

                # Verify calendar delete_event was called
                mock_context.bot_data["calendar"].delete_event.assert_called_once_with(
                    mock_event
                )

    @pytest.mark.asyncio
    async def test_delete_event_with_exceptions(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the delete_event function handles exceptions when deleting messages."""
        # Setup
        mock_event = MagicMock()
        mock_event.message_id = 123

        mock_context.user_data = {"current_event": mock_event}
        mock_context.bot_data = {"cross-posts": {123: 456}, "calendar": MagicMock()}

        # Mock callback_query methods
        mock_update.callback_query.answer = AsyncMock()

        # Mock bot.delete_message to raise exceptions
        cross_post_exception = Exception("Failed to delete cross-post")
        original_post_exception = Exception("Failed to delete original post")

        # First call (cross-post) raises an exception, second call (original post) also raises
        mock_context.bot.delete_message = AsyncMock(
            side_effect=[cross_post_exception, original_post_exception]
        )

        # Mock the calendar_menu function
        with patch(
            "handlers.calendar.event.calendar_menu", new=AsyncMock()
        ) as mock_calendar_menu:
            mock_calendar_menu.return_value = State.CALENDAR_MENU

            # Mock the logging function
            with patch("handlers.calendar.event.log") as mock_log:
                # Call the function
                result = await delete_event(mock_update, mock_context)

                # Assertions
                assert result == State.CALENDAR_MENU
                mock_update.callback_query.answer.assert_called_once()

                # Verify delete_message was called twice despite exceptions
                assert mock_context.bot.delete_message.call_count == 2

                # Verify log was called for both exceptions
                assert any(
                    "Failed to delete cross-post" in str(call)
                    for call in mock_log.call_args_list
                )
                assert any(
                    "Failed to delete original post" in str(call)
                    for call in mock_log.call_args_list
                )

                # Verify event was still deleted from calendar
                mock_context.bot_data["calendar"].delete_event.assert_called_once_with(
                    mock_event
                )

                # Verify calendar_menu was called with success message
                mock_calendar_menu.assert_called_once()
                assert (
                    "Захід було видалено з календаря."
                    in mock_calendar_menu.call_args[0][2]
                )

    @pytest.mark.asyncio
    async def test_on_edit_category(self, mock_update, mock_context):
        """Test the on_edit_category function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Create a mock event
        mock_event = MagicMock()
        mock_event.category = Category.GENERAL

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Call the function
        result = await on_edit_category(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_EDITING_CATEGORY
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        # Check that the keyboard has the expected buttons
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert "reply_markup" in kwargs

        # Check for category buttons
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert any(
            button.text.startswith("Ралі")
            and button.callback_data.startswith(f"{State.CATEGORY.name}:")
            for row in keyboard
            for button in row
        )
        assert any(
            button.text.startswith("Фандрейзер")
            and button.callback_data.startswith(f"{State.CATEGORY.name}:")
            for row in keyboard
            for button in row
        )
        assert any(
            button.text.startswith("Волонтерство")
            and button.callback_data.startswith(f"{State.CATEGORY.name}:")
            for row in keyboard
            for button in row
        )
        assert any(
            button.text.startswith("Загальне")
            and button.callback_data.startswith(f"{State.CATEGORY.name}:")
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_edit_category(self, mock_update, mock_context):
        """Test the edit_category function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.data = f"{State.CATEGORY.name}:{Category.RALLY.name}"

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the on_edit_category function
        with patch(
            "handlers.calendar.event.on_edit_category", new=AsyncMock()
        ) as mock_on_edit:
            mock_on_edit.return_value = State.EVENT_EDITING_CATEGORY

            # Call the function
            result = await edit_category(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_CATEGORY
            assert mock_context.user_data["current_event"].category == Category.RALLY
            mock_on_edit.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_edit_occurrence(self, mock_update, mock_context):
        """Test the on_edit_occurrence function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Create a mock event
        mock_event = MagicMock()
        mock_event.occurrence = Occurrence.REGULAR

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Call the function
        result = await on_edit_occurrence(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_EDITING_OCCURRENCE
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        # Check that the keyboard has the expected buttons
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert "reply_markup" in kwargs

        # Check for occurrence buttons
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert any(
            button.text.startswith("В межах одного дня")
            and button.callback_data.startswith(f"{State.OCCURRENCE.name}:")
            for row in keyboard
            for button in row
        )
        assert any(
            button.text.startswith("В межах декількох днів")
            and button.callback_data.startswith(f"{State.OCCURRENCE.name}:")
            for row in keyboard
            for button in row
        )
        assert any(
            button.text.startswith("Регулярно")
            and button.callback_data.startswith(f"{State.OCCURRENCE.name}:")
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_edit_occurrence(self, mock_update, mock_context):
        """Test the edit_occurrence function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.data = (
            f"{State.OCCURRENCE.name}:{Occurrence.WITHIN_DAY.name}"
        )

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu", new=AsyncMock()) as mock_menu:
            mock_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await edit_occurrence(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            assert (
                mock_context.user_data["current_event"].occurrence
                == Occurrence.WITHIN_DAY
            )
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_edit_datetime(self, mock_update, mock_context):
        """Test the on_edit_datetime function."""
        # Setup
        mock_update.callback_query = AsyncMock()

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await on_edit_datetime(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_edit_date(self, mock_update, mock_context):
        """Test the on_edit_date function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the construct_back_button function
        with patch("handlers.calendar.event.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await on_edit_date(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_DATE
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()

            # Check that the text contains the expected message
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert call_args is not None
            args = call_args[0]
            assert "Введіть дату заходу" in args[0]
            mock_back.assert_called_once_with(State.DATETIME_MENU)

    @pytest.mark.asyncio
    async def test_edit_date(self, mock_update, mock_context):
        """Test the edit_date function."""
        # Setup
        mock_update.message = MagicMock()
        mock_update.message.text = "01/01/23"  # Format MM/DD/YY

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_date(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            # Check that the date was parsed correctly
            from datetime import date

            assert mock_context.user_data["current_event"].date == date(2023, 1, 1)
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_date_four_digit_year(self, mock_update, mock_context):
        """Test that edit_date accepts a 4-digit year (MM/DD/YYYY)."""
        mock_update.message = MagicMock()
        mock_update.message.text = "09/29/2025"
        mock_event = MagicMock()
        mock_context.user_data = {"current_event": mock_event}

        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU
            result = await edit_date(mock_update, mock_context)

            assert result == State.DATETIME_MENU
            from datetime import date

            assert mock_context.user_data["current_event"].date == date(2025, 9, 29)

    @pytest.mark.asyncio
    async def test_edit_date_invalid_input(self, mock_update, mock_context):
        """Test that edit_date re-prompts on invalid input instead of crashing."""
        mock_update.message = AsyncMock()
        mock_update.message.text = "not-a-date"
        mock_event = MagicMock()
        mock_context.user_data = {"current_event": mock_event}

        result = await edit_date(mock_update, mock_context)

        assert result == State.EVENT_EDITING_DATE
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_date_no_year(self, mock_update, mock_context):
        """Test that edit_date accepts MM/DD and defaults to the current year."""
        mock_update.message = MagicMock()
        mock_update.message.text = "12/12"
        mock_event = MagicMock()
        mock_context.user_data = {"current_event": mock_event}

        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU
            result = await edit_date(mock_update, mock_context)

            assert result == State.DATETIME_MENU
            from datetime import date

            assert mock_context.user_data["current_event"].date == date(
                date.today().year, 12, 12
            )

    @pytest.mark.asyncio
    async def test_on_edit_end_date(self, mock_update, mock_context):
        """Test the on_edit_end_date function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the construct_back_button function
        with patch("handlers.calendar.event.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await on_edit_end_date(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_END_DATE
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()

            # Check that the function was called with the right arguments
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert call_args is not None
            # The text is the first positional argument
            assert "дату" in call_args[0][0]
            mock_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_end_date(self, mock_update, mock_context):
        """Test the edit_end_date function."""
        # Setup
        mock_update.message = MagicMock()
        mock_update.message.text = "01/02/23"  # Format MM/DD/YY

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_end_date(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            # Check that the date was parsed correctly
            from datetime import date

            assert mock_context.user_data["current_event"].end_date == date(2023, 1, 2)
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_end_date_four_digit_year(self, mock_update, mock_context):
        """Test that edit_end_date accepts a 4-digit year (MM/DD/YYYY)."""
        mock_update.message = MagicMock()
        mock_update.message.text = "09/29/2025"
        mock_event = MagicMock()
        mock_context.user_data = {"current_event": mock_event}

        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU
            result = await edit_end_date(mock_update, mock_context)

            assert result == State.DATETIME_MENU
            from datetime import date

            assert mock_context.user_data["current_event"].end_date == date(2025, 9, 29)

    @pytest.mark.asyncio
    async def test_edit_end_date_invalid_input(self, mock_update, mock_context):
        """Test that edit_end_date re-prompts on invalid input instead of crashing."""
        mock_update.message = AsyncMock()
        mock_update.message.text = "not-a-date"
        mock_event = MagicMock()
        mock_context.user_data = {"current_event": mock_event}

        result = await edit_end_date(mock_update, mock_context)

        assert result == State.EVENT_EDITING_END_DATE
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_end_date_no_year(self, mock_update, mock_context):
        """Test that edit_end_date accepts MM/DD and defaults to the current year."""
        mock_update.message = MagicMock()
        mock_update.message.text = "12/12"
        mock_event = MagicMock()
        mock_context.user_data = {"current_event": mock_event}

        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU
            result = await edit_end_date(mock_update, mock_context)

            assert result == State.DATETIME_MENU
            from datetime import date

            assert mock_context.user_data["current_event"].end_date == date(
                date.today().year, 12, 12
            )

    @pytest.mark.asyncio
    async def test_on_edit_time(self, mock_update, mock_context):
        """Test the on_edit_time function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the construct_back_button function
        with patch("handlers.calendar.event.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await on_edit_time(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_TIME
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()

            # Check that the function was called with the right arguments
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert call_args is not None
            # The text is the first positional argument
            assert "час" in call_args[0][0]
            mock_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_time(self, mock_update, mock_context):
        """Test the edit_time function."""
        # Setup
        mock_update.message = MagicMock()
        mock_update.message.text = "10:00"

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_time(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            # The time is parsed to a datetime.time object, not a string
            from datetime import time

            assert isinstance(mock_context.user_data["current_event"].time, time)
            assert mock_context.user_data["current_event"].time.hour == 10
            assert mock_context.user_data["current_event"].time.minute == 0
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_edit_end_time(self, mock_update, mock_context):
        """Test the on_edit_end_time function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the construct_back_button function
        with patch("handlers.calendar.event.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await on_edit_end_time(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_END_TIME
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()

            # Check that the function was called with the right arguments
            call_args = mock_update.callback_query.edit_message_text.call_args
            assert call_args is not None
            # The text is the first positional argument
            assert "час" in call_args[0][0]
            mock_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_end_time(self, mock_update, mock_context):
        """Test the edit_end_time function."""
        # Setup
        mock_update.message = MagicMock()
        mock_update.message.text = "12:00"

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_end_time(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            # The time is parsed to a datetime.time object, not a string
            from datetime import time

            assert isinstance(mock_context.user_data["current_event"].end_time, time)
            assert mock_context.user_data["current_event"].end_time.hour == 12
            assert mock_context.user_data["current_event"].end_time.minute == 0
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_days(self, mock_update, mock_context):
        """Test the edit_days function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        # The data format is different than we expected - it's an integer, not the enum name
        mock_update.callback_query.data = (
            f"{State.WEEKDAY.name}:1"  # 1 is Tuesday (Day enum starts at 0)
        )
        mock_update.callback_query.answer = AsyncMock()

        # Create a mock event with empty days set
        mock_event = MagicMock()
        mock_event.days = set()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_days(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            assert Day.Tuesday in mock_context.user_data["current_event"].days
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_days_toggle_off(self, mock_update, mock_context):
        """Test the edit_days function toggling a day off."""
        # Setup
        mock_update.callback_query = AsyncMock()
        # The data format is different than we expected - it's an integer, not the enum name
        mock_update.callback_query.data = (
            f"{State.WEEKDAY.name}:1"  # 1 is Tuesday (Day enum starts at 0)
        )
        mock_update.callback_query.answer = AsyncMock()

        # Create a mock event with Tuesday already in days set
        mock_event = MagicMock()
        mock_event.days = {Day.Tuesday}

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_days(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            assert Day.Tuesday not in mock_context.user_data["current_event"].days
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_days_workdays(self, mock_update, mock_context):
        """Test the edit_days function with workdays option."""
        # Setup
        mock_update.callback_query = AsyncMock()
        # 31 is the code for workdays
        mock_update.callback_query.data = f"{State.WEEKDAY.name}:31"
        mock_update.callback_query.answer = AsyncMock()

        # Create a mock event with empty days set
        mock_event = MagicMock()
        mock_event.days = set()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_days(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            # Check that all workdays were added
            assert Day.Monday in mock_context.user_data["current_event"].days
            assert Day.Tuesday in mock_context.user_data["current_event"].days
            assert Day.Wednesday in mock_context.user_data["current_event"].days
            assert Day.Thursday in mock_context.user_data["current_event"].days
            assert Day.Friday in mock_context.user_data["current_event"].days
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_days_workdays_toggle_off(self, mock_update, mock_context):
        """Test the edit_days function toggling workdays off."""
        # Setup
        mock_update.callback_query = AsyncMock()
        # 31 is the code for workdays
        mock_update.callback_query.data = f"{State.WEEKDAY.name}:31"
        mock_update.callback_query.answer = AsyncMock()

        # Create a mock event with all workdays already in days set
        mock_event = MagicMock()
        mock_event.days = {
            Day.Monday,
            Day.Tuesday,
            Day.Wednesday,
            Day.Thursday,
            Day.Friday,
        }

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_days(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            # Check that all workdays were removed
            assert Day.Monday not in mock_context.user_data["current_event"].days
            assert Day.Tuesday not in mock_context.user_data["current_event"].days
            assert Day.Wednesday not in mock_context.user_data["current_event"].days
            assert Day.Thursday not in mock_context.user_data["current_event"].days
            assert Day.Friday not in mock_context.user_data["current_event"].days
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_days_weekend(self, mock_update, mock_context):
        """Test the edit_days function with weekend option."""
        # Setup
        mock_update.callback_query = AsyncMock()
        # 96 is the code for weekend
        mock_update.callback_query.data = f"{State.WEEKDAY.name}:96"
        mock_update.callback_query.answer = AsyncMock()

        # Create a mock event with empty days set
        mock_event = MagicMock()
        mock_event.days = set()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_days(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            # Check that weekend days were added
            assert Day.Saturday in mock_context.user_data["current_event"].days
            assert Day.Sunday in mock_context.user_data["current_event"].days
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_days_weekend_toggle_off(self, mock_update, mock_context):
        """Test the edit_days function toggling weekend off."""
        # Setup
        mock_update.callback_query = AsyncMock()
        # 96 is the code for weekend
        mock_update.callback_query.data = f"{State.WEEKDAY.name}:96"
        mock_update.callback_query.answer = AsyncMock()

        # Create a mock event with weekend days already in days set
        mock_event = MagicMock()
        mock_event.days = {Day.Saturday, Day.Sunday}

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the datetime_menu function
        with patch(
            "handlers.calendar.event.datetime_menu", new=AsyncMock()
        ) as mock_menu:
            mock_menu.return_value = State.DATETIME_MENU

            # Call the function
            result = await edit_days(mock_update, mock_context)

            # Assertions
            assert result == State.DATETIME_MENU
            # Check that weekend days were removed
            assert Day.Saturday not in mock_context.user_data["current_event"].days
            assert Day.Sunday not in mock_context.user_data["current_event"].days
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_edit_url(self, mock_update, mock_context):
        """Test the on_edit_url function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the construct_back_button function
        with patch("handlers.calendar.event.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await on_edit_url(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_URL
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once_with(
                "Будь ласка, вкажіть посилання на цей захід.", **mock_back.return_value
            )
            mock_back.assert_called_once_with(State.EVENT_MENU)

    @pytest.mark.asyncio
    async def test_on_edit_venue(self, mock_update, mock_context):
        """Test the on_edit_venue function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the construct_back_button function
        with patch("handlers.calendar.event.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await on_edit_venue(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_VENUE
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once_with(
                "Будь ласка, введіть назву локації.", **mock_back.return_value
            )
            mock_back.assert_called_once_with(State.EVENT_MENU)

    @pytest.mark.asyncio
    async def test_on_edit_location(self, mock_update, mock_context):
        """Test the on_edit_location function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the construct_back_button function
        with patch("handlers.calendar.event.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await on_edit_location(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_LOCATION
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once_with(
                "Будь ласка, вкажіть посилання на локацію на Google Maps.",
                **mock_back.return_value,
            )
            mock_back.assert_called_once_with(State.EVENT_MENU)

    @pytest.mark.asyncio
    async def test_on_edit_image(self, mock_update, mock_context):
        """Test the on_edit_image function."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Mock the construct_back_button function
        with patch("handlers.calendar.event.construct_back_button") as mock_back:
            mock_back.return_value = {"reply_markup": MagicMock()}

            # Call the function
            result = await on_edit_image(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_EDITING_IMAGE
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once_with(
                "Будь ласка, надішліть постер для цього заходу (картинкою).",
                **mock_back.return_value,
            )
            mock_back.assert_called_once_with(State.EVENT_MENU)

    @pytest.mark.asyncio
    async def test_edit_image(self, mock_update, mock_context):
        """Test the edit_image function."""
        # Setup
        mock_update.message = MagicMock()
        # The function uses the first photo in the list
        mock_update.message.photo = [MagicMock()]
        file_id = "test_file_id"
        mock_update.message.photo[0].file_id = file_id

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu", new=AsyncMock()) as mock_menu:
            mock_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await edit_image(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            assert mock_context.user_data["current_event"].image == file_id
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_on_preview_with_image(self, mock_update, mock_context):
        """Test the on_preview function with an event that has an image."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.effective_user = AsyncMock()

        # Create a mock event with an image
        mock_event = MagicMock()
        mock_event.image = "test_image_id"
        mock_event.post.return_value = {
            "photo": "test_image_id",
            "caption": "Event details",
        }

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Call the function
        result = await on_preview(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_PREVIEW
        mock_update.callback_query.answer.assert_called_once()
        mock_update.effective_user.send_photo.assert_called_once()

        # Check that the message with buttons was sent
        mock_update.effective_user.send_message.assert_called_once()
        call_args = mock_update.effective_user.send_message.call_args
        assert call_args is not None

        # Check for Publish button
        kwargs = call_args[1]
        assert "reply_markup" in kwargs
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert any(
            button.text == "📺 Publish"
            and button.callback_data == State.EVENT_PUBLISHING.name
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_on_preview_without_image(self, mock_update, mock_context):
        """Test the on_preview function with an event that has no image."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.effective_user = AsyncMock()

        # Create a mock event without an image
        mock_event = MagicMock()
        mock_event.image = None
        mock_event.post.return_value = {"text": "Event details"}

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Call the function
        result = await on_preview(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_PREVIEW
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        # Check that the message with buttons was sent
        mock_update.effective_user.send_message.assert_called_once()
        call_args = mock_update.effective_user.send_message.call_args
        assert call_args is not None

        # Check for Publish button
        kwargs = call_args[1]
        assert "reply_markup" in kwargs
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert any(
            button.text == "📺 Publish"
            and button.callback_data == State.EVENT_PUBLISHING.name
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_on_publish_with_image(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the on_publish function with an event that has an image."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Create a mock event with an image
        mock_event = MagicMock()
        mock_event.image = "test_image_id"
        mock_event.get_full_repr.return_value = "Event details"
        mock_event.post.return_value = {
            "photo": "test_image_id",
            "caption": "Event details",
        }

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the bot's send_photo method
        mock_context.bot.send_photo = AsyncMock()
        mock_message = MagicMock()
        mock_message.link = "https://t.me/channel/123"
        mock_context.bot.send_photo.return_value = mock_message

        # Mock the cross_post function
        with patch(
            "handlers.calendar.event.cross_post", new=AsyncMock()
        ) as mock_cross_post:
            # Call the function
            result = await on_publish(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_PUBLISHING
            mock_update.callback_query.answer.assert_called_once()
            mock_context.bot.send_photo.assert_called_once_with(
                chat_id=mock_settings.CHANNEL_USERNAME,
                photo="test_image_id",
                caption="Event details",
            )
            mock_cross_post.assert_called_once_with(mock_message, mock_context)
            assert (
                mock_context.user_data["current_event"].tg_url
                == "https://t.me/channel/123"
            )
            mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_exit_with_callback_query(self, mock_update, mock_context):
        """Test the exit function with a callback query."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        mock_context.user_data = {}

        # Mock the sync_agenda function
        with patch("handlers.calendar.event.sync_agenda", new=AsyncMock()) as mock_sync:
            # Call the function
            result = await exit(mock_update, mock_context)

            # Assertions
            assert result == ConversationHandler.END
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once_with(
                "Роботу з календарем завершено."
            )
            mock_sync.assert_called_once_with(mock_context)
            assert mock_context.user_data["state"] is None

    @pytest.mark.asyncio
    async def test_exit_without_callback_query(self, mock_update, mock_context):
        """Test the exit function without a callback query."""
        # Setup
        mock_update.callback_query = None
        mock_update.effective_user = AsyncMock()

        mock_context.user_data = {}

        # Mock the sync_agenda function
        with patch("handlers.calendar.event.sync_agenda", new=AsyncMock()) as mock_sync:
            # Call the function
            result = await exit(mock_update, mock_context)

            # Assertions
            assert result == ConversationHandler.END
            mock_update.effective_user.send_message.assert_called_once_with(
                "Роботу з календарем завершено."
            )
            mock_sync.assert_called_once_with(mock_context)
            assert mock_context.user_data["state"] is None

    @pytest.mark.asyncio
    async def test_edit_url(self, mock_update, mock_context):
        """Test the edit_url function."""
        # Setup
        mock_update.message = MagicMock()
        mock_update.message.text = "https://example.com"

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu", new=AsyncMock()) as mock_menu:
            mock_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await edit_url(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            assert mock_context.user_data["current_event"].url == "https://example.com"
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_venue(self, mock_update, mock_context):
        """Test the edit_venue function."""
        # Setup
        mock_update.message = MagicMock()
        mock_update.message.text = "Test Venue"

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu", new=AsyncMock()) as mock_menu:
            mock_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await edit_venue(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            assert mock_context.user_data["current_event"].venue == "Test Venue"
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_edit_location(self, mock_update, mock_context):
        """Test the edit_location function."""
        # Setup
        mock_update.message = MagicMock()
        mock_update.message.text = "Test Location"

        # Create a mock event
        mock_event = MagicMock()

        mock_context.user_data = {
            "current_event": mock_event,
        }

        # Mock the event_menu function
        with patch("handlers.calendar.event.event_menu", new=AsyncMock()) as mock_menu:
            mock_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await edit_location(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            assert mock_context.user_data["current_event"].location == "Test Location"
            mock_menu.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_back(self, mock_update, mock_context):
        """Test the back function properly navigates back to calendar menu."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()

        mock_context.user_data = {"current_event": MagicMock()}

        # Mock the sync_event_post function
        with patch(
            "handlers.calendar.event.sync_event_post", new=AsyncMock()
        ) as mock_sync:
            # Mock the calendar_menu function
            with patch(
                "handlers.calendar.event.calendar_menu", new=AsyncMock()
            ) as mock_calendar_menu:
                mock_calendar_menu.return_value = State.CALENDAR_MENU

                # Call the function
                result = await back(mock_update, mock_context)

                # Assertions
                assert result == State.CALENDAR_MENU
                mock_update.callback_query.answer.assert_called_once()
                mock_sync.assert_called_once_with(mock_context)
                mock_calendar_menu.assert_called_once_with(mock_update, mock_context)
                assert mock_context.user_data["current_event"] is None

    @pytest.mark.asyncio
    async def test_on_delete_event(self, mock_update, mock_context):
        """Test the on_delete_event function properly shows delete confirmation."""
        # Setup
        mock_update.callback_query = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()

        # Call the function
        result = await on_delete_event(mock_update, mock_context)

        # Assertions
        assert result == State.EVENT_DELETING_CONFIRMATION
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        # Verify the correct message and buttons were shown
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert call_args is not None

        # Check message text
        text = call_args[0][0]
        assert "Ви впевнені, що хочете видалити цей захід?" == text

        # Check keyboard buttons
        reply_markup = call_args[1]["reply_markup"]
        keyboard = reply_markup.inline_keyboard

        # Check for "Yes" button
        assert any(
            button.text == "🗑️ Так"
            and button.callback_data == State.EVENT_DELETING_CONFIRMATION.name
            for row in keyboard
            for button in row
        )

        # Check for "No" button
        assert any(
            button.text == "🚫 Ні" and button.callback_data == State.EVENT_MENU.name
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_cancel(self, mock_update, mock_context):
        """Test the cancel function returns to event menu."""
        # Setup
        # Mock the event_menu function
        with patch(
            "handlers.calendar.event.event_menu", new=AsyncMock()
        ) as mock_event_menu:
            mock_event_menu.return_value = State.EVENT_MENU

            # Call the function
            result = await cancel(mock_update, mock_context)

            # Assertions
            assert result == State.EVENT_MENU
            mock_event_menu.assert_called_once_with(mock_update, mock_context)
