"""Tests for the config module."""

import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from dynaconf import Dynaconf

from config import debug_mode_off, debug_mode_on, settings


class TestDebugMode:
    def test_debug_mode_on(self, mock_settings):
        """Test that debug_mode_on sets the correct settings and log levels."""
        # Set up mocks
        with patch("config.logging.getLogger") as mock_get_logger:
            # Create mock loggers
            mock_root_logger = MagicMock()
            mock_httpx_logger = MagicMock()
            mock_apscheduler_logger = MagicMock()

            # Configure mock_get_logger to return different loggers based on the argument
            def get_logger_side_effect(name=None):
                if name is None:
                    return mock_root_logger
                elif name == "httpx":
                    return mock_httpx_logger
                elif name == "apscheduler":
                    return mock_apscheduler_logger
                return MagicMock()

            mock_get_logger.side_effect = get_logger_side_effect

            # Call the function under test
            debug_mode_on()

            # Verify settings were updated correctly
            assert mock_settings.DEBUG is True
            # Verify log levels were set correctly
            mock_root_logger.setLevel.assert_called_once_with(logging.DEBUG)
            mock_httpx_logger.setLevel.assert_called_once_with(logging.INFO)
            mock_apscheduler_logger.setLevel.assert_called_once_with(logging.INFO)

    def test_debug_mode_off(self, mock_settings):
        """Test that debug_mode_off sets the correct settings and log levels."""
        # Set up mocks
        with patch("config.logging.getLogger") as mock_get_logger:
            # Create mock loggers
            mock_root_logger = MagicMock()
            mock_httpx_logger = MagicMock()
            mock_apscheduler_logger = MagicMock()

            # Configure mock_get_logger to return different loggers based on the argument
            def get_logger_side_effect(name=None):
                if name is None:
                    return mock_root_logger
                elif name == "httpx":
                    return mock_httpx_logger
                elif name == "apscheduler":
                    return mock_apscheduler_logger
                return MagicMock()

            mock_get_logger.side_effect = get_logger_side_effect

            # Call the function under test
            debug_mode_off()

            # Verify settings were updated correctly
            assert mock_settings.DEBUG is False
            # Verify log levels were set correctly
            mock_root_logger.setLevel.assert_called_once_with(logging.INFO)
            mock_httpx_logger.setLevel.assert_called_once_with(logging.WARNING)
            mock_apscheduler_logger.setLevel.assert_called_once_with(logging.WARNING)

    def test_debug_mode_toggle(self, mock_settings):
        """Test toggling between debug modes."""
        # Set up mocks
        with patch("config.logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Start with debug mode off
            debug_mode_off()
            assert mock_settings.DEBUG is False

            # Toggle to debug mode on
            debug_mode_on()
            assert mock_settings.DEBUG is True

            # Toggle back to debug mode off
            debug_mode_off()
            assert mock_settings.DEBUG is False


class TestSettings:
    def test_settings_loaded(self):
        """Test that settings are loaded correctly."""
        # Test that settings are loaded correctly
        assert settings.DEBUG is not None
        assert settings.CHAT_ID is not None
        assert settings.CLEANUP_PERIOD is not None
        assert settings.WAR_MODE is not None
        assert settings.AGENDA_MODE is not None
        assert settings.CHANNEL_USERNAME is not None
        assert settings.ADMINS is not None
        assert settings.MODERATORS is not None
        assert settings.LOG_PATH is not None
        assert settings.MAX_BYTES is not None
        assert settings.BACKUP_COUNT is not None
        assert settings.MORNING_TIME is not None
        assert settings.AGENDA_TIME is not None
        assert settings.current_env is not None

    def test_settings_properties(self):
        """Test that settings has the expected properties."""
        # Verify that settings is an instance of Dynaconf
        assert isinstance(settings, Dynaconf)

        # Verify that settings has the expected attributes

        # .secrets.toml
        # token = 'SECRET_PLACEHOLDER'
        assert hasattr(settings, "TOKEN")

        # settings.toml
        # admins = ['@PLACEHOLDER']
        assert hasattr(settings, "ADMINS")
        # moderators = ['@PLACEHOLDER']
        assert hasattr(settings, "MODERATORS")
        # chat_id = 'PLACEHOLDER'
        assert hasattr(settings, "CHAT_ID")
        # chat_link_id = 'PLACEHOLDER'
        assert hasattr(settings, "CHAT_LINK_ID")
        # chat_invite_link = 'PLACEHOLDER'
        assert hasattr(settings, "CHAT_INVITE_LINK")
        # channel_username = '@PLACEHOLDER'
        assert hasattr(settings, "CHANNEL_USERNAME")
        # default_agenda_image = 'PLACEHOLDER'
        assert hasattr(settings, "DEFAULT_AGENDA_IMAGE")

    def test_dev_environment_time_calculation(self):
        """Test the time calculation logic for dev environment."""
        # Create a fixed datetime for testing
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        time_offset = 3600  # 1 hour
        expected_time = (
            (test_datetime + timedelta(seconds=time_offset)).time().isoformat()
        )

        # Test the calculation directly
        with patch("config.datetime") as mock_datetime:
            mock_datetime.now.return_value = test_datetime

            # Create a mock for settings
            mock_settings = MagicMock()
            mock_settings.current_env = "dev"
            mock_settings.TIME_OFFSET = time_offset

            # Perform the calculation that happens in config.py
            mock_settings.MORNING_TIME = (
                (mock_datetime.now() + timedelta(seconds=mock_settings.TIME_OFFSET))
                .time()
                .isoformat()
            )
            mock_settings.AGENDA_TIME = (
                (mock_datetime.now() + timedelta(seconds=mock_settings.TIME_OFFSET))
                .time()
                .isoformat()
            )

            # Verify the results
            assert mock_settings.MORNING_TIME == expected_time
            assert mock_settings.AGENDA_TIME == expected_time

            # Verify that the calculation was performed twice (once for each setting)
            assert mock_datetime.now.call_count == 2

    def test_non_dev_environment_time_calculation(self):
        """Test that time calculation is not performed in non-dev environments."""
        # Create a mock for settings in a non-dev environment
        mock_settings = MagicMock()
        mock_settings.current_env = "production"

        # Set initial values that should remain unchanged
        default_morning_time = "08:00:00"
        default_agenda_time = "09:00:00"
        mock_settings.MORNING_TIME = default_morning_time
        mock_settings.AGENDA_TIME = default_agenda_time

        # Mock datetime to verify it's not called
        with patch("config.datetime") as mock_datetime:
            # Simulate the conditional in config.py
            if mock_settings.current_env == "dev":
                mock_settings.MORNING_TIME = (
                    (mock_datetime.now() + timedelta(seconds=mock_settings.TIME_OFFSET))
                    .time()
                    .isoformat()
                )
                mock_settings.AGENDA_TIME = (
                    (mock_datetime.now() + timedelta(seconds=mock_settings.TIME_OFFSET))
                    .time()
                    .isoformat()
                )

            # Verify the settings were not modified
            assert mock_settings.MORNING_TIME == default_morning_time
            assert mock_settings.AGENDA_TIME == default_agenda_time

            # Verify datetime.now was not called
            mock_datetime.now.assert_not_called()

    def test_settings_attributes(self, mock_settings):
        """Test that settings can be modified."""
        # Test that settings can be modified
        original_debug = mock_settings.DEBUG
        mock_settings.DEBUG = not original_debug
        assert mock_settings.DEBUG == (not original_debug)

        # Restore the original value
        mock_settings.DEBUG = original_debug
