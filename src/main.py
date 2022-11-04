# coding=UTF-8

import logging
import argparse

import telegram.error
from telegram.ext import Updater, Defaults

import infra
import config
from commands import info, war, welcome

# API related calls & handlers.

# Error handler.
def error(update, context):
    logging.getLogger(__name__).warning(f'Update {update} caused error {context.error}')
    try:
        raise context.error
    except telegram.error.Unauthorized:
        # remove update.message.user_id from conversation list
        pass
    except telegram.error.BadRequest:
        # handle malformed requests - read more below!
        pass
    except telegram.error.TimedOut:
        # handle slow connection problems
        pass
    except telegram.error.NetworkError:
        # handle other connection problems
        pass
    except telegram.error.ChatMigrated:
        # the user_id of a group has changed, use e.new_user_id instead
        pass
    except telegram.error.TelegramError:
        # handle all other telegram related errors
        pass

# Parse arguments.
parser = argparse.ArgumentParser(
    description='''Runs a watchman bot for Sobornyi Telegram group.''')
parser.add_argument('--debug', dest='debug', action='store_true',
                    help="Whether to run in the debug mode.")
parser.set_defaults(debug=False)
args = parser.parse_args()

# Initialize infrastructure.
config = config.Config()
infra.init(config, args.debug)

# Setup the bot.
defaults = Defaults(parse_mode='Markdown')
updater = Updater(config.TOKEN, defaults=defaults)
# Admin commands.
updater.dispatcher.add_handler(info.create_handler(config))
# General chat handling.
updater.dispatcher.add_handler(war.create_handler(config))
updater.dispatcher.add_handler(welcome.create_handler(config))
# Error handling.
updater.dispatcher.add_error_handler(error)

# Add tasks.
war.queue_morning_message(updater, config)

# Start the bot.
updater.start_polling()
updater.idle()