# sobornyi-bot

Telegram bot for managing the Sobornyi group. Built with `python-telegram-bot` and `dynaconf`.

## Commands

```bash
make setup        # First-time setup (conda env + config generation)
make run          # Production mode (ENV_FOR_DYNACONF=prod, clears cache)
make debug        # Dev mode (ENV_FOR_DYNACONF=dev, clears cache+logs+conversations)
make test         # Run all tests
make test-unit    # Run unit tests only (excludes @pytest.mark.integration)
make test-cov     # Run tests with coverage, opens htmlcov/index.html
make migrate      # Run data migration tool
make init-dev     # Install pre-commit hooks + dev dependencies
```

## Architecture

```
src/
  bot.py          # Entry point — registers all handlers and starts polling
  config.py       # Dynaconf settings instance; debug_mode_on/off helpers
  init.py         # Bot initialization logic
  utils.py        # Shared utilities
  handlers/       # Telegram update handlers (commands, events)
    calendar/     # Multi-step calendar conversation handler
    debug/        # /debug, /debug_off, /info commands
    channel.py    # Cross-posting channel posts to group
    request.py    # Join request auto-approval
    topic.py      # /topic, /offtop commands
    war.py        # /war, /war_off commands (morning minute of silence)
    welcome.py    # New member welcome flow
  model/          # Data models (calendar, event)
  format/         # Formatting helpers (dates, links, Telegram markdown)
  templates/      # Message templates
config/
  settings.toml   # Default settings for all environments
tests/            # Pytest tests — mirrors src/ structure
tools/            # CLI tools (migration.py, generate_config.py)
```

## Configuration

Uses `dynaconf` with layered config files:

| File | Purpose | Tracked |
|------|---------|---------|
| `config/settings.toml` | Default values for all envs | Yes |
| `config/settings.local.yml` | Local overrides (dev + prod chat IDs, etc.) | No |
| `config/.secrets.local.yml` | Bot token and secrets | No |

Config is accessed via `from config import settings`. Environment selected by `ENV_FOR_DYNACONF` env var (`dev` or `prod`).

**Gotcha:** In `dev` env, `MORNING_TIME` and `AGENDA_TIME` are overridden at startup to `now + TIME_OFFSET` seconds — this makes scheduled jobs fire quickly for manual testing.

## Testing

- Tests live in `tests/`, pytest is configured via `pytest.ini` with `pythonpath = src`
- `asyncio_mode = auto` — all async tests work without extra decorators
- Tests always run with `DYNACONF_ENV=dev` (set in `pytest.ini`)
- Integration tests are marked with `@pytest.mark.integration`; run separately with `make test-integration`

## Data Persistence

File-based storage in `data/`:
- `data/db` — main persistent store (bot state, users, events)
- `data/db_conversations` — active conversation state (cleared by `make clean-state`)
- `data/db_callback_data` — callback query data (cleared by `make clean-state`)

Logs go to `logs/bot.log` with rotation (1 MB max, 5 backups).
