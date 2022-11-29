from telegram import Update
from telegram.ext import BaseHandler, CommandHandler, ContextTypes, ConversationHandler, filters

import config
import tools


def create_handlers() -> list:
    """Creates handlers that process prod/debug modes."""
    debug_on_handler = CommandHandler(
        'debug', debug_on,
        filters.User(username=config.ADMINS) & filters.Chat(config.CHAT_ID))
    debug_off_handler = CommandHandler(
        'debug_off', debug_off,
        filters.User(username=config.ADMINS) & filters.Chat(config.CHAT_ID))
    debug_toggle_handler = CommandHandler(
        'debug_toggle', debug_toggle,
        filters.User(username=config.ADMINS) & filters.Chat(config.CHAT_ID))
    return [debug_on_handler, debug_off_handler, debug_toggle_handler]


async def debug_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the debug mode."""
    tools.debug('debug_on')
    config.DEBUG_MODE = True


async def debug_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the prod mode."""
    tools.debug('debug_off')
    config.DEBUG_MODE = False


async def debug_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle between dev and prod modes."""
    tools.debug('debug_toggle')
    config.DEBUG_MODE = not config.DEBUG_MODE
