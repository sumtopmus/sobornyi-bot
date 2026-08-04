# Migration Tool

This document describes how to use the migration tool to update persistent data (bot/chat/user data) when moving to a newer model structure.

## Overview

The migration tool is designed to help you migrate your bot's persistent data when you make changes to the model structure. It can:

- Create backups of your data before migration
- Load data from pickle files
- Transform data from old format to new format
- Save migrated data to new files
- Log all operations to both console and file

## Usage

### Basic Usage

To run the migration tool with default settings, you can use the Makefile command:

```bash
make migrate
```

Or run the Python module directly:

```bash
uv run python -m tools.migration
```

You can also run the script directly (it's executable):

```bash
uv run ./tools/migration.py
```

This will:

1. Create backups of your data files in a `backup` directory
2. Load data from the default data directory (`data/db`)
3. Migrate the data to the new format
4. Save the migrated data back to the same directory
5. Log all operations to both console and file (`logs/migration.log`)

### Advanced Usage

The migration tool provides several command-line options:

```bash
uv run python -m tools.migration --help
```

```text
usage: migration.py [-h] [--source SOURCE] [--target TARGET] [--no-backup] [--bot-only] [--chat-only] [--user-only] [--verbose] [--no-console]

Migrate persistent data to newer model structures

options:
  -h, --help       show this help message and exit
  --source SOURCE  Path to the source data directory
  --target TARGET  Path to the target data directory (if different from source)
  --no-backup      Do not create backups of the source data
  --bot-only       Only migrate bot data
  --chat-only      Only migrate chat data
  --user-only      Only migrate user data
  --verbose        Enable verbose logging
  --no-console     Disable console logging (log to file only)
```

#### Examples

Migrate data from a specific directory to another directory:

```bash
uv run python -m tools.migration --source /path/to/old/data --target /path/to/new/data
```

Migrate only bot data:

```bash
uv run python -m tools.migration --bot-only
```

Migrate without creating backups:

```bash
uv run python -m tools.migration --no-backup
```

Enable verbose logging:

```bash
uv run python -m tools.migration --verbose
```

Disable console logging (log to file only):

```bash
uv run python -m tools.migration --no-console
```

## Testing the Migration

You can test the migration tool with sample data using the Makefile command:

```bash
make migrate-test
```

Or run the Python module directly:

```bash
uv run python -m tools.migration_test
```

You can also run the test script directly (it's executable):

```bash
uv run ./tools/migration_test.py
```

This will:

1. Create test data in both old and new formats
2. Run the migration on the old format data
3. Compare the migrated data with the new format data

## Customizing the Migration

When you make changes to your model structure, you'll need to update the migration logic in the `MigrationTool` class. The main methods to customize are:

- `_migrate_event`: Migrates an event from old format to new format
- `_migrate_calendar`: Migrates a calendar from old format to new format
- `_migrate_bot_data`: Migrates bot data
- `_migrate_chat_data`: Migrates chat data
- `_migrate_user_data`: Migrates user data

The migration tool uses a `DATA` enum to specify which data to migrate:

```python
DATA = Enum("DATA", ["ALL", "BOT", "CHAT", "USER"])
```

You can use the `migrate` method with the appropriate `DATA` enum value to migrate specific data:

```python
migration_tool = MigrationTool(source_path, target_path)
migration_tool.migrate(DATA.BOT)  # Migrate only bot data
migration_tool.migrate(DATA.ALL)  # Migrate all data
```

### Example: Adding a New Field to the Event Model

If you add a new field to the `Event` model, you'll need to update the `_migrate_event` method to handle the new field:

```python
def _migrate_event(self, event_data: Dict[str, Any]) -> Event:
    # ... existing migration logic ...

    # Handle the new field
    if "new_field" not in event_data:
        event_data["new_field"] = default_value

    # ... rest of migration logic ...

    return Event(**event_data)
```

### Example: Renaming a Field

If you rename a field in your model, you'll need to update the migration logic to handle the rename:

```python
def _migrate_event(self, event_data: Dict[str, Any]) -> Event:
    # ... existing migration logic ...

    # Handle renamed field
    if "old_field_name" in event_data:
        event_data["new_field_name"] = event_data.pop("old_field_name")

    # ... rest of migration logic ...

    return Event(**event_data)
```

## Logging

The migration tool includes comprehensive logging to help you track the migration process. Logs are written to both the console and a log file (`logs/migration.log`) by default.

By default, the tool logs at the INFO level, which includes basic information about the migration process. You can enable more detailed logging by using the `--verbose` flag, which sets the logging level to DEBUG.

You can disable console logging by using the `--no-console` flag, which will make the tool log only to the file. This is useful for running the migration in a script or as a background process.

The log file includes timestamps and more detailed information than the console output, making it useful for debugging migration issues.

## Best Practices

1. **Always create backups before migration**: The migration tool creates backups by default, but you can also manually back up your data.
2. **Test the migration on a copy of your data first**: Use the `--target` option to save migrated data to a different directory.
3. **Update the migration logic when you change your model structure**: Keep the migration tool up to date with your model changes.
4. **Version your data format**: Consider adding a version field to your data to track which migration has been applied.
5. **Check the logs**: The migration tool logs all operations to `logs/migration.log`.

## Troubleshooting

If you encounter issues during migration:

1. Check the migration log at `logs/migration.log`
2. Run the migration with the `--verbose` flag to get more detailed logging
3. Restore from backup if needed (backups are stored in the `backup` directory)
4. Update the migration logic to handle any edge cases

If you need to restore from a backup:

```bash
cp data/db/backup/db_bot_data_YYYYMMDD_HHMMSS data/db/db_bot_data
cp data/db/backup/db_chat_data_YYYYMMDD_HHMMSS data/db/db_chat_data
cp data/db/backup/db_user_data_YYYYMMDD_HHMMSS data/db/db_user_data
```
