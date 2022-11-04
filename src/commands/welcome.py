# coding=UTF-8

from telegram.ext import MessageHandler, ConversationHandler, Filters
import infra


# Creates a handler for dispatcher.
def create_handler(config):
    return ConversationHandler(
        entry_points=[MessageHandler(
            Filters.chat(config.CHAT_ID) & Filters.status_update.new_chat_members,
            welcome)],
        states={},
        fallbacks=[])


# When new user enters the chat.
def welcome(update, context):
    infra.debug('welcome', update, context)
    for user in update.message.new_chat_members:
        infra.debug(f'new user: {user.id}', update, context)
        message = (f'Cлава Україні, {infra.mention(user)}, і вітаємо тебе в Соборному! 🇺🇦✙\n'
        'У нас тут теплий і ламповий український чатик. '
        'В закріплених повідомленнях можеш знайти навігацію по Соборному мультиверсу '
        '(гештеґи, тематичні чати та инші цікавинки), '
        'а також Порядок тижневий з розкладом українських подій в DMV на цьому тижні. '
        'Ну, а поки ти знайомишся з чатиком, чатик хоче познайомитися з тобою, '
        'так що розкажи трохи про себе!')
        context.bot.sendMessage(chat_id=update.message.chat.id, text=f'{message}')
