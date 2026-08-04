"""Tests for the channel module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message

from handlers.channel import create_handlers, cross_post, edit, post


class TestChannel:
    """Tests for the channel module."""

    def test_create_handlers(self, mock_settings):
        """Test the create_handlers function."""
        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 2

        # Check that the handlers are correctly configured
        assert handlers[0].callback == post
        assert handlers[1].callback == edit

    @pytest.mark.asyncio
    async def test_post_with_text(self, mock_update, mock_context, mock_settings):
        """Test the post function with a text message."""
        # Setup
        mock_update.channel_post = MagicMock()
        mock_update.channel_post.text = "Test message"
        mock_update.channel_post.caption = None
        mock_update.channel_post.pinned_message = None

        # Mock the cross_post function
        with patch("handlers.channel.cross_post", new=AsyncMock()) as mock_cross_post:
            # Call the function
            await post(mock_update, mock_context)

            # Assertions
            mock_cross_post.assert_called_once_with(
                mock_update.channel_post, mock_context
            )

    @pytest.mark.asyncio
    async def test_post_with_caption(self, mock_update, mock_context, mock_settings):
        """Test the post function with a captioned message."""
        # Setup
        mock_update.channel_post = MagicMock()
        mock_update.channel_post.text = None
        mock_update.channel_post.caption = "Test caption"
        mock_update.channel_post.pinned_message = None

        # Mock the cross_post function
        with patch("handlers.channel.cross_post", new=AsyncMock()) as mock_cross_post:
            # Call the function
            await post(mock_update, mock_context)

            # Assertions
            mock_cross_post.assert_called_once_with(
                mock_update.channel_post, mock_context
            )

    @pytest.mark.asyncio
    async def test_post_with_pinned_message_found(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the post function with a pinned message that exists in cross-posts."""
        # Setup
        mock_update.channel_post = MagicMock()
        mock_update.channel_post.text = None
        mock_update.channel_post.caption = None
        mock_update.channel_post.pinned_message = MagicMock()
        mock_update.channel_post.pinned_message.id = 123

        # Setup bot_data with the cross-posted message
        mock_context.bot_data = {"cross-posts": {123: 456}}

        # Call the function
        await post(mock_update, mock_context)

        # Assertions
        mock_context.bot.pin_chat_message.assert_called_once_with(
            mock_settings.CHAT_ID, 456
        )

    @pytest.mark.asyncio
    async def test_post_with_pinned_message_not_found(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the post function with a pinned message that doesn't exist in cross-posts."""
        # Setup
        mock_update.channel_post = MagicMock()
        mock_update.channel_post.text = None
        mock_update.channel_post.caption = None
        mock_update.channel_post.pinned_message = MagicMock()
        mock_update.channel_post.pinned_message.id = 123

        # Setup bot_data without the cross-posted message
        mock_context.bot_data = {"cross-posts": {}}

        # Call the function
        await post(mock_update, mock_context)

        # Assertions
        mock_context.bot.pin_chat_message.assert_not_called()
        # The message ID should be added to the cross-posts dict with None value
        assert mock_context.bot_data["cross-posts"][123] is None

    @pytest.mark.asyncio
    async def test_cross_post_with_text(self, mock_context, mock_settings):
        """Test the cross_post function with a text message."""
        # Setup
        message = MagicMock(spec=Message)
        message.text = "Test message with #announcement"
        message.caption = None
        message.id = 123

        # Setup thread mapping in settings
        mock_settings.TAGS = {"#announcement": "announcements"}
        mock_settings.PRIORITIES = {"announcements": 1}
        mock_settings.TOPICS = {"announcements": 789}

        # Setup the copy method to return a message with an ID
        copied_message = MagicMock()
        copied_message.message_id = 456
        message.copy.return_value = copied_message
        message.copy = AsyncMock(return_value=copied_message)

        # Setup bot_data
        mock_context.bot_data = {"cross-posts": {}}

        # Call the function
        await cross_post(message, mock_context)

        # Assertions
        message.copy.assert_called_once_with(
            mock_settings.CHAT_ID, message_thread_id=789
        )
        assert mock_context.bot_data["cross-posts"][123] == 456

    @pytest.mark.asyncio
    async def test_cross_post_with_caption(self, mock_context, mock_settings):
        """Test the cross_post function with a captioned message."""
        # Setup
        message = MagicMock(spec=Message)
        message.text = None
        message.caption = "Test caption with #news"
        message.id = 123

        # Setup thread mapping in settings
        mock_settings.TAGS = {"#news": "news"}
        mock_settings.PRIORITIES = {"news": 2}
        mock_settings.TOPICS = {"news": 789}

        # Setup the copy method to return a message with an ID
        copied_message = MagicMock()
        copied_message.message_id = 456
        message.copy.return_value = copied_message
        message.copy = AsyncMock(return_value=copied_message)

        # Setup bot_data
        mock_context.bot_data = {"cross-posts": {}}

        # Call the function
        await cross_post(message, mock_context)

        # Assertions
        message.copy.assert_called_once_with(
            mock_settings.CHAT_ID, message_thread_id=789
        )
        assert mock_context.bot_data["cross-posts"][123] == 456

    @pytest.mark.asyncio
    async def test_cross_post_with_multiple_tags(self, mock_context, mock_settings):
        """Test the cross_post function with multiple tags, should use highest priority."""
        # Setup
        message = MagicMock(spec=Message)
        message.text = "Test message with #news and #announcement"
        message.caption = None
        message.id = 123

        # Setup thread mapping in settings with different priorities
        mock_settings.TAGS = {"#news": "news", "#announcement": "announcements"}
        mock_settings.PRIORITIES = {
            "news": 2,
            "announcements": 1,
        }  # Lower number = higher priority
        mock_settings.TOPICS = {"news": 789, "announcements": 987}

        # Setup the copy method to return a message with an ID
        copied_message = MagicMock()
        copied_message.message_id = 456
        message.copy.return_value = copied_message
        message.copy = AsyncMock(return_value=copied_message)

        # Setup bot_data
        mock_context.bot_data = {"cross-posts": {}}

        # Call the function
        await cross_post(message, mock_context)

        # Assertions - should use the announcements thread (higher priority)
        message.copy.assert_called_once_with(
            mock_settings.CHAT_ID, message_thread_id=987
        )
        assert mock_context.bot_data["cross-posts"][123] == 456

    @pytest.mark.asyncio
    async def test_cross_post_without_text_or_caption(
        self, mock_context, mock_settings
    ):
        """Test the cross_post function with neither text nor caption."""
        # Setup
        message = MagicMock(spec=Message)
        message.text = None
        message.caption = None
        message.id = 123

        # Setup bot_data
        mock_context.bot_data = {"cross-posts": {}}

        # Call the function
        await cross_post(message, mock_context)

        # Assertions - should return early without copying
        message.copy.assert_not_called()
        assert 123 not in mock_context.bot_data["cross-posts"]

    @pytest.mark.asyncio
    async def test_cross_post_without_matching_tags(self, mock_context, mock_settings):
        """Test the cross_post function with no matching tags."""
        # Setup
        message = MagicMock(spec=Message)
        message.text = "Test message without any tags"
        message.caption = None
        message.id = 123

        # Setup thread mapping in settings
        mock_settings.TAGS = {"#news": "news", "#announcement": "announcements"}
        mock_settings.PRIORITIES = {"news": 2, "announcements": 1}
        mock_settings.TOPICS = {"news": 789, "announcements": 987}

        # Setup the copy method to return a message with an ID
        copied_message = MagicMock()
        copied_message.message_id = 456
        message.copy.return_value = copied_message
        message.copy = AsyncMock(return_value=copied_message)

        # Setup bot_data
        mock_context.bot_data = {"cross-posts": {}}

        # Call the function
        await cross_post(message, mock_context)

        # Assertions - should copy to the main chat without a thread
        message.copy.assert_called_once_with(
            mock_settings.CHAT_ID, message_thread_id=None
        )
        assert mock_context.bot_data["cross-posts"][123] == 456

    @pytest.mark.asyncio
    async def test_edit_with_text(self, mock_update, mock_context, mock_settings):
        """Test the edit function with a text message."""
        # Setup
        mock_update.edited_channel_post = MagicMock()
        mock_update.edited_channel_post.id = 123
        mock_update.edited_channel_post.text = "Edited text"
        mock_update.edited_channel_post.caption = None
        mock_update.edited_channel_post.entities = []

        # Setup bot_data with the cross-posted message
        mock_context.bot_data = {"cross-posts": {123: 456}}

        # Call the function
        await edit(mock_update, mock_context)

        # Assertions
        mock_context.bot.edit_message_text.assert_called_once_with(
            "Edited text",
            chat_id=mock_settings.CHAT_ID,
            message_id=456,
            entities=[],
            parse_mode=None,
        )
        mock_context.bot.edit_message_caption.assert_not_called()

    @pytest.mark.asyncio
    async def test_edit_with_caption(self, mock_update, mock_context, mock_settings):
        """Test the edit function with a captioned message."""
        # Setup
        mock_update.edited_channel_post = MagicMock()
        mock_update.edited_channel_post.id = 123
        mock_update.edited_channel_post.text = None
        mock_update.edited_channel_post.caption = "Edited caption"
        mock_update.edited_channel_post.caption_entities = []

        # Setup bot_data with the cross-posted message
        mock_context.bot_data = {"cross-posts": {123: 456}}

        # Call the function
        await edit(mock_update, mock_context)

        # Assertions
        mock_context.bot.edit_message_caption.assert_called_once_with(
            chat_id=mock_settings.CHAT_ID,
            message_id=456,
            caption="Edited caption",
            caption_entities=[],
            parse_mode=None,
        )
        mock_context.bot.edit_message_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_edit_message_not_found(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the edit function when the message is not found in cross-posts."""
        # Setup
        mock_update.edited_channel_post = MagicMock()
        mock_update.edited_channel_post.id = 123
        mock_update.edited_channel_post.text = "Edited text"

        # Setup bot_data without the cross-posted message
        mock_context.bot_data = {"cross-posts": {}}

        # Call the function
        await edit(mock_update, mock_context)

        # Assertions
        mock_context.bot.edit_message_text.assert_not_called()
        mock_context.bot.edit_message_caption.assert_not_called()
        # The message ID should be added to the cross-posts dict with None value
        assert mock_context.bot_data["cross-posts"][123] is None
