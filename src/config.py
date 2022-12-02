from datetime import datetime, time, timedelta
import os
import pytz
from ruamel.yaml import YAML


# Debug config.
DEBUG_MODE = False

# Bot, admin, and chat config.
TOKEN = os.getenv('SOBORNYI_BOT_API_TOKEN')

# Main config.
yaml = YAML()
with open('config.yml', 'r') as f:
    config = yaml.load(f)
    BOT_USERNAME = config['bot-username']
    ADMINS = config['admins']
    CHAT_ID = config['chat-id']
    CHANNEL_USERNAME = config['channel-username']
    IS_FORUM = config['forum']
    MAIN_THREAD_ID = config.get('main-thread', None)
    WELCOME_THREAD_ID = config.get('welcome-thread', None)
    OFFTOP_THREAD_ID = config.get('offtop-thread', None)
    CHANNEL_THREAD_ID = config.get('channel-thread', None)
# Pathes.
DB_PATH = 'data/db'
LOG_PATH = 'logs/bot.log'
# General parameters.
TIMEZONE = pytz.timezone('US/Eastern')
# Behavior parameters.
WAR_MODE = True
WAR_START_DATE = datetime(2022, 2, 24)
MORNING_TIME = time(hour=9)
# Internal parameters.
MIN_SECONDS_INTERVAL = 5
WELCOME_TIMEOUT = timedelta(days=1)
WELCOME_CLEANUP_PERIOD = timedelta(days=1, hours=12)
BAN_CLEANUP_PERIOD = WELCOME_CLEANUP_PERIOD - WELCOME_TIMEOUT
BAN_PERIOD = timedelta(seconds=35)
