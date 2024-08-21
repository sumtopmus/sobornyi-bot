from hmac import new
from dynaconf import settings
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ContextTypes


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
    'EVENT_PREPRINT',
    'EVENT_POSTING',
    'EVENT_DELETING',
    'EVENT_DELETING_CONFIRMATION',
    'EVENT_FINDING',
    'EVENT_WAITING_FOR_TITLE',
    'EVENT_EDITING_TITLE',
    'EVENT_EDITING_EMOJI',
    'EVENT_EDITING_DESCRIPTION',
    'EVENT_EDITING_OCCURRENCE',
    'EVENT_EDITING_DATE',
    'EVENT_EDITING_TIME',
    'EVENT_EDITING_DATE_END',
    'EVENT_EDITING_VENUE',
    'EVENT_EDITING_LOCATION',
    'EVENT_EDITING_URL',
    'EVENT_EDITING_IMAGE',
])


async def update_menu(update: Update, menu: dict):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(**menu)
    else:
        await update.effective_user.send_message(**menu)


async def calendar_menu(update: Update, context: CallbackContext, prefix_text: str = None) -> State:
    log('calendar_menu')
    text = 'Ви знаходитесь в меню редагування календаря. Що Ви хочете зробити?'
    if prefix_text:
        text = prefix_text + '\n\n' + text
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
    menu = {'text': text, 'reply_markup': reply_markup}
    await update_menu(update, menu)
    context.user_data['state'] = State.CALENDAR_MENU
    return State.CALENDAR_MENU


def events_menu(events: dict, add_search_button: bool = True) -> dict:
    sorted_events = sorted(events, key=lambda item: (item[1].date is None, item[1].date))
    ids_and_titles = [(id, event.get_title()) for id, event in sorted_events]
    back_button = InlineKeyboardButton('« Назад', callback_data=State.CALENDAR_MENU.name)
    if len(ids_and_titles) == 0:
        text = 'Жодних подій не знайдено.'
        reply_markup = InlineKeyboardMarkup([[back_button]])
        return {'text': text, 'reply_markup': reply_markup}
    text = 'Будь ласка, оберіть захід, який Ви хочете відредагувати.'
    keyboard = []
    for index, (id, title) in enumerate(ids_and_titles):
        keyboard.append([InlineKeyboardButton(title, callback_data=f'{State.EVENT.name}:{id}')])
        if index == 4:
            break
    last_row = []
    if add_search_button:
        last_row.append(InlineKeyboardButton('🔍 Пошук', callback_data=State.EVENT_FINDING.name))
    last_row.append(back_button)
    keyboard.append(last_row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'text': text, 'reply_markup': reply_markup}


async def event_menu(update: Update, context: CallbackContext, prefix_text: str = None, new_message: bool = False) -> State:
    log('event_menu')
    event = context.bot_data['current_event']
    buttons = [
        ('Емоджи', event.emoji, State.EVENT_EDITING_EMOJI),
        ('Назва', event.title, State.EVENT_EDITING_TITLE),
        ('Опис', event.description, State.EVENT_EDITING_DESCRIPTION),
        ('Формат', event.occurrence, State.EVENT_EDITING_OCCURRENCE),
        ('Дата', event.date, State.EVENT_EDITING_DATE),
        ('Час', event.time, State.EVENT_EDITING_TIME),
        ('Локація', event.venue, State.EVENT_EDITING_VENUE),
        ('Мапа', event.location, State.EVENT_EDITING_LOCATION),
        ('Посилання', event.url, State.EVENT_EDITING_URL),
        ('Постер', event.image, State.EVENT_EDITING_IMAGE),
    ]
    keyboard = []
    row = []
    for text, value, state in buttons:
        row.append(InlineKeyboardButton(text + (' ✅' if value else ' 🚫'), callback_data=state.name))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    keyboard.extend([
        [
            InlineKeyboardButton("Препрінт 🖨️", callback_data=State.EVENT_PREPRINT.name),
            InlineKeyboardButton("Пост 📺", callback_data=State.EVENT_POSTING.name),
        ],
        [
            InlineKeyboardButton("Видалити ❌", callback_data=State.EVENT_DELETING.name),
            InlineKeyboardButton("« Назад", callback_data=State.CALENDAR_MENU.name),
        ]
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = event.get_full_repr()
    if prefix_text:
        if new_message:
            text = prefix_text
        else:
            text = prefix_text + '\n\n' + text
    menu = {'text': text, 'reply_markup': reply_markup}
    if new_message:
        await update.effective_user.send_message(**menu)
    else:
        await update_menu(update, menu)
    context.user_data['state'] = State.EVENT_MENU
    return State.EVENT_MENU


def construct_back_button(state: State = State.BACK) -> dict:
    log('construct_back_button')
    keyboard = [[InlineKeyboardButton('« Назад', callback_data=state.name)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'reply_markup': reply_markup}
