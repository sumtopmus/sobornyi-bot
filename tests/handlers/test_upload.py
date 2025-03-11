"""Tests for the upload module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram.ext import ConversationHandler

from handlers.upload import create_handlers, on_upload, upload, cancel, timeout, State


class TestUpload:
    """Tests for the upload module."""

    def test_create_handlers(self, mock_settings):
        """Test the create_handlers function."""
        # Setup
        mock_settings.ADMINS = ["admin1", "admin2"]
        mock_settings.CONVERSATION_TIMEOUT = 300

        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 1
        assert isinstance(handlers[0], ConversationHandler)

        # Check conversation handler configuration
        conv_handler = handlers[0]
        assert len(conv_handler.entry_points) == 1
        assert conv_handler.entry_points[0].callback == on_upload
        assert State.AWAITING in conv_handler.states
        assert ConversationHandler.TIMEOUT in conv_handler.states
        assert len(conv_handler.fallbacks) == 1
        assert conv_handler.fallbacks[0].callback == cancel
        assert conv_handler.allow_reentry is True
        assert conv_handler.conversation_timeout == 300
        assert conv_handler.name == "upload"
        assert conv_handler.per_chat is False

    @pytest.mark.asyncio
    async def test_on_upload(self, mock_update, mock_context):
        """Test the on_upload function."""
        # Setup
        mock_update.effective_user.send_message = AsyncMock()

        # Call the function
        with patch("handlers.upload.log") as mock_log:
            result = await on_upload(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("on_upload")
            mock_update.effective_user.send_message.assert_called_once_with(
                "Будь ласка, завантажте фото."
            )
            assert result == State.AWAITING

    @pytest.mark.asyncio
    async def test_upload(self, mock_update, mock_context):
        """Test the upload function."""
        # Setup
        mock_update.effective_user.send_message = AsyncMock()
        mock_update.message.photo = [MagicMock(), MagicMock()]

        # Call the function
        with patch("handlers.upload.log") as mock_log:
            result = await upload(mock_update, mock_context)

            # Assertions
            assert mock_log.call_count == 3  # One for "upload" and two for each photo
            mock_update.effective_user.send_message.assert_called_once_with(
                "Фото було додано в базу даних."
            )
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_cancel(self, mock_update, mock_context):
        """Test the cancel function."""
        # Setup
        mock_update.effective_user.send_message = AsyncMock()

        # Call the function
        with patch("handlers.upload.log") as mock_log:
            result = await cancel(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("cancel")
            mock_update.effective_user.send_message.assert_called_once_with(
                "Операцію скасовано."
            )
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_timeout(self, mock_update, mock_context):
        """Test the timeout function."""
        # Setup
        mock_update.effective_user.send_message = AsyncMock()

        # Call the function
        with patch("handlers.upload.log") as mock_log:
            result = await timeout(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("timeout")
            mock_update.effective_user.send_message.assert_called_once_with(
                "Запит скасовано автоматично через таймаут."
            )
            assert result == ConversationHandler.END
