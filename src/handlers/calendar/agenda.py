from config import settings
from datetime import date, datetime, time, timedelta
from telegram import Update
from telegram.ext import Application, CallbackContext

from handlers.channel import cross_post
from model import Calendar
from utils import log, calculate_hash


JOB_NAME = "weekly_agenda"


def agenda_on(app: Application) -> None:
    """Start the weekly agenda publishing."""
    log("agenda_on")
    if not app.job_queue.get_jobs_by_name(JOB_NAME):
        log(f"job_added: {JOB_NAME}")
        first_post_time = datetime.combine(
            Calendar.get_next_week(), time.fromisoformat(settings.AGENDA_TIME)
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
    context.bot_data["agenda"]["date"] = Calendar.get_this_week().isoformat()
    context.bot_data["agenda"]["hash"] = calculate_hash(text)
    context.bot_data["agenda"]["image"] = None


async def sync_agenda(context: CallbackContext):
    """Syncs the agenda."""
    log("sync_agenda")
    # TODO: temporary solution during migration
    if (
        "date" not in context.bot_data["agenda"]
        or "hash" not in context.bot_data["agenda"]
    ):
        return
    # end of temporary solution
    agenda_date = date.fromisoformat(context.bot_data["agenda"]["date"])
    if agenda_date == Calendar.get_this_week():
        text = context.bot_data["calendar"].get_agenda()
        if calculate_hash(text) == context.bot_data["agenda"]["hash"]:
            return
        context.bot_data["agenda"]["hash"] = calculate_hash(text)
        message_id = context.bot_data["agenda"]["message_id"]
        await context.bot.edit_message_caption(
            chat_id=settings.CHANNEL_USERNAME, message_id=message_id, caption=text
        )


async def publish_agenda_on_demand(update: Update, context: CallbackContext):
    await publish_agenda(context)
