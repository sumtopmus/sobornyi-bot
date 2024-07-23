from datetime import datetime, timedelta
from dynaconf import Dynaconf
import logging

settings = Dynaconf(
    settings_files=['settings.toml'],
    secrets=['.secrets.toml'],
    environments=True
)

if settings.current_env == 'dev':
    settings.MORNING_TIME = (datetime.now() + timedelta(seconds=settings.MORNING_TIME_OFFSET)).time().isoformat()


def debug_mode_on():
    settings.DEBUG = True
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger('httpx').setLevel(logging.INFO)
    logging.getLogger('apscheduler').setLevel(logging.INFO)


def debug_mode_off():
    settings.DEBUG = False
    logging.getLogger(__name__).setLevel(logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)