import copy
import logging
import logging.handlers
from datetime import datetime, timedelta
from warnings import filterwarnings

from telegram.ext import Application
from telegram.warnings import PTBUserWarning

# Suppress specific PTBUserWarning about CallbackQueryHandler and per_message=False
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)
# Suppress warning about nested conversations with conversation_timeout
filterwarnings(
    action="ignore", message=r".*nested conversations.*", category=PTBUserWarning
)


import handlers
import utils
from config import debug_mode_off, debug_mode_on, settings
from model import Calendar


def setup_logging() -> None:
    # Logging
    handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_PATH,
        maxBytes=settings.MAX_BYTES,
        backupCount=settings.BACKUP_COUNT,
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    if settings.DEBUG:
        debug_mode_on()
    else:
        debug_mode_off()


async def post_init(app: Application) -> None:
    """Initializes bot with data and its tasks."""
    if settings.WAR_MODE:
        handlers.war.enable_war_mode(app)
    if settings.AGENDA_MODE:
        handlers.calendar.agenda_on(app)
    app.bot_data.setdefault("calendar", Calendar())
    app.bot_data.setdefault("agenda", {"image": None})
    app.bot_data.setdefault("jobs", {})
    app.bot_data.setdefault("cross-posts", {})
    app.bot_data.setdefault("version", "1.0.0")

    # Process existing jobs
    jobs = copy.deepcopy(app.bot_data["jobs"])
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


def add_handlers(app: Application) -> None:
    # Error handler
    app.add_error_handler(handlers.error)
    # Debug & business logic handlers
    app.add_handlers(handlers.all)
