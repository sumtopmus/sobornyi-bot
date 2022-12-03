from datetime import datetime, time, timedelta

# Behavior
MORNING_TIME = time(hour=9)
WAR_START_DATE = datetime(2022, 2, 24)
# Internal parameters.
WELCOME_TIMEOUT = timedelta(days=1)
CLEANUP_PERIOD = timedelta(days=1, hours=12)