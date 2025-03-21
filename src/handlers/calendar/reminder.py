from datetime import datetime, time, timedelta

from telegram.ext import Application, CallbackContext

from config import settings
from model import next_week
from utils import log

JOB_NAME = "weekly_reminder"


def reminder_on(app: Application) -> None:
    """Start the weekly reminder job."""
    log("reminder_on")
    if not app.job_queue.get_jobs_by_name(JOB_NAME):
        log(f"job_added: {JOB_NAME}")
        first_reminder_time = datetime.combine(
            next_week() - timedelta(days=1), time.fromisoformat(settings.REMINDER_TIME)
        )
        app.job_queue.run_repeating(
            remind,
            interval=timedelta(weeks=1),
            first=first_reminder_time,
            name=JOB_NAME,
        )


async def remind(context: CallbackContext):
    """Reminds the managers who subscribed to the reminder."""
    log("remind")
    has_poster = context.bot_data["agenda"]["image"] is not None
    prefix = "✅" if has_poster else "🚫"
    text = f"⏰ Час оновити календар!\n\n{prefix} Постер"
    for user_id in context.bot_data["subscribers"]:
        await context.bot.send_message(chat_id=user_id, text=text)
