from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler

from utils import log
from .menu import State, construct_calendar_menu
from model import Calendar, Event


def create_handlers() -> list:
    """Creates handlers that process all calendar requests."""
    return [ConversationHandler(
        entry_points= [CommandHandler('calendar', calendar_menu)],
        states={
            State.CALENDAR_MENU: [
                CallbackQueryHandler(add_event_request, pattern="^" + State.EVENT_ADDING.name + "$"),
            ],
            State.EVENT_WAITING_FOR_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_title)
            ],
            State.EVENT_WAITING_FOR_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_date)
            ],
            State.EVENT_WAITING_FOR_OCCURRENCE: [
                CallbackQueryHandler(set_event_duration_within_day, pattern=Event.OCCURRENCE.WITHIN_DAY.name + "$"),
                CallbackQueryHandler(ask_event_date_end, pattern=Event.OCCURRENCE.WITHIN_DAYS.name + "$"),
            ],
            State.EVENT_WAITING_FOR_DATE_END: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_date_end)
            ],
            State.EVENT_WAITING_FOR_EMOJI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_emoji)
            ],
            State.EVENT_WAITING_FOR_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_url)
            ],
            State.EVENT_WAITING_FOR_IMAGE: [
                MessageHandler(filters.PHOTO, set_event_image)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(exit, pattern="^" + State.EXIT.name + "$")
        ],
        name="calendar_menu",
        persistent=True)]


async def calendar_menu(update: Update, context: CallbackContext) -> State:
    """When a user goes to the calendar menu."""
    log('calendar_menu')
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(**construct_calendar_menu())
    else:
        await update.effective_user.send_message(**construct_calendar_menu())
    context.user_data['state'] = State.CALENDAR_MENU
    return State.CALENDAR_MENU


async def add_event_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to add an event."""
    log('add_event_request')
    await update.callback_query.answer()
    message = 'Будь ласка, напишіть назву заходу чи події, які Ви хочете додати в календар.'
    await update.callback_query.edit_message_text(message)
    return State.EVENT_WAITING_FOR_TITLE


async def set_event_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the event title."""
    log('set_event_title')
    title = update.message.text
    context.bot_data['current_event'] = Event(title)
    message = 'Введіть дату заходу в форматі MM/DD/YY.'
    await update.effective_user.send_message(message)
    return State.EVENT_WAITING_FOR_DATE


async def set_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the event date."""
    log('set_event_date')
    date = update.message.text
    context.bot_data['current_event'].date = datetime.strptime(date, '%m/%d/%y')
    message = 'Як довго захід триватиме?'
    keyboard = [
        [
            InlineKeyboardButton("В межах одного дня", callback_data=Event.OCCURRENCE.WITHIN_DAY.name),
        ],
        [
            InlineKeyboardButton("В межах декількох днів", callback_data=Event.OCCURRENCE.WITHIN_DAYS.name),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(message, reply_markup=reply_markup)
    return State.EVENT_WAITING_FOR_OCCURRENCE


async def set_event_duration_within_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user chooses a single day event."""
    await update.callback_query.answer()
    context.bot_data['current_event'].occurrence = Event.OCCURRENCE.WITHIN_DAY
    return await ask_event_emoji(update, context)


async def ask_event_date_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user chooses a multiday event."""
    log('ask_event_date_end')
    date = update.message.text
    log(update.callback_query.data)
    context.bot_data['current_event'].occurrence = Event.OCCURRENCE(update.callback_query.data.split(':')[1])
    log(context.bot_data['current_event'])
    message = 'Коли захід закінчиться? Оберіть відповідний варіант або введіть дату в форматі MM/DD/YYYY.'
    keyboard = [
        [
            InlineKeyboardButton("Немає фіксованої дати", callback_data=State.EVENT_WAITING_FOR_DATE_END.name),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(message, reply_markup=reply_markup)
    return State.EVENT_WAITING_FOR_DATE_END


async def set_event_date_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the event end date."""
    log('set_event_date_end')
    date = update.message.text
    context.bot_data['current_event'].end_date = datetime.strptime(date, 'mm/dd/yyyy')
    return await ask_event_emoji(update, context)


async def ask_event_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user is asked for the event emoji."""
    log('ask_event_emoji')
    message = 'Оберіть емоджи, яке описує захід.'
    if update.callback_query:
        await update.callback_query.edit_message_text(message)
    else:
        await update.effective_user.send_message(message)
    return State.EVENT_WAITING_FOR_EMOJI


async def set_event_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the event emoji."""
    log('set_event_emoji')
    context.bot_data['current_event'].emoji = update.message.text
    message = 'Введіть посилання на захід.'
    await update.effective_user.send_message(message)
    return State.EVENT_WAITING_FOR_URL


async def set_event_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the event url."""
    log('set_event_url')
    context.bot_data['current_event'].url = update.message.text
    message = 'Надішліть постер до заходу (картинкою).'
    await update.effective_user.send_message(message)
    return State.EVENT_WAITING_FOR_IMAGE


async def set_event_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user sends the event image."""
    log('set_event_image')
    context.bot_data['current_event'].image = update.message.photo[0].file_id
    context.bot_data['calendar'].append(context.bot_data['current_event'])
    message = f'"{context.bot_data['current_event'].title}" було додано до календаря.'
    menu = construct_calendar_menu()
    menu['text'] = f"{message} {menu['text']}"
    await update.effective_user.send_message(**menu)
    return State.CALENDAR_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user cancels the conversation."""
    log('cancel')
    message = 'Операцію скасовано.'
    menu = construct_calendar_menu()
    menu['text'] = f"{message} {menu['text']}"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(**menu)
    else:
        await update.effective_user.send_message(**menu)
    return ConversationHandler.END


async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user exits the conversation."""
    log('exit')
    message = 'Роботу з календарем завершено.'
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message)
    else:
        await update.effective_user.send_message(message)
    context.user_data['state'] = None
    return ConversationHandler.END