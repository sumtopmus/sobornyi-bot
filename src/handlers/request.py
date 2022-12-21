# coding=UTF-8

from dynaconf import settings
from telegram import Update
from telegram.ext import ChatJoinRequestHandler, ContextTypes

import utils


def create_handlers() -> list:
    """Creates handlers that process join requests."""
    return [ChatJoinRequestHandler(request, chat_id=settings.CHAT_ID)]


async def request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When a join request is sent."""
    utils.log('request')
    await update.chat_join_request.from_user.approve_join_request(
        update.chat_join_request.chat.id)
