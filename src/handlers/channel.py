import logging
from telegram import Message, Update
from telegram.ext import MessageHandler, ContextTypes, filters

from config import settings
import utils


def create_handlers() -> list:
    """Creates handlers that process channel posts."""
    return [
        MessageHandler(
            filters.SenderChat(username=settings.CHANNEL_USERNAME)
            & filters.UpdateType.CHANNEL_POST,
            post,
        ),
        MessageHandler(
            filters.SenderChat(username=settings.CHANNEL_USERNAME)
            & filters.UpdateType.EDITED_CHANNEL_POST,
            edit,
        ),
    ]


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When new post appeares on the channel."""
    utils.log("post")
    if update.channel_post.text or update.channel_post.caption:
        await cross_post(update.channel_post, context)
    elif update.channel_post.pinned_message:
        message_to_pin_id = context.chat_data["cross-posts"].setdefault(
            update.channel_post.pinned_message.id, None
        )
        if not message_to_pin_id:
            utils.log(f"pinned message is missing from the index", logging.INFO)
            return
        await context.bot.pin_chat_message(settings.CHAT_ID, message_to_pin_id)


async def cross_post(message: Message, context: ContextTypes.DEFAULT_TYPE) -> None:
    if message.text:
        text = message.text
    elif message.caption:
        text = message.caption
    else:
        return
    target_thread_id = None
    current_priority = float("inf")
    for tag, thread in settings.TAGS.items():
        if tag in text and settings.PRIORITIES[thread] < current_priority:
            target_thread_id = settings.TOPICS[thread]
            current_priority = settings.PRIORITIES[thread]
    copy = await message.copy(settings.CHAT_ID, message_thread_id=target_thread_id)
    context.chat_data["cross-posts"][message.id] = copy.message_id


async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When a post is edited on the channel."""
    utils.log("edit")
    copied_message_id = context.chat_data["cross-posts"].setdefault(
        update.edited_channel_post.id, None
    )
    if not copied_message_id:
        utils.log(f"message is missing from the index")
        return
    if update.edited_channel_post.text:
        await context.bot.edit_message_text(
            update.edited_channel_post.text,
            chat_id=settings.CHAT_ID,
            message_id=copied_message_id,
            entities=update.edited_channel_post.entities,
            parse_mode=None,
        )
    if update.edited_channel_post.caption:
        await context.bot.edit_message_caption(
            chat_id=settings.CHAT_ID,
            message_id=copied_message_id,
            caption=update.edited_channel_post.caption,
            caption_entities=update.edited_channel_post.caption_entities,
            parse_mode=None,
        )
