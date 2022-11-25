# coding=UTF-8

from telegram import Update
from telegram.ext import ChatJoinRequestHandler, ContextTypes

import config
import tools


def create_handlers() -> list:
    """Creates a handler that processses join requests."""
    return [ChatJoinRequestHandler(request, chat_id=config.CHAT_ID)]


async def request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When a join request is sent."""
    tools.debug('request')
    await update.chat_join_request.from_user.approve_join_request(
        update.chat_join_request.chat.id)
