# Tests for Sobornyi Bot

This directory contains tests for the Sobornyi Bot application.

## Structure

- `conftest.py`: Contains pytest fixtures used across multiple test files
- `test_utils.py`: Tests for utility functions in `src/utils.py`
- `test_config.py`: Tests for configuration functions in `src/config.py`
- `test_init.py`: Tests for initialization functions in `src/init.py`

## Running Tests

To run all tests:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=src
```

To run a specific test file:

```bash
pytest tests/test_utils.py
```

## Fixtures

The `conftest.py` file provides several fixtures for testing:

- `disable_logging`: Disables logging during tests
- `mock_settings`: Mocks the settings object
- `mock_user`: Mocks a Telegram User
- `mock_chat`: Mocks a Telegram Chat
- `mock_message`: Mocks a Telegram Message
- `mock_update`: Mocks a Telegram Update
- `mock_context`: Mocks a Telegram Context

## Environment

Tests run with `DYNACONF_ENV=dev` to ensure they use the development configuration.
