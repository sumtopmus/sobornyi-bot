# coding=UTF-8

from dynaconf import settings
from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

import utils


JOB_NAME = 'morning_message'


def create_handlers() -> list:
    """Creates handlers that process piece/war modes."""
    war_handler = CommandHandler(
        'war', war_on,
        filters.User(username=settings.ADMINS) & filters.Chat(settings.CHAT_ID))
    war_off_handler = CommandHandler(
        'war_off', war_off,
        filters.User(username=settings.ADMINS) & filters.Chat(settings.CHAT_ID))
    return [war_handler, war_off_handler]


def war_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the war mode (morning minute of silence)."""
    utils.log('war_on')
    if not context.job_queue.get_jobs_by_name(JOB_NAME):
        utils.log('job_added')
        context.job_queue.run_daily(
            morning_message,
            settings.MORNING_TIME,
            name=JOB_NAME)


def war_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to the piece mode."""
    utils.log('war_off')
    utils.clear_jobs(context.application, JOB_NAME)


async def morning_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send morning message and add a new timer."""
    utils.log('morning_message')
    days_since_war_started = (datetime.today() - settings.WAR_START_DATE).days + 1;
    message = (f'*День {days_since_war_started} героїчного спротиву українського народу*\n'
    '🕯 Щоденна хвилина мовчання за українцями, які віддали своє життя, '
    'за всіма, хто міг би ще жити, якби ₚосія не почала цю війну.')
    await context.bot.sendMessage(
        chat_id=settings.CHAT_ID, text=message)
