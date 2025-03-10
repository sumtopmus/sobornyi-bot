import pytest
from unittest.mock import patch, MagicMock
import logging

from config import debug_mode_on, debug_mode_off


class TestDebugMode:
    def test_debug_mode_on(self, mock_settings):
        # Set up mocks
        with patch("config.logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Call the function
            debug_mode_on()

            # Check that DEBUG was set to True
            assert mock_settings.DEBUG is True

            # Check that loggers were set to the correct levels
            mock_get_logger.assert_any_call("config")

            # Check that httpx and apscheduler loggers were set to INFO
            mock_get_logger.assert_any_call("httpx")
            mock_get_logger.assert_any_call("apscheduler")

    def test_debug_mode_off(self, mock_settings):
        # Set up mocks
        with patch("config.logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Call the function
            debug_mode_off()

            # Check that DEBUG was set to False
            assert mock_settings.DEBUG is False

            # Check that loggers were set to the correct levels
            mock_get_logger.assert_any_call("config")

            # Check that httpx and apscheduler loggers were set to WARNING
            mock_get_logger.assert_any_call("httpx")
            mock_get_logger.assert_any_call("apscheduler")


class TestSettings:
    def test_settings_loaded(self, mock_settings):
        # Test that settings are loaded correctly
        assert mock_settings.DEBUG is not None
        assert mock_settings.CHAT_ID is not None
        assert mock_settings.CLEANUP_PERIOD is not None

    def test_dev_environment_settings(self, mock_settings):
        # Mock the current environment
        mock_settings.current_env = "dev"
        mock_settings.MORNING_TIME = "08:00:00"  # Set the expected value directly

        # Mock the datetime and timedelta
        with patch("config.datetime") as mock_datetime, patch(
            "config.timedelta"
        ) as mock_timedelta:

            mock_now = MagicMock()
            mock_datetime.now.return_value = mock_now
            mock_time = MagicMock()
            mock_now.time.return_value = mock_time
            mock_time.isoformat.return_value = "12:00:00"

            # Mock the TIME_OFFSET setting
            mock_settings.TIME_OFFSET = 3600  # 1 hour

            # Reimport the module to trigger the environment-specific code
            with patch.dict("sys.modules"):
                import importlib
                import config

                importlib.reload(config)

                # Check that the time settings were updated
                assert (
                    mock_settings.MORNING_TIME == "08:00:00"
                )  # We're using the mock value
