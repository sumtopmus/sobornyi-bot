"""Tests for the info module."""

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch, call

from handlers.info import create_handlers, info


class TestInfo:
    """Tests for the info module."""

    def test_create_handlers(self, mock_settings):
        """Test the create_handlers function."""
        # Setup
        mock_settings.ADMINS = ["admin1", "admin2"]

        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 1

        # Check that the handler is correctly configured
        assert handlers[0].callback == info
        assert handlers[0].commands == {"info"}

        # Check that the filters are correctly configured
        assert "admin1" in handlers[0].filters.usernames
        assert "admin2" in handlers[0].filters.usernames

    @pytest.mark.asyncio
    async def test_info(self, mock_update, mock_context):
        """Test the info function."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Mock the log function
        with patch("handlers.info.log") as mock_log:
            # Call the function
            await info(mock_update, mock_context)

            # Assertions
            # Check that log is called with the correct arguments
            assert mock_log.call_args_list[0] == call("info")
            assert mock_log.call_args_list[1] == call("chat_id: 12345", logging.INFO)
            assert mock_log.call_args_list[2] == call("user_id: 67890", logging.INFO)
            assert len(mock_log.call_args_list) == 3
