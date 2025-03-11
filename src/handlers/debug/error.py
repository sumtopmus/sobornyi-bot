import logging
import telegram
from telegram import Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced error handler with detailed error management."""
    try:
        raise context.error
    except telegram.error.BadRequest as e:
        logger.warning(f"BadRequest: {e}")
    except telegram.error.TimedOut as e:
        logger.warning(f"TimedOut: {e}")
    except telegram.error.NetworkError as e:
        logger.error(f"NetworkError: {e}")
    except telegram.error.Forbidden as e:
        logger.error(f"Forbidden: {e}")
    except telegram.error.ChatMigrated as e:
        logger.info(f"Chat migrated to {e.new_chat_id}")
    except telegram.error.RetryAfter as e:
        logger.warning(f"RetryAfter: {e}")
    except telegram.error.InvalidToken:
        logger.critical("Invalid bot token!")
        raise SystemExit("Bot token is invalid")
    except telegram.error.PassportDecryptionError as e:
        logger.error(f"PassportDecryptionError: {e}")
    except telegram.error.Conflict as e:
        logger.error(f"Conflict: {e}")
    except telegram.error.TelegramError as e:
        logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.error(
            "Error while getting Updates:",
            exc_info=context.error,
            extra={"update": update if update else None},
        )
    finally:
        pass
