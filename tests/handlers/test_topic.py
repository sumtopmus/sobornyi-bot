"""Tests for the topic module."""

import logging
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from handlers.topic import create_handlers, move, offtop, topic


class TestTopic:
    """Tests for the topic module."""

    def test_create_handlers(self, mock_settings):
        """Test the create_handlers function."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.ADMINS = ["admin1", "admin2"]

        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 2

        # Check that the handlers are correctly configured
        assert handlers[0].callback == topic
        assert handlers[1].callback == offtop

        # Check that the filters are applied (without checking specific attributes)
        # We can't directly check filter attributes as they're complex objects
        assert handlers[0].filters is not None
        assert handlers[1].filters is not None

    @pytest.mark.asyncio
    async def test_topic_with_valid_args(self, mock_update, mock_context):
        """Test the topic function with valid arguments."""
        # Setup
        mock_context.args = ["test_topic"]

        # Mock the offtop function
        with patch("handlers.topic.offtop", AsyncMock()) as mock_offtop, patch(
            "handlers.topic.utils.log"
        ) as mock_log:
            # Call the function
            await topic(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("func: topic")
            mock_offtop.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_topic_with_invalid_args(self, mock_update, mock_context):
        """Test the topic function with invalid arguments."""
        # Setup
        mock_context.args = []  # No arguments

        # Mock the utils.log function
        with patch("handlers.topic.utils.log") as mock_log:
            # Call the function
            await topic(mock_update, mock_context)

            # Assertions
            assert mock_log.call_count == 2
            mock_log.assert_has_calls(
                [call("func: topic"), call("invalid number of arguments", logging.INFO)]
            )

    @pytest.mark.asyncio
    async def test_offtop_no_args(self, mock_update, mock_context, mock_settings):
        """Test the offtop function with no arguments."""
        # Setup
        mock_context.args = []
        mock_settings.TOPICS = {"offtop": 123456}

        # Mock the move function
        with patch("handlers.topic.move", AsyncMock()) as mock_move, patch(
            "handlers.topic.utils.log"
        ) as mock_log:
            # Call the function
            await offtop(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("func: offtop")
            mock_move.assert_called_once_with(mock_update, mock_context, 123456, True)

    @pytest.mark.asyncio
    async def test_offtop_with_known_topic(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the offtop function with a known topic."""
        # Setup
        mock_context.args = ["test_topic"]
        mock_settings.TOPICS = {"offtop": 123456, "test_topic": 789012}

        # Mock the move function
        with patch("handlers.topic.move", AsyncMock()) as mock_move, patch(
            "handlers.topic.utils.log"
        ) as mock_log:
            # Call the function
            await offtop(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("func: offtop")
            mock_move.assert_called_once_with(mock_update, mock_context, 789012, True)

    @pytest.mark.asyncio
    async def test_offtop_with_unknown_topic(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the offtop function with an unknown topic."""
        # Setup
        mock_context.args = ["unknown_topic"]
        mock_settings.TOPICS = {"offtop": 123456}

        # Mock the utils.log function
        with patch("handlers.topic.utils.log") as mock_log:
            # Call the function
            await offtop(mock_update, mock_context)

            # Assertions
            assert mock_log.call_count == 2
            mock_log.assert_has_calls(
                [
                    call("func: offtop"),
                    call(
                        "topic unknown_topic is unknown: {'offtop': 123456, 'unknown_topic': -1}",
                        logging.INFO,
                    ),
                ]
            )

    @pytest.mark.asyncio
    async def test_offtop_with_too_many_args(self, mock_update, mock_context):
        """Test the offtop function with too many arguments."""
        # Setup
        mock_context.args = ["topic1", "topic2"]

        # Mock the utils.log function
        with patch("handlers.topic.utils.log") as mock_log:
            # Call the function
            await offtop(mock_update, mock_context)

            # Assertions
            assert mock_log.call_count == 2
            mock_log.assert_has_calls(
                [
                    call("func: offtop"),
                    call("invalid number of arguments", logging.INFO),
                ]
            )

    @pytest.mark.asyncio
    async def test_move_with_reply(self, mock_update, mock_context, mock_settings):
        """Test the move function with reply_to_message."""
        # Setup
        destination_thread_id = 123456
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 789012}

        # Create mock messages
        mock_update.message = MagicMock()
        mock_update.message.reply_to_message = MagicMock()
        mock_update.message.reply_to_message.from_user = MagicMock()
        mock_update.message.reply_to_message.from_user.id = 987654
        mock_update.message.reply_to_message.has_protected_content = False
        mock_update.message.reply_to_message.forward = AsyncMock(
            return_value=MagicMock()
        )
        mock_update.message.reply_to_message.delete = AsyncMock()
        mock_update.message.delete = AsyncMock()

        # Mock mention
        with patch("handlers.topic.mention", return_value="@user") as mock_mention:
            # Call the function
            result = await move(mock_update, mock_context, destination_thread_id, True)

            # Assertions
            mock_mention.assert_called_once_with(
                mock_update.message.reply_to_message.from_user
            )
            mock_context.bot.sendMessage.assert_called_once_with(
                chat_id=-1001234567890,
                message_thread_id=destination_thread_id,
                text="@user, вас було переміщено у відповідну гілку.\n\n⬇️ продовжуйте дискусію тут ⬇️",
            )
            mock_update.message.reply_to_message.forward.assert_called_once_with(
                -1001234567890, message_thread_id=destination_thread_id
            )
            mock_update.message.delete.assert_called_once()
            mock_update.message.reply_to_message.delete.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_move_to_welcome_topic(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the move function to welcome topic."""
        # Setup
        destination_thread_id = 789012
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 789012}

        # Create mock messages
        mock_update.message = MagicMock()
        mock_update.message.from_user = MagicMock()
        mock_update.message.from_user.id = 987654
        mock_update.message.has_protected_content = False
        mock_update.message.forward = AsyncMock(return_value=MagicMock())
        mock_update.message.delete = AsyncMock()

        # Mock mention
        with patch("handlers.topic.mention", return_value="@user") as mock_mention:
            # Call the function
            result = await move(mock_update, mock_context, destination_thread_id, False)

            # Assertions
            mock_mention.assert_called_once_with(mock_update.message.from_user)
            mock_context.bot.sendMessage.assert_called_once_with(
                chat_id=-1001234567890,
                message_thread_id=destination_thread_id,
                text="@user, вас було переміщено у відповідну гілку.\n\n⬇️ представтеся тут ⬇️",
            )
            mock_update.message.forward.assert_called_once_with(
                -1001234567890, message_thread_id=destination_thread_id
            )
            mock_update.message.delete.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_move_with_protected_content(
        self, mock_update, mock_context, mock_settings
    ):
        """Test the move function with protected content."""
        # Setup
        destination_thread_id = 123456
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 789012}

        # Create mock messages
        mock_update.message = MagicMock()
        mock_update.message.from_user = MagicMock()
        mock_update.message.from_user.id = 987654
        mock_update.message.has_protected_content = True
        mock_update.message.copy = AsyncMock(return_value=MagicMock())
        mock_update.message.delete = AsyncMock()

        # Mock mention
        with patch("handlers.topic.mention", return_value="@user") as mock_mention:
            # Call the function
            result = await move(mock_update, mock_context, destination_thread_id, False)

            # Assertions
            mock_mention.assert_has_calls(
                [
                    call(mock_update.message.from_user),
                    call(mock_update.message.from_user),
                ]
            )
            assert mock_context.bot.sendMessage.call_count == 2
            mock_context.bot.sendMessage.assert_has_calls(
                [
                    call(
                        chat_id=-1001234567890,
                        message_thread_id=destination_thread_id,
                        text="@user, вас було переміщено у відповідну гілку.\n\n⬇️ продовжуйте дискусію тут ⬇️",
                    ),
                    call(
                        chat_id=-1001234567890,
                        message_thread_id=destination_thread_id,
                        text="@user написав(-ла):",
                    ),
                ]
            )
            mock_update.message.copy.assert_called_once_with(
                -1001234567890, message_thread_id=destination_thread_id
            )
            mock_update.message.delete.assert_called_once()
            assert result is not None
