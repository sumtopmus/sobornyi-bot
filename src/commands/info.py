from telegram.ext import CommandHandler, ConversationHandler, Filters
import infra


# Creates a handler for dispatcher.
def create_handler(config):
    return ConversationHandler(
        entry_points=[CommandHandler('info', info, Filters.user(config.ADMIN_ID))],
        states={},
        fallbacks=[])

# Basic admin info command.
def info(update, context):
    infra.debug('info', update, context)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    infra.debug(f'chat_id: {chat_id}', update, context)
    infra.debug(f'user_id: {user_id}', update, context)