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
            edit)]


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When new post appeares on the channel."""
    tools.log('post')
    if update.channel_post.text or update.channel_post.caption:
        copy = await update.channel_post.copy(
            settings.CHAT_ID, message_thread_id=settings.TOPICS['agenda'])
        context.chat_data['channel-thread'][update.channel_post.id] = copy.message_id
    elif update.channel_post.pinned_message:
        message_to_pin_id = context.chat_data['channel-thread'].setdefault(
            update.channel_post.pinned_message.id, None)
        if not message_to_pin_id:
            tools.log(f'pinned message is missing from the index')
            return
        await context.bot.pin_chat_message(settings.CHAT_ID, message_to_pin_id)


async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When a post is edited on the channel."""
    tools.log('edit')
    copied_message_id = context.chat_data['channel-thread'].setdefault(
        update.edited_channel_post.id, None)
    if not copied_message_id:
        tools.log(f'message is missing from the index')
        return
    if update.edited_channel_post.text:
        await context.bot.edit_message_text(
            update.edited_channel_post.text, chat_id=settings.CHAT_ID, message_id=copied_message_id,
            entities=update.edited_channel_post.entities, parse_mode=None)
    if update.edited_channel_post.caption:
        await context.bot.edit_message_caption(
            chat_id=settings.CHAT_ID, message_id=copied_message_id,
            caption=update.edited_channel_post.caption,
            caption_entities=update.edited_channel_post.caption_entities, parse_mode=None)