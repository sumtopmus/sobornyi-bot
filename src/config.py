import logging
from datetime import datetime, timedelta

from dynaconf import Dynaconf


class _Settings:
    # Switchers
    DEBUG: bool
    FORUM: bool
    WAR_MODE: bool
    AGENDA_MODE: bool
    # Assets
    AGENDA_IMAGE: str
    DEFAULT_AGENDA_IMAGE: str
    # Data
    DB_PATH: str
    # Logging
    LOG_PATH: str
    PASSPHRASE_LOG_PATH: str
    MAX_BYTES: int
    BACKUP_COUNT: int
    # General
    TIMEZONE: str
    TOKEN: str
    # Chat
    CHAT_ID: int
    CHAT_LINK_ID: int
    CHAT_INVITE_LINK: str
    CHANNEL_USERNAME: str
    ADMINS: list[str]
    MODERATORS: list[str]
    TOPICS: dict[str, int]
    TAGS: dict[str, str]
    PRIORITIES: dict[str, int]
    # Scheduled times
    MORNING_TIME: str
    AGENDA_TIME: str
    REMINDER_TIME: str
    WAR_START_DATE: str
    # Formats
    DATE_FORMAT: str
    DATETIME_FORMAT: str
    # Timeouts / periods (seconds)
    CONVERSATION_TIMEOUT: int
    WELCOME_TIMEOUT: int
    CLEANUP_PERIOD: int
    # Dev only
    TIME_OFFSET: int
    # dynaconf internals
    current_env: str


settings: _Settings = Dynaconf(  # type: ignore[assignment]
    settings_files=["settings.toml"],
    secrets=[".secrets.toml"],
    load_dotenv=True,
    environments=True,
)

if settings.current_env == "dev":
    settings.MORNING_TIME = (
        (datetime.now() + timedelta(seconds=settings.TIME_OFFSET)).time().isoformat()
    )
    settings.AGENDA_TIME = (
        (datetime.now() + timedelta(seconds=settings.TIME_OFFSET)).time().isoformat()
    )


def debug_mode_on():
    settings.DEBUG = True
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def debug_mode_off():
    settings.DEBUG = False
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
