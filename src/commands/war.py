# coding=UTF-8

from datetime import datetime, time, timedelta
from threading import Timer
from telegram.ext import CommandHandler, ConversationHandler, Filters
import infra

WAR_MODE = True
WAR_START = datetime(2022, 2, 24)


# Creates a handler for dispatcher.
def create_handler(config):
    war_on_handler = CommandHandler(
        'war_on', war_on, Filters.user(config.ADMIN_ID) & Filters.chat(config.CHAT_ID))
    war_off_handler = CommandHandler(
        'war_off', war_off, Filters.user(config.ADMIN_ID) & Filters.chat(config.CHAT_ID))
    return ConversationHandler(
        entry_points=[war_on_handler, war_off_handler],
        states={},
        fallbacks=[])


# Switch to the war mode (morning minute of silence).
def war_on(update, context):
    infra.debug('war_on', update, context)
    global WAR_MODE
    WAR_MODE = True


# Switch to the piece mode.
def war_off(update, context):
    infra.debug('war_off', update, context)
    global WAR_MODE
    WAR_MODE = False


# Add morning message to a timer.
def queue_morning_message(updater, config):
    infra.debug('queue_morning_message')
    time_to_9am = datetime.combine(datetime.today(), time(hour=9)) - datetime.now();
    if time_to_9am.total_seconds() < config.MIN_SECONDS_INTERVAL:
        time_to_9am += timedelta(hours=24)
    Timer(int(time_to_9am.total_seconds()), morning_message, (updater, config)).start()


# Send morning message and add a new timer.
def morning_message(updater, config):
    infra.debug('morning_message')
    if WAR_MODE:
        days_since_war_started = (datetime.today() - WAR_START).days + 1;
        message = (f'*День {days_since_war_started} героїчного спротиву українського народу*\n'
        '🕯 Щоденна хвилина мовчання за українцями, які віддали своє життя, '
        'за всіма, хто міг би ще жити, якби Росія не почала цю війну.')
        updater.bot.sendMessage(chat_id=config.CHAT_ID, text=f'{message}')
        queue_morning_message(updater, config)
