from dynaconf import settings
import logging
from telegram import Update
import telegram.error
from telegram.ext import CommandHandler, ContextTypes, filters

import utils


def create_handlers() -> list:
    """Creates handlers that process admin's `topic`/`offtop` commands."""
    return [
        CommandHandler(
            'topic', topic,
            filters.Chat(settings.CHAT_ID) & filters.User(username=settings.ADMINS)),
        CommandHandler(
            'offtop', offtop,
            filters.Chat(settings.CHAT_ID) & filters.User(username=settings.ADMINS))]


async def topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to redirect discussion to a different thread."""
    utils.log('func: topic')
    if len(context.args) != 1:
        utils.log('invalid number of arguments', logging.INFO)
        return
    else:
        await offtop(update, context)


async def offtop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to redirect discussion to a different thread (offtop thread by default)."""
    utils.log('func: offtop')
    match len(context.args):
        case 0:
            destination_thread_id = settings.TOPICS['offtop']
        case 1:
            destination_thread_id = settings.TOPICS.setdefault(context.args[0], -1)
            if destination_thread_id == -1:
                utils.log(f'topic {context.args[0]} is unknown: {settings.TOPICS}', logging.INFO)
                return
        case _:
            utils.log('invalid number of arguments', logging.INFO)
            return
    await move(update, context, destination_thread_id)


async def move(update: Update, context: ContextTypes.DEFAULT_TYPE, destination_thread_id: int) -> int:
    # TODO: remove before commit
    if settings.DEBUG:
        destination_thread_id = None
    original_message = update.message.reply_to_message
    user = original_message.from_user
    message = f'{utils.mention(user)}, вас було переміщено у відповідну гілку.'
    if destination_thread_id != settings.TOPICS['welcome']:
        message += '\n\n⬇️ продовжуйте дискусію тут ⬇️'
    else:
        message += '\n\n⬇️ представтеся тут ⬇️'
    await context.bot.sendMessage(
        chat_id=settings.CHAT_ID, message_thread_id=destination_thread_id,
        text=message)
    try:
        if original_message.has_protected_content:
            raise telegram.error.Forbidden(f'the message has protected content and can\'t be forwarded: {original_message.text}')
        moved_message_id = await original_message.forward(
            settings.CHAT_ID, message_thread_id=destination_thread_id)
    except:
        message = f'{utils.mention(user)} написав(-ла):'
        await context.bot.sendMessage(
            chat_id=settings.CHAT_ID, message_thread_id=destination_thread_id,
            text=message)
        moved_message_id = await original_message.copy(
            settings.CHAT_ID, message_thread_id=destination_thread_id)
    await update.message.delete()
    await original_message.delete()
    return moved_message_id