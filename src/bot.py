import os
import pytz
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults, PicklePersistence

from config import settings
import init


def main() -> None:
    """Runs bot."""
    # Create directory tree structure
    for path in [settings.DB_PATH, settings.LOG_PATH]:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

    # Set up logging
    init.setup_logging()

    # Setup the bot.
    defaults = Defaults(
        parse_mode=ParseMode.MARKDOWN, tzinfo=pytz.timezone(settings.TIMEZONE)
    )
    persistence = PicklePersistence(filepath=settings.DB_PATH, single_file=False)
    app = (
        Application.builder()
        .token(settings.TOKEN)
        .defaults(defaults)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .post_init(init.post_init)
        .build()
    )
    # Add handlers.
    init.add_handlers(app)
    # Start the bot.
    app.run_polling()


if __name__ == "__main__":
    main()
