from enum import Enum
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler, TypeHandler

from config import settings
from utils import log


State = Enum('State', ['AWAITING'])


def create_handlers() -> list:
    """Creates handlers that process new users."""
    return [ConversationHandler(
        entry_points=[CommandHandler('upload', on_upload, filters.User(username=settings.ADMINS))],
        states={
            State.AWAITING: [MessageHandler(filters.PHOTO, upload)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        conversation_timeout=settings.CONVERSATION_TIMEOUT,
        name="upload",
        per_chat=False)]


async def on_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user uses /upload command."""
    log('on_upload')
    message = 'Будь ласка, завантажте фото.'
    await update.effective_user.send_message(message)
    return State.AWAITING


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user uploads a photo."""
    log('upload')
    photos = update.message.photo
    for photo in photos:
        log(photo)
    message = 'Фото було додано в базу даних.'
    await update.effective_user.send_message(message)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user cancels the conversation."""
    log('cancel')
    message = 'Операцію скасовано.'
    await update.effective_user.send_message(message)
    return ConversationHandler.END


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When the conversation timepout is exceeded."""
    log('timeout')
    message = 'Запит скасовано автоматично через таймаут.'
    await update.effective_user.send_message(message)
    return ConversationHandler.END