from dynaconf import settings
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


from model import Calendar, Event
from utils import log


State = Enum('State', [
    # Menu state:
    'CALENDAR_MENU',
    'EVENT_MENU',
    'BACK',
    'EXIT',
    # Prefix states:
    'EVENT',
    # Process states:
    'EVENT_ADDING',
    'EVENT_EDITING',
    'EVENT_PICKING',
    'EVENT_DELETING',
    'EVENT_FINDING',
    'EVENT_WAITING_FOR_TITLE',
    'EVENT_WAITING_FOR_DATE',
    'EVENT_WAITING_FOR_OCCURRENCE',
    'EVENT_WAITING_FOR_DATE_END',
    'EVENT_WAITING_FOR_TIME',
    'EVENT_WAITING_FOR_EMOJI',
    'EVENT_WAITING_FOR_URL',
    'EVENT_WAITING_FOR_IMAGE',
    'EVENT_EDITING_TITLE',
    'EVENT_EDITING_EMOJI',
    'EVENT_EDITING_DESCRIPTION',
    'EVENT_EDITING_OCCURRENCE',
    'EVENT_EDITING_DATE',
    'EVENT_EDITING_TIME',
    'EVENT_EDITING_DATE_END',
    'EVENT_EDITING_URL',
    'EVENT_EDITING_IMAGE',
])


def construct_calendar_menu() -> dict:
    log('construct_calendar_menu')
    text = 'Ви знаходитесь в меню редагування календаря. Що Ви хочете зробити?'
    keyboard = [
        [
            InlineKeyboardButton("Додати подію", callback_data=State.EVENT_ADDING.name),
            InlineKeyboardButton("Редагувати подію", callback_data=State.EVENT_EDITING.name),
        ],
        [
            InlineKeyboardButton("« Вийти", callback_data=State.EXIT.name),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'text': text, 'reply_markup': reply_markup}


def construct_events_menu(context: ContextTypes.DEFAULT_TYPE) -> dict:
    log('construct_events_menu')
    text = 'Будь ласка, оберіть захід, який Ви хочете відредагувати.'
    events = sorted(context.bot_data.get('calendar', {}), key=lambda x: x.date)
    titles = [event.title for event in events]
    back_button = InlineKeyboardButton('« Назад', callback_data=State.CALENDAR_MENU.name)
    if len(titles) == 0:
        reply_markup = InlineKeyboardMarkup([[back_button]])
        return {'text': 'Жодних подій не знайдено.', 'reply_markup': reply_markup}
    keyboard = []
    for index, title in enumerate(titles):
        keyboard.append([InlineKeyboardButton(title, callback_data=f'{State.EVENT.name}:{title}')])
        if index == 4:
            break
    keyboard.append([
        InlineKeyboardButton('🔍 Пошук', callback_data=State.EVENT_FINDING.name),
        back_button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'text': text, 'reply_markup': reply_markup}


def construct_event_menu(event: Event) -> dict:
    log('construct_event_menu')
    log(event)
    menu = {}
    if event.image:
        menu['photo'] = event.image
    else:
        menu['photo'] = settings.missing_poster
    menu['caption'] = event.get_full_repr()
    keyboard = [
        [
            InlineKeyboardButton('Емоджи', callback_data=State.EVENT_EDITING_EMOJI.name),
            InlineKeyboardButton('Назва', callback_data=State.EVENT_EDITING_TITLE.name),
        ],
        [
            InlineKeyboardButton('Опис', callback_data=State.EVENT_EDITING_DESCRIPTION.name),
            InlineKeyboardButton('Формат', callback_data=State.EVENT_EDITING_OCCURRENCE.name),
        ],
        [
            InlineKeyboardButton('Дата', callback_data=State.EVENT_EDITING_DATE.name),
            InlineKeyboardButton('Час', callback_data=State.EVENT_EDITING_TIME.name),
        ],
        [
            InlineKeyboardButton('Посилання', callback_data=State.EVENT_EDITING_URL.name),
            InlineKeyboardButton('Постер', callback_data=State.EVENT_EDITING_IMAGE.name),
        ],
        [
            InlineKeyboardButton("Видалити ❌", callback_data=State.EVENT_DELETING.name),
            InlineKeyboardButton("« Back", callback_data=State.CALENDAR_MENU.name),
        ]
    ]        
    menu['reply_markup'] = InlineKeyboardMarkup(keyboard)
    return menu


async def event_menu(update: Update, context: CallbackContext):
    log('event_menu')
    event = context.bot_data['current_event']
    menu = construct_event_menu(event)
    if update.callback_query:
        await update.callback_query.answer()
        if update.callback_query.message.photo != event.image:
            log('deleting message')
            await update.callback_query.delete_message()
            await update.effective_user.send_photo(**menu)
        else:
            log('replacing text and keyboard, keeping image')
            await update.callback_query.edit_message_text(**menu)
    else:
        log('sending new photo message')
        await update.effective_user.send_photo(**menu)
    context.user_data['state'] = State.EVENT_MENU
    return State.EVENT_MENU


def construct_back_button(state: State = State.BACK) -> dict:
    log('construct_back_button')
    keyboard = [[InlineKeyboardButton('« Назад', callback_data=state.name)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'reply_markup': reply_markup}
