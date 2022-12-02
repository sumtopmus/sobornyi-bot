from dynaconf import settings
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

import tools


def create_handlers() -> list:
    """Creates handlers that process admin's `info` command."""
    return [CommandHandler('info', info, filters.User(username=settings.ADMINS))]

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Basic admin info command."""
    tools.debug('info')
    tools.debug(f'chat_id: {update.effective_chat.id}')
    tools.debug(f'user_id: {update.effective_user.id}')