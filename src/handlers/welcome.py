# coding=UTF-8

from dynaconf import settings
from enum import Enum
from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, ConversationHandler, filters

import tools


WELCOME_TIMEOUT_JOB = 'welcome_timeout'

State = Enum('State', ['JOIN', 'AWAITING'])


def create_handlers() -> list:
    """Creates handlers that process new users."""
    return [ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Chat(settings.CHAT_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
                welcome)],
        states={
            State.AWAITING: [
                MessageHandler(
                    filters.Chat(settings.CHAT_ID) & filters.Regex(r'#about'),
                    about)]},
        fallbacks=[
            # TODO: add bot's goodbye message as a fallback.
        ],
        conversation_timeout=settings.WELCOME_TIMEOUT,
        name="welcome",
        persistent=True)]


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When new user enters the chat."""
    tools.debug('welcome')
    for user in update.message.new_chat_members:
        tools.debug(f'new user: {user.id} ({user.full_name})')
        if user.is_bot:
            tools.debug(f'new user is a bot')
            continue
        if 'about' in context.user_data:
            tools.debug(f'user already introduced themselves')
            continue
        message = (f'Cлава Україні, {tools.mention(user)}! Вітаємо тебе в Соборному! \n'
        'Ми хочемо познайомитися з тобою, так що розкажи трохи про себе '
        'і додай, будь ласка, до повідомлення теґ #about.\n\n'
        'На це у тебе є одна доба. Якщо ми від тебе нічого не почуємо, ми попрощаємось.')
        reply_to_message_id = None if settings.FORUM else update.message.id
        bot_message = await context.bot.sendMessage(
            chat_id=update.message.chat.id, message_thread_id=settings.WELCOME_THREAD_ID,
            text=message, reply_to_message_id=reply_to_message_id)
        # timeout & cleanup jobs
        tools.add_job(welcome_timeout, settings.WELCOME_TIMEOUT,\
            context.application, WELCOME_TIMEOUT_JOB, user.id)
        tools.add_message_cleanup_job(context.application, bot_message.id)
    return State.AWAITING


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user writes #about."""
    tools.debug('about')
    if update.message:
        incoming_message = update.message
    else:
        incoming_message = update.edited_message
    context.user_data['about'] = incoming_message.text
    message = f'Вітаємо тебе, {tools.mention(update.message.from_user)}!'
    # TODO: handle the case when update.message.message_thread_id is incorrect.
    bot_message = await context.bot.sendMessage(
        chat_id=incoming_message.chat.id, message_thread_id=settings.WELCOME_THREAD_ID,
        text=message, reply_to_message_id=incoming_message.id)
    tools.add_message_cleanup_job(context.application, bot_message.id)
    tools.clear_jobs(context.application, WELCOME_TIMEOUT_JOB, incoming_message.from_user.id)
    return ConversationHandler.END


async def welcome_timeout(context: ContextTypes.DEFAULT_TYPE) -> int:
    """When #about was not written in time."""
    tools.debug('welcome_timeout')
    chat_member = await context.bot.get_chat_member(settings.CHAT_ID, context.job.data)
    message = f'На жаль, {tools.mention(chat_member.user)} покидає Соборний.'
    bot_message = await context.bot.sendMessage(
        chat_id=settings.CHAT_ID, message_thread_id=settings.WELCOME_THREAD_ID, text=message)
    tools.add_message_cleanup_job(context.application, bot_message.id)
    await context.bot.ban_chat_member(settings.CHAT_ID, context.job.data, revoke_messages=False)
    await context.bot.unban_chat_member(settings.CHAT_ID, context.job.data)
    tools.clear_jobs(context.application, WELCOME_TIMEOUT_JOB, context.job.data)
    return ConversationHandler.END