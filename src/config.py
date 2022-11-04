import os

class Config():
    # Magic values.
    def __init__(self):
        # Bot, admin, and chat config.
        self.TOKEN = os.getenv('SOBORNYI_BOT_API_TOKEN')
        if admin_id := os.getenv('TELEGRAM_ADMIN_ID'):
            self.ADMIN_ID = int(admin_id)
        if chat_id := os.getenv('TELEGRAM_SOBORNYI_CHAT_ID'):
            self.CHAT_ID = int(chat_id)

        # Logs.
        self.LOG_FILE = 'logs/bot.log'

        # Internal parameters.
        self.MIN_SECONDS_INTERVAL = 5
