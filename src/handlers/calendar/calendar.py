from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

from config import settings
from utils import log

from .agenda import publish_agenda_on_demand, sync_agenda
from .event import create_handlers as event_handlers
from .menu import State, calendar_menu, construct_back_button, events_menu, update_menu


def create_handlers() -> list:
    """Creates handlers that process all calendar requests."""
    return [
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    "calendar",
                    calendar_menu,
                    filters.User(username=settings.ADMINS + settings.MODERATORS),
                )
            ],
            states={
                State.CALENDAR_MENU: [
                    CallbackQueryHandler(
                        on_edit_event, pattern="^" + State.EVENT_EDITING.name + "$"
                    ),
                    CallbackQueryHandler(
                        on_edit_image,
                        pattern="^" + State.AGENDA_EDITING_IMAGE.name + "$",
                    ),
                    CallbackQueryHandler(
                        on_agenda_preview, pattern="^" + State.AGENDA_PREVIEW.name + "$"
                    ),
                    CallbackQueryHandler(
                        on_agenda_urls, pattern="^" + State.AGENDA_URLS.name + "$"
                    ),
                    CallbackQueryHandler(
                        on_cleanup, pattern="^" + State.CALENDAR_CLEANUP.name + "$"
                    ),
                ]
                + event_handlers(),
                State.EVENT_PICKING: [
                    CallbackQueryHandler(
                        on_find_event, pattern="^" + State.EVENT_FINDING.name + "$"
                    ),
                ]
                + event_handlers(),
                State.EVENT_FINDING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, find_event),
                ],
                State.EVENT_NOT_FOUND: [
                    CallbackQueryHandler(
                        on_edit_event, pattern="^" + State.EVENT_EDITING.name + "$"
                    ),
                ],
                State.AGENDA_EDITING_IMAGE: [
                    MessageHandler(filters.PHOTO, edit_image),
                ],
                State.AGENDA_PREVIEW: [
                    CallbackQueryHandler(
                        on_agenda_publish,
                        pattern="^" + State.AGENDA_PUBLISHING.name + "$",
                    ),
                ],
                ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)],
            },
            fallbacks=[
                CallbackQueryHandler(
                    back, pattern="^" + State.CALENDAR_MENU.name + "$"
                ),
                CallbackQueryHandler(exit, pattern="^" + State.EXIT.name + "$"),
                CommandHandler("cancel", cancel),
                CommandHandler("exit", exit),
            ],
            allow_reentry=True,
            conversation_timeout=settings.CONVERSATION_TIMEOUT,
            name="calendar_menu",
            persistent=True,
        )
    ]


async def on_edit_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    log("on_edit_event")
    await update.callback_query.answer()
    menu = events_menu(context.bot_data["calendar"].items())
    await update.callback_query.edit_message_text(**menu)
    return State.EVENT_PICKING


async def on_edit_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user wants to edit the image for the agenda."""
    log("on_edit_image")
    await update.callback_query.answer()
    text = "Будь ласка, завантажте фото (картинкою)."
    await update.callback_query.edit_message_text(text)
    return State.AGENDA_EDITING_IMAGE


async def edit_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user uploads a photo."""
    log("edit_image")
    context.bot_data["agenda"]["image"] = update.message.photo[-1].file_id
    return await calendar_menu(update, context)


async def on_agenda_preview(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> State:
    """When a user requests to preview the agenda of the current week."""
    log("on_agenda_preview")
    await update.callback_query.answer()
    text = context.bot_data["calendar"].get_agenda()
    image = context.bot_data["agenda"]["image"]
    if image:
        await update.effective_user.send_photo(image, text)
    else:
        await update.effective_user.send_photo(settings.DEFAULT_AGENDA_IMAGE, text)
    text = f"Так виглядатиме порядок тижневий. Якщо все вірно, Ви можете опублікувати його."
    keyboard = [
        [
            InlineKeyboardButton(
                "📺 Publish", callback_data=State.AGENDA_PUBLISHING.name
            ),
            InlineKeyboardButton("🔙", callback_data=State.CALENDAR_MENU.name),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(text, reply_markup=reply_markup)
    return State.AGENDA_PREVIEW


async def on_agenda_publish(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> State:
    """When a user requests to publish the agenda."""
    log("on_agenda_publish")
    await update.callback_query.answer()
    await publish_agenda_on_demand(update, context)
    text = "Порядок тижневий було опубліковано."
    return await calendar_menu(update, context, prefix_text=text)


async def on_agenda_urls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user requests to see the agenda URLs."""
    log("on_agenda_urls")
    await update.callback_query.answer()
    text = context.bot_data["calendar"].get_agenda_as_urls()
    if text:
        await update.effective_user.send_message(text)
        text = "Готово ⬆️"
    return await calendar_menu(update, context, prefix_text=text, new_message=True)


async def on_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user requests a cleanup of the calendar."""
    log("on_cleanup")
    context.bot_data["calendar"].remove_past_events()
    await sync_agenda(context)
    text = "Минулі події було видалено та порядок оновлено."
    return await calendar_menu(update, context, prefix_text=text)


async def on_find_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user presses the find button."""
    log("on_find_event")
    text = "Введіть назву події, яку Ви хочете знайти (можна частково)."
    menu = {"text": text}
    await update_menu(update, menu)
    return State.EVENT_FINDING


async def find_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user searches for an event."""
    log("find_event")
    partial_title = update.message.text.lower()
    events = {}
    for id, event in context.bot_data["calendar"].items():
        if partial_title in event.title.lower():
            events[id] = event
    if len(events) == 0:
        text = "Подій не знайдено."
        await update.effective_user.send_message(
            text, **construct_back_button(State.EVENT_EDITING)
        )
        return State.EVENT_NOT_FOUND
    menu = events_menu(events.items(), add_search_button=False)
    await update.effective_user.send_message(**menu)
    return State.EVENT_PICKING


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user presses the back button."""
    log("back")
    return await calendar_menu(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user cancels the action."""
    log("cancel")
    text = "Операцію скасовано."
    return await calendar_menu(update, context, text)


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When the conversation timepout is exceeded."""
    log("timeout")
    await sync_agenda(context)
    text = "Ви були неактивні протягом 15 хвилин. Роботу з календарем завершено автоматично."
    menu = {"text": text}
    if update.callback_query:
        await update.callback_query.edit_message_text(**menu)
    else:
        await update.effective_user.send_message(**menu, disable_notification=True)
    context.user_data["state"] = None
    return ConversationHandler.END


async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user exits the conversation."""
    log("exit")
    await sync_agenda(context)
    text = "Роботу з календарем завершено."
    menu = {"text": text}
    await update_menu(update, menu)
    context.user_data["state"] = None
    return ConversationHandler.END
