from dynaconf import settings
import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

import tools


def create_handlers() -> list:
    """Creates handlers that process prod/debug modes."""
    debug_on_handler = CommandHandler(
        'debug', debug_on, filters.User(username=settings.ADMINS))
    debug_off_handler = CommandHandler(
        'debug_off', debug_off, filters.User(username=settings.ADMINS))
    return [debug_on_handler, debug_off_handler]


async def debug_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the debug mode."""
    settings.DEBUG = True
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    tools.log('debug_on')


async def debug_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the prod mode."""
    tools.log('debug_off')
    settings.DEBUG = False
    logging.getLogger(__name__).setLevel(logging.INFO)
