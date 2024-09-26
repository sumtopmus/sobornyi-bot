from datetime import timedelta
from enum import Enum
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import telegram.error
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
    TypeHandler,
)

from config import settings
from handlers import topic
import utils


State = Enum("State", ["JOIN", "AWAITING"])


def create_handlers() -> list:
    """Creates handlers that process new users."""
    return [
        ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.Chat(settings.CHAT_ID)
                    & filters.StatusUpdate.NEW_CHAT_MEMBERS,
                    welcome,
                )
            ],
            states={
                State.AWAITING: [
                    MessageHandler(
                        filters.Chat(settings.CHAT_ID) & (~filters.Regex(r"#about")),
                        not_about,
                    ),
                    MessageHandler(
                        filters.Chat(settings.CHAT_ID) & filters.Regex(r"#about"), about
                    ),
                ],
                ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)],
            },
            fallbacks=[
                # TODO: add bot's goodbye message as a fallback.
            ],
            conversation_timeout=settings.WELCOME_TIMEOUT,
            name="welcome",
            persistent=True,
        )
    ]


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When new user enters the chat."""
    utils.log("welcome")
    for user in update.message.new_chat_members:
        utils.log(f"new user: {user.id} ({user.full_name})", logging.INFO)
        if user.is_bot:
            utils.log(f"new user is a bot")
            continue
        if "about" in context.user_data:
            utils.log(f"user {user.id} already introduced themselves", logging.INFO)
            message = f"Cлава Україні, {utils.mention(user)}! Вітаємо тебе в Соборному, знову!"
            reply_to_message_id = None if settings.FORUM else update.message.id
            bot_message = await context.bot.sendMessage(
                chat_id=update.message.chat.id,
                message_thread_id=settings.TOPICS["welcome"],
                text=message,
                reply_to_message_id=reply_to_message_id,
            )
            # cleanup job
            utils.add_message_cleanup_job(context.application, bot_message.id)
            return ConversationHandler.END
        message = (
            f"Cлава Україні, {utils.mention(user)}! Вітаємо тебе в Соборному!\n\n"
            "Ми хочемо познайомитися з тобою, так що розкажи трохи про себе (в цій гілці) "
            "і додай, будь ласка, до повідомлення теґ #about. "
            "На це у тебе є одна доба. Якщо ми від тебе нічого не почуємо, ми попрощаємось.\n\n"
            "Якщо ти хочеш виключно слідкувати за українськими подіями в DMV та іншою "
            "актуальною інформацією, можеш підписатися на наш канал."
        )
        reply_to_message_id = None if settings.FORUM else update.message.id
        channel = await context.bot.get_chat(settings.CHANNEL_USERNAME)
        button = InlineKeyboardButton(text="Підписатись", url=channel.link)
        reply_markup = InlineKeyboardMarkup([[button]])
        bot_message = await context.bot.sendMessage(
            chat_id=update.message.chat.id,
            message_thread_id=settings.TOPICS["welcome"],
            text=message,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        # cleanup job
        utils.add_message_cleanup_job(context.application, bot_message.id)
    return State.AWAITING


async def not_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user does not write #about."""
    utils.log("not_about")
    user = update.message.from_user
    reply_to_message_id = update.message.id
    message = (
        f"{utils.mention(user)}, додай, будь ласка, до свого повідомлення теґ #about"
    )
    if update.message.message_thread_id != settings.TOPICS["welcome"]:
        message += " і напиши його в цій гілці (у Вітальні)"
        reply_to_message_id = await topic.move(
            update, context, settings.TOPICS["welcome"]
        )
    message += "."
    bot_message = await context.bot.sendMessage(
        chat_id=update.message.chat.id,
        message_thread_id=settings.TOPICS["welcome"],
        text=message,
        reply_to_message_id=reply_to_message_id,
    )
    utils.add_message_cleanup_job(context.application, reply_to_message_id)
    utils.add_message_cleanup_job(context.application, bot_message.id)
    return State.AWAITING


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user writes #about."""
    utils.log("about")
    if update.message:
        incoming_message = update.message
    else:
        incoming_message = update.edited_message
        utils.clear_jobs(
            context.application, utils.MESSAGE_CLEANUP_JOB, incoming_message.id
        )
    context.user_data["about"] = incoming_message.text
    user = incoming_message.from_user
    utils.log(f"user introduced themselves: {user.id} ({user.full_name})", logging.INFO)
    message = f"Вітаємо тебе, {utils.mention(user)}!"
    if settings.FORUM:
        message += f"\n\n#️⃣ [Соборний](https://t.me/c/{settings.CHAT_LINK_ID}/1) – основна гілка\n"
        if "navigation" in settings.TOPICS:
            message += (
                f"🧭 [Навігація](https://t.me/c/{settings.CHAT_LINK_ID}/{settings.TOPICS['navigation']})"
                f" – що у нас є\n"
            )
        if "guides" in settings.TOPICS:
            message += (
                f"🗂️ [Довідник](https://t.me/c/{settings.CHAT_LINK_ID}/{settings.TOPICS['guides']})"
                f" – місцевий довідник\n"
            )
        if "agenda" in settings.TOPICS:
            message += (
                f"🗓 [Порядок тижневий](https://t.me/c/{settings.CHAT_LINK_ID}/{settings.TOPICS['agenda']})"
                f" – календар українських заходів в DMV\n"
            )
    utils.log(f"about: {user.id} ({user.full_name})", logging.INFO)
    reply_to_message_id = incoming_message.id
    if (
        incoming_message.message_thread_id
        and incoming_message.message_thread_id != settings.TOPICS["welcome"]
    ):
        try:
            if incoming_message.has_protected_content:
                raise telegram.error.Forbidden(
                    f"the message has protected content "
                    f"and can't be forwarded: {incoming_message.text}"
                )
            forwarded_message = await incoming_message.forward(
                settings.CHAT_ID, message_thread_id=settings.TOPICS["welcome"]
            )
            reply_to_message_id = forwarded_message.id
        except:
            message = f"{utils.mention(user)} написав(-ла):"
            await context.bot.sendMessage(
                chat_id=settings.CHAT_ID,
                message_thread_id=settings.TOPICS["welcome"],
                text=message,
            )
            copied_message = await incoming_message.copy(
                settings.CHAT_ID, message_thread_id=settings.TOPICS["welcome"]
            )
            reply_to_message_id = copied_message.id
        await incoming_message.delete()
    bot_message = await context.bot.sendMessage(
        chat_id=incoming_message.chat.id,
        message_thread_id=settings.TOPICS["welcome"],
        text=message,
        reply_to_message_id=reply_to_message_id,
    )
    utils.add_message_cleanup_job(context.application, bot_message.id)
    return ConversationHandler.END


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When the conversation timepout is exceeded."""
    utils.log("timeout")
    user = update.effective_user
    message = f"На жаль, {utils.mention(user)} покидає Соборний."
    bot_message = await context.bot.sendMessage(
        chat_id=settings.CHAT_ID,
        message_thread_id=settings.TOPICS["welcome"],
        text=message,
    )
    utils.add_message_cleanup_job(context.application, bot_message.id)
    await context.bot.ban_chat_member(settings.CHAT_ID, user.id, revoke_messages=False)
    await context.bot.unban_chat_member(settings.CHAT_ID, user.id)
    utils.log(f"kicked: {user.id} ({user.full_name})", logging.INFO)
    return ConversationHandler.END
