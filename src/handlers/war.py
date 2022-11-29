# coding=UTF-8

from datetime import datetime
from telegram import Update
from telegram.ext import Application, BaseHandler, CommandHandler, ContextTypes, ConversationHandler, filters

import config
import tools


JOB_NAME = 'morning_message'


def create_handlers() -> list:
    """Creates handlers that process piece/war modes."""
    war_handler = CommandHandler(
        'war', war_on,
        filters.User(username=config.ADMINS) & filters.Chat(config.CHAT_ID))
    war_off_handler = CommandHandler(
        'war_off', war_off,
        filters.User(username=config.ADMINS) & filters.Chat(config.CHAT_ID))
    return [war_handler, war_off_handler]


def war_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the war mode (morning minute of silence)."""
    tools.debug('war_on')
    if not context.job_queue.get_jobs_by_name(JOB_NAME):
        tools.debug('job_added')
        context.job_queue.run_daily(
            morning_message,
            config.MORNING_TIME,
            name=JOB_NAME,
            chat_id=update.update.message.chat.id)


def war_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the piece mode."""
    tools.debug('war_off')
    tools.clear_jobs(context, JOB_NAME)


async def morning_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send morning message and add a new timer."""
    tools.debug('morning_message')
    days_since_war_started = (datetime.today() - config.WAR_START_DATE).days + 1;
    message = (f'*День {days_since_war_started} героїчного спротиву українського народу*\n'
    '🕯 Щоденна хвилина мовчання за українцями, які віддали своє життя, '
    'за всіма, хто міг би ще жити, якби Росія не почала цю війну.')
    await context.bot.sendMessage(
        chat_id=context.job.chat_id, text=f'{message}',
        message_thread_id=config.MAIN_THREAD_ID)
