# coding=UTF-8

from dynaconf import settings
from enum import Enum
import logging
from telegram import Update
import telegram.error
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
    tools.log('welcome')
    for user in update.message.new_chat_members:
        tools.log(f'new user: {user.id} ({user.full_name})', logging.INFO)
        if user.is_bot:
            tools.log(f'new user is a bot')
            continue
        if 'about' in context.user_data:
            tools.log(f'user {user.id} already introduced themselves', logging.INFO)
            continue
        message = (f'Cлава Україні, {tools.mention(user)}! Вітаємо тебе в Соборному!\n\n'
        'Ми хочемо познайомитися з тобою, так що розкажи трохи про себе (в цій гілці) '
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
    tools.log('about')
    if update.message:
        incoming_message = update.message
    else:
        incoming_message = update.edited_message
    context.user_data['about'] = incoming_message.text
    user = incoming_message.from_user
    tools.log(f'user introduced themselves: {user.id} ({user.full_name})', logging.INFO)
    message = (f'Вітаємо тебе, {tools.mention(user)}!\n\n'
    f'#️⃣[Соборний](https://t.me/c/{settings.CHAT_LINK_ID}/1) – основна гілка чату\n'
    f'🗓[Порядок тижневий](https://t.me/c/{settings.CHAT_LINK_ID}/{settings.AGENDA_THREAD_ID}) '
    f'– календар українських заходів в DMV\n'
    f'🧭[Навігація](https://t.me/c/{settings.CHAT_LINK_ID}/{settings.NAVI_THREAD_ID}) '
    f'– що ще є в нашому чаті')
    tools.log(f'about: {user.id} ({user.full_name})', logging.INFO)
    reply_to_message_id = incoming_message.id
    if incoming_message.message_thread_id != settings.WELCOME_THREAD_ID:
        try:
            if incoming_message.has_protected_content:
                raise telegram.error.Forbidden(f'the message has protected content '
                f'and can\'t be forwarded: {incoming_message.text}')
            forwarded_message = await incoming_message.forward(
                settings.CHAT_ID,message_thread_id=settings.WELCOME_THREAD_ID)
            reply_to_message_id = forwarded_message.id
        except:
            message = f'{tools.mention(user)} написав(-ла):'
            await context.bot.sendMessage(
                chat_id=settings.CHAT_ID, message_thread_id=settings.WELCOME_THREAD_ID,
                text=message)
            copied_message = await incoming_message.copy(
                settings.CHAT_ID, message_thread_id=settings.WELCOME_THREAD_ID)
            reply_to_message_id = copied_message.id
        await incoming_message.delete()
    bot_message = await context.bot.sendMessage(
        chat_id=incoming_message.chat.id, message_thread_id=settings.WELCOME_THREAD_ID,
        text=message, reply_to_message_id=reply_to_message_id)
    tools.add_message_cleanup_job(context.application, bot_message.id)
    tools.clear_jobs(context.application, WELCOME_TIMEOUT_JOB, user.id)
    return ConversationHandler.END


async def welcome_timeout(context: ContextTypes.DEFAULT_TYPE) -> int:
    """When #about was not written in time."""
    tools.log('welcome_timeout')
    chat_member = await context.bot.get_chat_member(settings.CHAT_ID, context.job.data)
    message = f'На жаль, {tools.mention(chat_member.user)} покидає Соборний.'
    tools.log(f'banned: {chat_member.user.id} ({chat_member.user.full_name})', logging.INFO)
    bot_message = await context.bot.sendMessage(
        chat_id=settings.CHAT_ID, message_thread_id=settings.WELCOME_THREAD_ID, text=message)
    tools.add_message_cleanup_job(context.application, bot_message.id)
    await context.bot.ban_chat_member(settings.CHAT_ID, context.job.data, revoke_messages=False)
    await context.bot.unban_chat_member(settings.CHAT_ID, context.job.data)
    tools.clear_jobs(context.application, WELCOME_TIMEOUT_JOB, context.job.data)
    return ConversationHandler.END