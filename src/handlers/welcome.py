# coding=UTF-8

from datetime import datetime
from enum import Enum
from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, ConversationHandler, filters

import config
import tools


WELCOME_TIMEOUT_JOB = 'welcome_timeout'

State = Enum('State', ['JOIN', 'AWAITING'])


def create_handlers() -> list:
    """Creates a handler that processses new users."""
    return [ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Chat(config.CHAT_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
                welcome)],
        states={
            State.AWAITING: [
                MessageHandler(
                    filters.Chat(config.CHAT_ID) & filters.Regex(r'#about'),
                    about)]},
        fallbacks=[
            # TODO: add bot's goodbye message as a fallback.
            # MessageHandler(
            #     filters.User(username=config.BOT_USERNAME) & filters.Regex(r'жаль')
            # )
        ],
        conversation_timeout=config.WELCOME_TIMEOUT,
        name="welcome",
        persistent=False)]


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When new user enters the chat."""
    tools.debug('welcome')
    for user in update.message.new_chat_members:
        tools.debug(f'new user: {user.id} ({user.full_name})')
        message = (f'Cлава Україні, {tools.mention(user)}, і вітаємо тебе в Соборному! \n'
        'Ми хочемо познайомитися з тобою, так що розкажи трохи про себе '
        'і не забудь додати теґ #about!\n\n'
        'На це у тебе є одна доба. Якщо ми від тебе нічого не почуємо, ми попрощаємось.')
        reply_to_message_id = None if config.IS_FORUM else update.message.message_id
        welcome_message = await context.bot.sendMessage(
            chat_id=update.message.chat.id, message_thread_id=config.WELCOME_THREAD_ID,
            text=message, reply_to_message_id=reply_to_message_id)
        context.user_data.setdefault('about', '')
        context.job_queue.run_once(
            welcome_timeout,
            config.WELCOME_TIMEOUT,
            data=user,
            name=f'{WELCOME_TIMEOUT_JOB}:{user.id}',
            chat_id=update.message.chat.id,
            user_id=user.id)
        context.job_queue.run_once(
            tools.message_cleanup,
            config.WELCOME_CLEANUP_PERIOD,
            data=welcome_message.id,
            name=f'welcome_cleanup',
            chat_id=update.message.chat.id)
    return State.AWAITING


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user writes #about."""
    tools.debug('about')
    tools.clear_jobs(context, f'{WELCOME_TIMEOUT_JOB}:{update.message.from_user.id}')
    context.user_data['about'] = update.message.text
    message = f'Вітаємо тебе, {tools.mention(update.message.from_user)}!'
    # TODO: handle the case when update.message.message_thread_id is incorrect.
    welcome_message = await context.bot.sendMessage(
            chat_id=update.message.chat.id, message_thread_id=config.WELCOME_THREAD_ID,
            text=message, reply_to_message_id=update.message.message_id)
    context.job_queue.run_once(
            tools.message_cleanup,
            config.WELCOME_CLEANUP_PERIOD,
            data=welcome_message.id,
            name=f'welcome_cleanup',
            chat_id=update.message.chat.id)
    return ConversationHandler.END


async def welcome_timeout(context: ContextTypes.DEFAULT_TYPE) -> int:
    """When #about was not written in time."""
    tools.debug('welcome_timeout')
    message = f'На жаль, {tools.mention(context.job.data)} покидає Соборний.'
    ban_message = await context.bot.sendMessage(
        chat_id=context.job.chat_id, message_thread_id=config.WELCOME_THREAD_ID, text=message)
    unban_date = datetime.now() + config.BAN_PERIOD
    await context.bot.ban_chat_member(
        context.job.chat_id, context.job.user_id,
        until_date=unban_date, revoke_messages=False)
    await context.bot.unban_chat_member(context.job.chat_id, context.job.user_id)
    context.job_queue.run_once(
            tools.message_cleanup,
            config.BAN_CLEANUP_PERIOD,
            data=ban_message.id,
            name=f'ban_cleanup',
            chat_id=context.job.chat_id)
    return ConversationHandler.END