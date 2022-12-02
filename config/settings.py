from datetime import time, timedelta

# Behavior
MORNING_TIME = time(hour=9)
# Internal parameters.
WELCOME_TIMEOUT = timedelta(days=1)
CLEANUP_PERIOD = timedelta(days=1, hours=12)