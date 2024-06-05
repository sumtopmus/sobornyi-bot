from datetime import datetime, timedelta
from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=['settings.toml'],
    secrets=['.secrets.toml'],
    environments=True
)

if settings.current_env == 'dev':
    settings.MORNING_TIME = (datetime.now() + timedelta(seconds=settings.MORNING_TIME_OFFSET)).time().isoformat()
