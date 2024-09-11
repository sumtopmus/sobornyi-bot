import logging
from telegram import Update
import telegram.error
from telegram.ext import ContextTypes


def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Error handler."""
    logging.getLogger(__name__).error(
        f"Exception while handling the update {update}:", exc_info=context.error
    )
    # TODO: add actual error handling.
    try:
        raise context.error
    except telegram.error.BadRequest:
        # handle malformed requests
        pass
    except telegram.error.ChatMigrated:
        # handle migrated chats (use error.new_user_id instead)
        pass
    except telegram.error.Conflict:
        # handle conflicting long polls/webhooks
        pass
    except telegram.error.Forbidden:
        # handle actions that bot do not have rights to perform
        pass
    except telegram.error.InvalidToken:
        # handle invalid token case
        pass
    except telegram.error.TimedOut:
        # handle slow connection problems
        pass
    except telegram.error.NetworkError:
        # handle other connection problems
        pass
    except telegram.error.PassportDecryptionError:
        # handle problems with decryption
        pass
    except telegram.error.RetryAfter:
        # handle the exceeded flood limits
        pass
    except telegram.error.TelegramError:
        # handle all other telegram related errors
        pass
