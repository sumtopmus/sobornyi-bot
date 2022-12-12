import copy
from datetime import datetime, timedelta
from dynaconf import settings
from telegram.ext import Application

from handlers import channel, debug, error, info, request, war, welcome
import tools


async def post_init(app: Application) -> None:
    """Initializes bot with data and its tasks."""
    tools.log('post_init')
    if settings.WAR_MODE:
        tools.log('init_war')
        app.job_queue.run_daily(
            war.morning_message,
            settings.MORNING_TIME,
            chat_id=settings.CHAT_ID,
            name=war.JOB_NAME)
    tools.log('restoring_jobs')
    jobs = copy.deepcopy(app.bot_data.setdefault('jobs', {}))
    app.bot_data['jobs'] = {}
    for job_name, job_params in jobs.items():
        delay = max(timedelta(seconds=0), job_params['time'] - datetime.now())
        match job_name.partition(':')[0]:
            case 'message_cleanup':
                tools.add_job(tools.message_cleanup, delay, app,\
                    tools.MESSAGE_CLEANUP_JOB, job_params['data'])
            case 'welcome_timeout':
                tools.add_job(welcome.welcome_timeout, delay, app,\
                    welcome.WELCOME_TIMEOUT_JOB, job_params['data'])
            case _:
                pass
    channel = await app.bot.get_chat(settings.CHANNEL_USERNAME)
    app.chat_data[channel.id].setdefault('channel-thread', {})


def add_handlers(app: Application) -> None:
    # Error handler.
    app.add_error_handler(error.handler)
    # Admin commands.
    for module in [debug, info]:
        app.add_handlers(module.create_handlers())
    # General chat handling.
    for module in [channel, request, welcome, war]:
        app.add_handlers(module.create_handlers())