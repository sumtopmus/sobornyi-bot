import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from config import settings
from utils import log


def create_handlers() -> list:
    """Creates handlers that process admin's `info` command."""
    return [CommandHandler('info', info, filters.User(username=settings.ADMINS))]


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Basic admin info command."""
    log('info')
    log(f'chat_id: {update.effective_chat.id}', logging.INFO)
    log(f'user_id: {update.effective_user.id}', logging.INFO)