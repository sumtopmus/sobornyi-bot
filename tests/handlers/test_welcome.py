"""Tests for the welcome module."""

from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from telegram import User
from telegram.error import Forbidden, TelegramError
from telegram.ext import ConversationHandler

from handlers.welcome import (
    MAX_TRIES,
    State,
    about,
    check_passphrase,
    create_handlers,
    join,
    join_request,
    not_about,
    timeout,
)


class TestCreateHandlers:
    """Tests for the create_handlers function."""

    def test_create_handlers(self, mock_settings):
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.WELCOME_TIMEOUT = 86400

        handlers = create_handlers()

        assert len(handlers) == 1
        conv_handler = handlers[0]
        assert isinstance(conv_handler, ConversationHandler)
        assert len(conv_handler.entry_points) == 2
        assert State.PASSPHRASE in conv_handler.states
        assert State.AWAITING in conv_handler.states
        assert ConversationHandler.TIMEOUT in conv_handler.states
        assert conv_handler.conversation_timeout == 86400
        assert conv_handler.name == "welcome"
        assert conv_handler.persistent is True
        assert conv_handler.per_chat is False
        assert conv_handler.allow_reentry is True


class TestJoin:
    """Tests for the join entry point (direct join via invite link)."""

    @pytest.mark.asyncio
    async def test_join_admin_add_kicks_all(
        self, mock_settings, mock_update, mock_context
    ):
        """Users added by admin are kicked so they can rejoin through the proper channel."""
        mock_settings.CHAT_ID = -1001234567890
        admin = MagicMock(spec=User)
        admin.id = 1
        user1 = MagicMock(spec=User)
        user1.id = 42
        user1.full_name = "User One"
        user1.is_bot = False
        user2 = MagicMock(spec=User)
        user2.id = 43
        user2.full_name = "User Two"
        user2.is_bot = False
        mock_update.effective_user = admin
        mock_update.message.new_chat_members = [user1, user2]
        mock_update.message.chat.id = -1001234567890
        mock_update.message.delete = AsyncMock()
        mock_context.bot.ban_chat_member = AsyncMock()
        mock_context.bot.unban_chat_member = AsyncMock()

        with patch("handlers.welcome.utils.log"):
            result = await join(mock_update, mock_context)

        mock_update.message.delete.assert_awaited_once()
        assert mock_context.bot.ban_chat_member.await_count == 2
        assert mock_context.bot.unban_chat_member.await_count == 2
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_join_admin_add_skips_bots(
        self, mock_settings, mock_update, mock_context
    ):
        """Bot users in an admin-add are skipped (not kicked)."""
        mock_settings.CHAT_ID = -1001234567890
        admin = MagicMock(spec=User)
        admin.id = 1
        bot_user = MagicMock(spec=User)
        bot_user.id = 99
        bot_user.full_name = "SomeBot"
        bot_user.is_bot = True
        mock_update.effective_user = admin
        mock_update.message.new_chat_members = [bot_user]
        mock_update.message.chat.id = -1001234567890
        mock_update.message.delete = AsyncMock()
        mock_context.bot.ban_chat_member = AsyncMock()
        mock_context.bot.unban_chat_member = AsyncMock()

        with patch("handlers.welcome.utils.log"):
            result = await join(mock_update, mock_context)

        mock_context.bot.ban_chat_member.assert_not_awaited()
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_join_new_user(self, mock_settings, mock_update, mock_context):
        """Direct link joiner (new user) skips passphrase and enters AWAITING."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {"welcome": 123}
        mock_settings.CHANNEL_USERNAME = "@test_channel"
        user = MagicMock(spec=User)
        user.id = 42
        user.full_name = "New User"
        user.is_bot = False
        mock_update.effective_user = user
        mock_update.message.new_chat_members = [user]
        mock_update.message.chat.id = -1001234567890
        mock_context.user_data = {}
        mock_context.bot.sendMessage = AsyncMock()
        mock_context.bot.get_chat = AsyncMock()
        channel = MagicMock()
        channel.link = "https://t.me/test"
        mock_context.bot.get_chat.return_value = channel

        with patch("handlers.welcome.utils.log"), patch(
            "handlers.welcome.mention", return_value="@user"
        ), patch("handlers.welcome.utils.add_message_cleanup_job"):
            result = await join(mock_update, mock_context)

        mock_context.bot.sendMessage.assert_awaited_once()
        assert result == State.AWAITING

    @pytest.mark.asyncio
    async def test_join_returning_user(self, mock_settings, mock_update, mock_context):
        """Returning user who already introduced themselves gets a short welcome."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {"welcome": 123}
        user = MagicMock(spec=User)
        user.id = 42
        user.full_name = "Returning User"
        user.is_bot = False
        mock_update.effective_user = user
        mock_update.message.new_chat_members = [user]
        mock_update.message.chat.id = -1001234567890
        mock_context.user_data = {"about": "intro text"}
        mock_context.bot.sendMessage = AsyncMock()

        with patch("handlers.welcome.utils.log"), patch(
            "handlers.welcome.mention", return_value="@user"
        ), patch("handlers.welcome.utils.add_message_cleanup_job"):
            result = await join(mock_update, mock_context)

        mock_context.bot.sendMessage.assert_awaited_once()
        assert result == ConversationHandler.END


class TestJoinRequest:
    """Tests for the join_request entry point."""

    @pytest.mark.asyncio
    async def test_join_request_new_user(
        self, mock_settings, mock_update, mock_context
    ):
        """New user who hasn't passed passphrase gets the challenge via DM."""
        mock_settings.CHAT_ID = -1001234567890
        mock_context.user_data = {}
        mock_context.bot.send_message = AsyncMock()
        user = MagicMock()
        user.id = 42
        user.full_name = "New User"
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await join_request(mock_update, mock_context)

        mock_context.bot.send_message.assert_awaited_once_with(42, "Гасло?")
        assert mock_context.user_data["passphrase_tries"] == 0
        assert mock_context.user_data["join_via_request"] is True
        assert result == State.PASSPHRASE

    @pytest.mark.asyncio
    async def test_join_request_already_passed(
        self, mock_settings, mock_update, mock_context
    ):
        """User who already passed passphrase gets their request approved."""
        mock_settings.CHAT_ID = -1001234567890
        mock_context.user_data = {"passphrase_passed": True}
        user = MagicMock()
        user.id = 42
        user.full_name = "Passed User"
        user.approve_join_request = AsyncMock()
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await join_request(mock_update, mock_context)

        user.approve_join_request.assert_awaited_once_with(-1001234567890)
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_join_request_cannot_dm(
        self, mock_settings, mock_update, mock_context
    ):
        """When bot cannot DM user, request is declined and conversation ends."""
        mock_settings.CHAT_ID = -1001234567890
        mock_context.user_data = {}
        mock_context.bot.send_message = AsyncMock(side_effect=Forbidden("blocked"))
        user = MagicMock()
        user.id = 42
        user.full_name = "User"
        user.decline_join_request = AsyncMock()
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await join_request(mock_update, mock_context)

        user.decline_join_request.assert_awaited_once_with(-1001234567890)
        assert result == ConversationHandler.END


class TestCheckPassphrase:
    """Tests for the check_passphrase handler."""

    @pytest.mark.asyncio
    async def test_correct_ukrainian(self, mock_settings, mock_update, mock_context):
        """Ukrainian passphrase triggers Ukrainian reply with chat link."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.CHAT_INVITE_LINK = "https://t.me/+invite"
        mock_context.user_data = {"passphrase_tries": 0, "join_via_request": False}
        mock_update.message.text = "Слава Україні!"
        mock_update.message.reply_text = AsyncMock()
        user = MagicMock()
        user.id = 42
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await check_passphrase(mock_update, mock_context)

        assert mock_context.user_data["passphrase_passed"] is True
        reply_call = mock_update.message.reply_text.call_args
        assert reply_call.args[0] == "Героям слава!"
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_correct_english(self, mock_settings, mock_update, mock_context):
        """English passphrase triggers English reply with chat link."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.CHAT_INVITE_LINK = "https://t.me/+invite"
        mock_context.user_data = {"passphrase_tries": 0, "join_via_request": False}
        mock_update.message.text = "Glory to Ukraine!"
        mock_update.message.reply_text = AsyncMock()
        user = MagicMock()
        user.id = 42
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await check_passphrase(mock_update, mock_context)

        assert mock_context.user_data["passphrase_passed"] is True
        reply_call = mock_update.message.reply_text.call_args
        assert reply_call.args[0] == "Glory to heroes!"
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_correct_via_join_request_approves(
        self, mock_settings, mock_update, mock_context
    ):
        """Correct answer via join request approves the request instead of sending link."""
        mock_settings.CHAT_ID = -1001234567890
        mock_context.user_data = {"passphrase_tries": 0, "join_via_request": True}
        mock_update.message.text = "Слава Україні"
        mock_update.message.reply_text = AsyncMock()
        user = MagicMock()
        user.id = 42
        user.approve_join_request = AsyncMock()
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await check_passphrase(mock_update, mock_context)

        user.approve_join_request.assert_awaited_once_with(-1001234567890)
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_wrong_answer_first_try(
        self, mock_settings, mock_update, mock_context
    ):
        """Wrong answer on first try sends remaining count and stays in PASSPHRASE."""
        mock_context.user_data = {"passphrase_tries": 0, "join_via_request": False}
        mock_update.message.text = "Привіт"
        mock_update.message.reply_text = AsyncMock()
        user = MagicMock()
        user.id = 42
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await check_passphrase(mock_update, mock_context)

        assert mock_context.user_data["passphrase_tries"] == 1
        assert "passphrase_passed" not in mock_context.user_data
        mock_update.message.reply_text.assert_awaited_once_with(f"Гасло?")
        assert result == State.PASSPHRASE

    @pytest.mark.asyncio
    async def test_wrong_answer_last_try(
        self, mock_settings, mock_update, mock_context
    ):
        """Wrong answer on last try ends the conversation."""
        mock_context.user_data = {
            "passphrase_tries": MAX_TRIES - 1,
            "join_via_request": False,
        }
        mock_update.message.text = "Нічого"
        mock_update.message.reply_text = AsyncMock()
        user = MagicMock()
        user.id = 42
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await check_passphrase(mock_update, mock_context)

        mock_update.message.reply_text.assert_awaited_once_with("Нехай щастить!")
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_wrong_answer_last_try_bans_and_declines_request(
        self, mock_settings, mock_update, mock_context
    ):
        """Wrong answer on last try via join request bans the user and declines the request."""
        mock_settings.CHAT_ID = -1001234567890
        mock_context.user_data = {
            "passphrase_tries": MAX_TRIES - 1,
            "join_via_request": True,
        }
        mock_update.message.text = "Нічого"
        mock_update.message.reply_text = AsyncMock()
        mock_context.bot.ban_chat_member = AsyncMock()
        user = MagicMock()
        user.id = 42
        user.full_name = "User"
        user.decline_join_request = AsyncMock()
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await check_passphrase(mock_update, mock_context)

        mock_context.bot.ban_chat_member.assert_awaited_once_with(-1001234567890, 42)
        user.decline_join_request.assert_awaited_once_with(-1001234567890)
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_passphrase_case_insensitive(
        self, mock_settings, mock_update, mock_context
    ):
        """Passphrase matching is case-insensitive."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.CHAT_INVITE_LINK = "https://t.me/+invite"
        mock_context.user_data = {"passphrase_tries": 0, "join_via_request": False}
        mock_update.message.text = "СЛАВА УКРАЇНІ"
        mock_update.message.reply_text = AsyncMock()
        user = MagicMock()
        user.id = 42
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await check_passphrase(mock_update, mock_context)

        assert result == ConversationHandler.END
        assert mock_context.user_data["passphrase_passed"] is True

    @pytest.mark.asyncio
    async def test_passphrase_slava_ukraini_latin(
        self, mock_settings, mock_update, mock_context
    ):
        """'Slava Ukraini' (Latin) is accepted as English variant."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.CHAT_INVITE_LINK = "https://t.me/+invite"
        mock_context.user_data = {"passphrase_tries": 0, "join_via_request": False}
        mock_update.message.text = "Slava Ukraini!"
        mock_update.message.reply_text = AsyncMock()
        user = MagicMock()
        user.id = 42
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await check_passphrase(mock_update, mock_context)

        assert result == ConversationHandler.END
        reply_call = mock_update.message.reply_text.call_args
        assert reply_call.args[0] == "Glory to heroes!"


class TestNotAbout:
    """Tests for the not_about handler (unchanged logic)."""

    @pytest.mark.asyncio
    async def test_not_about_in_welcome_topic(
        self, mock_settings, mock_update, mock_context
    ):
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 123}
        mock_update.message.from_user.id = 123456789
        mock_update.message.from_user.full_name = "Test User"
        mock_update.message.chat.id = -1001234567890
        mock_update.message.message_thread_id = 123
        mock_update.message.id = 1
        mock_context.bot.sendMessage = AsyncMock()

        with patch("handlers.welcome.utils.log"), patch(
            "handlers.welcome.mention", return_value="@testuser"
        ), patch("handlers.welcome.utils.add_message_cleanup_job") as mock_add_cleanup:
            result = await not_about(mock_update, mock_context)

        mock_context.bot.sendMessage.assert_called_once_with(
            chat_id=mock_update.message.chat.id,
            message_thread_id=123,
            text="@testuser, додай, будь ласка, до свого повідомлення теґ #about.",
            reply_to_message_id=1,
        )
        assert mock_add_cleanup.call_count == 2
        assert result == State.AWAITING

    @pytest.mark.asyncio
    async def test_not_about_in_other_topic(
        self, mock_settings, mock_update, mock_context
    ):
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 123}
        mock_update.message.from_user.id = 123456789
        mock_update.message.from_user.full_name = "Test User"
        mock_update.message.chat.id = -1001234567890
        mock_update.message.message_thread_id = 456
        mock_update.message.id = 1
        mock_context.bot.sendMessage = AsyncMock()

        with patch("handlers.welcome.utils.log"), patch(
            "handlers.welcome.mention", return_value="@testuser"
        ), patch(
            "handlers.welcome.utils.add_message_cleanup_job"
        ) as mock_add_cleanup, patch(
            "handlers.welcome.topic.move", return_value=2
        ) as mock_move:
            result = await not_about(mock_update, mock_context)

        mock_move.assert_called_once_with(mock_update, mock_context, 123)
        mock_context.bot.sendMessage.assert_called_once_with(
            chat_id=mock_update.message.chat.id,
            message_thread_id=123,
            text="@testuser, додай, будь ласка, до свого повідомлення теґ #about і напиши його в цій гілці (у Вітальні).",
            reply_to_message_id=2,
        )
        assert result == State.AWAITING


class TestAbout:
    """Tests for the about handler (unchanged logic)."""

    @pytest.mark.asyncio
    async def test_about_in_welcome_topic(
        self, mock_settings, mock_update, mock_context
    ):
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {
            "welcome": 123,
            "navigation": 456,
            "guides": 789,
            "agenda": 101112,
        }
        mock_settings.CHAT_LINK_ID = "1234567890"
        mock_update.message.from_user.id = 123456789
        mock_update.message.from_user.full_name = "Test User"
        mock_update.message.chat.id = -1001234567890
        mock_update.message.message_thread_id = 123
        mock_update.message.id = 1
        mock_update.message.text = "Hello, I'm new here #about"
        mock_update.edited_message = None
        mock_context.user_data = {}
        mock_context.bot.sendMessage = AsyncMock()

        with patch("handlers.welcome.utils.log"), patch(
            "handlers.welcome.mention", return_value="@testuser"
        ), patch("handlers.welcome.utils.add_message_cleanup_job"), patch(
            "handlers.welcome.utils.clear_jobs"
        ):
            result = await about(mock_update, mock_context)

        assert mock_context.user_data["about"] == "Hello, I'm new here #about"
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_about_edited_message(self, mock_settings, mock_update, mock_context):
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.FORUM = True
        mock_settings.TOPICS = {"welcome": 123}
        mock_settings.CHAT_LINK_ID = "1234567890"
        mock_update.message = None
        mock_update.edited_message = MagicMock()
        mock_update.edited_message.from_user.id = 123456789
        mock_update.edited_message.from_user.full_name = "Test User"
        mock_update.edited_message.chat.id = -1001234567890
        mock_update.edited_message.message_thread_id = 123
        mock_update.edited_message.id = 1
        mock_update.edited_message.text = "Hello #about (edited)"
        mock_context.user_data = {}
        mock_context.bot.sendMessage = AsyncMock()

        with patch("handlers.welcome.utils.log"), patch(
            "handlers.welcome.mention", return_value="@testuser"
        ), patch("handlers.welcome.utils.add_message_cleanup_job"), patch(
            "handlers.welcome.utils.clear_jobs"
        ) as mock_clear_jobs:
            result = await about(mock_update, mock_context)

        mock_clear_jobs.assert_called_once_with(
            mock_context.application, "message_cleanup", 1
        )
        assert mock_context.user_data["about"] == "Hello #about (edited)"
        assert result == ConversationHandler.END


class TestTimeout:
    """Tests for the timeout handler."""

    @pytest.mark.asyncio
    async def test_timeout_during_passphrase(
        self, mock_settings, mock_update, mock_context
    ):
        """Timeout during passphrase challenge sends DM and ends conversation."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 123}
        mock_context.user_data = {"join_via_request": False}
        mock_context.bot.send_message = AsyncMock()
        user = MagicMock()
        user.id = 42
        user.full_name = "User"
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await timeout(mock_update, mock_context)

        mock_context.bot.send_message.assert_awaited_once_with(
            42, "Час вийшов. Нехай щастить!"
        )
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_timeout_during_passphrase_declines_request(
        self, mock_settings, mock_update, mock_context
    ):
        """Timeout during passphrase via join request declines the request."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 123}
        mock_context.user_data = {"join_via_request": True}
        mock_context.bot.send_message = AsyncMock()
        user = MagicMock()
        user.id = 42
        user.full_name = "User"
        user.decline_join_request = AsyncMock()
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log"):
            result = await timeout(mock_update, mock_context)

        user.decline_join_request.assert_awaited_once_with(-1001234567890)
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_timeout_during_awaiting(
        self, mock_settings, mock_update, mock_context
    ):
        """Timeout during #about stage kicks user from the group."""
        mock_settings.CHAT_ID = -1001234567890
        mock_settings.TOPICS = {"welcome": 123}
        mock_context.user_data = {"passphrase_passed": True}
        mock_context.bot.sendMessage = AsyncMock()
        mock_context.bot.ban_chat_member = AsyncMock()
        mock_context.bot.unban_chat_member = AsyncMock()
        user = MagicMock()
        user.id = 42
        user.full_name = "User"
        mock_update.effective_user = user

        with patch("handlers.welcome.utils.log") as mock_log, patch(
            "handlers.welcome.mention", return_value="@user"
        ), patch("handlers.welcome.utils.add_message_cleanup_job"):
            result = await timeout(mock_update, mock_context)

        mock_context.bot.ban_chat_member.assert_awaited_once_with(
            -1001234567890, 42, revoke_messages=False
        )
        mock_context.bot.unban_chat_member.assert_awaited_once_with(-1001234567890, 42)
        mock_log.assert_any_call(
            f"kicked: 42 (User)", pytest.importorskip("logging").INFO
        )
        assert result == ConversationHandler.END
