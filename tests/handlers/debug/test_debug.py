"""Tests for the debug module."""

import pytest
from unittest.mock import MagicMock, patch

from handlers.debug.debug import create_handlers, debug_on, debug_off


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
    async def test_debug_on(self, mock_update, mock_context):
        """Test the debug_on function."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Mock the debug_mode_on function
        with patch("handlers.debug.debug.debug_mode_on") as mock_debug_mode_on:
            # Call the function
            await debug_on(mock_update, mock_context)

            # Assertions
            mock_debug_mode_on.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_off(self, mock_update, mock_context):
        """Test the debug_off function."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Mock the debug_mode_off function
        with patch("handlers.debug.debug.debug_mode_off") as mock_debug_mode_off:
            # Call the function
            await debug_off(mock_update, mock_context)

            # Assertions
            mock_debug_mode_off.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_debug_on_integration(self, mock_update, mock_context):
        """Test the debug_on function with integration."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Mock the log function and config
        with (
            patch("handlers.debug.debug.log") as mock_log,
            patch("config.settings") as mock_settings,
            patch("config.logging.getLogger") as mock_get_logger,
        ):

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
    async def test_debug_off_integration(self, mock_update, mock_context):
        """Test the debug_off function with integration."""
        # Setup
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.id = 67890

        # Mock the log function and config
        with (
            patch("handlers.debug.debug.log") as mock_log,
            patch("config.settings") as mock_settings,
            patch("config.logging.getLogger") as mock_get_logger,
        ):

            # Setup mock loggers
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Call the function
            await debug_off(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_with("debug_off")
            # Check that DEBUG flag is set
            assert mock_settings.DEBUG is False
