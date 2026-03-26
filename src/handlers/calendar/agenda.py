from datetime import date, datetime, time, timedelta

from telegram import Update
from telegram.ext import Application, CallbackContext

from config import settings
from handlers.channel import cross_post, edit_post
from model import next_week, this_week
from utils import calculate_hash, log

JOB_NAME = "weekly_agenda"


def agenda_on(app: Application) -> None:
    """Start the weekly agenda publishing."""
    log("agenda_on")
    if not app.job_queue.get_jobs_by_name(JOB_NAME):
        log(f"job_added: {JOB_NAME}")
        first_post_time = datetime.combine(
            next_week(), time.fromisoformat(settings.AGENDA_TIME)
        )
        app.job_queue.run_repeating(
            publish_agenda,
            interval=timedelta(weeks=1),
            first=first_post_time,
            name=JOB_NAME,
        )


async def publish_agenda(context: CallbackContext):
    """Publishes the agenda."""
    log("publish_agenda")
    text = context.bot_data["calendar"].get_agenda()
    image = context.bot_data["agenda"]["image"]
    if image:
        message = await context.bot.send_photo(
            chat_id=settings.CHANNEL_USERNAME, photo=image, caption=text
        )
    else:
        message = await context.bot.send_photo(
            chat_id=settings.CHANNEL_USERNAME,
            photo=settings.DEFAULT_AGENDA_IMAGE,
            caption=text,
        )
    await cross_post(message, context)
    context.bot_data["agenda"]["message_id"] = message.message_id
    context.bot_data["agenda"]["date"] = this_week().isoformat()
    context.bot_data["agenda"]["hash"] = calculate_hash(text)
    context.bot_data["agenda"]["image"] = None


async def sync_agenda(context: CallbackContext):
    """Syncs the agenda."""
    log("sync_agenda")
    raw_date = context.bot_data["agenda"].get("date")
    if not raw_date:
        return
    agenda_date = date.fromisoformat(raw_date)
    if agenda_date == this_week():
        text = context.bot_data["calendar"].get_agenda()
        if calculate_hash(text) == context.bot_data["agenda"]["hash"]:
            return
        context.bot_data["agenda"]["hash"] = calculate_hash(text)
        message_id = context.bot_data["agenda"]["message_id"]
        message = await context.bot.edit_message_caption(
            chat_id=settings.CHANNEL_USERNAME, message_id=message_id, caption=text
        )
        await edit_post(message, context)


async def publish_agenda_on_demand(update: Update, context: CallbackContext):
    await publish_agenda(context)
