"""Tests for the error module."""

from unittest.mock import patch

import pytest
import telegram

from handlers.debug.error import handler


class TestError:
    """Tests for the error module."""

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_bad_request(self, mock_logger, mock_update, mock_context):
        """Test the handler function with a BadRequest error."""
        # Setup
        mock_context.error = telegram.error.BadRequest("Bad request error")

        # Call the function
        await handler(mock_update, mock_context)

        # Assertions
        mock_logger.warning.assert_called_once_with("BadRequest: Bad request error")
        mock_logger.error.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_timed_out(self, mock_logger, mock_update, mock_context):
        """Test the handler function with a TimedOut error."""
        # Setup
        mock_context.error = telegram.error.TimedOut("Timed out error")

        # Call the function
        await handler(mock_update, mock_context)

        # Assertions
        mock_logger.warning.assert_called_once_with("TimedOut: Timed out error")
        mock_logger.error.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_network_error(self, mock_logger, mock_update, mock_context):
        """Test the handler function with a NetworkError error."""
        # Setup
        mock_context.error = telegram.error.NetworkError("Network error")

        # Call the function
        await handler(mock_update, mock_context)

        # Assertions
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_called_once_with("NetworkError: Network error")
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_forbidden(self, mock_logger, mock_update, mock_context):
        """Test the handler function with a Forbidden error."""
        # Setup
        mock_context.error = telegram.error.Forbidden("Forbidden error")

        # Call the function
        await handler(mock_update, mock_context)

        # Assertions
        mock_logger.error.assert_called_once_with("Forbidden: Forbidden error")
        mock_logger.warning.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()

    # TODO: Difficult to mock ChatMigrated exception properly
    @pytest.mark.skip(reason="Difficult to mock ChatMigrated exception properly")
    @pytest.mark.asyncio
    async def test_handler_chat_migrated(self, mock_update, mock_context):
        """Test the handler function with a ChatMigrated error."""
        pass

    # TODO: Difficult to mock RetryAfter exception properly
    @pytest.mark.skip(reason="Difficult to mock RetryAfter exception properly")
    @pytest.mark.asyncio
    async def test_handler_retry_after(self, mock_update, mock_context):
        """Test the handler function with a RetryAfter error."""
        pass

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_invalid_token(self, mock_logger, mock_update, mock_context):
        """Test the handler function with an InvalidToken error."""
        # Setup
        mock_context.error = telegram.error.InvalidToken()

        # Call the function and assert SystemExit
        with pytest.raises(SystemExit) as excinfo:
            await handler(mock_update, mock_context)

        # Assertions
        mock_logger.critical.assert_called_once_with("Invalid bot token!")
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_not_called()
        assert str(excinfo.value) == "Bot token is invalid"

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_passport_decryption_error(
        self, mock_logger, mock_update, mock_context
    ):
        """Test the handler function with a PassportDecryptionError error."""
        # Setup
        # Create a real PassportDecryptionError
        mock_context.error = telegram.error.PassportDecryptionError(
            "Passport decryption error"
        )

        # Call the function
        await handler(mock_update, mock_context)

        # Assertions
        mock_logger.error.assert_called_once_with(
            "PassportDecryptionError: PassportDecryptionError: Passport decryption error"
        )
        mock_logger.warning.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_conflict(self, mock_logger, mock_update, mock_context):
        """Test the handler function with a Conflict error."""
        # Setup
        mock_context.error = telegram.error.Conflict("Conflict error")

        # Call the function
        await handler(mock_update, mock_context)

        # Assertions
        mock_logger.error.assert_called_once_with("Conflict: Conflict error")
        mock_logger.warning.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_telegram_error(self, mock_logger, mock_update, mock_context):
        """Test the handler function with a TelegramError error."""
        # Setup
        mock_context.error = telegram.error.TelegramError("Telegram error")

        # Call the function
        await handler(mock_update, mock_context)

        # Assertions
        mock_logger.error.assert_called_once_with("Telegram error: Telegram error")
        mock_logger.warning.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_generic_exception(
        self, mock_logger, mock_update, mock_context
    ):
        """Test the handler function with a generic Exception."""
        # Setup
        mock_context.error = Exception("Generic error")

        # Call the function
        await handler(mock_update, mock_context)

        # Assertions
        mock_logger.error.assert_called_once_with(
            "Error while getting Updates:",
            exc_info=mock_context.error,
            extra={"update": mock_update},
        )
        mock_logger.warning.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    @patch("handlers.debug.error.logger")
    async def test_handler_with_none_update(self, mock_logger, mock_context):
        """Test the handler function with a None update."""
        # Setup
        mock_context.error = Exception("Generic error")

        # Call the function
        await handler(None, mock_context)

        # Assertions
        mock_logger.error.assert_called_once_with(
            "Error while getting Updates:",
            exc_info=mock_context.error,
            extra={"update": None},
        )
        mock_logger.warning.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.info.assert_not_called()
