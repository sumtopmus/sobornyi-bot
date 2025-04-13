"""Tests for the utils module."""

import hashlib
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import telegram.error

from utils import (
    MESSAGE_CLEANUP_JOB,
    add_job,
    add_message_cleanup_job,
    calculate_hash,
    clear_jobs,
    log,
    message_cleanup,
)


class TestLog:
    def test_log_with_debug_off(self, mock_settings, caplog):
        mock_settings.DEBUG = False
        with patch("utils.logging.getLogger") as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value.log = mock_log

            log("Test message")

            mock_log.assert_called_once()
            mock_logger.assert_called_once_with("utils")

    def test_log_with_debug_on(self, mock_settings, caplog):
        mock_settings.DEBUG = True
        with patch("utils.logging.getLogger") as mock_logger, patch(
            "utils.print"
        ) as mock_print, patch("utils.datetime") as mock_datetime:

            mock_log = MagicMock()
            mock_logger.return_value.log = mock_log
            mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

            log("Test message")

            mock_log.assert_called_once()
            mock_print.assert_called_once_with("⌚️ 2023-01-01 12:00:00: Test message")


class TestCalculateHash:
    def test_calculate_hash(self):
        # Test with a known input and expected output
        test_text = "test_string"
        expected_hash = hashlib.sha256(test_text.encode("utf-8")).hexdigest()

        result = calculate_hash(test_text)

        assert result == expected_hash
        assert len(result) == 64  # SHA-256 produces a 64-character hex string


class TestMessageCleanup:
    @pytest.mark.asyncio
    async def test_message_cleanup_success(self, mock_context, mock_settings):
        # Test successful message deletion
        await message_cleanup(mock_context)

        mock_context.bot.delete_message.assert_called_once_with(
            mock_settings.CHAT_ID, mock_context.job.data
        )
        mock_context.application.job_queue.get_jobs_by_name.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_cleanup_error(self, mock_context, mock_settings):
        # Test handling of deletion error
        mock_context.bot.delete_message.side_effect = telegram.error.BadRequest(
            "Message to delete not found"
        )

        with patch("utils.log") as mock_log:
            await message_cleanup(mock_context)

            # Check that the error was logged
            mock_log.assert_any_call(
                "BadRequest: Message to delete not found", logging.ERROR
            )


class TestJobManagement:
    def test_add_job(self, mock_context):
        app = mock_context.application
        job_function = MagicMock()
        delay = timedelta(seconds=60)
        job_family = "test_job"
        job_data = 123

        with patch("utils.log") as mock_log, patch("utils.datetime") as mock_datetime:

            mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
            expected_time = mock_datetime.now.return_value + delay

            add_job(job_function, delay, app, job_family, job_data)

            # Check that the job was added to the queue
            app.job_queue.run_once.assert_called_once_with(
                job_function, delay, data=job_data, name=f"{job_family}:{job_data}"
            )

            # Check that the job was stored in bot_data
            assert app.bot_data["jobs"][f"{job_family}:{job_data}"] == {
                "time": expected_time,
                "data": job_data,
            }

    def test_add_message_cleanup_job(self, mock_context):
        app = mock_context.application
        message_id = 12345

        with patch("utils.add_job") as mock_add_job, patch(
            "utils.log"
        ) as mock_log, patch("utils.timedelta") as mock_timedelta:

            mock_timedelta.return_value = timedelta(seconds=60)

            add_message_cleanup_job(app, message_id)

            # Check that add_job was called with the correct parameters
            mock_add_job.assert_called_once_with(
                message_cleanup,
                mock_timedelta.return_value,
                app,
                MESSAGE_CLEANUP_JOB,
                message_id,
            )

    def test_clear_jobs_with_data(self, mock_context):
        app = mock_context.application
        job_family = "test_job"
        job_data = 123
        job_name = f"{job_family}:{job_data}"

        # Set up mock jobs
        mock_job1 = MagicMock()
        mock_job2 = MagicMock()
        app.job_queue.get_jobs_by_name.return_value = [mock_job1, mock_job2]
        app.bot_data["jobs"][job_name] = {"time": datetime.now(), "data": job_data}

        with patch("utils.log") as mock_log:
            clear_jobs(app, job_family, job_data)

            # Check that jobs were removed from the queue
            app.job_queue.get_jobs_by_name.assert_called_once_with(job_name)
            mock_job1.schedule_removal.assert_called_once()
            mock_job2.schedule_removal.assert_called_once()

            # Check that the job was removed from bot_data
            assert job_name not in app.bot_data["jobs"]

    def test_clear_jobs_without_data(self, mock_context):
        app = mock_context.application
        job_family = "test_job"

        with patch("utils.log") as mock_log:
            clear_jobs(app, job_family)

            # Check that jobs were looked up with just the job family
            app.job_queue.get_jobs_by_name.assert_called_once_with(job_family)
