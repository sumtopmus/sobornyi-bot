# coding=UTF-8

from datetime import datetime, timedelta
from dynaconf import settings
import logging
from telegram import User
from telegram.ext import Application, ContextTypes


MESSAGE_CLEANUP_JOB = 'message_cleanup'


def debug(message: str) -> None:
    """Debugging helper."""
    logging.getLogger(__name__).debug(message)
    if settings.DEBUG:
        print(f'⌚️ {datetime.now().strftime(settings.DATETIME_FORMAT)}: {message}')


def mention(user: User) -> str:
    """Create a user's mention."""
    result = user.mention_markdown(user.name)
    if user.username:
        debug(user.username)
        result += f' ({user.mention_markdown()})'
    return result


async def message_cleanup(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cleans up outdated messages."""
    debug(f'message_cleanup: {context.job.data}')
    await context.bot.delete_message(settings.CHAT_ID, context.job.data)
    clear_jobs(context.application, MESSAGE_CLEANUP_JOB, context.job.data)


def add_job(job, delay: timedelta, app: Application, job_family: str, job_data) -> None:
    """Adds a job to the bot scheduler."""
    job_name = f'{job_family}:{job_data}'
    debug(f'add_job: {job_name}')
    app.job_queue.run_once(job, delay, data=job_data, name=job_name)
    app.bot_data['jobs'][job_name] = {
        'time': datetime.now() + delay,
        'data': job_data}


def add_message_cleanup_job(app: Application, message_id: int) -> None:
    """Adds a message cleanup job to the scheduler."""
    debug(f'add_message_cleanup_job: {message_id}')
    add_job(message_cleanup, settings.CLEANUP_PERIOD, app, MESSAGE_CLEANUP_JOB, message_id)


def clear_jobs(app: Application, job_family: str, job_data=None) -> None:
    """Clears the existing jobs."""
    job_name = job_family
    if job_data:
        job_name += f':{job_data}'
    debug(f'clear_jobs: {job_name}')
    current_jobs = app.job_queue.get_jobs_by_name(job_name)
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
    app.bot_data['jobs'].pop(job_name, None)