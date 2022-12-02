# coding=UTF-8

from dynaconf import settings
from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

import tools


def create_handlers() -> list:
    """Creates handlers that process channel posts."""
    return [
        MessageHandler(
            filters.SenderChat(username=settings.CHANNEL_USERNAME)
            & filters.UpdateType.CHANNEL_POST,
            post),
        MessageHandler(
            filters.SenderChat(username=settings.CHANNEL_USERNAME)
            & filters.UpdateType.EDITED_CHANNEL_POST,
            edit)
    ]


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When new post appeares on the channel."""
    tools.debug('post')
    copy = await update.channel_post.copy(
        settings.CHAT_ID, message_thread_id=settings.CHANNEL_THREAD_ID)
    context.chat_data.setdefault('channel-thread', {})[update.channel_post.id] = copy.message_id


async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When a post is edited on the channel."""
    tools.debug('edit')
    copied_message_id = context.chat_data.setdefault('channel-thread', {}).setdefault(
        update.edited_channel_post.id, None)
    if not copied_message_id:
        return
    await context.bot.edit_message_text(
        update.edited_channel_post.text_markdown, settings.CHAT_ID, copied_message_id)