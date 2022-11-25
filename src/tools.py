# coding=UTF-8
from datetime import datetime
import logging
from telegram import User
from telegram.ext import ContextTypes

import config


# Magic values.
FMT = '%Y-%m-%d %H:%M:%S'


def debug(message: str) -> None:
    """Debugging helper."""
    logging.getLogger(__name__).debug(message)
    if config.DEBUG_MODE:
        print(f'⌚️ {datetime.now().strftime(FMT)}: {message}')


def mention(user: User) -> None:
    """Create a user's mention."""
    # TODO: add more advanced user mention, e.g. `name (@username)`.
    result = f'[{user.name}]'
    if user.username:
        result += f'(mention:{user.name})'
    else:
        result += f'(tg://user?id={user.id})'
    return result


async def message_cleanup(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cleans up outdated messages."""
    debug('message_cleanup')
    await context.bot.delete_message(context.job.chat_id, context.job.data)


def clear_jobs(context: ContextTypes.DEFAULT_TYPE, job_name: str) -> None:
    """Clears the existing jobs."""
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    if not current_jobs:
        return
    for job in current_jobs:
        job.schedule_removal()