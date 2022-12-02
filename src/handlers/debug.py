from dynaconf import settings
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

import tools


def create_handlers() -> list:
    """Creates handlers that process prod/debug modes."""
    debug_on_handler = CommandHandler(
        'debug', debug_on, filters.User(username=settings.ADMINS))
    debug_off_handler = CommandHandler(
        'debug_off', debug_off, filters.User(username=settings.ADMINS))
    debug_toggle_handler = CommandHandler(
        'debug_toggle', debug_toggle, filters.User(username=settings.ADMINS))
    return [debug_on_handler, debug_off_handler, debug_toggle_handler]


async def debug_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the debug mode."""
    settings.DEBUG = True
    tools.debug('debug_on')


async def debug_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the prod mode."""
    tools.debug('debug_off')
    settings.DEBUG = False


async def debug_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle between dev and prod modes."""
    tools.debug('debug_toggle')
    settings.DEBUG = not settings.DEBUG
