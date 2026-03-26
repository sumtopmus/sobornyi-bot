import copy
import logging
import logging.handlers
import os
import time
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


class _UnlimitedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """RotatingFileHandler that never deletes old files — uses timestamp suffixes."""

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None  # type: ignore[assignment]
        suffix = time.strftime("%Y%m%d-%H%M%S")
        dfn = self.rotation_filename(f"{self.baseFilename}.{suffix}")
        if os.path.exists(dfn):
            os.remove(dfn)
        self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()


def setup_logging() -> None:
    # Main log
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

    # Passphrase log — size-limited, unlimited number of rotated files
    passphrase_log_path = str(settings.PASSPHRASE_LOG_PATH)
    passphrase_log_dir = os.path.dirname(passphrase_log_path)
    if passphrase_log_dir and not os.path.exists(passphrase_log_dir):
        os.makedirs(passphrase_log_dir)
    passphrase_handler = _UnlimitedRotatingFileHandler(
        filename=passphrase_log_path,
        maxBytes=settings.MAX_BYTES,
        backupCount=0,
    )
    passphrase_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    passphrase_logger = logging.getLogger("passphrase")
    passphrase_logger.addHandler(passphrase_handler)
    passphrase_logger.propagate = False

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
    handlers.calendar.reminder_on(app)
    app.bot_data.setdefault("calendar", Calendar())
    app.bot_data.setdefault("agenda", {"image": None})
    app.bot_data.setdefault("subscribers", set())
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
