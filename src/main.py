# coding=UTF-8

import argparse
from telegram.ext import Application, Defaults, PicklePersistence

from handlers import debug, error, info, request, war, welcome
import config
import infra


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
    defaults = Defaults(parse_mode='Markdown', tzinfo=config.TIMEZONE)
    persistence = PicklePersistence(filepath=config.DB_PATH, single_file=False)
    app = Application.builder().token(config.TOKEN).defaults(defaults)\
        .persistence(persistence).arbitrary_callback_data(True).build()
    # Error handler.
    app.add_error_handler(error.handler)
    # Admin commands.
    for module in [debug, info]:
        app.add_handlers(module.create_handlers())
    # General chat handling.
    for module in [request, welcome, war]:
        app.add_handlers(module.create_handlers())

    # Initialize tasks.
    war.init(app)

    # Start the bot.
    app.run_polling()


if __name__ == "__main__":
    main()