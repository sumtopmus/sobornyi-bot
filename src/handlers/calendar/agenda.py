from config import settings
from datetime import time, timedelta, datetime
from telegram import Update
from telegram.ext import Application, CallbackContext

from model import Calendar
from utils import log


JOB_NAME = 'weekly_agenda'


def agenda_on(app: Application) -> None:
    """Start the weekly agenda publishing."""
    log('agenda_on')
    if not app.job_queue.get_jobs_by_name(JOB_NAME):
        log(f'job_added: {JOB_NAME}')
        first_post_time = datetime.combine(Calendar.get_next_week(),
                                           time.fromisoformat(settings.AGENDA_TIME))
        app.job_queue.run_repeating(
            publish_agenda,
            interval=timedelta(weeks=1),
            first=first_post_time,
            name=JOB_NAME)


async def publish_agenda(context: CallbackContext):
    """Publishes the agenda."""
    log('publish_agenda')
    text = context.bot_data['calendar'].get_agenda()
    image = context.bot_data['agenda']['image']
    if image:
        message = await context.bot.send_photo(
            chat_id=settings.channel_username, photo=image, caption=text)
    else:
        message = await context.bot.send_photo(
            chat_id=settings.channel_username, photo=settings.DEFAULT_AGENDA_IMAGE, caption=text)
    context.bot_data['agenda']['message_id'] = message.message_id
    context.bot_data['agenda']['image'] = None