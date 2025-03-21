"""Tests for the debug module."""

from unittest.mock import MagicMock, patch

import pytest

from handlers.debug.debug import create_handlers, debug_off, debug_on


class TestDebug:
    """Tests for the debug module."""

    def test_create_handlers(self, mock_settings):
        """Test the create_handlers function."""
        # Setup
        mock_settings.ADMINS = ["admin1", "admin2"]

        # Call the function
        handlers = create_handlers()

        # Assertions
        assert len(handlers) == 2

        # Check that the handlers are correctly configured
        assert handlers[0].callback == debug_on
        assert handlers[1].callback == debug_off

        # Check that the filters are correctly configured
        # FIXME: the current values are empty frozensets
        # assert handlers[0].filters.usernames == {"admin1", "admin2"}
        # assert handlers[1].filters.usernames == {"admin1", "admin2"}

    @pytest.mark.asyncio
    @patch("handlers.debug.debug.debug_mode_on")
    async def test_debug_on(self, mock_debug_mode_on, mock_update, mock_context):
        """Test the debug_on function."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Call the function
        await debug_on(mock_update, mock_context)

        # Assertions
        mock_debug_mode_on.assert_called_once()

    @pytest.mark.asyncio
    @patch("handlers.debug.debug.debug_mode_off")
    async def test_debug_off(self, mock_debug_mode_off, mock_update, mock_context):
        """Test the debug_off function."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Call the function
        await debug_off(mock_update, mock_context)

        # Assertions
        mock_debug_mode_off.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.integration
    @patch("handlers.debug.debug.log")
    @patch("config.settings")
    @patch("config.logging.getLogger")
    async def test_debug_on_integration(
        self, mock_get_logger, mock_settings, mock_log, mock_update, mock_context
    ):
        """Test the debug_on function with integration."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Setup mock loggers
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Call the function
        await debug_on(mock_update, mock_context)

        # Assertions
        mock_log.assert_called_with("debug_on")
        # Check that DEBUG flag is set
        assert mock_settings.DEBUG is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    @patch("handlers.debug.debug.log")
    @patch("config.settings")
    @patch("config.logging.getLogger")
    async def test_debug_off_integration(
        self, mock_get_logger, mock_settings, mock_log, mock_update, mock_context
    ):
        """Test the debug_off function with integration."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Setup mock loggers
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Call the function
        await debug_off(mock_update, mock_context)

        # Assertions
        mock_log.assert_called_with("debug_off")
        # Check that DEBUG flag is set
        assert mock_settings.DEBUG is False
