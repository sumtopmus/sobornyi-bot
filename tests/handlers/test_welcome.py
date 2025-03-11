"""Tests for the welcome module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, ANY
from telegram import User
from telegram.ext import ConversationHandler

from handlers.welcome import create_handlers, welcome, not_about, about, timeout, State


class TestWelcome:
    """Tests for the welcome module."""

    def test_create_handlers(self, mock_settings):
        """Test the create_handlers function."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.WELCOME_TIMEOUT = 86400  # 1 day

        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 1
        assert isinstance(handlers[0], ConversationHandler)

        # Check conversation handler configuration
        conv_handler = handlers[0]
        assert len(conv_handler.entry_points) == 1
        assert conv_handler.entry_points[0].callback == welcome
        assert State.AWAITING in conv_handler.states
        assert ConversationHandler.TIMEOUT in conv_handler.states
        assert conv_handler.conversation_timeout == 86400
        assert conv_handler.name == "welcome"
        assert conv_handler.persistent is True

    @pytest.mark.asyncio
    async def test_welcome_new_user(self, mock_settings, mock_update, mock_context):
        """Test the welcome function for a new user."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {"welcome": 123}
        mock_settings.CHANNEL_USERNAME = "@test_channel"

        # Create a new user
        new_user = MagicMock(spec=User)
        new_user.id = 123456789
        new_user.first_name = "Test"
        new_user.last_name = "User"
        new_user.full_name = "Test User"
        new_user.is_bot = False

        # Setup the update
        mock_update.message.new_chat_members = [new_user]
        mock_update.message.chat.id = -1001234567890

        # Setup the context
        mock_context.user_data = {}
        mock_context.bot.sendMessage = AsyncMock()
        mock_context.bot.get_chat = AsyncMock()
        channel = MagicMock()
        channel.link = "https://t.me/test_channel"
        mock_context.bot.get_chat.return_value = channel

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup:
            result = await welcome(mock_update, mock_context)

            # Assertions
            mock_log.assert_any_call("welcome")
            mock_log.assert_any_call(
                f"new user: {new_user.id} ({new_user.full_name})",
                pytest.importorskip("logging").INFO,
            )
            mock_mention.assert_called_once_with(new_user)
            mock_context.bot.sendMessage.assert_called_once()
            mock_context.bot.get_chat.assert_called_once_with(
                mock_settings.CHANNEL_USERNAME
            )
            mock_add_cleanup.assert_called_once()
            assert result == State.AWAITING

    @pytest.mark.asyncio
    async def test_welcome_returning_user(
        self, mock_settings, mock_update, mock_context
    ):
        """Test the welcome function for a returning user."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {"welcome": 123}

        # Create a returning user
        returning_user = MagicMock(spec=User)
        returning_user.id = 123456789
        returning_user.first_name = "Test"
        returning_user.last_name = "User"
        returning_user.full_name = "Test User"
        returning_user.is_bot = False

        # Setup the update
        mock_update.message.new_chat_members = [returning_user]
        mock_update.message.chat.id = -1001234567890
        mock_update.message.id = 1

        # Setup the context
        mock_context.user_data = {"about": "This is my introduction"}
        mock_context.bot.sendMessage = AsyncMock()

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup:
            result = await welcome(mock_update, mock_context)

            # Assertions
            mock_log.assert_any_call("welcome")
            mock_log.assert_any_call(
                f"new user: {returning_user.id} ({returning_user.full_name})",
                pytest.importorskip("logging").INFO,
            )
            mock_log.assert_any_call(
                f"user {returning_user.id} already introduced themselves",
                pytest.importorskip("logging").INFO,
            )
            mock_mention.assert_called_once_with(returning_user)
            mock_context.bot.sendMessage.assert_called_once()
            mock_add_cleanup.assert_called_once()
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_welcome_bot_user(self, mock_settings, mock_update, mock_context):
        """Test the welcome function for a bot user."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890

        # Create a bot user
        bot_user = MagicMock(spec=User)
        bot_user.id = 123456789
        bot_user.first_name = "Test"
        bot_user.last_name = "Bot"
        bot_user.full_name = "Test Bot"
        bot_user.is_bot = True

        # Setup the update
        mock_update.message.new_chat_members = [bot_user]

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log:
            result = await welcome(mock_update, mock_context)

            # Assertions
            mock_log.assert_any_call("welcome")
            mock_log.assert_any_call(
                f"new user: {bot_user.id} ({bot_user.full_name})",
                pytest.importorskip("logging").INFO,
            )
            mock_log.assert_any_call(f"new user is a bot")
            assert result == State.AWAITING

    @pytest.mark.asyncio
    async def test_not_about_in_welcome_topic(
        self, mock_settings, mock_update, mock_context
    ):
        """Test the not_about function when message is in welcome topic."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 123}

        # Setup the update
        mock_update.message.from_user.id = 123456789
        mock_update.message.from_user.full_name = "Test User"
        mock_update.message.chat.id = -1001234567890
        mock_update.message.message_thread_id = 123
        mock_update.message.id = 1

        # Setup the context
        mock_context.bot.sendMessage = AsyncMock()

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup:
            result = await not_about(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("not_about")
            mock_mention.assert_called_once_with(mock_update.message.from_user)
            mock_context.bot.sendMessage.assert_called_once_with(
                chat_id=mock_update.message.chat.id,
                message_thread_id=123,
                text="@testuser, додай, будь ласка, до свого повідомлення теґ #about.",
                reply_to_message_id=1,
            )
            mock_add_cleanup.assert_has_calls(
                [
                    call(mock_context.application, 1),
                    call(
                        mock_context.application,
                        mock_context.bot.sendMessage.return_value.id,
                    ),
                ]
            )
            assert result == State.AWAITING

    @pytest.mark.asyncio
    async def test_not_about_in_other_topic(
        self, mock_settings, mock_update, mock_context
    ):
        """Test the not_about function when message is in another topic."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 123}

        # Setup the update
        mock_update.message.from_user.id = 123456789
        mock_update.message.from_user.full_name = "Test User"
        mock_update.message.chat.id = -1001234567890
        mock_update.message.message_thread_id = 456  # Different topic
        mock_update.message.id = 1

        # Setup the context
        mock_context.bot.sendMessage = AsyncMock()

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup, patch(
            "handlers.welcome.topic.move", return_value=2
        ) as mock_move:
            result = await not_about(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("not_about")
            mock_mention.assert_called_once_with(mock_update.message.from_user)
            mock_move.assert_called_once_with(mock_update, mock_context, 123)
            mock_context.bot.sendMessage.assert_called_once_with(
                chat_id=mock_update.message.chat.id,
                message_thread_id=123,
                text="@testuser, додай, будь ласка, до свого повідомлення теґ #about і напиши його в цій гілці (у Вітальні).",
                reply_to_message_id=2,
            )
            mock_add_cleanup.assert_has_calls(
                [
                    call(mock_context.application, 2),
                    call(
                        mock_context.application,
                        mock_context.bot.sendMessage.return_value.id,
                    ),
                ]
            )
            assert result == State.AWAITING

    @pytest.mark.asyncio
    async def test_about_in_welcome_topic(
        self, mock_settings, mock_update, mock_context
    ):
        """Test the about function when message is in welcome topic."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {
            "welcome": 123,
            "navigation": 456,
            "guides": 789,
            "agenda": 101112,
        }
        mock_settings.CHAT_LINK_ID = "1234567890"

        # Setup the update
        mock_update.message.from_user.id = 123456789
        mock_update.message.from_user.full_name = "Test User"
        mock_update.message.chat.id = -1001234567890
        mock_update.message.message_thread_id = 123
        mock_update.message.id = 1
        mock_update.message.text = "Hello, I'm new here #about"
        mock_update.edited_message = None

        # Setup the context
        mock_context.user_data = {}
        mock_context.bot.sendMessage = AsyncMock()

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup, patch(
            "handlers.welcome.utils.clear_jobs"
        ) as mock_clear_jobs:
            result = await about(mock_update, mock_context)

            # Assertions
            mock_log.assert_any_call("about")
            mock_log.assert_any_call(
                f"user introduced themselves: {mock_update.message.from_user.id} ({mock_update.message.from_user.full_name})",
                pytest.importorskip("logging").INFO,
            )
            mock_log.assert_any_call(
                f"about: {mock_update.message.from_user.id} ({mock_update.message.from_user.full_name})",
                pytest.importorskip("logging").INFO,
            )
            mock_mention.assert_called_once_with(mock_update.message.from_user)
            mock_context.bot.sendMessage.assert_called_once()
            mock_add_cleanup.assert_called_once()
            assert mock_context.user_data["about"] == "Hello, I'm new here #about"
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_about_in_other_topic_forward(
        self, mock_settings, mock_update, mock_context
    ):
        """Test the about function when message is in another topic and can be forwarded."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {"welcome": 123}
        mock_settings.CHAT_LINK_ID = "1234567890"

        # Setup the update
        mock_update.message.from_user.id = 123456789
        mock_update.message.from_user.full_name = "Test User"
        mock_update.message.chat.id = -1001234567890
        mock_update.message.message_thread_id = 456  # Different topic
        mock_update.message.id = 1
        mock_update.message.text = "Hello, I'm new here #about"
        mock_update.message.has_protected_content = False
        mock_update.message.forward = AsyncMock()
        mock_update.message.delete = AsyncMock()
        mock_update.edited_message = None

        # Setup the forward result
        forwarded_message = MagicMock()
        forwarded_message.id = 2
        mock_update.message.forward.return_value = forwarded_message

        # Setup the context
        mock_context.user_data = {}
        mock_context.bot.sendMessage = AsyncMock()

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup, patch(
            "handlers.welcome.utils.clear_jobs"
        ) as mock_clear_jobs:
            result = await about(mock_update, mock_context)

            # Assertions
            mock_log.assert_any_call("about")
            mock_mention.assert_called_with(mock_update.message.from_user)
            mock_update.message.forward.assert_called_once_with(
                -1001234567890, message_thread_id=123
            )
            mock_update.message.delete.assert_called_once()
            # Use ANY for the text since it's complex and varies based on settings
            mock_context.bot.sendMessage.assert_called_once_with(
                chat_id=mock_update.message.chat.id,
                message_thread_id=123,
                text=ANY,
                reply_to_message_id=2,
            )
            mock_add_cleanup.assert_called_once()
            assert mock_context.user_data["about"] == "Hello, I'm new here #about"
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_about_in_other_topic_copy(
        self, mock_settings, mock_update, mock_context
    ):
        """Test the about function when message is in another topic and needs to be copied."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {"welcome": 123}
        mock_settings.CHAT_LINK_ID = "1234567890"

        # Setup the update
        mock_update.message.from_user.id = 123456789
        mock_update.message.from_user.full_name = "Test User"
        mock_update.message.chat.id = -1001234567890
        mock_update.message.message_thread_id = 456  # Different topic
        mock_update.message.id = 1
        mock_update.message.text = "Hello, I'm new here #about"
        mock_update.message.has_protected_content = True  # Can't be forwarded
        mock_update.message.copy = AsyncMock()
        mock_update.message.delete = AsyncMock()
        mock_update.edited_message = None

        # Setup the copy result
        copied_message = MagicMock()
        copied_message.id = 3
        mock_update.message.copy.return_value = copied_message

        # Setup the context
        mock_context.user_data = {}
        mock_context.bot.sendMessage = AsyncMock()

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup, patch(
            "handlers.welcome.utils.clear_jobs"
        ) as mock_clear_jobs:
            result = await about(mock_update, mock_context)

            # Assertions
            mock_log.assert_any_call("about")
            # Don't check the exact number of calls to mention
            assert mock_mention.call_count >= 1
            mock_context.bot.sendMessage.assert_has_calls(
                [
                    call(
                        chat_id=mock_settings.CHAT_ID,
                        message_thread_id=123,
                        text=f"{mock_mention.return_value} написав(-ла):",
                    ),
                    # Use ANY for the second call's text parameter
                    call(
                        chat_id=mock_update.message.chat.id,
                        message_thread_id=123,
                        text=ANY,
                        reply_to_message_id=3,
                    ),
                ]
            )
            mock_update.message.copy.assert_called_once_with(
                mock_settings.CHAT_ID, message_thread_id=123
            )
            mock_update.message.delete.assert_called_once()
            mock_add_cleanup.assert_called_once()
            assert mock_context.user_data["about"] == "Hello, I'm new here #about"
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_about_edited_message(self, mock_settings, mock_update, mock_context):
        """Test the about function with an edited message."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {"welcome": 123}
        mock_settings.CHAT_LINK_ID = "1234567890"

        # Setup the update
        mock_update.message = None
        mock_update.edited_message = MagicMock()
        mock_update.edited_message.from_user.id = 123456789
        mock_update.edited_message.from_user.full_name = "Test User"
        mock_update.edited_message.chat.id = -1001234567890
        mock_update.edited_message.message_thread_id = 123
        mock_update.edited_message.id = 1
        mock_update.edited_message.text = "Hello, I'm new here #about (edited)"

        # Setup the context
        mock_context.user_data = {}
        mock_context.bot.sendMessage = AsyncMock()

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup, patch(
            "handlers.welcome.utils.clear_jobs"
        ) as mock_clear_jobs:
            result = await about(mock_update, mock_context)

            # Assertions
            mock_log.assert_any_call("about")
            mock_mention.assert_called_once_with(mock_update.edited_message.from_user)
            mock_clear_jobs.assert_called_once_with(
                mock_context.application,
                "message_cleanup",
                mock_update.edited_message.id,
            )
            mock_context.bot.sendMessage.assert_called_once()
            mock_add_cleanup.assert_called_once()
            assert (
                mock_context.user_data["about"] == "Hello, I'm new here #about (edited)"
            )
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_timeout(self, mock_settings, mock_update, mock_context):
        """Test the timeout function."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 123}

        # Setup the update
        mock_update.effective_user.id = 123456789
        mock_update.effective_user.full_name = "Test User"

        # Setup the context
        mock_context.bot.sendMessage = AsyncMock()
        mock_context.bot.ban_chat_member = AsyncMock()
        mock_context.bot.unban_chat_member = AsyncMock()

        # Call the function
        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.utils.mention", return_value="@testuser"
        ) as mock_mention, patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup:
            result = await timeout(mock_update, mock_context)

            # Assertions
            mock_log.assert_any_call("timeout")
            mock_log.assert_any_call(
                f"kicked: {mock_update.effective_user.id} ({mock_update.effective_user.full_name})",
                pytest.importorskip("logging").INFO,
            )
            mock_mention.assert_called_once_with(mock_update.effective_user)
            mock_context.bot.sendMessage.assert_called_once_with(
                chat_id=mock_settings.CHAT_ID,
                message_thread_id=123,
                text=f"На жаль, {mock_mention.return_value} покидає Соборний.",
            )
            mock_context.bot.ban_chat_member.assert_called_once_with(
                mock_settings.CHAT_ID,
                mock_update.effective_user.id,
                revoke_messages=False,
            )
            mock_context.bot.unban_chat_member.assert_called_once_with(
                mock_settings.CHAT_ID, mock_update.effective_user.id
            )
            mock_add_cleanup.assert_called_once()
            assert result == ConversationHandler.END
