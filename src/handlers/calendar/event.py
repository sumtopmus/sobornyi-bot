from datetime import datetime, time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler

from utils import log
from .menu import State, construct_calendar_menu, event_menu, construct_back_button
from model import Calendar, Event, Occurrence


def create_handlers() -> list:
    """Creates handlers that process all event editing requests."""
    return [ConversationHandler(
        entry_points= [
            CallbackQueryHandler(event_menu_entry, pattern="^" + State.EVENT.name)
        ],
        states={
            State.EVENT_MENU: [
                CallbackQueryHandler(on_edit_title, pattern="^" + State.EVENT_EDITING_TITLE.name + "$"),
                CallbackQueryHandler(on_edit_emoji, pattern="^" + State.EVENT_EDITING_EMOJI.name + "$"),
                CallbackQueryHandler(on_edit_description, pattern="^" + State.EVENT_EDITING_DESCRIPTION.name + "$"),
                CallbackQueryHandler(on_edit_occurrence, pattern="^" + State.EVENT_EDITING_OCCURRENCE.name + "$"),
                CallbackQueryHandler(on_edit_date, pattern="^" + State.EVENT_EDITING_DATE.name + "$"),
                # CallbackQueryHandler(on_edit_date_end, pattern="^" + State.EVENT_EDITING_DATE_END.name + "$"),
                CallbackQueryHandler(on_edit_time, pattern="^" + State.EVENT_EDITING_TIME.name + "$"),
                CallbackQueryHandler(on_edit_url, pattern="^" + State.EVENT_EDITING_URL.name + "$"),
                CallbackQueryHandler(on_edit_image, pattern="^" + State.EVENT_EDITING_IMAGE.name + "$"),
                CallbackQueryHandler(back, pattern="^" + State.CALENDAR_MENU.name + "$"),
            ],
            State.EVENT_EDITING_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_title),
            ],
            State.EVENT_EDITING_EMOJI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_emoji),
            ],
            State.EVENT_EDITING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_description),
            ],       
            State.EVENT_EDITING_OCCURRENCE: [
                CallbackQueryHandler(edit_occurrence, pattern="^" + Occurrence.WITHIN_DAY.name + "$"),
                CallbackQueryHandler(edit_occurrence, pattern="^" + Occurrence.WITHIN_DAYS.name + "$"),
            ],
            State.EVENT_EDITING_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_date),
            ],
            # State.EVENT_EDITING_DATE_END: [
            #     MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_date_end),
            #     CallbackQueryHandler(set_event_date_end, pattern=Occurrence.WITHIN_DAYS.name + "$"),
            # ],
            State.EVENT_EDITING_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_time),
            ],
            State.EVENT_EDITING_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_url),
            ],
            State.EVENT_EDITING_IMAGE: [
                MessageHandler(filters.PHOTO, edit_image),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(cancel, pattern="^" + State.EVENT_MENU.name + "$"),
            CallbackQueryHandler(exit, pattern="^" + State.EXIT.name + "$")
        ],
        map_to_parent={
            State.CALENDAR_MENU: State.CALENDAR_MENU,
        },
        name="event_menu",
        persistent=True)]


async def event_menu_entry(update: Update, context: CallbackContext) -> State:
    """When a user goes to the event editing menu."""
    log('event_menu')
    title = update.callback_query.data.split(':')[-1]
    event = context.bot_data['calendar'].get_event_by_title(title)
    context.bot_data['current_event'] = event
    return await event_menu(update, context)


async def on_edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the title."""
    log('on_edit_title')
    await update.callback_query.answer()
    message = 'Будь ласка, вкажіть назву заходу:'
    await update.callback_query.edit_message_caption(message, **construct_back_button(State.EVENT_MENU))
    return State.EVENT_EDITING_TITLE


async def edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the title."""
    log('edit_title')
    context.bot_data['current_event'].title = update.message.text
    return await event_menu(update, context)


async def on_edit_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the emoji."""
    log('on_edit_emoji')
    await update.callback_query.answer()
    message = 'Будь ласка, вкажіть емоджи, яке символізує цей захід:'
    await update.callback_query.edit_message_caption(message, **construct_back_button(State.EVENT_MENU))
    return State.EVENT_EDITING_EMOJI


async def edit_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the emoji."""
    log('edit_emoji')
    context.bot_data['current_event'].emoji = update.message.text
    return await event_menu(update, context)


async def on_edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the description."""
    log('on_edit_description')
    await update.callback_query.answer()
    message = 'Будь ласка, вкажіть більш детальний опис цього заходу:'
    await update.callback_query.edit_message_caption(message, **construct_back_button(State.EVENT_MENU))
    return State.EVENT_EDITING_DESCRIPTION


async def edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the description."""
    log('edit_description')
    context.bot_data['current_event'].description = update.message.text
    return await event_menu(update, context)


async def on_edit_occurrence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the occurrence."""
    log('on_edit_occurrence')
    await update.callback_query.answer()
    message = 'Як довго захід триватиме?'
    keyboard = [
        [
            InlineKeyboardButton("В межах одного дня", callback_data=Occurrence.WITHIN_DAY.name),
        ],
        [
            InlineKeyboardButton("В межах декількох днів", callback_data=Occurrence.WITHIN_DAYS.name),
        ],
        [
            InlineKeyboardButton('« Назад', callback_data=State.EVENT_MENU.name),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_caption(message, reply_markup=reply_markup)
    return State.EVENT_EDITING_OCCURRENCE


async def edit_occurrence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the occurrence."""
    log('edit_occurrence')
    context.bot_data['current_event'].occurrence = Occurrence[update.callback_query.data]
    return await event_menu(update, context)


async def on_edit_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the date."""
    log('on_edit_date')
    await update.callback_query.answer()
    message = 'Введіть дату заходу в форматі MM/DD/YY:'
    await update.callback_query.edit_message_caption(message, **construct_back_button(State.EVENT_MENU))
    return State.EVENT_EDITING_DATE


async def edit_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the date."""
    log('edit_date')
    context.bot_data['current_event'].date = datetime.strptime(update.message.text, '%m/%d/%y')
    return await event_menu(update, context)


async def on_edit_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the time."""
    log('on_edit_time')
    await update.callback_query.answer()
    message = 'Введіть час початку заходу в 24-годинному форматі HH:MM:'
    await update.callback_query.edit_message_caption(message, **construct_back_button(State.EVENT_MENU))
    return State.EVENT_EDITING_TIME


async def edit_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the time."""
    log('edit_time')
    context.bot_data['current_event'].time = datetime.strptime(update.message.text, '%H:%M').time()
    return await event_menu(update, context)


async def on_edit_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the URL."""
    log('on_edit_url')
    await update.callback_query.answer()
    message = 'Будь ласка, вкажіть посилання на цей захід:'
    await update.callback_query.edit_message_caption(message, **construct_back_button(State.EVENT_MENU))
    return State.EVENT_EDITING_URL


async def edit_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the url."""
    log('edit_url')
    context.bot_data['current_event'].url = update.message.text
    return await event_menu(update, context)



async def on_edit_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the poster."""
    log('on_edit_image')
    await update.callback_query.answer()
    message = 'Будь ласка, надішліть постер для цього заходу (картинкою):'
    await update.callback_query.edit_message_caption(message, **construct_back_button(State.EVENT_MENU))
    return State.EVENT_EDITING_IMAGE


async def edit_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user enters the image."""
    log('edit_image')
    context.bot_data['current_event'].image = update.message.photo[0].file_id
    return await event_menu(update, context)


async def back(update: Update, context: CallbackContext) -> State:
    """When a user presses the back button."""
    log('back')
    # TODO: save event
    # old_event = context.bot_data['calendar'].get_event_by_title(context.bot_data['current_event'].title)
    # old_event = context.bot_data['current_event']
    menu = construct_calendar_menu()
    if update.callback_query:
        await update.callback_query.answer()
        if update.callback_query.message.photo:
            log('deleting message')
            await update.callback_query.delete_message()
            await update.effective_user.send_message(**menu)
        else:
            log('replacing text and keyboard, keeping image')
            await update.callback_query.edit_message_text(**menu)
    else:
        log('sending new text message')
        await update.effective_user.send_message(**menu)
    context.user_data['state'] = State.CALENDAR_MENU
    return State.CALENDAR_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user cancels the conversation."""
    log('cancel')
    return await event_menu(update, context)


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