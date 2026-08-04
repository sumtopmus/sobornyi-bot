# Sobornyi Bot

Telegram bot to control the Sobornyi group.

## Setup Guide

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (>=0.11)
- Telegram account

### Initial Setup

1. Create a bot through [@BotFather](https://t.me/BotFather) and get your bot token.
2. Create a Telegram chat group for the bot to manage.
3. Create a Telegram channel for announcements.
4. Add your bot to both the group and channel as an admin with full rights.
5. Configure the project:

   ```bash
   # Clone the repository
   git clone <repository-url>
   cd sobornyi-bot

   # Quick setup (creates environment, installs dependencies, generates config files)
   make setup
   ```

6. Update configuration files:
   - Edit `config/settings.local.yml` with your specific environment settings for `dev` and `prod`.
   - Add your bot token to `config/.secrets.local.yml`.

7. Run the bot:

   ```bash
   # Development mode with debug logging
   make debug

   # Production mode
   make run
   ```

**Hint**: To get the `chat_id` of a group, turn on "Show Peer IDs in Profile" in Telegram Desktop.

## Usage Guide

### Bot Commands

The bot offers various commands organized by function:

#### Moderator Commands

- `/topic [name]` - Redirect discussion to a specific topic thread
- `/offtop` - Redirect off-topic discussions to the dedicated thread
- `/calendar` - Access the event calendar menu for creating, editing, and managing events
- `/cancel` - Cancel an ongoing conversation with the bot

#### Admin Commands

- `/war` - Enable war mode with morning minute of silence
- `/war_off` - Disable war mode notifications

#### Dev/Debug Commands

- `/debug` - Enable debug mode with verbose logging
- `/debug_off` - Disable debug mode and return to normal logging levels
- `/info` - Display information about the current chat, including chat ID and configuration details
- `/upload` - Start conversation to upload photos to the bot storage

#### Auto-Processed Events

- **New Members** - Bot automatically welcomes new members to the group
- **Join Requests** - Bot automatically processes join requests to the group
- **Channel Posts** - Bot manages cross-posting between the channel and group

### Maintenance Commands

Use these Makefile commands to maintain the bot:

```bash
# Backup data and logs
make backup

# Clean all generated files
make clean

# Clean only cache and logs (keeps data)
make clean-state

# Run tests
make test

# Run tests with coverage report
make test-cov

# Display code coverage in browser
make display-coverage
```

## Data Migration

When updating the model structure, you may need to migrate your persistent data. The bot includes a migration tool for this purpose:

```bash
# Run database migrations
make migrate

# Show migration help
make migrate-help
```

For advanced migration options:

```bash
# Run with specific options
uv run python tools/migration.py --source /path/to/old/data --target /path/to/new/data

# Migrate only specific data types
uv run python tools/migration.py --bot-only
uv run python tools/migration.py --chat-only
uv run python tools/migration.py --user-only

# Other options
uv run python tools/migration.py --no-backup  # Skip creating backups
uv run python tools/migration.py --verbose    # Enable verbose logging
```

For more information about the migration tool, see [tools/README.md](tools/README.md).

## Complete Makefile Reference

| Command | Description |
|---------|-------------|
| `make` | ℹ️ Show this help message |
| `make setup` | 🏗️ First-time setup: install dependencies and configure project |
| `make env` | 📦 Create virtual environment and install dependencies |
| `make init-dev` | 🛠️ Setup development environment with pre-commit hooks |
| `make run` | 🚀 Run bot in production mode |
| `make debug` | 🐞 Run bot in debug mode |
| `make backup` | 💾 Create backup of data and logs |
| `make migrate` | 🔄 Run database migrations |
| `make migrate-help` | 🚑 Show migration help |
| `make test` | 🧪 Run all tests |
| `make test-unit` | 🔬 Run unit tests only |
| `make test-integration` | 🔌 Run integration tests only |
| `make test-cov` | 📊 Run tests with coverage report |
| `make display-coverage` | 📈 Open coverage report in browser |
| `make clean` | 🧹 Remove all generated files |
| `make clean-state` | 🧼 Clean cache and logs |
| `make clean-cache` | 🗑️ Remove cache files |
| `make clean-logs` | 📝 Remove log files |
| `make clean-data` | 📁 Remove data files |
| `make clean-conversations` | 💬 Remove conversation files |
| `make config` | 🧰 Generate configuration files |
| `make version` | 🏷️ Show the project version |
| `make docs` | 📚 Generate project documentation |
| `make lock` | 🔒 Upgrade and relock dependencies |
| `make check-deps` | ✅ Check if required tools are installed |

## Development

For developers looking to contribute:

1. Set up the development environment:

   ```bash
   make init-dev
   ```

2. This installs pre-commit hooks and development dependencies.

   **Updating an existing clone?** Re-run `make init-dev` after pulling the uv
   migration — the previously installed pre-commit hook points at the old
   conda interpreter and will stop working once that environment is gone.

3. Before committing changes, run tests:

   ```bash
   make test
   ```

## Version

Current version: Use `make version` to display.
