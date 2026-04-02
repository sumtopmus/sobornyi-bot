---
name: add-telegram-command
description: Use when adding a new command or handler to the sobornyi-bot Telegram bot. Covers simple commands, access-controlled commands, and conversation handlers.
---

# Adding a Telegram Command to sobornyi-bot

## Overview

All handlers follow the same registration pattern: a module with a `create_handlers() -> list` function that is imported and listed in `src/handlers/__init__.py`.

## Quick Reference

| Handler type | Use for |
|---|---|
| `CommandHandler` | `/command` slash commands |
| `MessageHandler` | Reacting to messages (by type/content) |
| `ChatJoinRequestHandler` | Join request events |
| `ConversationHandler` | Multi-step dialogs |

Access control filters:

| Filter | Who |
|---|---|
| `filters.User(username=settings.ADMINS)` | Admins only |
| `filters.User(username=settings.MODERATORS)` | Moderators only |
| `filters.User(username=settings.ADMINS + settings.MODERATORS)` | Admins or moderators |
| `filters.Chat(settings.CHAT_ID)` | Main group chat only |

## Implementation

### Step 1 — Create the handler file

**Business logic command** → `src/handlers/mycommand.py`
**Dev/debug command** → `src/handlers/debug/mycommand.py`

Minimal template:

```python
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from config import settings
import utils


def create_handlers() -> list:
    """Creates handlers for the `mycommand` command."""
    return [
        CommandHandler(
            "mycommand",
            mycommand,
            filters.Chat(settings.CHAT_ID) & filters.User(username=settings.ADMINS),
        )
    ]


async def mycommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """What this command does."""
    utils.log("mycommand")
    await update.message.reply_text("Response text")
```

Notes:
- Default parse mode is Markdown (set globally in `bot.py`).
- `utils.log("func_name")` logs at DEBUG level and prints when `settings.DEBUG` is on.
- `context.args` holds space-separated arguments after the command.
- `context.bot_data` is the persistent dict shared across all handlers.

### Step 2 — Register in `src/handlers/__init__.py`

Add an import and include the module in `modules`:

```python
# existing imports ...
from . import mycommand   # add this

modules = [calendar, channel, mycommand, request, topic, war, welcome]  # add mycommand
```

For a **debug command**, add to `src/handlers/debug/__init__.py` instead:

```python
from . import mycommand   # add this

handlers = []
for module in [debug, info, mycommand, upload]:   # add mycommand
    handlers.extend(module.create_handlers())
```

### Step 3 — Add to CLAUDE.md and README.md (optional)

Document the new command in the Bot Commands section of [README.md](README.md) and the relevant section of [CLAUDE.md](CLAUDE.md).

## Common Mistakes

- **Missing `async`** — handler functions must be `async def`; only sync helpers (like `enable_war_mode`) can be plain `def`.
- **Wrong filter order** — combine filters with `&`: `filters.Chat(...) & filters.User(...)`.
- **Forgetting registration** — adding the file without updating `__init__.py` means the handler is never registered and silently ignored.
- **No `utils.log`** — omitting the log call makes debugging hard; always add it as the first line.
