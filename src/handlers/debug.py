from dynaconf import settings
import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

import utils


def create_handlers() -> list:
    """Creates handlers that process prod/debug modes."""
    return [
        CommandHandler(
            'debug', debug_on, filters.User(username=settings.ADMINS)),
        CommandHandler(
            'debug_off', debug_off, filters.User(username=settings.ADMINS))]


async def debug_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the debug mode."""
    settings.DEBUG = True
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    utils.log('debug_on')


async def debug_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the prod mode."""
    utils.log('debug_off')
    settings.DEBUG = False
    logging.getLogger(__name__).setLevel(logging.INFO)
