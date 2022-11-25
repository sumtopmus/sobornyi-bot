from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

import config
import tools


# Creates a handler for application.
def create_handlers() -> list:
    """Creates a handler that processes admin's `info` command."""
    return [CommandHandler('info', info, filters.User(username=config.ADMINS))]

# Basic admin info command.
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tools.debug('info')
    tools.debug(f'chat_id: {update.effective_chat.id}')
    tools.debug(f'user_id: {update.effective_user.id}')