"""Tests for the debug module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.debug import create_handlers, debug_on, debug_off


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
        assert "admin1" in handlers[0].filters.usernames
        assert "admin2" in handlers[0].filters.usernames
        assert "admin1" in handlers[1].filters.usernames
        assert "admin2" in handlers[1].filters.usernames

    @pytest.mark.asyncio
    async def test_debug_on(self, mock_update, mock_context):
        """Test the debug_on function."""
        # Setup
        with (
            patch("handlers.debug.debug_mode_on") as mock_debug_mode_on,
            patch("handlers.debug.log") as mock_log,
        ):
            # Call the function
            await debug_on(mock_update, mock_context)

            # Assertions
            mock_debug_mode_on.assert_called_once()
            mock_log.assert_called_once_with("debug_on")

    @pytest.mark.asyncio
    async def test_debug_off(self, mock_update, mock_context):
        """Test the debug_off function."""
        # Setup
        with (
            patch("handlers.debug.debug_mode_off") as mock_debug_mode_off,
            patch("handlers.debug.log") as mock_log,
        ):
            # Call the function
            await debug_off(mock_update, mock_context)

            # Assertions
            mock_debug_mode_off.assert_called_once()
            mock_log.assert_called_once_with("debug_off")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_debug_mode_on_integration(self, mock_update, mock_context):
        """Test the debug_on function with actual debug_mode_on function."""
        # Setup
        with (
            patch("handlers.debug.log") as mock_log,
            patch("config.logging.getLogger") as mock_get_logger,
        ):
            # Setup mock loggers
            mock_logger = MagicMock()
            mock_get_logger.side_effect = lambda name: {
                "__main__": mock_logger,
                "httpx": mock_logger,
                "apscheduler": mock_logger,
            }.get(name, mock_logger)

            # Call the function
            await debug_on(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("debug_on")

            # Check that DEBUG flag is set
            from config import settings

            assert settings.DEBUG is True

            # Check that logger levels are set correctly
            mock_logger.setLevel.assert_any_call(pytest.importorskip("logging").DEBUG)
            mock_logger.setLevel.assert_any_call(pytest.importorskip("logging").INFO)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_debug_mode_off_integration(self, mock_update, mock_context):
        """Test the debug_off function with actual debug_mode_off function."""
        # Setup
        with (
            patch("handlers.debug.log") as mock_log,
            patch("config.logging.getLogger") as mock_get_logger,
        ):
            # Setup mock loggers
            mock_logger = MagicMock()
            mock_get_logger.side_effect = lambda name: {
                "__main__": mock_logger,
                "httpx": mock_logger,
                "apscheduler": mock_logger,
            }.get(name, mock_logger)

            # Call the function
            await debug_off(mock_update, mock_context)

            # Assertions
            mock_log.assert_called_once_with("debug_off")

            # Check that DEBUG flag is set
            from config import settings

            assert settings.DEBUG is False

            # Check that logger levels are set correctly
            mock_logger.setLevel.assert_any_call(pytest.importorskip("logging").INFO)
            mock_logger.setLevel.assert_any_call(pytest.importorskip("logging").WARNING)
