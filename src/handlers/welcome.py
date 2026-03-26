import logging
import re
from enum import Enum

import telegram.error
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import (
    ChatJoinRequestHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

import utils
from config import settings
from format import mention
from handlers import topic

State = Enum("State", ["PASSPHRASE", "AWAITING"])

_UA_PASSPHRASE = re.compile(r"^\s*слава\s+україні!?\s*$", re.IGNORECASE)
_EN_PASSPHRASE = re.compile(
    r"^\s*(glory\s+to\s+ukraine|slava\s+ukraini)!?\s*$", re.IGNORECASE
)
MAX_TRIES = 3


def create_handlers() -> list:
    """Creates handlers that process new users."""
    return [
        ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.Chat(settings.CHAT_ID)
                    & filters.StatusUpdate.NEW_CHAT_MEMBERS,
                    join,
                ),
                ChatJoinRequestHandler(join_request, chat_id=settings.CHAT_ID),
            ],
            states={
                State.PASSPHRASE: [
                    MessageHandler(
                        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
                        check_passphrase,
                    ),
                ],
                State.AWAITING: [
                    MessageHandler(
                        filters.Chat(settings.CHAT_ID) & ~filters.Regex(r"#about"),
                        not_about,
                    ),
                    MessageHandler(
                        filters.Chat(settings.CHAT_ID) & filters.Regex(r"#about"),
                        about,
                    ),
                ],
                ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)],
            },
            fallbacks=[],
            allow_reentry=True,
            conversation_timeout=settings.WELCOME_TIMEOUT,
            name="welcome",
            per_chat=False,
            persistent=True,
        )
    ]


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When users join the chat directly via an invite link."""
    utils.log("join")
    new_member_ids = {u.id for u in update.message.new_chat_members}
    if update.effective_user.id not in new_member_ids:
        # Admin added users directly — this should not happen in the normal flow.
        # Kick all added users (ban+unban) so they can rejoin through the proper channel.
        await update.message.delete()
        for user in update.message.new_chat_members:
            if user.is_bot:
                continue
            utils.log(
                f"admin-added user, kicking: {user.id} ({user.full_name})", logging.INFO
            )
            try:
                await context.bot.ban_chat_member(update.message.chat.id, user.id)
                await context.bot.unban_chat_member(update.message.chat.id, user.id)
            except telegram.error.TelegramError as e:
                utils.log(f"could not kick {user.id}: {e}", logging.ERROR)
        return ConversationHandler.END

    # Self-join via invite link: skip passphrase, welcome directly.
    user = update.effective_user
    if user is None:
        return ConversationHandler.END
    utils.log(f"new user: {user.id} ({user.full_name})", logging.INFO)
    if user.is_bot:
        utils.log("new user is a bot")
        return ConversationHandler.END
    return await _welcome_member(update, context, user)


async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a join request is received."""
    utils.log("join_request")
    user = update.effective_user
    utils.log(f"join request from {user.id} ({user.full_name})", logging.INFO)
    if context.user_data.get("passphrase_passed"):
        try:
            await user.approve_join_request(settings.CHAT_ID)
            utils.log(f"{user.id} already passed passphrase, approved", logging.INFO)
        except telegram.error.TelegramError as e:
            utils.log(f"could not approve request: {e}", logging.ERROR)
        return ConversationHandler.END
    context.user_data["passphrase_tries"] = 0
    context.user_data["join_via_request"] = True
    try:
        await context.bot.send_message(user.id, "Гасло?")
        utils.log(f"passphrase challenge sent to {user.id}", logging.INFO)
    except telegram.error.Forbidden as e:
        utils.log(f"cannot DM {user.id}: {e}", logging.ERROR)
        try:
            await user.decline_join_request(settings.CHAT_ID)
        except telegram.error.TelegramError:
            pass
        return ConversationHandler.END
    return State.PASSPHRASE


async def check_passphrase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """Checks the user's passphrase response."""
    utils.log("check_passphrase")
    user = update.effective_user
    text = update.message.text.strip()
    tries = context.user_data.get("passphrase_tries", 0) + 1
    context.user_data["passphrase_tries"] = tries

    is_ua = bool(_UA_PASSPHRASE.match(text))
    is_en = bool(_EN_PASSPHRASE.match(text))

    if is_ua or is_en:
        context.user_data["passphrase_passed"] = True
        utils.log(f"{user.id} passed passphrase on try {tries}", logging.INFO)
        if is_ua:
            reply_text = "Героям слава!"
            btn_text = "Перейти до чату"
        else:
            reply_text = "Glory to heroes!"
            btn_text = "Join the chat"
        if context.user_data.get("join_via_request"):
            try:
                await user.approve_join_request(settings.CHAT_ID)
            except telegram.error.TelegramError as e:
                utils.log(f"could not approve request: {e}", logging.ERROR)
            await update.message.reply_text(reply_text)
        else:
            button = InlineKeyboardButton(text=btn_text, url=settings.CHAT_INVITE_LINK)
            await update.message.reply_text(
                reply_text, reply_markup=InlineKeyboardMarkup([[button]])
            )
        return ConversationHandler.END

    utils.log(f"{user.id} wrong passphrase (try {tries}/{MAX_TRIES})", logging.INFO)
    if tries >= MAX_TRIES:
        await update.message.reply_text("Нехай щастить!")
        if context.user_data.get("join_via_request"):
            try:
                await user.decline_join_request(settings.CHAT_ID)
            except telegram.error.TelegramError as e:
                utils.log(f"could not decline request: {e}", logging.ERROR)
        return ConversationHandler.END

    remaining = MAX_TRIES - tries
    await update.message.reply_text(f"Гасло?")
    return State.PASSPHRASE


async def _welcome_member(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User
) -> State:
    """Sends a welcome message for a user who already passed the passphrase."""
    if "about" in context.user_data:
        utils.log(f"{user.id} already introduced themselves", logging.INFO)
        message = f"Cлава Україні, {mention(user)}! Вітаємо тебе в Соборному, знову!"
        reply_to_message_id = None if settings.FORUM else update.message.id
        bot_message = await context.bot.sendMessage(
            chat_id=update.message.chat.id,
            message_thread_id=settings.TOPICS["welcome"],
            text=message,
            reply_to_message_id=reply_to_message_id,
        )
        utils.add_message_cleanup_job(context.application, bot_message.id)
        return ConversationHandler.END

    message = (
        f"Cлава Україні, {mention(user)}! Вітаємо тебе в Соборному!\n\n"
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
    utils.add_message_cleanup_job(context.application, bot_message.id)
    return State.AWAITING


async def not_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user does not write #about."""
    utils.log("not_about")
    user = update.message.from_user
    reply_to_message_id = update.message.id
    message = f"{mention(user)}, додай, будь ласка, до свого повідомлення теґ #about"
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
    message = f"Вітаємо тебе, {mention(user)}!"
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
            message = f"{mention(user)} написав(-ла):"
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
    """When the conversation timeout is exceeded."""
    utils.log("timeout")
    user = update.effective_user
    if not context.user_data.get("passphrase_passed"):
        # Timeout during passphrase challenge
        try:
            await context.bot.send_message(user.id, "Час вийшов. Нехай щастить!")
        except telegram.error.TelegramError:
            pass
        if context.user_data.get("join_via_request"):
            try:
                await user.decline_join_request(settings.CHAT_ID)
            except telegram.error.TelegramError as e:
                utils.log(f"could not decline request: {e}")
        utils.log(f"passphrase timeout: {user.id} ({user.full_name})", logging.INFO)
        return ConversationHandler.END
    # Timeout during AWAITING (#about) stage — kick from group
    message = f"На жаль, {mention(user)} покидає Соборний."
    bot_message = await context.bot.sendMessage(
        chat_id=settings.CHAT_ID,
        message_thread_id=settings.TOPICS["welcome"],
        text=message,
    )
    utils.add_message_cleanup_job(context.application, bot_message.id)
    try:
        await context.bot.ban_chat_member(
            settings.CHAT_ID, user.id, revoke_messages=False
        )
        await context.bot.unban_chat_member(settings.CHAT_ID, user.id)
    except telegram.error.TelegramError as e:
        utils.log(f"could not kick {user.id}: {e}", logging.ERROR)
    utils.log(f"kicked: {user.id} ({user.full_name})", logging.INFO)
    return ConversationHandler.END
