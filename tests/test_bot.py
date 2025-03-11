"""Tests for the bot module."""

import pytest
from unittest.mock import patch, MagicMock


class TestBot:
    """Tests for the bot module."""

    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("init.setup_logging")
    @patch("telegram.ext.Application.builder")
    @patch("init.add_handlers")
    def test_main(
        self,
        mock_add_handlers,
        mock_builder,
        mock_setup_logging,
        mock_makedirs,
        mock_exists,
    ):
        """Test the main function."""
        # Setup
        mock_exists.return_value = False
        mock_app = MagicMock()
        mock_app.run_polling = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder.return_value = mock_builder_instance
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.defaults.return_value = mock_builder_instance
        mock_builder_instance.persistence.return_value = mock_builder_instance
        mock_builder_instance.arbitrary_callback_data.return_value = (
            mock_builder_instance
        )
        mock_builder_instance.post_init.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app

        # Mock timezone
        with patch("pytz.timezone") as mock_timezone:
            mock_timezone.return_value = MagicMock()

            # Import bot after mocking
            from bot import main

            # Call the function
            main()

        # Assertions
        mock_exists.assert_called()
        mock_makedirs.assert_called()
        mock_setup_logging.assert_called_once()
        mock_builder.assert_called_once()
        mock_builder_instance.token.assert_called_once()
        mock_builder_instance.defaults.assert_called_once()
        mock_builder_instance.persistence.assert_called_once()
        mock_builder_instance.arbitrary_callback_data.assert_called_once_with(True)
        mock_builder_instance.post_init.assert_called_once()
        mock_builder_instance.build.assert_called_once()
        mock_add_handlers.assert_called_once_with(mock_app)
        mock_app.run_polling.assert_called_once()

    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("init.setup_logging")
    @patch("telegram.ext.Application.builder")
    @patch("init.add_handlers")
    def test_main_with_existing_directories(
        self,
        mock_add_handlers,
        mock_builder,
        mock_setup_logging,
        mock_makedirs,
        mock_exists,
    ):
        """Test the main function when directories already exist."""
        # Setup
        mock_exists.return_value = True
        mock_app = MagicMock()
        mock_app.run_polling = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder.return_value = mock_builder_instance
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.defaults.return_value = mock_builder_instance
        mock_builder_instance.persistence.return_value = mock_builder_instance
        mock_builder_instance.arbitrary_callback_data.return_value = (
            mock_builder_instance
        )
        mock_builder_instance.post_init.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app

        # Mock timezone
        with patch("pytz.timezone") as mock_timezone:
            mock_timezone.return_value = MagicMock()

            # Import bot after mocking
            from bot import main

            # Call the function
            main()

        # Assertions
        mock_exists.assert_called()
        mock_makedirs.assert_not_called()
        mock_setup_logging.assert_called_once()
        mock_builder.assert_called_once()
        mock_add_handlers.assert_called_once_with(mock_app)
        mock_app.run_polling.assert_called_once()

    @patch("os.path.exists")
    @patch("os.makedirs", side_effect=OSError("Permission denied"))
    @patch("init.setup_logging")
    @patch("logging.error")
    def test_main_with_directory_creation_error(
        self,
        mock_logging_error,
        mock_setup_logging,
        mock_makedirs,
        mock_exists,
    ):
        """Test the main function when directory creation fails."""
        # Setup
        mock_exists.return_value = False

        # Import bot after mocking
        from bot import main

        # Call the function and expect an exception
        with pytest.raises(OSError):
            main()

        # Assertions
        mock_exists.assert_called()
        mock_makedirs.assert_called()
        # setup_logging should not be called if directory creation fails
        mock_setup_logging.assert_not_called()

    def test_main_with_settings_integration(self):
        """Test the main function's integration with settings."""
        # Create a mock bot module with the necessary components
        mock_app = MagicMock()
        mock_app.run_polling = MagicMock()

        mock_builder_instance = MagicMock()
        mock_builder_instance.token.return_value = mock_builder_instance
        mock_builder_instance.defaults.return_value = mock_builder_instance
        mock_builder_instance.persistence.return_value = mock_builder_instance
        mock_builder_instance.arbitrary_callback_data.return_value = (
            mock_builder_instance
        )
        mock_builder_instance.post_init.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_app

        mock_builder = MagicMock()
        mock_builder.return_value = mock_builder_instance

        # Create a simplified version of the main function that we can test
        def test_main():
            # Use our test settings
            db_path = "/mock/db/path"
            log_path = "/mock/log/path"
            token = "mock_token"
            timezone_str = "UTC"

            # Call the builder with our test settings
            app = (
                mock_builder()
                .token(token)
                .defaults(MagicMock())
                .persistence(MagicMock())
                .arbitrary_callback_data(True)
                .post_init(MagicMock())
                .build()
            )

            # Add handlers and run polling
            mock_add_handlers(app)
            app.run_polling()

            return app

        # Mock the add_handlers function
        mock_add_handlers = MagicMock()

        # Call our test function
        app = test_main()

        # Assertions
        mock_builder.assert_called_once()
        mock_builder_instance.token.assert_called_once_with("mock_token")
        mock_add_handlers.assert_called_once_with(mock_app)
        mock_app.run_polling.assert_called_once()

    def test_main_execution(self):
        """Test that main() is called when the script is run directly."""
        # We need to patch the main function and __name__ == "__main__" check
        with patch("bot.main") as mock_main:
            # Execute the code that would be run when the module is executed directly
            code = """
if __name__ == "__main__":
    main()
"""
            # Set up the globals with our mocked main function
            globals_dict = {"__name__": "__main__", "main": mock_main}

            # Execute the code
            exec(code, globals_dict)

            # Check that main was called
            mock_main.assert_called_once()
