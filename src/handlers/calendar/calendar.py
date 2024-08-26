from asyncio import events
from hmac import new
from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler

from utils import log
from .event import create_handlers as event_handlers
from .menu import State, calendar_menu, construct_back_button, events_menu, update_menu


def create_handlers() -> list:
    """Creates handlers that process all calendar requests."""
    return [ConversationHandler(
        entry_points= [
            CommandHandler('calendar', calendar_menu)
        ],
        states={
            State.CALENDAR_MENU: [
                CallbackQueryHandler(on_edit_event, pattern='^' + State.EVENT_EDITING.name + '$'),
                CallbackQueryHandler(on_digest, pattern='^' + State.CALENDAR_DIGEST.name + '$'),
                CallbackQueryHandler(on_cleanup, pattern='^' + State.CALENDAR_CLEANUP.name + '$'),
            ] + event_handlers(),
            State.EVENT_PICKING: [
                CallbackQueryHandler(on_find_event, pattern='^' + State.EVENT_FINDING.name + '$'),
            ] + event_handlers(),
            State.EVENT_FINDING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, find_event),
            ],
            State.EVENT_NOT_FOUND: [
                CallbackQueryHandler(on_edit_event, pattern='^' + State.EVENT_EDITING.name + '$'),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(back, pattern='^' + State.CALENDAR_MENU.name + '$'),
            CallbackQueryHandler(exit, pattern='^' + State.EXIT.name + '$'),
            CommandHandler('cancel', cancel),
            CommandHandler('exit', exit),
        ],
        name="calendar_menu",
        persistent=True)]


async def on_edit_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    log('on_edit_event')
    await update.callback_query.answer()
    menu = events_menu(context.bot_data['calendar'].items())
    await update.callback_query.edit_message_text(**menu)
    return State.EVENT_PICKING


async def on_digest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user requests a digest of the calendar."""
    log('on_digest')
    text = context.bot_data['calendar'].get_digest()
    await update.effective_user.send_message(text, disable_web_page_preview=True)
    return await calendar_menu(update, context, new_message=True)


async def on_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user requests a cleanup of the calendar."""
    log('on_cleanup')
    context.bot_data['calendar'].remove_past_events()
    text = 'Минулі події було видалено.'
    return await calendar_menu(update, context, prefix_text=text)


async def on_find_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user presses the find button."""
    log('on_find_event')
    text = 'Введіть назву події, яку Ви хочете знайти (можна частково).'
    menu = {'text': text}
    await update_menu(update, menu)
    return State.EVENT_FINDING


async def find_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user searches for an event."""
    log('find_event')
    partial_title = update.message.text.lower()
    events = {}
    for id, event in context.bot_data['calendar'].items():
        if partial_title in event.title.lower():
            events[id] = event
    if len(events) == 0:
        text = 'Подій не знайдено.'
        await update.effective_user.send_message(text, **construct_back_button(State.EVENT_EDITING))
        return State.EVENT_NOT_FOUND
    menu = events_menu(events.items(), add_search_button=False)
    await update.effective_user.send_message(**menu)
    return State.EVENT_PICKING


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user presses the back button."""
    log('back')
    return await calendar_menu(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user cancels the action."""
    log('cancel')
    text = 'Операцію скасовано.'
    return await calendar_menu(update, context, text)


async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user exits the conversation."""
    log('exit')
    text = 'Роботу з календарем завершено.'
    menu = {'text': text}
    await update_menu(update, menu)
    context.user_data['state'] = None
    return ConversationHandler.END