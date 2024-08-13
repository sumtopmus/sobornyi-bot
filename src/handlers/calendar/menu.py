from dynaconf import settings
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from model import Calendar
from utils import log


State = Enum('State', [
    # Menu state:
    'CALENDAR_MENU',
    'BACK',
    'EXIT',
    # Prefix states:
    'EVENT',
    # Process states:
    'EVENT_ADDING',
    'EVENT_EDITING',
    'EVENT_PICKING',
    'EVENT_FINDING',
    'EVENT_WAITING_FOR_TITLE',
    'EVENT_WAITING_FOR_DATE',
    'EVENT_WAITING_FOR_OCCURRENCE',
    'EVENT_WAITING_FOR_DATE_END',
    'EVENT_WAITING_FOR_TIME',
    'EVENT_WAITING_FOR_EMOJI',
    'EVENT_WAITING_FOR_URL',
    'EVENT_WAITING_FOR_IMAGE',
])


def construct_calendar_menu() -> dict:
    log('construct_calendar_menu')
    text = 'Що Ви хочете зробити?'
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
    log(titles)
    back_button = InlineKeyboardButton('« Назад', callback_data=State.CALENDAR_MENU.name)
    if len(titles) == 0:
        reply_markup = InlineKeyboardMarkup([[back_button]])
        return {'text': 'Жодних подій не знайдено.', 'reply_markup': reply_markup}
    keyboard = []
    for index, title in enumerate(titles):
        keyboard.append([InlineKeyboardButton(title, callback_data=f'{State.EVENT.name}/{title}')])
        if index == 4:
            break
    keyboard.append([
        InlineKeyboardButton('🔍 Пошук', callback_data=State.EVENT_FINDING.name),
        back_button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    log(keyboard)
    return {'text': text, 'reply_markup': reply_markup}


def construct_back_button(text: str, context: ContextTypes.DEFAULT_TYPE, state: State = State.BACK) -> dict:
    log('construct_back_button')
    keyboard = [[InlineKeyboardButton('« Назад', callback_data=state.name)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'text': text, 'reply_markup': reply_markup}
