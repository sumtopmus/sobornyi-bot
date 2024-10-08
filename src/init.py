import copy
import logging
from datetime import datetime, timedelta
from telegram.ext import Application
from telegram.warnings import PTBUserWarning
from warnings import filterwarnings

from config import settings
import handlers
from model import Calendar
import utils


def setup_logging() -> None:
    # Logging
    logging_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        filename=settings.LOG_PATH,
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # Debugging
    filterwarnings(
        action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
    )


async def post_init(app: Application) -> None:
    """Initializes bot with data and its tasks."""
    if settings.WAR_MODE:
        handlers.war.war_on(app)
    if settings.AGENDA_MODE:
        handlers.calendar.agenda_on(app)
    app.bot_data.setdefault("calendar", Calendar())
    app.bot_data.setdefault("agenda", {"image": None})
    jobs = copy.deepcopy(app.bot_data.setdefault("jobs", {}))
    app.bot_data["jobs"] = {}
    for job_name, job_params in jobs.items():
        delay = max(timedelta(seconds=0), job_params["time"] - datetime.now())
        match job_name.partition(":")[0]:
            case "message_cleanup":
                utils.add_job(
                    utils.message_cleanup,
                    delay,
                    app,
                    utils.MESSAGE_CLEANUP_JOB,
                    job_params["data"],
                )
            case _:
                pass
    app.bot_data.setdefault("cross-posts", {})


def add_handlers(app: Application) -> None:
    # Error handler
    app.add_error_handler(handlers.error)
    # Debug & business logic handlers
    app.add_handlers(handlers.all)
