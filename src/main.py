# coding=UTF-8

import argparse
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults, PicklePersistence

import config
import infra
import init


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
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN, tzinfo=config.TIMEZONE)
    persistence = PicklePersistence(filepath=config.DB_PATH, single_file=False)
    app = Application.builder().token(config.TOKEN).defaults(defaults)\
        .persistence(persistence).arbitrary_callback_data(True).\
        post_init(init.post_init).build()
    
    # Add handlers.
    init.add_handlers(app)
    # Start the bot.
    app.run_polling()


if __name__ == "__main__":
    main()