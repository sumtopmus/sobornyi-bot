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
        ],
        [
            InlineKeyboardButton("« Вийти", callback_data=State.EXIT.name),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'text': text, 'reply_markup': reply_markup}


def construct_back_button(text: str, context: ContextTypes.DEFAULT_TYPE, state: State = State.BACK) -> dict:
    log('construct_back_button')
    keyboard = [[InlineKeyboardButton('« Назад', callback_data=state.name)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'text': text, 'reply_markup': reply_markup}
