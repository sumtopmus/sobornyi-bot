from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from config import settings, debug_mode_on, debug_mode_off
from utils import log


def create_handlers() -> list:
    """Creates handlers that process prod/debug modes."""
    return [
        CommandHandler("debug", debug_on, filters.User(username=settings.ADMINS)),
        CommandHandler("debug_off", debug_off, filters.User(username=settings.ADMINS)),
    ]


async def debug_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the debug mode."""
    debug_mode_on()
    log("debug_on")


async def debug_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the prod mode."""
    log("debug_off")
    debug_mode_off()
