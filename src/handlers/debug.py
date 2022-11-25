from telegram import Update
from telegram.ext import BaseHandler, CommandHandler, ContextTypes, ConversationHandler, filters

import config
import tools


def create_handlers() -> list:
    """Creates a handler that processes prod/debug modes."""
    debug_on_handler = CommandHandler(
        'debug_on', debug_on, filters.User(config.ADMIN_ID) & filters.Chat(config.CHAT_ID))
    debug_off_handler = CommandHandler(
        'debug_off', debug_off, filters.User(config.ADMIN_ID) & filters.Chat(config.CHAT_ID))
    debug_switch_handler = CommandHandler(
        'debug', debug_switch, filters.User(config.ADMIN_ID) & filters.Chat(config.CHAT_ID))
    return [debug_on_handler, debug_off_handler, debug_switch_handler]


async def debug_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the dev mode."""
    tools.debug('debug_on')
    config.DEBUG_MODE = True


async def debug_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the prod mode."""
    tools.debug('debug_off')
    config.DEBUG_MODE = False


async def debug_switch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch between dev and prod modes."""
    tools.debug('debug_switch')
    config.DEBUG_MODE = not config.DEBUG_MODE
