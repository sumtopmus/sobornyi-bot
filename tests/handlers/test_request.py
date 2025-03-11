"""Tests for the request module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.request import create_handlers, request


class TestRequest:
    """Tests for the request module."""

    def test_create_handlers(self, mock_settings):
        """Test the create_handlers function."""
        # Setup
        mock_settings.CHAT_ID = -1001234567890

        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 1

        # Check that the handler is correctly configured
        assert handlers[0].callback == request
        assert -1001234567890 in handlers[0]._chat_ids

    @pytest.mark.asyncio
    async def test_request(self, mock_update, mock_context):
        """Test the request function."""
        # Setup
        # Create a mock chat_join_request
        mock_update.chat_join_request = MagicMock()
        mock_update.chat_join_request.from_user = MagicMock()
        mock_update.chat_join_request.from_user.approve_join_request = AsyncMock()
        mock_update.chat_join_request.chat = MagicMock()
        mock_update.chat_join_request.chat.id = 12345

        # Mock the log function
        with patch("handlers.request.utils.log") as mock_log:
            # Call the function
            await request(mock_update, mock_context)

            # Assertions
            # Check that log is called with the correct arguments
            mock_log.assert_called_once_with("request")

            # Check that approve_join_request is called with the correct arguments
            mock_update.chat_join_request.from_user.approve_join_request.assert_called_once_with(
                12345
            )
