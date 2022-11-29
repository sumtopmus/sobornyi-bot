# coding=UTF-8

import argparse
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults, PicklePersistence

from handlers import channel, debug, error, info, request, war, welcome
import config
import infra
import tools


def init(app: Application) -> None:
    """Initializes bot and its tasks."""
    tools.debug('init_war')
    if config.WAR_MODE:
        app.job_queue.run_daily(
            war.morning_message,
            config.MORNING_TIME,
            chat_id=config.CHAT_ID,
            name=war.JOB_NAME)


def main() -> None:
    """Main program to run."""
    # Parse arguments.
    parser = argparse.ArgumentParser(
        description='''Runs a controller bot for Sobornyi Telegram group.''')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help="Whether to run in the debug mode.")
    parser.set_defaults(debug=False)
    args = parser.parse_args()

    # Initialize infrastructure.
    config.DEBUG_MODE = args.debug
    infra.init()

    # Setup the bot.
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN_V2, tzinfo=config.TIMEZONE)
    persistence = PicklePersistence(filepath=config.DB_PATH, single_file=False)
    app = Application.builder().token(config.TOKEN).defaults(defaults)\
        .persistence(persistence).arbitrary_callback_data(True).build()
    # Error handler.
    app.add_error_handler(error.handler)
    # Admin commands.
    for module in [debug, info]:
        app.add_handlers(module.create_handlers())
    # General chat handling.
    for module in [channel, request, welcome, war]:
        app.add_handlers(module.create_handlers())

    # Initialize tasks.
    init(app)
    # Start the bot.
    app.run_polling()


if __name__ == "__main__":
    main()