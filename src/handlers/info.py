from dynaconf import settings
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

import utils


def create_handlers() -> list:
    """Creates handlers that process admin's `info` command."""
    return [CommandHandler('info', info, filters.User(username=settings.ADMINS))]


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Basic admin info command."""
    utils.log('info')
    utils.log(f'chat_id: {update.effective_chat.id}')
    utils.log(f'user_id: {update.effective_user.id}')