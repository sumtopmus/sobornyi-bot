# coding=UTF-8

import os
import logging
import argparse
from datetime import datetime, time, timedelta
from threading import Timer

import telegram.error
from telegram.ext import Updater, Defaults, CommandHandler, Filters

# Magic values.
FMT = '%Y-%m-%d %H:%M:%S'
TOKEN = os.getenv('SOBORNYI_BOT_API_TOKEN')
if ADMIN_ID := os.getenv('TELEGRAM_ADMIN_ID'):
    ADMIN_ID = int(ADMIN_ID)
if CHAT_ID := os.getenv('TELEGRAM_SOBORNYI_CHAT_ID'):
    CHAT_ID = int(CHAT_ID)

LOG_FILE = 'logs/bot.log'

# Settings.
DEBUG_MODE = False
WAR_MODE = True
WAR_START = datetime(2022, 2, 24)

# Internal parameters.
MIN_SECONDS_INTERVAL = 10

# Debugging helper.
def debug(message, update=None, context=None):
    logging.getLogger(__name__).debug(message)
    if DEBUG_MODE:
        message = f'⌚️ {datetime.now().strftime(FMT)}: {message}'
        if update and context:
            context.bot.sendMessage(chat_id=update.message.chat.id,
                                    text=f'```{message}```')
        print(message)

# Creates the directiry tree structure.
def makedirs():
    for path in [LOG_FILE]:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))


# API related calls & handlers.

# Error handler.
def error(update, context):
    logging.getLogger(__name__).warning(f'Update {update} caused error {context.error}')
    try:
        raise context.error
    except telegram.error.Unauthorized:
        # remove update.message.user_id from conversation list
        pass
    except telegram.error.BadRequest:
        # handle malformed requests - read more below!
        pass
    except telegram.error.TimedOut:
        # handle slow connection problems
        pass
    except telegram.error.NetworkError:
        # handle other connection problems
        pass
    except telegram.error.ChatMigrated:
        # the user_id of a group has changed, use e.new_user_id instead
        pass
    except telegram.error.TelegramError:
        # handle all other telegram related errors
        pass

# Modes

# Switch between dev and prod modes.
def debug_switch(update, context):
    debug('debug_switch', update, context)
    global DEBUG_MODE
    DEBUG_MODE = not DEBUG_MODE
# Switch to the dev mode.
def debug_on(update, context):
    debug('debug_on', update, context)
    global DEBUG_MODE
    DEBUG_MODE = True
# Switch to the prod mode.
def debug_off(update, context):
    debug('debug_off', update, context)
    global DEBUG_MODE
    DEBUG_MODE = False
# Switch between war and piece modes.
def war_switch(update, context):
    debug('war_switch', update, context)
    global WAR_MODE
    WAR_MODE = not WAR_MODE
# Switch to the war mode (morning minute of silence).
def war_on(update, context):
    debug('war_on', update, context)
    global WAR_MODE
    WAR_MODE = True
# Switch to the piece mode.
def war_off(update, context):
    debug('war_off', update, context)
    global WAR_MODE
    WAR_MODE = False

# Basic admin info command.
def info(update, context):
    debug('info', update, context)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    debug(f'\nchat_id: {chat_id}\nuser_id: {user_id}', update, context)

# Add morning message to a timer.
def queue_morning_message():
    debug('queue_morning_message')
    time_to_9am = datetime.combine(datetime.today(), time(hour=9)) - datetime.now();
    if time_to_9am.total_seconds() < MIN_SECONDS_INTERVAL:
        time_to_9am += timedelta(hours=24)
    Timer(int(time_to_9am.total_seconds()), morning_message).start()

# Send morning message and add a new timer.
def morning_message():
    debug('morning_message')
    if WAR_MODE:
        days_since_war_started = (datetime.today() - WAR_START).days + 1;
        message = f'*День {days_since_war_started} війни*\n'\
        '🕯Щоденна хвилина мовчання за українцями, які віддали своє життя, '\
        'за всіма, хто міг би ще жити, якби Росія не почала цю війну.'
        updater.bot.sendMessage(chat_id=CHAT_ID, text=f'{message}')
        queue_morning_message()

# Parse arguments.
parser = argparse.ArgumentParser(
    description='''Runs a watchman bot for a Telegram group.''')
parser.add_argument('--debug', dest='debug', action='store_true',
                    help="Whether to run in the debug mode.")
parser.set_defaults(debug=False)
args = parser.parse_args()

# Settings.
DEBUG_MODE = args.debug

# Create directory tree structure.
makedirs()
# Set up logging and debugging.
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
logging_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(filename=LOG_FILE, level=logging_level,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Show admin and chat ids.
debug(f'admin: {ADMIN_ID}, chat: {CHAT_ID}')

# Setup the bot.
defaults = Defaults(parse_mode='Markdown')
updater = Updater(TOKEN, defaults=defaults)
# Admin commands.
updater.dispatcher.add_handler(CommandHandler('debug', debug_switch,
    Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))
updater.dispatcher.add_handler(CommandHandler('debug_on', debug_on,
    Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))
updater.dispatcher.add_handler(CommandHandler('debug_off', debug_off,
    Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))
updater.dispatcher.add_handler(CommandHandler('war', war_switch,
    Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))
updater.dispatcher.add_handler(CommandHandler('war_on', war_on,
    Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))
updater.dispatcher.add_handler(CommandHandler('war_off', war_off,
    Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))
updater.dispatcher.add_handler(CommandHandler('info', info,
    Filters.user(ADMIN_ID)))
# Error handling.
updater.dispatcher.add_error_handler(error)

# Add tasks.
queue_morning_message()

# Start the bot.
updater.start_polling()
updater.idle()